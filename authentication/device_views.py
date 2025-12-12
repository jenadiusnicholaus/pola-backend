# authentication/device_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q

from .device_models import UserDevice, UserSession, LoginHistory, SecurityAlert
from .device_serializers import (
    UserDeviceSerializer, RegisterDeviceSerializer, UserSessionSerializer,
    LoginHistorySerializer, SecurityAlertSerializer, LocationUpdateSerializer
)
from .device_utils import (
    get_client_ip, parse_user_agent, get_location_from_ip,
    generate_device_fingerprint, detect_suspicious_activity,
    create_security_alert, calculate_session_expiry
)


class UserDeviceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user devices
    
    list: Get all devices for the authenticated user
    retrieve: Get specific device details
    create: Register a new device
    update: Update device information
    destroy: Remove a device
    """
    serializer_class = UserDeviceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter devices by authenticated user"""
        return UserDevice.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Register a new device"""
        serializer = RegisterDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        device_data = serializer.validated_data
        device_id = device_data['device_id']
        
        # Get IP and location
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        location_data = get_location_from_ip(ip_address)
        
        # Parse user agent if device info not provided
        ua_data = parse_user_agent(user_agent)
        
        # Merge data (client data takes precedence)
        for key, value in ua_data.items():
            if key not in device_data or not device_data.get(key):
                device_data[key] = value
        
        # Check if this exact device already exists for this user
        existing_device = UserDevice.objects.filter(
            user=request.user,
            device_id=device_id
        ).first()
        
        if existing_device:
            # Device already registered in DB - update and return
            existing_device.device_name = device_data.get('device_name', existing_device.device_name)
            existing_device.fcm_token = device_data.get('fcm_token', existing_device.fcm_token)
            existing_device.app_version = device_data.get('app_version', existing_device.app_version)
            existing_device.last_ip = ip_address
            existing_device.is_active = True
            existing_device.save()
            
            serializer = UserDeviceSerializer(existing_device, context={'request': request})
            return Response({
                'is_registered': True,
                'device': serializer.data,
                'message': 'Device already registered'
            }, status=status.HTTP_200_OK)
        
        # Check if user has other devices registered
        user_has_devices = UserDevice.objects.filter(user=request.user).exists()
        
        if user_has_devices:
            # User has existing devices, new device requires verification
            # Device NOT stored in DB yet, so is_registered = false
            return Response({
                'is_registered': False,
                'requires_verification': True,
                'reason': 'new_device',
                'message': 'New device detected. Please verify this device to continue.',
                'device_info': {
                    'device_id': device_id,
                    'device_name': device_data.get('device_name', ''),
                    'device_type': device_data.get('device_type', 'unknown'),
                    'device_model': device_data.get('device_model', ''),
                    'os_name': device_data.get('os_name', 'unknown'),
                    'location': f"{location_data.get('city', 'Unknown')}, {location_data.get('country', 'Unknown')}",
                    'ip_address': ip_address,
                }
            }, status=status.HTTP_202_ACCEPTED)
        
        # First device - register without verification and save to DB
        device = UserDevice.objects.create(
            user=request.user,
            device_id=device_id,
            device_name=device_data.get('device_name', ''),
            device_type=device_data.get('device_type', 'unknown'),
            os_name=device_data.get('os_name', 'unknown'),
            os_version=device_data.get('os_version', ''),
            browser_name=device_data.get('browser_name', ''),
            browser_version=device_data.get('browser_version', ''),
            app_version=device_data.get('app_version', ''),
            device_model=device_data.get('device_model', ''),
            device_manufacturer=device_data.get('device_manufacturer', ''),
            fcm_token=device_data.get('fcm_token', ''),
            last_ip=ip_address,
            is_active=True,
        )
        
        serializer = UserDeviceSerializer(device, context={'request': request})
        return Response({
            'is_registered': True,
            'device': serializer.data,
            'message': 'First device registered successfully'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def trust(self, request, pk=None):
        """Mark device as trusted"""
        device = self.get_object()
        device.is_trusted = True
        device.save()
        
        serializer = self.get_serializer(device)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def untrust(self, request, pk=None):
        """Mark device as untrusted"""
        device = self.get_object()
        device.is_trusted = False
        device.save()
        
        serializer = self.get_serializer(device)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a device"""
        device = self.get_object()
        device.is_active = False
        device.save()
        
        # Terminate all sessions for this device
        UserSession.objects.filter(
            device=device,
            status='active'
        ).update(
            status='terminated',
            logout_time=timezone.now()
        )
        
        return Response({
            'message': 'Device deactivated successfully',
            'device_id': device.device_id
        })
    
    @action(detail=False, methods=['post'])
    def verify_and_register(self, request):
        """Verify and register a new device after user confirmation"""
        serializer = RegisterDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        device_data = serializer.validated_data
        device_id = device_data['device_id']
        
        # Get IP and location
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        location_data = get_location_from_ip(ip_address)
        
        # Parse user agent if device info not provided
        ua_data = parse_user_agent(user_agent)
        
        # Merge data (client data takes precedence)
        for key, value in ua_data.items():
            if key not in device_data or not device_data.get(key):
                device_data[key] = value
        
        # Check if device already exists
        existing_device = UserDevice.objects.filter(
            user=request.user,
            device_id=device_id
        ).first()
        
        if existing_device:
            return Response({
                'error': 'Device already registered',
                'device_id': device_id
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create the new verified device
        device = UserDevice.objects.create(
            user=request.user,
            device_id=device_id,
            device_name=device_data.get('device_name', ''),
            device_type=device_data.get('device_type', 'unknown'),
            os_name=device_data.get('os_name', 'unknown'),
            os_version=device_data.get('os_version', ''),
            browser_name=device_data.get('browser_name', ''),
            browser_version=device_data.get('browser_version', ''),
            app_version=device_data.get('app_version', ''),
            device_model=device_data.get('device_model', ''),
            device_manufacturer=device_data.get('device_manufacturer', ''),
            fcm_token=device_data.get('fcm_token', ''),
            last_ip=ip_address,
            is_active=True,
            is_trusted=True,  # Auto-trust verified devices
        )
        
        # Create security alert for new device
        create_security_alert(
            user=request.user,
            alert_type='new_device',
            title='New Device Verified and Added',
            message=f'A new device was verified and added to your account: {device.device_name or device.device_model or device_id[:8]}',
            severity='low',
            device=device,
            details={
                'ip_address': ip_address,
                'location': f"{location_data.get('city', 'Unknown')}, {location_data.get('country', 'Unknown')}",
                'device_info': {
                    'type': device.device_type,
                    'os': device.os_name,
                    'model': device.device_model,
                },
                'verified': True,
            }
        )
        
        serializer = UserDeviceSerializer(device, context={'request': request})
        return Response({
            'device': serializer.data,
            'message': 'Device verified and registered successfully'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def update_location(self, request):
        """Update current device location"""
        serializer = LocationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        device_id = request.data.get('device_id')
        if not device_id:
            return Response(
                {'error': 'device_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            device = UserDevice.objects.get(
                user=request.user,
                device_id=device_id
            )
            device.mark_as_seen(get_client_ip(request))
            
            return Response({
                'message': 'Location updated successfully',
                'device_id': device.device_id
            })
        except UserDevice.DoesNotExist:
            return Response(
                {'error': 'Device not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class UserSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing user sessions
    
    list: Get all sessions for the authenticated user
    retrieve: Get specific session details
    """
    serializer_class = UserSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter sessions by authenticated user"""
        return UserSession.objects.filter(
            user=self.request.user
        ).select_related('device')
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active sessions"""
        sessions = self.get_queryset().filter(status='active')
        serializer = self.get_serializer(sessions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def terminate(self, request, pk=None):
        """Terminate a specific session"""
        session = self.get_object()
        
        if session.status == 'active':
            session.terminate()
            return Response({
                'message': 'Session terminated successfully',
                'session_id': session.id
            })
        else:
            return Response(
                {'error': f'Session is already {session.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def terminate_all(self, request):
        """Terminate all sessions except current"""
        current_session_key = request.session.session_key
        
        terminated_count = UserSession.objects.filter(
            user=request.user,
            status='active'
        ).exclude(
            session_key=current_session_key
        ).update(
            status='terminated',
            logout_time=timezone.now()
        )
        
        return Response({
            'message': f'Terminated {terminated_count} session(s)',
            'count': terminated_count
        })


class LoginHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing login history
    
    list: Get all login attempts for the authenticated user
    retrieve: Get specific login attempt details
    """
    serializer_class = LoginHistorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter login history by authenticated user"""
        return LoginHistory.objects.filter(
            Q(user=self.request.user) | Q(email=self.request.user.email)
        )
    
    @action(detail=False, methods=['get'])
    def failed(self, request):
        """Get only failed login attempts"""
        failed = self.get_queryset().filter(status='failed')
        serializer = self.get_serializer(failed, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def suspicious(self, request):
        """Get only suspicious login attempts"""
        suspicious = self.get_queryset().filter(is_suspicious=True)
        serializer = self.get_serializer(suspicious, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get login statistics"""
        queryset = self.get_queryset()
        
        total = queryset.count()
        successful = queryset.filter(status='success').count()
        failed = queryset.filter(status='failed').count()
        suspicious = queryset.filter(is_suspicious=True).count()
        
        # Get unique locations
        locations = queryset.values('country', 'city').distinct().count()
        
        # Get unique IPs
        unique_ips = queryset.values('ip_address').distinct().count()
        
        return Response({
            'total_attempts': total,
            'successful_logins': successful,
            'failed_attempts': failed,
            'suspicious_attempts': suspicious,
            'unique_locations': locations,
            'unique_ip_addresses': unique_ips,
            'success_rate': round((successful / total * 100) if total > 0 else 0, 2)
        })


class SecurityAlertViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing security alerts
    
    list: Get all security alerts for the authenticated user
    retrieve: Get specific alert details
    update: Mark alert as read/resolved
    """
    serializer_class = SecurityAlertSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch', 'delete']
    
    def get_queryset(self):
        """Filter alerts by authenticated user"""
        return SecurityAlert.objects.filter(
            user=self.request.user
        ).select_related('device', 'session')
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get only unread alerts"""
        unread = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(unread, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unresolved(self, request):
        """Get only unresolved alerts"""
        unresolved = self.get_queryset().filter(is_resolved=False)
        serializer = self.get_serializer(unresolved, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark alert as read"""
        alert = self.get_object()
        alert.mark_as_read()
        
        serializer = self.get_serializer(alert)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark alert as resolved"""
        alert = self.get_object()
        alert.resolve()
        
        serializer = self.get_serializer(alert)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all alerts as read"""
        updated_count = self.get_queryset().filter(
            is_read=False
        ).update(is_read=True)
        
        return Response({
            'message': f'Marked {updated_count} alert(s) as read',
            'count': updated_count
        })
