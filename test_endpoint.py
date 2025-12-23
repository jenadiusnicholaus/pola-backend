import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from django.test import Client

client = Client()
response = client.get('/api/v1/admin/disbursements/59/download_receipt/?format=excel')
print(f'Status: {response.status_code}')
if response.status_code == 200:
    print('Success!')
elif response.status_code == 401:
    print('Authentication required (expected)')
else:
    print(f'Response: {response.content}')
