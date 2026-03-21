# 📱 Admin API Reference Guide

## 🎯 **Topic → Subtopic → Materials Management**

Complete API reference for the admin educational content management system.

---

## 🔐 **Authentication**

### **Login Endpoint**

- **Method**: POST
- **URL**: `/api/v1/authentication/login/`
- **Headers**: `Content-Type: application/json`
- **Body**: Email and password credentials
- **Response**: Access token, refresh token, and user data

### **Required Headers**

All admin requests require:

- `Authorization: Bearer {access_token}`
- `Content-Type: application/json`

---

## 📋 **Topics Management**

### **List Topics**

- **Method**: GET
- **URL**: `/api/v1/admin/hubs/topics/`
- **Parameters**: page, page_size, search
- **Response**: Paginated list of topics with counts

### **Create Topic**

- **Method**: POST
- **URL**: `/api/v1/admin/hubs/topics/`
- **Body**: Topic data (name, name_sw, slug, description, display_order, is_active)

### **Update Topic**

- **Method**: PATCH
- **URL**: `/api/v1/admin/hubs/topics/{id}/`
- **Body**: Partial topic data

### **Delete Topic**

- **Method**: DELETE
- **URL**: `/api/v1/admin/hubs/topics/{id}/`

### **Toggle Topic Status**

- **Method**: POST
- **URL**: `/api/v1/admin/hubs/topics/{id}/toggle/`
- **Body**: is_active boolean

### **Topic Statistics**

- **Method**: GET
- **URL**: `/api/v1/admin/hubs/topics/stats/`
- **Response**: Topic statistics and counts

---

## 📑 **Subtopics Management**

### **List Subtopics**

- **Method**: GET
- **URL**: `/api/v1/admin/hubs/subtopics/`
- **Parameters**: topic (filter by topic ID)
- **Response**: List of subtopics with topic data

### **Create Subtopic**

- **Method**: POST
- **URL**: `/api/v1/admin/hubs/subtopics/`
- **Body**: Subtopic data (topic, name, name_sw, slug, description, display_order, is_active)

### **Update Subtopic**

- **Method**: PATCH
- **URL**: `/api/v1/admin/hubs/subtopics/{id}/`
- **Body**: Partial subtopic data

### **Delete Subtopic**

- **Method**: DELETE
- **URL**: `/api/v1/admin/hubs/subtopics/{id}/`

### **Subtopic Statistics**

- **Method**: GET
- **URL**: `/api/v1/admin/hubs/subtopics/stats/`

---

## 📄 **Materials Management**

### **List All Materials**

- **Method**: GET
- **URL**: `/api/v1/admin/hubs/hub-content/`
- **Parameters**: topic_slug, language, ordering, page, page_size, content_type, uploader_type, hub_type
- **Response**: Paginated list with full material details

### **Create Material**

- **Method**: POST
- **URL**: `/api/v1/admin/hubs/hub-content/`
- **Body**: Material data (title, description, content, content_type, hub_type, topic, subtopic, language, price, is_downloadable, is_active)

### **Update Material**

- **Method**: PATCH
- **URL**: `/api/v1/admin/hubs/hub-content/{id}/`
- **Body**: Partial material data

### **Delete Material**

- **Method**: DELETE
- **URL**: `/api/v1/admin/hubs/hub-content/{id}/`

### **Upload File for Material**

- **Method**: PATCH
- **URL**: `/api/v1/admin/hubs/hub-content/{id}/`
- **Headers**: `Content-Type: multipart/form-data`
- **Body**: File upload

---

## 🎯 **Key Flow Endpoints**

### **Topic → Materials Flow**

- **Method**: GET
- **URL**: `/api/v1/admin/hubs/topics/{topic_id}/materials/`
- **Parameters**: language, ordering, page, page_size, search
- **Response**: Topic info with materials list (direct + subtopic materials)

### **Subtopic → Materials Flow**

- **Method**: GET
- **URL**: `/api/v1/admin/hubs/subtopics/{subtopic_id}/materials/`
- **Parameters**: language, ordering, page, page_size, search
- **Response**: Subtopic info with materials list

---

## 🔍 **Filtering Parameters**

### **Common Parameters**

- `language=en|sw` - Filter by language
- `ordering=-created_at|created_at|title` - Sort order
- `page=1&page_size=20` - Pagination
- `search=text` - Search in title/description
- `is_active=true|false` - Filter by active status
- `is_approved=true|false` - Filter by approval status

### **Material-Specific Filters**

- `content_type=document|article|tutorial` - Filter by content type
- `uploader_type=admin|lecturer|student` - Filter by uploader type
- `hub_type=legal_ed|students|advocates` - Filter by hub type
- `topic_slug=constitutional-law` - Filter by topic slug
- `price_min=1000&price_max=10000` - Price range filter

---

## � **Bulk Operations**

### **Bulk Toggle Topics**

- **Method**: POST
- **URL**: `/api/v1/admin/hubs/topics/bulk-toggle/`
- **Body**: ids array and is_active boolean

### **Reorder Topics**

- **Method**: POST
- **URL**: `/api/v1/admin/hubs/topics/reorder/`
- **Body**: items array with id and display_order

### **Bulk Material Actions**

- **Method**: POST
- **URL**: `/api/v1/admin/hubs/hub-content/bulk_action/`
- **Body**: content_ids array and action type

---

## ✅ **Response Codes**

- `200` - Success (GET, PUT, PATCH)
- `201` - Created (POST)
- `204` - No Content (DELETE)
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Server Error

---

## 🚀 **Curl Examples**

### **Authentication**

```bash
curl -X POST "http://localhost:8000/api/v1/authentication/login/" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}'
```

### **Topics Management**

```bash
# List topics
curl -H "Authorization: Bearer {token}" \
  "http://localhost:8000/api/v1/admin/hubs/topics/"

# Create topic
curl -X POST "http://localhost:8000/api/v1/admin/hubs/topics/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Criminal Law",
    "name_sw": "Sheria ya Jinai",
    "slug": "criminal-law",
    "description": "Criminal law topics",
    "display_order": 1,
    "is_active": true
  }'

# Update topic
curl -X PATCH "http://localhost:8000/api/v1/admin/hubs/topics/1/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Criminal Law"}'

# Delete topic
curl -X DELETE "http://localhost:8000/api/v1/admin/hubs/topics/1/" \
  -H "Authorization: Bearer {token}"
```

### **Subtopics Management**

```bash
# List subtopics
curl -H "Authorization: Bearer {token}" \
  "http://localhost:8000/api/v1/admin/hubs/subtopics/?topic=1"

# Create subtopic
curl -X POST "http://localhost:8000/api/v1/admin/hubs/subtopics/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": 1,
    "name": "Fundamental Rights",
    "name_sw": "Haki za Kimsingi",
    "slug": "fundamental-rights",
    "display_order": 1,
    "is_active": true
  }'
```

### **Materials Management**

```bash
# List materials
curl -H "Authorization: Bearer {token}" \
  "http://localhost:8000/api/v1/admin/hubs/hub-content/?topic_slug=constitutional-law&language=en"

# Create material
curl -X POST "http://localhost:8000/api/v1/admin/hubs/hub-content/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Constitutional Law Guide",
    "description": "Comprehensive guide",
    "content_type": "document",
    "hub_type": "legal_ed",
    "topic": 1,
    "language": "en",
    "price": "5000.00",
    "is_active": true
  }'

# Upload file
curl -X PATCH "http://localhost:8000/api/v1/admin/hubs/hub-content/1/" \
  -H "Authorization: Bearer {token}" \
  -F "file=@/path/to/document.pdf"
```

### **Key Flow Endpoints**

```bash
# Topic materials
curl -H "Authorization: Bearer {token}" \
  "http://localhost:8000/api/v1/admin/hubs/topics/1/materials/?language=en"

# Subtopic materials
curl -H "Authorization: Bearer {token}" \
  "http://localhost:8000/api/v1/admin/hubs/subtopics/1/materials/"
```

---

## 🎯 **Quick Reference**

### **Base URLs**

- Topics: `/api/v1/admin/hubs/topics/`
- Subtopics: `/api/v1/admin/hubs/subtopics/`
- Materials: `/api/v1/admin/hubs/hub-content/`
- Auth: `/api/v1/authentication/login/`

### **Key Endpoints**

- Topic Materials: `GET /topics/{id}/materials/`
- Subtopic Materials: `GET /subtopics/{id}/materials/`
- Topic Stats: `GET /topics/stats/`
- Subtopic Stats: `GET /subtopics/stats/`

### **Management Flow**

1. Authenticate to get access token
2. List topics to see available categories
3. Get topic materials to view content
4. Create/update materials as needed
5. Use subtopics for detailed categorization

This API reference provides complete coverage for Topic → Subtopic → Materials management! 🚀
