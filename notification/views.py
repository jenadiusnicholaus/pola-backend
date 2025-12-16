import logging
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets

from notification.google_firebase_service.push_notification.auth_api import GoogleAuth
from notification.google_firebase_service.push_notification.fcm_api import FCM
from notification.models import FcmNotification, FcmTokenModel
from notification.serializers import FcmNotificationSerializer, FcmTokenModelSerializer
from vasta_settings import settings as settings
from rest_framework.permissions import AllowAny


class FcmNotificationViewSet(viewsets.ModelViewSet):
    queryset = FcmNotification.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = FcmNotificationSerializer

    def list(self, request):
        user = request.user
        notifications = self.queryset.filter(to_user=user)
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data, status=200)
    
    def delete(self, request):
        user = request.user
        n_id = request.query_params.get('notification_id')
        notifications = self.queryset.filter(to_user=user, pk=n_id)
        if not notifications.exists():
            return Response({
                'status': 'error',
                'message': 'Notification does not exist'
            },
            status=404)
        notifications.delete()
        return Response({
            'status': 'success',
            'message': 'Notifications deleted successfully'
        },
        status=200)
    


class SendFcmNotification(viewsets.ModelViewSet):
    queryset = FcmNotification.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = FcmNotificationSerializer



    def create(self, request):
        project_id = 'vista-9e65c'
        data = request.data
        title = data.get('title')
        body = data.get('body')
        token = data.get('device_registration_token')
        data_d = data.get('data')
        to_user = data.get('to_user')


        print(request.data)
        try:
            google_auth = GoogleAuth(project_id)
            access_token = google_auth.get_access_token()

        except Exception as e:
            logging.error(f'Error: {e}')
            return Response({
                'status': 'error',
                'error': f'{e}',
                'message': 'Error occurred while authenticating google cloud platform'
            },
            status=500)

        try:
            fcm = FCM(project_id, access_token)
        except Exception as e:
            return Response({
                'status': 'error',
                'error': f'{e}',
                'message': 'Error occurred while sending notification'
            },
            status=500) 

        serializers = self.get_serializer(data={
            'user': request.user.id,    
            'title': title,
            'body': body,
            'data': data_d,
            "to_user": to_user
            })

        if not serializers.is_valid():
            return Response(serializers.errors, status=400)
        
        status_code, response = fcm.send_notification(
            device_registration_token=token,
            title=title,
            body=body,
            data=data_d)
        if status_code == 200:
            serializers.save()
            return Response({
                'status': 'success',
                'message': 'Notification sent successfully'
            },
            status=status_code)
        else:
            return Response(response, status=status_code) 
        

from rest_framework.decorators import api_view, permission_classes as permission_classes_decorator
from notification.models import UserOnlineStatus


@api_view(['POST'])
@permission_classes_decorator([IsAuthenticated])
def update_heartbeat(request):
    """
    Update user's heartbeat timestamp for online status tracking
    
    POST /api/v1/notifications/heartbeat/
    
    Frontend should call this every 30 seconds to maintain online status
    """
    user = request.user
    
    try:
        online_status, created = UserOnlineStatus.objects.get_or_create(user=user)
        online_status.mark_online()  # Updates last_heartbeat and sets status to 'available'
        
        return Response({
            'success': True,
            'status': online_status.status,
            'is_online': online_status.is_online,
            'last_heartbeat': online_status.last_heartbeat.isoformat() if online_status.last_heartbeat else None
        }, status=200)
    
    except Exception as e:
        logging.error(f'Error updating heartbeat for {user.email}: {e}')
        return Response({
            'error': 'Failed to update heartbeat',
            'message': str(e)
        }, status=500)


class FcmTokenViewSet(viewsets.ModelViewSet):
    queryset = FcmTokenModel.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = FcmTokenModelSerializer

    def list(self, request):
        user = request.user
        try:
            token = FcmTokenModel.objects.get(user=user)
        except FcmTokenModel.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Token does not exist'
            },
            status=404)
        token = FcmTokenModel.objects.get(user=user)
        serializer = self.get_serializer(token)
        return Response(serializer.data, status=200)    

    def create(self, request):
        data = request.data
        token = data.get('fcm_token')
        user = request.user
        serializer = self.get_serializer(data={
            'user': user.id,
            'fcm_token': token
        })
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        serializer.save()
        return Response({
            'status': 'success',
            'message': 'Token saved successfully'
        },
        status=200)
    
    def patch(self, request):
        data = request.data
        token = data.get('fcm_token')
        user = request.user
        token_instance = FcmTokenModel.objects.get(user=user)
        data = {
            'user': user.id,
            'fcm_token': token,
            "is_stale": False,
        }
        instance = self.get_serializer(token_instance, data=data, partial=True)

        if not instance.is_valid():
            return Response(instance.errors, status=400)
        instance.save()
        return Response({
            'status': 'success',
            'message': 'Token updated successfully'
        },
        status=200)



    


        

