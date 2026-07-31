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
from .otp_service import OTPService

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
            
            # 2. Fallback to device_id (check globally since device_id is unique)
            if not existing_device:
                existing_device = UserDevice.objects.filter(
                    device_id=device_id
                ).first()
                if existing_device:
                    if existing_device.user != request.user:
                        logger.warning(f"⚠️  Device {device_id} belongs to user {existing_device.user.id}, not {request.user.id}")
                        # Device belongs to another account - send OTP to BOTH parties
                        # 1. Send OTP to current owner (stored on device record)
                        owner_otp_result = OTPService.generate_and_send_otp(
                            existing_device.user, existing_device, method='email', force=True
                        )
                        # 2. Send OTP to new user (stored in cache, no duplicate device)
                        new_user_otp = OTPService.generate_otp()
                        cache_key = f"takeover_otp_{device_id}_{request.user.id}"
                        cache.set(cache_key, {
                            'otp': new_user_otp,
                            'device_id': device_id,
                            'new_user_id': request.user.id,
                            'new_user_email': request.user.email,
                            'device_data': device_data,
                        }, timeout=600)  # 10 minutes expiry
                        
                        new_user_sent = False
                        if request.user.email:
                            new_user_sent = OTPService.send_otp_via_email(
                                request.user.email, new_user_otp
                            )
                            if new_user_sent:
                                logger.info(f"✅ Takeover OTP sent to new user {request.user.email}")
                            else:
                                logger.warning(f"❌ Failed to send takeover OTP to new user")
                        
                        otp_sent = owner_otp_result.get('success', False) or new_user_sent
                        otp_errors = []
                        if not owner_otp_result.get('success'):
                            otp_errors.append(f"Owner: {owner_otp_result.get('message')}")
                        if not new_user_sent:
                            otp_errors.append("New user: Failed to send OTP")
                        
                        return Response({
                            'device_takeover_required': True,
                            'message': 'This device is registered to another account. OTP sent to both you and the current owner for verification.',
                            'action_required': 'verify_otp_for_takeover',
                            'device_id': device_id,
                            'new_user_email': request.user.email,
                            'current_owner_email': existing_device.user.email,
                            'device_data': device_data,
                            'otp_sent': otp_sent,
                            'otp_sent_to_owner': owner_otp_result.get('success', False),
                            'otp_sent_to_new_user': new_user_sent,
                            'otp_error': '; '.join(otp_errors) if otp_errors else None
                        }, status=status.HTTP_200_OK)
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
            
            # Check if this is the user's first device (no verification needed)
            # If user already has devices, create device (unverified) and send OTP
            is_first_device = (user_device_count == 0)
            is_device_change = (user_device_count > 0)
            
            # If user already has devices, create device and send OTP
            if is_device_change:
                logger.info(f"📱 Device change detected - will create device and send OTP")
                current_device = UserDevice.objects.filter(
                    user=request.user,
                    is_current_device=True
                ).first()
                
                # Create new device (unverified, NOT current yet)
                # Old device stays as current until new one is verified
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
                        is_current_device=False,  # NOT current until verified
                        is_verified=False,  # Requires OTP verification
                    )
                    
                    logger.info(f"✅ Device created (unverified) - sending OTP")
                    
                    # Send OTP for verification
                    otp_result = OTPService.generate_and_send_otp(request.user, device, method='email')
                    
                    serializer = UserDeviceSerializer(device, context={'request': request})
                    
                    response_data = {
                        'device': serializer.data,
                        'message': 'Device registered. OTP sent to your email for verification.',
                        'is_verified': False,
                        'verification_required': True,
                        'current_device': {
                            'device_id': current_device.device_id if current_device else None,
                            'device_name': current_device.device_name if current_device else None,
                        }
                    }
                    
                    if otp_result.get('success'):
                        response_data['otp_sent'] = True
                    else:
                        response_data['otp_sent'] = False
                        response_data['otp_error'] = otp_result.get('message')
                    
                    return Response(response_data, status=status.HTTP_201_CREATED)
                    
                except IntegrityError:
                    # Race condition - device was created between check and create
                    existing_device = UserDevice.objects.filter(device_id=device_id).first()
                    if existing_device and existing_device.user != request.user:
                        return Response({
                            'error': 'This device is already registered to another account'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    if existing_device:
                        serializer = UserDeviceSerializer(existing_device, context={'request': request})
                        return Response({
                            'device': serializer.data,
                            'message': 'Device already registered',
                            'is_verified': existing_device.is_verified
                        }, status=status.HTTP_200_OK)
                    return Response({
                        'error': 'Device registration failed'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # First device - auto-register and auto-verify
            logger.info(f"🎉 Registering first device (auto-verified)")
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
                    is_verified=True,  # First device auto-verified
                )
                
                logger.info(f"✅ First device created and auto-verified (ID: {device.id})")
                logger.info(f"🎯 Marked as current device")
            except IntegrityError:
                # Race condition: device was created between check and create
                logger.warning(f"⚠️  Race condition detected - device was just created")
                existing_device = UserDevice.objects.filter(device_id=device_id).first()
                
                if not existing_device:
                    return Response({
                        'error': 'Device registration failed'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
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
                'message': 'Device registered successfully',
                'is_verified': device.is_verified,
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
        
        # Check if device already exists (globally, since device_id is unique)
        existing_device = UserDevice.objects.filter(
            device_id=device_id
        ).first()
        
        if existing_device:
            if existing_device.user != request.user:
                return Response({
                    'error': 'This device is already registered to another account',
                    'message': 'Please use a different device or contact support'
                }, status=status.HTTP_400_BAD_REQUEST)
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
    
    @action(detail=False, methods=['post'])
    def check_device(self, request):
        """
        Check device status for the authenticated user.
        Returns whether the device is registered, verified, and current.
        If device is not verified, prompts the user to verify.
        If device belongs to another account, triggers takeover flow.
        """
        device_id = request.data.get('device_id')
        if not device_id:
            return Response({
                'error': 'device_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if device exists globally
        device = UserDevice.objects.filter(device_id=device_id).first()
        
        if not device:
            # Device not registered to anyone
            return Response({
                'device_registered': False,
                'is_verified': False,
                'is_current_device': False,
                'action_required': 'register',
                'message': 'Device not registered. Please register this device.'
            }, status=status.HTTP_200_OK)
        
        # Check if device belongs to another user
        if device.user != request.user:
            logger.warning(f"⚠️  Device {device_id} belongs to user {device.user.id}, not {request.user.id}")
            # Send OTP to both current owner and new user for takeover
            owner_otp_result = OTPService.generate_and_send_otp(
                device.user, device, method='email', force=True
            )
            # New user OTP stored in cache (no duplicate device entries)
            new_user_otp = OTPService.generate_otp()
            cache_key = f"takeover_otp_{device_id}_{request.user.id}"
            cache.set(cache_key, {
                'otp': new_user_otp,
                'device_id': device_id,
                'new_user_id': request.user.id,
                'new_user_email': request.user.email,
                'device_data': request.data,
            }, timeout=600)
            
            new_user_sent = False
            if request.user.email:
                new_user_sent = OTPService.send_otp_via_email(
                    request.user.email, new_user_otp
                )
            
            return Response({
                'device_registered': True,
                'is_verified': False,
                'is_current_device': False,
                'device_takeover_required': True,
                'action_required': 'verify_otp_for_takeover',
                'device_id': device_id,
                'new_user_email': request.user.email,
                'current_owner_email': device.user.email,
                'message': 'This device is registered to another account. OTP sent to both you and the current owner.',
                'otp_sent_to_owner': owner_otp_result.get('success', False),
                'otp_sent_to_new_user': new_user_sent,
            }, status=status.HTTP_200_OK)
        
        # Device belongs to this user
        if not device.is_verified:
            # Device exists but not verified - send OTP automatically
            otp_result = OTPService.generate_and_send_otp(
                request.user, device, method='email', force=True
            )
            return Response({
                'device_registered': True,
                'is_verified': False,
                'is_current_device': device.is_current_device,
                'action_required': 'verify_otp',
                'device_id': device_id,
                'message': 'Device not verified. OTP sent to your email for verification.',
                'otp_sent': otp_result.get('success', False),
                'otp_error': otp_result.get('message') if not otp_result.get('success') else None
            }, status=status.HTTP_200_OK)
        
        # Device is verified
        # Check if it's the current device
        if not device.is_current_device:
            # Make it current
            UserDevice.objects.filter(
                user=request.user,
                is_current_device=True
            ).update(is_current_device=False)
            device.is_current_device = True
            device.save(update_fields=['is_current_device'])
        
        serializer = UserDeviceSerializer(device, context={'request': request})
        return Response({
            'device_registered': True,
            'is_verified': True,
            'is_current_device': True,
            'action_required': None,
            'device': serializer.data,
            'message': 'Device is verified and current.'
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def send_verification_otp(self, request, pk=None):
        """Send OTP to verify device"""
        device = self.get_object()
        
        # Check if device belongs to current user
        if device.user != request.user:
            return Response(
                {'error': 'Device does not belong to you'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get method (sms or email)
        method = request.data.get('method', 'sms')
        if method not in ['sms', 'email']:
            return Response(
                {'error': 'Invalid method. Use "sms" or "email"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate and send OTP
        result = OTPService.generate_and_send_otp(request.user, device, method)
        
        if result.get('success'):
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def verify_otp(self, request, pk=None):
        """Verify OTP code for device"""
        device = self.get_object()
        
        # Check if device belongs to current user
        if device.user != request.user:
            return Response(
                {'error': 'Device does not belong to you'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        otp_code = request.data.get('otp')
        if not otp_code:
            return Response(
                {'error': 'OTP code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate OTP
        result = OTPService.validate_otp(device, otp_code)
        
        if result.get('success'):
            # OTP verified - switch current device to this one
            UserDevice.objects.filter(
                user=request.user,
                is_current_device=True
            ).update(is_current_device=False)
            
            device.is_current_device = True
            device.save(update_fields=['is_current_device'])
            
            result['message'] = 'Device verified and set as current device'
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def verify_otp_for_takeover(self, request):
        """Verify OTP from current owner and transfer device to new user"""
        otp_code = request.data.get('otp')
        device_id = request.data.get('device_id')
        new_user_email = request.data.get('new_user_email')
        
        if not otp_code:
            return Response({
                'error': 'OTP code is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not device_id:
            return Response({
                'error': 'device_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not new_user_email:
            return Response({
                'error': 'new_user_email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find the device (current owner's device)
        device = UserDevice.objects.filter(device_id=device_id).first()
        if not device:
            return Response({
                'error': 'Device not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if the requester is the current owner or the new user
        is_owner = (device.user == request.user)
        
        # Find new user
        from django.contrib.auth import get_user_model
        User = get_user_model()
        new_user = User.objects.filter(email=new_user_email).first()
        if not new_user:
            return Response({
                'error': 'New user not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        is_new_user = (request.user == new_user)
        
        if not is_owner and not is_new_user:
            return Response({
                'error': 'You are not authorized to verify this takeover'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if is_owner:
            # Owner validates against the real device
            result = OTPService.validate_otp(device, otp_code, force=True)
            if not result.get('success'):
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
            # Owner approved - transfer device to new user
            # Unmark current device for new user
            UserDevice.objects.filter(
                user=new_user,
                is_current_device=True
            ).update(is_current_device=False)
            
            # Transfer device to new user
            device.user = new_user
            device.is_verified = True
            device.is_current_device = True
            device.verification_otp = None
            device.otp_expires_at = None
            device.otp_attempts = 0
            device.save()
            
            # Clean up cache
            cache_key = f"takeover_otp_{device_id}_{new_user.id}"
            cache.delete(cache_key)
            
            serializer = UserDeviceSerializer(device, context={'request': request})
            
            return Response({
                'device': serializer.data,
                'message': 'Device transferred successfully. Owner approved the takeover.',
                'is_verified': True
            }, status=status.HTTP_200_OK)
        
        else:
            # New user validates against cache
            cache_key = f"takeover_otp_{device_id}_{request.user.id}"
            cached_data = cache.get(cache_key)
            
            if not cached_data:
                return Response({
                    'error': 'No OTP found. Please request device takeover again.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            if cached_data.get('otp') != otp_code:
                return Response({
                    'success': False,
                    'message': 'Invalid OTP. Please try again.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # New user verified - still need owner approval
            return Response({
                'success': True,
                'message': 'Your OTP verified. Waiting for current owner to approve the device transfer.',
                'owner_approval_required': True,
                'current_owner_email': device.user.email
            }, status=status.HTTP_200_OK)


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
