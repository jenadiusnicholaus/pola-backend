from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from authentication.models import UserRole, Specialization, Document, DocumentType

User = get_user_model()

EXPECTED_SPECIALIZATIONS = [
    'Administrative Law',
    'Contract Law',
    'Civil Litigation',
    'Probate Law',
    'Labour and Employment Law',
    'Banking and Finance Law',
    'Insurance Law',
    'Mining and Natural Resources Law',
    'Cyber Law',
    'International Law',
]


class SeededDataTestCase(TestCase):
    """Data provided by migrations/seeders"""

    def test_lecturer_role_exists(self):
        self.assertTrue(UserRole.objects.filter(role_name='lecturer').exists())

    def test_new_specializations_exist(self):
        for name_en in EXPECTED_SPECIALIZATIONS:
            self.assertTrue(
                Specialization.objects.filter(name_en=name_en).exists(),
                f'Specialization {name_en} should exist',
            )


class DocumentUploadTestCase(APITestCase):
    """Multipart document upload via DocumentUploadViewSet"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='uploader@test.com',
            password='pass123',
            first_name='Up',
            last_name='Loader',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = reverse('authentication:document-list')

    def test_multipart_upload_without_title(self):
        """A multipart upload without a title succeeds and derives a title"""
        file = SimpleUploadedFile(
            'national_id.pdf', b'%PDF-1.4 fake content', content_type='application/pdf'
        )
        response = self.client.post(
            self.url,
            {'document_type': 'id_document', 'file': file},
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        document = Document.objects.get(user=self.user)
        self.assertEqual(document.document_type, 'id_document')
        self.assertEqual(document.title, 'national_id.pdf')

    def test_upload_unknown_document_type_rejected(self):
        file = SimpleUploadedFile(
            'doc.pdf', b'%PDF-1.4 fake content', content_type='application/pdf'
        )
        response = self.client.post(
            self.url,
            {'document_type': 'not_a_real_type', 'file': file},
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_dynamic_document_type(self):
        """A DocumentType code not in legacy DOCUMENT_TYPES is uploadable"""
        doc_type = DocumentType.objects.create(
            code='admin_configured_long_document_type_code',
            label='Admin Configured Document',
        )
        file = SimpleUploadedFile(
            'doc.pdf', b'%PDF-1.4 fake content', content_type='application/pdf'
        )
        response = self.client.post(
            self.url,
            {'document_type': doc_type.code, 'file': file},
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        document = Document.objects.get(user=self.user)
        self.assertEqual(document.document_type, doc_type.code)
        self.assertEqual(document.document_type_ref, doc_type)
