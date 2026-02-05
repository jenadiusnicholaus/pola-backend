from django.contrib import admin 
from . models import FcmNotification

# NOTE: FcmTokenModel has been deprecated.
# FCM tokens are now stored in authentication.device_models.UserDevice

class FcmNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'to_user', 'title', 'body', 'data', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__email', 'title', 'body', 'to_user__email')
    ordering = ('-created_at',)

admin.site.register(FcmNotification, FcmNotificationAdmin)


