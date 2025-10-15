# 📚 Pola Backend Documentation

Welcome to the Pola Legal Platform documentation hub.

---

## 📁 Documentation Structure

```
docs/
├── subscription/          # ⭐ Subscription & Payment System (NEW)
│   ├── README.md          # Start here for subscription system
│   └── ... (12 comprehensive guides)
│
└── API Documentation (below)
```

---

## 🎯 Featured: Subscription System Documentation

### � **NEW: Complete Subscription System**

All documentation for the redesigned subscription and payment system (NO wallet, direct AzamPay).

👉 **[Go to Subscription Docs →](./subscription/README.md)**

**Quick links:**
- [Quick Start Guide](./subscription/QUICK_START_GUIDE.md) - 5 min overview
- [Implementation Plan](./subscription/REVISED_IMPLEMENTATION_PLAN.md) - Full technical details
- [Pricing Guide](./subscription/PRICING_CONFIGURATION_GUIDE.md) - Admin-managed pricing
- [Admin Guide](./subscription/ADMIN_PRICING_GUIDE.md) - For administrators

**Status:** ✅ Planning complete, ready for Phase 1 (Database models)

---

## 📚 API Documentation

### Verification System
- **[Verification System Guide](09-VERIFICATION-SYSTEM.md)** - Complete guide to user verification with document uploads and admin approval
- **[Verification Quick Reference](10-VERIFICATION-QUICK-REFERENCE.md)** - Quick reference for verification requirements and commands

### Lookups API
- **[Lookups API Reference](11-LOOKUPS-API.md)** - Complete reference for all lookup/reference data endpoints

## 🔐 Verification Overview

The Pola platform implements role-based verification:

### Auto-Verified (No Admin Required)
- ✅ **Citizens** - Verified immediately upon registration
- ✅ **Law Students/Lecturers** - Verified immediately upon registration

### Admin Verification Required
- 📄 **Advocates** - Requires 3 documents (Roll Number Cert, Practice License, Work Certificate)
- 📄 **Lawyers** - Requires 2 documents (Professional Cert, Employment Letter)
- 📄 **Paralegals** - Requires 2 documents (Professional Cert, Employment Letter)
- 📄 **Law Firms** - Requires 2 documents (Business License, Registration Cert)

## 🚀 Quick Start

### For Users

**1. Register:**
```bash
POST /api/v1/authentication/register/
```

**2. Check Verification Status:**
```bash
GET /api/v1/authentication/verifications/my_status/
```

**3. Upload Documents (if required):**
```bash
POST /api/v1/authentication/documents/
```

### For Admins

**1. View Pending Verifications:**
```bash
GET /api/v1/authentication/verifications/pending/
```

**2. Review Documents:**
```bash
POST /api/v1/authentication/documents/{id}/verify/
```

**3. Approve User:**
```bash
POST /api/v1/authentication/verifications/{id}/approve/
```

## 📋 Key Endpoints

### User Endpoints
- `GET /verifications/my_status/` - Get verification status
- `POST /documents/` - Upload verification document
- `GET /documents/` - List uploaded documents

### Admin Endpoints
- `GET /verifications/pending/` - Get pending verifications
- `POST /verifications/{id}/approve/` - Approve user verification
- `POST /verifications/{id}/reject/` - Reject user verification
- `POST /documents/{id}/verify/` - Verify a document
- `GET /admin-verification/statistics/` - Get verification statistics

## 🔗 API Base URL

```
http://localhost:8000/api/v1/authentication/
```

## 📖 Interactive Documentation

- **Swagger UI**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/

## 📞 Support

For detailed information, refer to the specific documentation files above.
