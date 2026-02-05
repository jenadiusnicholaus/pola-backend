# authentication/device_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from django.db import IntegrityError
import logging

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

logger = logging.getLogger(__name__)


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
        # Handle swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return UserDevice.objects.none()
        
        return UserDevice.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Register a new device"""
        try:
            # Log incoming request data
            logger.info("=" * 80)
            logger.info(f"📱 DEVICE REGISTRATION REQUEST")
            logger.info(f"User: {request.user.email} (ID: {request.user.id})")
            logger.info(f"Request Data: {request.data}")
            logger.info("=" * 80)
            
            serializer = RegisterDeviceSerializer(data=request.data)
            if not serializer.is_valid():
                # Log validation errors
                logger.error(f"❌ Validation failed: {serializer.errors}")
                return Response({
                    'error': 'Validation failed',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info("✅ Validation passed")
            serializer.is_valid(raise_exception=True)
            
            device_data = serializer.validated_data
            device_id = device_data['device_id']
            logger.info(f"🔑 Device ID: {device_id}")
            logger.info(f"📍 GPS Coordinates: lat={device_data.get('latitude')}, lon={device_data.get('longitude')}")
            
            # Get IP and location
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            location_data = get_location_from_ip(ip_address)
            logger.info(f"🌐 IP Address: {ip_address}")
            logger.info(f"📡 User Agent: {user_agent[:100]}...")
            logger.info(f"🗺️  IP Location: {location_data.get('city')}, {location_data.get('country')}")
            
            # Parse user agent if device info not provided
            ua_data = parse_user_agent(user_agent)
            
            # Merge data (client data takes precedence)
            for key, value in ua_data.items():
                if key not in device_data or not device_data.get(key):
                    device_data[key] = value
            
            # Check if device already exists for this user
            # Priority order:
            # 1. FCM token (if provided and not empty)
            # 2. Device ID
            # 3. Device fingerprint (name + model combination)
            existing_device = None
            fcm_token = device_data.get('fcm_token', '').strip()
            device_name = device_data.get('device_name', '').strip()
            device_model = device_data.get('device_model', '').strip()
            
            # 1. Try FCM token first (most reliable if provided)
            if fcm_token:
                existing_device = UserDevice.objects.filter(
                    user=request.user,
                    fcm_token=fcm_token
                ).first()
                if existing_device:
                    logger.info(f"🔍 Found device by FCM token (ID: {existing_device.id})")
            
            # 2. Fallback to device_id
            if not existing_device:
                existing_device = UserDevice.objects.filter(
                    user=request.user,
                    device_id=device_id
                ).first()
                if existing_device:
                    logger.info(f"🔍 Found device by device_id (ID: {existing_device.id})")
            
            # 3. Fingerprint match as last resort (prevent duplicates from same physical device)
            if not existing_device and device_name and device_model:
                existing_device = UserDevice.objects.filter(
                    user=request.user,
                    device_name=device_name,
                    device_model=device_model,
                    is_active=True
                ).first()
                if existing_device:
                    logger.info(f"🔍 Found device by fingerprint (name+model) (ID: {existing_device.id})")
                    logger.info(f"   Updating device_id from {existing_device.device_id} to {device_id}")
                    existing_device.device_id = device_id  # Update to new device_id
            
            if existing_device:
                logger.info(f"🔄 Device already exists (ID: {existing_device.id}) - updating")
                
                # Unmark all other devices as current
                UserDevice.objects.filter(
                    user=request.user,
                    is_current_device=True
                ).exclude(id=existing_device.id).update(is_current_device=False)
                
                # Update all fields with new data
                update_fields = []
                
                if device_data.get('latitude') and device_data.get('latitude') != existing_device.latitude:
                    existing_device.latitude = device_data.get('latitude')
                    update_fields.append('latitude')
                    
                if device_data.get('longitude') and device_data.get('longitude') != existing_device.longitude:
                    existing_device.longitude = device_data.get('longitude')
                    update_fields.append('longitude')
                    
                if device_data.get('device_name') and device_data.get('device_name') != existing_device.device_name:
                    existing_device.device_name = device_data.get('device_name')
                    update_fields.append('device_name')
                    
                if fcm_token and fcm_token != existing_device.fcm_token:
                    existing_device.fcm_token = fcm_token
                    update_fields.append('fcm_token')
                    
                if device_data.get('app_version') and device_data.get('app_version') != existing_device.app_version:
                    existing_device.app_version = device_data.get('app_version')
                    update_fields.append('app_version')
                
                # Always update these
                existing_device.last_ip = ip_address
                existing_device.is_active = True
                existing_device.is_current_device = True
                existing_device.last_seen = timezone.now()
                update_fields.extend(['last_ip', 'is_active', 'is_current_device', 'last_seen'])
                
                existing_device.save()
                logger.info(f"💾 Updated existing device. Fields changed: {', '.join(update_fields) if update_fields else 'none (just refreshed)'}")
                logger.info(f"🎯 Marked as current device")
                
                # Check what's still missing
                missing_fields = []
                if not existing_device.latitude:
                    missing_fields.append('latitude')
                if not existing_device.longitude:
                    missing_fields.append('longitude')
                if not existing_device.device_name:
                    missing_fields.append('device_name')
                
                serializer = UserDeviceSerializer(existing_device, context={'request': request})
                response_data = {
                    'is_registered': True,
                    'device': serializer.data,
                    'message': 'Device already registered'
                }
                
                if missing_fields:
                    response_data['missing_fields'] = missing_fields
                    response_data['message'] = f'Device registered but missing: {", ".join(missing_fields)}'
                    logger.warning(f"⚠️  Missing fields: {missing_fields}")
                
                logger.info(f"✅ Returning existing device (200 OK)")
                return Response(response_data, status=status.HTTP_200_OK)
            
            # Check if user has other devices registered
            user_device_count = UserDevice.objects.filter(user=request.user).count()
            logger.info(f"📊 User has {user_device_count} devices registered")
            
            # Unmark all other devices as current for this user
            if user_device_count > 0:
                logger.info(f"🔄 Unmarking {user_device_count} existing device(s) as current")
                UserDevice.objects.filter(user=request.user, is_current_device=True).update(is_current_device=False)
            
            # Register new device (no verification required)
            logger.info(f"🎉 Registering new device (total devices will be {user_device_count + 1})")
            logger.info(f"Creating device with:")
            logger.info(f"  - device_id: {device_id}")
            logger.info(f"  - device_name: {device_data.get('device_name', '')}")
            logger.info(f"  - device_type: {device_data.get('device_type', 'unknown')}")
            logger.info(f"  - os_name: {device_data.get('os_name', 'unknown')}")
            logger.info(f"  - latitude: {device_data.get('latitude')}")
            logger.info(f"  - longitude: {device_data.get('longitude')}")
            
            try:
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
                    latitude=device_data.get('latitude'),
                    longitude=device_data.get('longitude'),
                    is_active=True,
                    is_current_device=True,  # Mark as current device
                )
                
                logger.info(f"✅ Device created successfully (ID: {device.id})")
                logger.info(f"🎯 Marked as current device")
            except IntegrityError:
                # Race condition: device was created between check and create
                logger.warning(f"⚠️  Race condition detected - device was just created")
                existing_device = UserDevice.objects.get(device_id=device_id)
                
                # Check if device belongs to current user
                if existing_device.user != request.user:
                    logger.error(f"❌ Device belongs to different user (User ID: {existing_device.user.id})")
                    return Response({
                        'error': 'This device is already registered to another account',
                        'message': 'Please use a different device or contact support'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Update existing device
                logger.info(f"🔄 Updating device that was just created")
                existing_device.latitude = device_data.get('latitude')
                existing_device.longitude = device_data.get('longitude')
                existing_device.device_name = device_data.get('device_name', '')
                existing_device.fcm_token = device_data.get('fcm_token', '')
                existing_device.last_ip = ip_address
                existing_device.is_active = True
                existing_device.is_current_device = True
                existing_device.save()
                device = existing_device
                logger.info(f"✅ Updated device successfully")
            
            serializer = UserDeviceSerializer(device, context={'request': request})
            logger.info(f"🎊 Returning success response (201 CREATED)")
            logger.info("=" * 80)
            return Response({
                'is_registered': True,
                'device': serializer.data,
                'message': 'Device registered successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            # If any error occurs, don't register the device
            logger.error(f"💥 EXCEPTION during device registration: {str(e)}")
            logger.exception(e)
            return Response({
                'is_registered': False,
                'error': str(e),
                'message': 'Device registration failed'
            }, status=status.HTTP_400_BAD_REQUEST)
    
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
    
    @action(detail=True, methods=['patch'])
    def update_fcm_token(self, request, pk=None):
        """
        Update FCM token for a specific device
        
        PATCH /api/v1/security/devices/{id}/update_fcm_token/
        
        Request body:
        {
            "fcm_token": "new_fcm_token_here"
        }
        """
        device = self.get_object()
        fcm_token = request.data.get('fcm_token')
        
        if not fcm_token:
            return Response({
                'error': 'fcm_token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        device.fcm_token = fcm_token
        device.last_seen = timezone.now()
        device.save(update_fields=['fcm_token', 'last_seen', 'updated_at'])
        
        logger.info(f"✅ FCM token updated for device {device.id} (user: {device.user.email})")
        
        return Response({
            'success': True,
            'message': 'FCM token updated successfully',
            'device': UserDeviceSerializer(device, context={'request': request}).data
        })
    
    @action(detail=False, methods=['patch'])
    def update_current_device_token(self, request):
        """
        Update FCM token for the current active device
        
        PATCH /api/v1/security/devices/update_current_device_token/
        
        Request body:
        {
            "fcm_token": "new_fcm_token_here"
        }
        """
        fcm_token = request.data.get('fcm_token')
        
        if not fcm_token:
            return Response({
                'error': 'fcm_token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find current device
        device = UserDevice.objects.filter(
            user=request.user,
            is_current_device=True,
            is_active=True
        ).first()
        
        if not device:
            return Response({
                'error': 'No current device found. Please register device first.',
                'register_url': '/api/v1/authentication/devices/register/'
            }, status=status.HTTP_404_NOT_FOUND)
        
        device.fcm_token = fcm_token
        device.last_seen = timezone.now()
        device.save(update_fields=['fcm_token', 'last_seen', 'updated_at'])
        
        logger.info(f"✅ FCM token updated for current device {device.id} (user: {device.user.email})")
        
        return Response({
            'success': True,
            'message': 'FCM token updated successfully',
            'device': UserDeviceSerializer(device, context={'request': request}).data
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
            latitude=device_data.get('latitude'),
            longitude=device_data.get('longitude'),
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
        # Handle swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return UserSession.objects.none()
        
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
        # Handle swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return LoginHistory.objects.none()
        
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
        # Handle swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return SecurityAlert.objects.none()
        
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
