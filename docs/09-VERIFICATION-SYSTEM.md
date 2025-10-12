# User Verification System

Complete guide to the Pola platform's user verification system with document uploads and admin approval workflows.

## Table of Contents

- [Overview](#overview)
- [Verification Requirements by Role](#verification-requirements-by-role)
- [Document Upload](#document-upload)
- [User Verification Flow](#user-verification-flow)
- [Admin Verification Process](#admin-verification-process)
- [API Endpoints](#api-endpoints)
- [Examples](#examples)

---

## Overview

The Pola platform implements a role-based verification system where different user types have different verification requirements:

### Verification Types

1. **Auto-Verification** - Citizens and Law Students
   - Verified automatically upon registration
   - No admin confirmation required
   - Immediate access to platform features

2. **Admin Verification** - Advocates, Lawyers, Paralegals, Law Firms
   - Requires document upload
   - Admin review and approval
   - Multi-step verification process

---

## Verification Requirements by Role

### 1. Citizen
**Verification:** Auto-verified ✓

- No documents required
- Verified immediately upon registration
- Full access to citizen features

### 2. Law Student / Lecturer / Professor
**Verification:** Auto-verified ✓

- No documents required
- Verified immediately upon registration
- Academic credentials validated through university email (optional)

### 3. Advocate
**Verification:** Admin confirmation required

**Required Documents:**
1. **Roll Number Certificate** (`roll_number_cert`)
   - Official certificate showing advocate roll number
   - Issued by Tanganyika Law Society

2. **Practice License** (`practice_license`)
   - Current practicing license
   - Must be valid and not expired

3. **Certificate of Work** (`work_certificate`)
   - Employment certificate or firm association letter
   - Proof of current practice

**Verification Process:**
1. User uploads all 3 required documents
2. Admin reviews each document
3. Admin approves/rejects verification
4. User receives notification of status

### 4. Lawyer
**Verification:** Admin confirmation required

**Required Documents:**
1. **Professional Certificate** (`professional_cert`)
   - Law degree or professional qualification
   - LLB, JD, or equivalent

2. **Employment Letter** (`employment_letter`)
   - Letter from current employer
   - Must state position and responsibilities

**Optional Documents:**
- **Organization Certificate** (`organization_cert`)
  - Certificate from employing organization
  - Useful for government/NGO lawyers

### 5. Paralegal
**Verification:** Admin confirmation required

**Required Documents:**
1. **Professional Certificate** (`professional_cert`)
   - Paralegal certification or training certificate
   - Diploma in law or related field

2. **Employment Letter** (`employment_letter`)
   - Letter from current employer
   - Must state position as paralegal

**Optional Documents:**
- **Organization Certificate** (`organization_cert`)
  - Certificate from employing organization

### 6. Law Firm
**Verification:** Admin confirmation required

**Required Documents:**
1. **Business License** (`business_license`)
   - Valid business operating license
   - Issued by BRELA or local authority

2. **Registration Certificate** (`registration_cert`)
   - Certificate of incorporation
   - Firm registration with Law Society

**Optional Documents:**
- **Other Firm Documents** (`firm_documents`)
  - Partnership agreements
  - Additional certifications

---

## Document Upload

### Supported File Types

- **PDF** - Preferred format
- **Images** - JPG, JPEG, PNG
- **Documents** - DOC, DOCX

### File Size Limits

- Maximum file size: **10MB** per document
- Recommended: Compress large files before upload

### Upload Process

**Endpoint:** `POST /api/v1/authentication/documents/`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request Body:**
```json
{
  "document_type": "roll_number_cert",
  "title": "Advocate Roll Number Certificate",
  "description": "Official roll number certificate from TLS",
  "file": <binary_file_data>
}
```

**Response:**
```json
{
  "id": 1,
  "document_type": "roll_number_cert",
  "document_type_display": "Roll Number Certificate",
  "title": "Advocate Roll Number Certificate",
  "description": "Official roll number certificate from TLS",
  "file_url": "http://localhost:8000/media/user_documents/cert.pdf",
  "verification_status": "pending",
  "verification_status_display": "Pending Verification",
  "created_at": "2025-10-12T09:00:00Z"
}
```

---

## User Verification Flow

### Step 1: Registration
```bash
POST /api/v1/authentication/register/
```

- User registers with role-specific information
- Verification record created automatically
- Citizens/Students: Auto-verified
- Others: Status set to "pending"

### Step 2: Check Verification Status
```bash
GET /api/v1/authentication/verifications/my_status/
```

**Response:**
```json
{
  "id": 1,
  "user_email": "advocate@example.com",
  "user_name": "Jane Smith",
  "user_role": {
    "id": 2,
    "name": "advocate",
    "display": "Advocate / Wakili"
  },
  "status": "pending",
  "status_display": "Pending Verification",
  "current_step": "documents",
  "current_step_display": "Document Verification",
  "progress": 20.0,
  "required_documents": [
    {
      "type": "roll_number_cert",
      "label": "Roll Number Certificate",
      "required": true,
      "uploaded": false,
      "status": null
    },
    {
      "type": "practice_license",
      "label": "Practice License",
      "required": true,
      "uploaded": false,
      "status": null
    },
    {
      "type": "work_certificate",
      "label": "Certificate of Work",
      "required": true,
      "uploaded": false,
      "status": null
    }
  ]
}
```

### Step 3: Upload Required Documents
```bash
POST /api/v1/authentication/documents/
```

Upload each required document one by one.

### Step 4: Wait for Admin Review

- Admin reviews uploaded documents
- Admin can approve, reject, or request additional documents
- User receives notification of decision

### Step 5: Verification Complete

Once approved:
- `is_verified` set to `true`
- Full access to platform features
- Can update profile and use all services

---

## Admin Verification Process

### Admin Dashboard

**Get Verification Statistics:**
```bash
GET /api/v1/authentication/admin-verification/statistics/
```

**Response:**
```json
{
  "overview": {
    "total_users": 150,
    "verified_users": 95,
    "pending_verifications": 45,
    "rejected_verifications": 10,
    "verification_rate": 63.33
  },
  "by_role": {
    "advocate": {
      "total": 30,
      "verified": 20,
      "pending": 8
    },
    "lawyer": {
      "total": 25,
      "verified": 18,
      "pending": 5
    }
  }
}
```

### Review Pending Verifications

**Get All Pending:**
```bash
GET /api/v1/authentication/verifications/pending/
```

**Get by Role:**
```bash
GET /api/v1/authentication/verifications/by_role/?role=advocate
```

### Review Documents

**Get Pending Documents:**
```bash
GET /api/v1/authentication/admin-verification/pending_documents/
```

**Verify a Document:**
```bash
POST /api/v1/authentication/documents/{id}/verify/
```

**Request Body:**
```json
{
  "status": "verified",
  "notes": "Document verified and approved"
}
```

**Reject a Document:**
```bash
POST /api/v1/authentication/documents/{id}/reject/
```

**Request Body:**
```json
{
  "reason": "Document is not clear, please re-upload"
}
```

### Approve User Verification

**Endpoint:**
```bash
POST /api/v1/authentication/verifications/{id}/approve/
```

**Request Body:**
```json
{
  "notes": "All documents verified. User approved."
}
```

**Response:**
```json
{
  "message": "User verification approved",
  "verification": {
    "id": 1,
    "status": "verified",
    "verification_date": "2025-10-12T10:00:00Z",
    "verified_by_name": "Admin User"
  }
}
```

### Reject User Verification

**Endpoint:**
```bash
POST /api/v1/authentication/verifications/{id}/reject/
```

**Request Body:**
```json
{
  "reason": "Invalid documents provided"
}
```

### Request Additional Documents

**Endpoint:**
```bash
POST /api/v1/authentication/verifications/{id}/request_documents/
```

**Request Body:**
```json
{
  "documents": ["practice_license", "work_certificate"],
  "message": "Please upload a clearer copy of your practice license and current employment certificate"
}
```

---

## API Endpoints

### User Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/verifications/my_status/` | Get own verification status | Yes |
| GET | `/documents/` | List own documents | Yes |
| POST | `/documents/` | Upload a document | Yes |
| GET | `/documents/{id}/` | Get document details | Yes |
| DELETE | `/documents/{id}/` | Delete own document | Yes |

### Admin Endpoints

| Method | Endpoint | Description | Admin Only |
|--------|----------|-------------|------------|
| GET | `/verifications/` | List all verifications | Yes |
| GET | `/verifications/pending/` | Get pending verifications | Yes |
| GET | `/verifications/by_role/` | Filter by role | Yes |
| POST | `/verifications/{id}/approve/` | Approve verification | Yes |
| POST | `/verifications/{id}/reject/` | Reject verification | Yes |
| POST | `/verifications/{id}/request_documents/` | Request more docs | Yes |
| POST | `/documents/{id}/verify/` | Verify a document | Yes |
| POST | `/documents/{id}/reject/` | Reject a document | Yes |
| GET | `/admin-verification/statistics/` | Get statistics | Yes |
| GET | `/admin-verification/pending_documents/` | Get pending docs | Yes |
| GET | `/admin-verification/users_needing_review/` | Users ready for review | Yes |

---

## Examples

### Example 1: Advocate Verification Flow

**1. Register as Advocate:**
```bash
curl -X POST http://localhost:8000/api/v1/authentication/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "advocate@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "Jane",
    "last_name": "Smith",
    "user_role": 2,
    "roll_number": "ADV-2010-12345",
    "practice_status": "practising",
    ...
  }'
```

**2. Login:**
```bash
curl -X POST http://localhost:8000/api/v1/authentication/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "advocate@example.com", "password": "SecurePass123!"}'
```

**3. Check Verification Status:**
```bash
curl -X GET http://localhost:8000/api/v1/authentication/verifications/my_status/ \
  -H "Authorization: Bearer <token>"
```

**4. Upload Roll Number Certificate:**
```bash
curl -X POST http://localhost:8000/api/v1/authentication/documents/ \
  -H "Authorization: Bearer <token>" \
  -F "document_type=roll_number_cert" \
  -F "title=Roll Number Certificate" \
  -F "file=@/path/to/roll_cert.pdf"
```

**5. Upload Practice License:**
```bash
curl -X POST http://localhost:8000/api/v1/authentication/documents/ \
  -H "Authorization: Bearer <token>" \
  -F "document_type=practice_license" \
  -F "title=Practice License 2025" \
  -F "file=@/path/to/license.pdf"
```

**6. Upload Work Certificate:**
```bash
curl -X POST http://localhost:8000/api/v1/authentication/documents/ \
  -H "Authorization: Bearer <token>" \
  -F "document_type=work_certificate" \
  -F "title=Employment Certificate" \
  -F "file=@/path/to/work_cert.pdf"
```

**7. Wait for Admin Approval**

### Example 2: Admin Approving Advocate

**1. Login as Admin:**
```bash
curl -X POST http://localhost:8000/api/v1/authentication/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@pola.co.tz", "password": "admin123"}'
```

**2. Get Pending Advocates:**
```bash
curl -X GET "http://localhost:8000/api/v1/authentication/verifications/by_role/?role=advocate" \
  -H "Authorization: Bearer <admin_token>"
```

**3. Review Documents:**
```bash
curl -X GET http://localhost:8000/api/v1/authentication/documents/ \
  -H "Authorization: Bearer <admin_token>"
```

**4. Verify Each Document:**
```bash
# Verify roll number cert
curl -X POST http://localhost:8000/api/v1/authentication/documents/1/verify/ \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "verified", "notes": "Roll number verified with TLS"}'

# Verify practice license
curl -X POST http://localhost:8000/api/v1/authentication/documents/2/verify/ \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "verified", "notes": "Valid license"}'

# Verify work certificate
curl -X POST http://localhost:8000/api/v1/authentication/documents/3/verify/ \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "verified", "notes": "Employment confirmed"}'
```

**5. Approve User Verification:**
```bash
curl -X POST http://localhost:8000/api/v1/authentication/verifications/1/approve/ \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"notes": "All documents verified. Advocate approved."}'
```

---

## Verification Status Codes

| Status | Description |
|--------|-------------|
| `pending` | Awaiting admin review |
| `verified` | Approved by admin |
| `rejected` | Rejected by admin |

## Verification Steps

| Step | Description | Progress |
|------|-------------|----------|
| `documents` | Document upload and verification | 20% |
| `identity` | Identity verification | 40% |
| `contact` | Contact information verification | 60% |
| `role_specific` | Role-specific requirements | 80% |
| `final` | Final approval | 100% |

---

## Best Practices

### For Users

1. **Upload Clear Documents**
   - Scan at high resolution (300 DPI minimum)
   - Ensure text is readable
   - Use PDF format when possible

2. **Provide Accurate Information**
   - Match document names with actual content
   - Add helpful descriptions
   - Upload current/valid documents

3. **Check Status Regularly**
   - Monitor verification progress
   - Respond to admin requests promptly
   - Re-upload if documents are rejected

### For Admins

1. **Review Thoroughly**
   - Check document authenticity
   - Verify information matches user profile
   - Cross-reference with official databases

2. **Provide Clear Feedback**
   - Explain rejection reasons clearly
   - Specify what needs to be corrected
   - Be helpful and professional

3. **Maintain Records**
   - Add detailed verification notes
   - Document any special circumstances
   - Keep audit trail

---

## Troubleshooting

### User Issues

**Q: My documents were rejected. What should I do?**
A: Check the rejection reason in your verification status. Re-upload clearer or corrected documents.

**Q: How long does verification take?**
A: Typically 1-3 business days. Complex cases may take longer.

**Q: Can I use the platform while pending verification?**
A: Limited access is available. Full features unlock after verification.

### Admin Issues

**Q: User uploaded wrong document type. What should I do?**
A: Reject the document with a clear reason and request the correct document type.

**Q: Document is unclear. Should I reject?**
A: Yes, reject with a note asking for a clearer copy.

**Q: User has all documents but one is expired. Can I approve?**
A: No, request an updated version of the expired document.

---

## Security Considerations

1. **Document Storage**
   - All documents stored securely
   - Access controlled by authentication
   - Regular backups maintained

2. **Privacy**
   - Users can only see their own documents
   - Admins have audited access
   - Sensitive data encrypted

3. **Audit Trail**
   - All verification actions logged
   - Timestamps recorded
   - Admin actions traceable

---

## See Also

- [Registration Guide](03-REGISTRATION-GUIDE.md)
- [API Endpoints](08-API-ENDPOINTS.md)
- [Admin Guide](10-ADMIN-GUIDE.md) (Coming soon)
