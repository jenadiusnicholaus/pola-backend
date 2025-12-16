import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import os
import io

class GoogleAuth:
    def __init__(self, project_id):
        self.service_account_file = os.path.join(os.path.dirname(__file__), 'service_account_file.json')
        self.project_id = project_id
        self.credentials = service_account.Credentials.from_service_account_file(
            self.service_account_file,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        self.auth_req = Request()
        self.credentials.refresh(self.auth_req)
        self.access_token = self.credentials.token

    def get_access_token(self):
            return self.access_token
    





    



