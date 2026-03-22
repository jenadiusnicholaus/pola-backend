# 🔧 Subscription CRUD API - Admin Testing

## 🎯 **Admin API for Subscription Management**

Complete CRUD operations for managing user subscriptions, specifically designed for testing subscription time updates.

---

## 🔐 **Authentication**

### **Required Headers**
All admin requests require:
- `Authorization: Bearer {admin_access_token}`
- `Content-Type: application/json`

---

## 📋 **Subscription CRUD Operations**

### **List All Subscriptions**
- **Method**: GET
- **URL**: `/api/v1/admin/subscriptions/`
- **Parameters**: page, page_size, user_id, status, plan_type
- **Response**: Paginated list of user subscriptions

### **Create Subscription**
- **Method**: POST
- **URL**: `/api/v1/admin/subscriptions/`
- **Body**: User subscription data
- **Response**: Created subscription details

### **Get Subscription Details**
- **Method**: GET
- **URL**: `/api/v1/admin/subscriptions/{id}/`
- **Response**: Full subscription information

### **Update Subscription**
- **Method**: PATCH
- **URL**: `/api/v1/admin/subscriptions/{id}/`
- **Body**: Partial subscription data (for testing time updates)
- **Response**: Updated subscription details

### **Delete Subscription**
- **Method**: DELETE
- **URL**: `/api/v1/admin/subscriptions/{id}/`
- **Response**: Deletion confirmation

---

## ⏰ **Subscription Time Management (Testing)**

### **Extend Subscription Time**
- **Method**: PATCH
- **URL**: `/api/v1/admin/subscriptions/{id}/extend-time/`
- **Body**: Time extension data
- **Response**: Updated end date

### **Set Custom End Date**
- **Method**: PATCH
- **URL**: `/api/v1/admin/subscriptions/{id}/set-end-date/`
- **Body**: Custom end date
- **Response**: Updated subscription with new end date

### **Reset Subscription Period**
- **Method**: POST
- **URL**: `/api/v1/admin/subscriptions/{id}/reset-period/`
- **Body**: New period configuration
- **Response**: Reset subscription with new dates

---

## 📊 **Subscription Management**

### **Bulk Update Subscriptions**
- **Method**: POST
- **URL**: `/api/v1/admin/subscriptions/bulk-update/`
- **Body**: Subscription IDs and update data
- **Response**: Bulk update results

### **Subscription Statistics**
- **Method**: GET
- **URL**: `/api/v1/admin/subscriptions/stats/`
- **Parameters**: date_from, date_to, plan_type
- **Response**: Subscription analytics

### **Expiring Subscriptions**
- **Method**: GET
- **URL**: `/api/v1/admin/subscriptions/expiring/`
- **Parameters**: days_ahead, page, page_size
- **Response**: List of soon-to-expire subscriptions

---

## 🚀 **Curl Examples**

### **Authentication**
```bash
curl -X POST "http://localhost:8000/api/v1/authentication/login/" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}'
```

### **List Subscriptions**
```bash
curl -H "Authorization: Bearer {admin_token}" \
  "http://localhost:8000/api/v1/admin/subscriptions/?page=1&page_size=20"
```

### **Create Subscription**
```bash
curl -X POST "http://localhost:8000/api/v1/admin/subscriptions/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "user": 1,
    "plan": "premium",
    "start_date": "2026-03-22T00:00:00Z",
    "end_date": "2026-04-22T00:00:00Z",
    "status": "active",
    "auto_renew": true
  }'
```

### **Update Subscription (Time Testing)**
```bash
# Extend subscription by 30 days
curl -X PATCH "http://localhost:8000/api/v1/admin/subscriptions/1/extend-time/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "extend_days": 30,
    "reason": "testing_subscription_extension"
  }'

# Set custom end date
curl -X PATCH "http://localhost:8000/api/v1/admin/subscriptions/1/set-end-date/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "end_date": "2026-12-31T23:59:59Z",
    "reason": "testing_custom_end_date"
  }'

# Reset subscription period
curl -X POST "http://localhost:8000/api/v1/admin/subscriptions/1/reset-period/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "new_start_date": "2026-03-22T00:00:00Z",
    "new_end_date": "2026-06-22T00:00:00Z",
    "reason": "testing_period_reset"
  }'
```

### **Bulk Update for Testing**
```bash
curl -X POST "http://localhost:8000/api/v1/admin/subscriptions/bulk-update/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "subscription_ids": [1, 2, 3, 4, 5],
    "extend_days": 60,
    "reason": "bulk_testing_extension"
  }'
```

### **Get Expiring Subscriptions**
```bash
curl -H "Authorization: Bearer {admin_token}" \
  "http://localhost:8000/api/v1/admin/subscriptions/expiring/?days_ahead=7&page=1&page_size=20"
```

---

## 📝 **Request/Response Formats**

### **Subscription Create/Update Body**
```json
{
  "user": 1,
  "plan": "premium|basic|trial",
  "start_date": "2026-03-22T00:00:00Z",
  "end_date": "2026-04-22T00:00:00Z",
  "status": "active|expired|cancelled|suspended",
  "auto_renew": true,
  "payment_method": "mobile_money|card|bank_transfer",
  "amount": "15000.00",
  "currency": "TZS"
}
```

### **Time Extension Body**
```json
{
  "extend_days": 30,
  "extend_hours": 0,
  "reason": "testing_subscription_extension",
  "notify_user": false
}
```

### **Custom End Date Body**
```json
{
  "end_date": "2026-12-31T23:59:59Z",
  "reason": "testing_custom_end_date",
  "notify_user": false
}
```

### **Period Reset Body**
```json
{
  "new_start_date": "2026-03-22T00:00:00Z",
  "new_end_date": "2026-06-22T00:00:00Z",
  "reason": "testing_period_reset",
  "reset_renewal_count": true
}
```

### **Subscription Response**
```json
{
  "id": 1,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "plan": "premium",
  "start_date": "2026-03-22T00:00:00Z",
  "end_date": "2026-04-22T00:00:00Z",
  "status": "active",
  "auto_renew": true,
  "days_remaining": 31,
  "is_active": true,
  "created_at": "2026-03-22T10:30:00Z",
  "updated_at": "2026-03-22T10:30:00Z"
}
```

---

## 🔍 **Filtering Parameters**

### **Common Parameters**
- `page=1&page_size=20` - Pagination
- `user_id=1` - Filter by specific user
- `status=active|expired|cancelled` - Filter by status
- `plan_type=premium|basic|trial` - Filter by plan type
- `date_from=2026-03-01` - Filter start date
- `date_to=2026-03-31` - Filter end date

### **Time Management Parameters**
- `days_ahead=7` - Days before expiration
- `extend_days=30` - Number of days to extend
- `reason=testing` - Reason for changes
- `notify_user=true|false` - Send notification to user

---

## ✅ **Response Codes**

- `200` - Success (GET, PATCH)
- `201` - Created (POST)
- `204` - No Content (DELETE)
- `400` - Bad Request (invalid dates, etc.)
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Subscription not found
- `422` - Validation error
- `500` - Server Error

---

## 🎯 **Quick Reference**

### **Base URLs**
- Subscriptions: `/api/v1/admin/subscriptions/`
- Authentication: `/api/v1/authentication/login/`

### **Key Endpoints**
- List Subscriptions: `GET /admin/subscriptions/`
- Create Subscription: `POST /admin/subscriptions/`
- Update Subscription: `PATCH /admin/subscriptions/{id}/`
- Extend Time: `PATCH /admin/subscriptions/{id}/extend-time/`
- Set End Date: `PATCH /admin/subscriptions/{id}/set-end-date/`
- Reset Period: `POST /admin/subscriptions/{id}/reset-period/`
- Bulk Update: `POST /admin/subscriptions/bulk-update/`
- Expiring Soon: `GET /admin/subscriptions/expiring/`

### **Testing Workflow**
1. **List subscriptions** to see current state
2. **Create test subscription** for testing scenarios
3. **Extend time** to test renewal logic
4. **Set custom end date** for specific test cases
5. **Reset period** to test subscription cycles
6. **Bulk update** multiple subscriptions for load testing
7. **Monitor expiring** subscriptions for notifications

This API provides complete subscription management capabilities for admin testing! 🔧
