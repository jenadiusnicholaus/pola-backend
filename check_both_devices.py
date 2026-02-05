#!/usr/bin/env python
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from authentication.device_models import UserDevice
from authentication.models import PolaUser

# Check rama's devices
rama = PolaUser.objects.get(email='rama@gmail.com')
print(f'User: {rama.email} (ID: {rama.id})')
devices = UserDevice.objects.filter(user=rama)
for d in devices:
    print(f'  Device {d.id}: {d.device_name}')
    print(f'    is_active: {d.is_active}')
    print(f'    is_current_device: {d.is_current_device}')
    print(f'    fcm_token: {bool(d.fcm_token)}')

# Check micheal's devices
print()
micheal = PolaUser.objects.get(email='micheal@gmail.com')
print(f'User: {micheal.email} (ID: {micheal.id})')
devices = UserDevice.objects.filter(user=micheal)
for d in devices:
    print(f'  Device {d.id}: {d.device_name}')
    print(f'    is_active: {d.is_active}')
    print(f'    is_current_device: {d.is_current_device}')
    print(f'    fcm_token: {bool(d.fcm_token)}')
