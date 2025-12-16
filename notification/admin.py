from django.contrib import admin 
from . models import FcmNotification, FcmTokenModel

# admin.site.register(FcmNotification)
# admin.site.register(FcmTokenModel)

class FcmTokenModelAdmin(admin.ModelAdmin):
    list_display = ('user', 'fcm_token', 'time_stamp', 'is_stale', 'stale_time')
    list_filter = ('is_stale', 'stale_time')
    search_fields = ('user', 'fcm_token', 'time_stamp', 'is_stale', 'stale_time')
    ordering = ('user', 'fcm_token', 'time_stamp', 'is_stale', 'stale_time')

class FcmNotificationAdmin(admin.ModelAdmin):
    list_display = ('user',"to_user", 'title',  'body',  'data', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user', 'title', 'body',  'created_at', 'updated_at', 'to_user')
    ordering = ('user', 'title', 'body',  'created_at', 'updated_at', "to_user")

admin.site.register(FcmTokenModel, FcmTokenModelAdmin)
admin.site.register(FcmNotification, FcmNotificationAdmin)


