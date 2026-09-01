# Pola Backend API — Flutter Integration Guide

Base URL: `https://api.pola.co.tz/api/v1`

---

## Authentication

### Login (returns tokens + user data)

```bash
curl -X POST /authentication/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"xxx"}'
```

**Response:**
```json
{
  "refresh": "eyJ...",
  "access": "eyJ...",
  "user_id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "role": "advocate",
  "is_active": true,
  "is_verified": true,
  "user": { "...full profile..." }
}
```

**Implement in:** Login screen — store tokens and user data.

---

## Block & Report Users

### Block a User

```bash
curl -X POST /authentication/block/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 5, "reason": "spam behavior"}'
```

**Response (201):**
```json
{"message": "User blocked successfully", "blocked": true, "blocked_user_id": 5}
```

**Implement in:** User profile screen → overflow menu → "Block".

---

### Unblock a User

```bash
curl -X POST /authentication/block/5/unblock/ \
  -H "Authorization: Bearer <TOKEN>"
```

**Response:**
```json
{"message": "User unblocked successfully", "blocked": false}
```

**Implement in:** Settings → Blocked Users list → swipe to unblock.

---

### Check if User is Blocked

```bash
curl -X GET /authentication/block/5/check/ \
  -H "Authorization: Bearer <TOKEN>"
```

**Response:**
```json
{"is_blocked": true}
```

**Implement in:** Before showing call/chat buttons — hide if blocked.

---

### List Blocked Users

```bash
curl -X GET /authentication/blocked-users/ \
  -H "Authorization: Bearer <TOKEN>"
```

**Response:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "blocked": 5,
      "blocked_email": "user5@example.com",
      "blocked_name": "Jane Doe",
      "blocked_profile_picture": "https://...",
      "reason": "spam behavior",
      "created_at": "2026-09-01T22:18:24Z"
    }
  ]
}
```

**Implement in:** Settings → "Blocked Users" screen.

---

### Report a User

```bash
curl -X POST /authentication/report/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"reported_user_id": 5, "report_type": "harassment", "description": "unwanted messages"}'
```

**Report types:** `harassment`, `spam`, `inappropriate`, `impersonation`, `fake_profile`, `other`

**Response (201):**
```json
{"message": "Report submitted successfully", "report_id": 1, "status": "pending"}
```

**Implement in:** User profile → overflow menu → "Report" → reason picker dialog.

---

### Report Content (no specific user)

```bash
curl -X POST /authentication/report/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"report_type": "inappropriate", "content_type": "document", "content_id": "123", "description": "offensive"}'
```

**Implement in:** Long-press on any user-generated content → "Report".

---

### List My Reports

```bash
curl -X GET /authentication/reports/ \
  -H "Authorization: Bearer <TOKEN>"
```

**Implement in:** Settings → "My Reports" screen.

---

## Account & Data Deletion

### Delete Entire Account

```bash
curl -X POST /authentication/delete-account/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"deletion_type": "account", "confirm": true, "reason": "no longer needed"}'
```

**Response (201):**
```json
{
  "message": "Deletion request submitted successfully.",
  "request_id": 2,
  "status": "pending",
  "scheduled_deletion_date": "2026-10-01T19:18:26Z",
  "grace_period_days": 30,
  "note": "Your account has been deactivated. You can cancel within 30 days..."
}
```

> Account is deactivated immediately. 30-day grace period before permanent deletion.

**Implement in:** Settings → "Delete Account" → confirmation dialog with checkbox.

---

### Cancel Account Deletion

```bash
curl -X POST /authentication/deletion/cancel/2/ \
  -H "Authorization: Bearer <TOKEN>"
```

**Response:**
```json
{"message": "Deletion request cancelled. Your account is reactivated.", "status": "cancelled"}
```

**Implement in:** Show banner on login if account is pending deletion → "Cancel Deletion" button.

---

### Delete Specific Data (keep account)

```bash
curl -X POST /authentication/delete-data/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"data_categories": ["location", "device_info", "call_history"]}'
```

**Categories:** `profile`, `documents`, `call_history`, `messages`, `location`, `device_info`, `payment`, `all`

**Response:**
```json
{
  "message": "Data deletion completed.",
  "deleted": {
    "location": "Cleared location data from 2 device(s)",
    "device_info": "Deleted 3 device record(s)",
    "call_history": "Deleted 15 call record(s)"
  }
}
```

**Implement in:** Settings → Privacy → "Manage My Data" → checkboxes per category.

---

### List Deletion Requests

```bash
curl -X GET /authentication/deletion/requests/ \
  -H "Authorization: Bearer <TOKEN>"
```

**Implement in:** Settings → "My Deletion Requests" screen.

---

## Public Endpoints (No Auth)

### Play Store Deletion Page

```
URL: https://api.pola.co.tz/api/v1/authentication/deletion/info/
```

Returns HTML page with deletion steps and email form. Use this URL for Google Play Store listing.

### Public Deletion Request

```bash
curl -X POST /authentication/deletion/public-request/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

**Response:**
```json
{
  "message": "Account deletion request submitted. Permanent deletion within 30 days.",
  "request_id": 3,
  "scheduled_deletion_date": "2026-10-01T19:18:26Z"
}
```

**Implement in:** Already built into the public HTML page.

---

## Device Location

### Update Device Location

```bash
curl -X POST /security/devices/update_location/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"latitude": -6.82349, "longitude": 39.26966}'
```

**Implement in:** Background service — call every 30-60 seconds with live GPS.

---

## Nearby Search

### Search Nearby Legal Professionals

```bash
curl -X GET "/authentication/nearby-legal-professionals/?latitude=-6.82349&longitude=39.26966&radius=20&types=advocate,lawyer" \
  -H "Authorization: Bearer <TOKEN>"
```

**Query params:**
- `latitude` / `longitude` — GPS coords (fallback to device location)
- `radius` — km (default: 50)
- `types` — comma-separated roles (default: `advocate,lawyer,paralegal,law_firm`)
- `page` / `page_size` — pagination

**Implement in:** "Find Lawyers Near Me" screen — pass live GPS or device location.

---

## Where to Implement in Flutter

| Screen | APIs |
|---|---|
| Login screen | Login |
| User profile | Block, Report |
| Chat/call screen | Check blocked before allowing |
| Settings → Blocked Users | List blocked, Unblock |
| Settings → My Reports | List reports |
| Settings → Delete Account | Delete account, Delete data |
| Settings → Privacy → Manage Data | Delete specific data |
| Login (if pending deletion) | Cancel deletion |
| Background service | Update device location |
| Find Lawyers screen | Nearby search |
| Play Store listing | Public deletion URL |

---

## Error Responses

```json
{"error": "User not found"}
{"error": "You cannot block yourself"}
{"error": "You already have a pending deletion request.", "request_id": 2, "status": "pending"}
```
