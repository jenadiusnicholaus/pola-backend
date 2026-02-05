# authentication/nearby_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from geopy.distance import geodesic
import logging

from .device_models import UserDevice
from .models import UserRole, Contact, Address

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nearby_legal_professionals(request):
    """
    Find nearby legal professionals (advocates, lawyers, paralegals, law firms)
    based on user's current device location.
    
    Query Parameters:
    - radius: Search radius in kilometers (default: 20, min: 1, max: 100)
    - types: Comma-separated user types (default: advocate,lawyer,paralegal,law_firm)
    - limit: Maximum results to return (default: 50, max: 100)
    """
    
    # Get query parameters
    try:
        radius_km = float(request.query_params.get('radius', 20))
        radius_km = max(1, min(100, radius_km))  # Clamp between 1-100
    except ValueError:
        radius_km = 20
    
    types_param = request.query_params.get('types', 'advocate,lawyer,paralegal,law_firm')
    user_types = [t.strip() for t in types_param.split(',')]
    
    try:
        limit = int(request.query_params.get('limit', 50))
        limit = max(1, min(100, limit))  # Clamp between 1-100
    except ValueError:
        limit = 50
    
    # Get current user's device location (prioritize current device)
    user_device = UserDevice.objects.filter(
        user=request.user,
        is_current_device=True,
        is_active=True,
        latitude__isnull=False,
        longitude__isnull=False
    ).first()
    
    # Fallback to any active device with location if no current device
    if not user_device:
        user_device = UserDevice.objects.filter(
            user=request.user,
            is_active=True,
            latitude__isnull=False,
            longitude__isnull=False
        ).first()
    
    if not user_device or not user_device.latitude or not user_device.longitude:
        return Response({
            'error': 'Your device location is not available. Please register your device with location first.',
            'missing_fields': ['latitude', 'longitude'],
            'hint': 'Register your device at /api/v1/security/devices/ with GPS coordinates'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user_location = (float(user_device.latitude), float(user_device.longitude))
    
    # Get all legal professionals with devices
    legal_professionals = User.objects.filter(
        user_role__role_name__in=user_types,
        is_active=True
    ).exclude(
        id=request.user.id  # Exclude current user
    ).select_related(
        'user_role',
        'contact',
        'address',
        'regional_chapter',
        'place_of_work'
    ).prefetch_related(
        'devices',
        'professional_specializations__specialization',
        'operating_regions__region',
        'operating_districts__district'
    )
    
    logger.info(f"🔍 [NEARBY] User {request.user.email} searching with types={user_types}, radius={radius_km}km")
    logger.info(f"🔍 [NEARBY] User location: {user_location}")
    logger.info(f"🔍 [NEARBY] Found {legal_professionals.count()} professionals matching role filter")
    
    # Calculate distances and filter by radius
    results = []
    
    for professional in legal_professionals:
        # Get their current device location (prioritize current device)
        device = professional.devices.filter(
            is_current_device=True,
            is_active=True,
            latitude__isnull=False,
            longitude__isnull=False
        ).first()
        
        # Fallback to any active device with location
        if not device:
            device = professional.devices.filter(
                is_active=True,
                latitude__isnull=False,
                longitude__isnull=False
            ).first()
        
        if not device or not device.latitude or not device.longitude:
            logger.info(f"🔍 [NEARBY] Skipping {professional.email} - no device location")
            continue
        
        professional_location = (float(device.latitude), float(device.longitude))
        
        # Calculate distance
        distance_km = geodesic(user_location, professional_location).kilometers
        
        logger.info(f"🔍 [NEARBY] {professional.email}: distance={distance_km:.2f}km (radius={radius_km}km)")
        
        # Filter by radius
        if distance_km > radius_km:
            logger.info(f"🔍 [NEARBY] Skipping {professional.email} - outside radius")
            continue
        
        # Get contact info
        try:
            contact = professional.contact
        except:
            contact = None
        
        # Get address info
        try:
            address = professional.address
        except:
            address = None
        
        # Get specializations as comma-separated string
        specialization_names = []
        for ps in professional.professional_specializations.all():
            specialization_names.append(ps.specialization.name_en)
        specialization_string = ", ".join(specialization_names) if specialization_names else None
        
        # Check online status
        is_online = False
        try:
            from notification.models import UserOnlineStatus
            status_obj = UserOnlineStatus.objects.get(user=professional)
            is_online = status_obj.is_online and status_obj.is_available_for_call()
        except UserOnlineStatus.DoesNotExist:
            pass
        
        # Build profile picture URL
        profile_picture_url = None
        if professional.profile_picture:
            profile_picture_url = request.build_absolute_uri(professional.profile_picture.url)
        
        # Get consultant profile if exists
        from subscriptions.models import ConsultantProfile
        consultant_profile = ConsultantProfile.objects.filter(
            user=professional,
            is_available=True
        ).first()
        
        # Build result matching consultant API structure
        # Use consultant_profile.id as the primary ID (same as Talk to Lawyer API)
        result = {
            'id': consultant_profile.id if consultant_profile else None,  # ConsultantProfile ID
            'user': professional.id,
            'user_details': {
                'id': professional.id,
                'email': professional.email,
                'first_name': professional.first_name,
                'last_name': professional.last_name,
                'full_name': f"{professional.first_name} {professional.last_name}".strip(),
                'phone_number': contact.phone_number if contact else None,
                'profile_picture': profile_picture_url,
            },
            'consultant_type': consultant_profile.consultant_type if consultant_profile else (professional.user_role.role_name if professional.user_role else None),
            'specialization': consultant_profile.specialization if consultant_profile else specialization_string,
            'years_of_experience': consultant_profile.years_of_experience if consultant_profile else professional.years_of_experience,
            'offers_mobile_consultations': consultant_profile.offers_mobile_consultations if consultant_profile else True,
            'offers_physical_consultations': consultant_profile.offers_physical_consultations if consultant_profile else bool(address and address.office_address),
            'city': consultant_profile.city if consultant_profile else (address.district.name if address and address.district else None),
            'is_available': consultant_profile.is_available if consultant_profile else professional.is_active,
            'total_consultations': consultant_profile.total_consultations if consultant_profile else 0,
            'total_earnings': str(consultant_profile.total_earnings) if consultant_profile else "0.00",
            'average_rating': float(consultant_profile.average_rating) if consultant_profile and consultant_profile.average_rating else None,
            'total_reviews': consultant_profile.total_reviews if consultant_profile else 0,
            'pricing': consultant_profile.get_pricing() if consultant_profile else {
                'mobile': {
                    'price': 0.0,
                    'consultant_share': 50.0,
                    'platform_share': 50.0
                }
            },
            'is_online': is_online,
            'distance_km': round(distance_km, 2),
            'location': {
                'latitude': float(device.latitude),
                'longitude': float(device.longitude),
                'office_address': address.office_address if address else None,
                'ward': address.ward if address else None,
                'district': address.district.name if address and address.district else None,
                'region': address.region.name if address and address.region else None,
            },
            'created_at': consultant_profile.created_at.isoformat() if consultant_profile and consultant_profile.created_at else (professional.date_joined.isoformat() if professional.date_joined else None),
            'updated_at': consultant_profile.updated_at.isoformat() if consultant_profile and consultant_profile.updated_at else (professional.last_login.isoformat() if professional.last_login else None),
        }
        
        # Only include if they have a consultant profile (so they can be called)
        if consultant_profile:
            results.append(result)
            logger.info(f"✅ [NEARBY] Added {professional.email} (ConsultantProfile ID: {consultant_profile.id})")
        else:
            logger.info(f"⚠️ [NEARBY] Skipping {professional.email} - no ConsultantProfile")
    
    # Sort by distance (nearest first)
    results.sort(key=lambda x: x['distance_km'])
    
    # Apply limit
    results = results[:limit]
    
    return Response({
        'count': len(results),
        'radius_km': radius_km,
        'your_location': {
            'latitude': float(user_device.latitude),
            'longitude': float(user_device.longitude),
        },
        'results': results
    }, status=status.HTTP_200_OK)
