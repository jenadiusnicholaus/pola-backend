# Verification System - Quick Reference

Quick reference guide for the Pola verification system.

## Verification Requirements Summary

| Role | Auto-Verify | Required Documents | Admin Approval |
|------|-------------|-------------------|----------------|
| **Citizen** | ✅ Yes | None | ❌ No |
| **Law Student** | ✅ Yes | None | ❌ No |
| **Lecturer** | ✅ Yes | None | ❌ No |
| **Advocate** | ❌ No | 3 documents | ✅ Yes |
| **Lawyer** | ❌ No | 2 documents | ✅ Yes |
| **Paralegal** | ❌ No | 2 documents | ✅ Yes |
| **Law Firm** | ❌ No | 2 documents | ✅ Yes |

## Required Documents by Role

### Advocate
1. Roll Number Certificate
2. Practice License
3. Certificate of Work

### Lawyer
1. Professional Certificate
2. Employment Letter

### Paralegal
1. Professional Certificate
2. Employment Letter

### Law Firm
1. Business License
2. Registration Certificate

## Quick Commands

### User: Check Verification Status
```bash
curl -X GET http://localhost:8000/api/v1/authentication/verifications/my_status/ \
  -H "Authorization: Bearer <token>"
```

### User: Upload Document
```bash
curl -X POST http://localhost:8000/api/v1/authentication/documents/ \
  -H "Authorization: Bearer <token>" \
  -F "document_type=roll_number_cert" \
  -F "title=My Certificate" \
  -F "file=@/path/to/file.pdf"
```

### Admin: Get Pending Verifications
```bash
curl -X GET http://localhost:8000/api/v1/authentication/verifications/pending/ \
  -H "Authorization: Bearer <admin_token>"
```

### Admin: Approve User
```bash
curl -X POST http://localhost:8000/api/v1/authentication/verifications/{id}/approve/ \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"notes": "Approved"}'
```

### Admin: Verify Document
```bash
curl -X POST http://localhost:8000/api/v1/authentication/documents/{id}/verify/ \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "verified", "notes": "Document OK"}'
```

## Document Types

| Code | Label | Used By |
|------|-------|---------|
| `roll_number_cert` | Roll Number Certificate | Advocate |
| `practice_license` | Practice License | Advocate |
| `work_certificate` | Certificate of Work | Advocate |
| `professional_cert` | Professional Certificate | Lawyer, Paralegal |
| `employment_letter` | Employment Letter | Lawyer, Paralegal |
| `organization_cert` | Organization Certificate | Lawyer, Paralegal (optional) |
| `business_license` | Business License | Law Firm |
| `registration_cert` | Registration Certificate | Law Firm |
| `firm_documents` | Other Firm Documents | Law Firm (optional) |
| `id_document` | ID Document | All (optional) |
| `academic` | Academic Certificate | All (optional) |
| `other` | Other Document | All (optional) |

## Verification Status

- `pending` - Awaiting review
- `verified` - Approved
- `rejected` - Rejected

## File Requirements

- **Max Size:** 10MB
- **Formats:** PDF, JPG, PNG, DOC, DOCX
- **Recommended:** PDF at 300 DPI

## API Endpoints Summary

### User Endpoints
- `GET /verifications/my_status/` - My verification status
- `GET /documents/` - My documents
- `POST /documents/` - Upload document
- `DELETE /documents/{id}/` - Delete document

### Admin Endpoints
- `GET /verifications/pending/` - Pending verifications
- `GET /verifications/by_role/?role=advocate` - Filter by role
- `POST /verifications/{id}/approve/` - Approve user
- `POST /verifications/{id}/reject/` - Reject user
- `POST /documents/{id}/verify/` - Verify document
- `POST /documents/{id}/reject/` - Reject document
- `GET /admin-verification/statistics/` - Statistics
- `GET /admin-verification/pending_documents/` - Pending docs

## Workflow Diagram

```
User Registration
       ↓
Is Citizen/Student? → YES → Auto-Verify ✓
       ↓ NO
Upload Required Documents
       ↓
Admin Reviews Documents
       ↓
All Documents OK? → NO → Request Re-upload
       ↓ YES
Admin Approves User
       ↓
User Verified ✓
```

## Common Scenarios

### Scenario 1: New Advocate Registration
1. Register → Status: Pending
2. Upload 3 documents
3. Wait for admin review
4. Admin verifies each document
5. Admin approves user
6. Status: Verified ✓

### Scenario 2: Document Rejected
1. Admin rejects document with reason
2. User checks status
3. User uploads corrected document
4. Admin re-reviews
5. Document approved

### Scenario 3: Law Student Registration
1. Register → Auto-Verified ✓
2. Immediate access to platform

## Tips

### For Users
- Upload clear, high-quality scans
- Use descriptive titles
- Check status regularly
- Respond to admin requests quickly

### For Admins
- Review documents thoroughly
- Provide clear rejection reasons
- Use verification notes
- Maintain audit trail

## Support

For detailed information, see [Verification System Guide](09-VERIFICATION-SYSTEM.md)
