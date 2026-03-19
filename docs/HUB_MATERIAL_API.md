# HUB MATERIAL API DOCUMENTATION

## Overview
This document provides complete API documentation for managing hub materials with direct topic assignment. The subtopic logic is deprecated - materials are now assigned directly to topics.

## 🔄 **New Flow: Topic → Materials**
- **OLD**: Topic → Subtopic → Materials
- **NEW**: Topic → Materials (Direct assignment)

---

## 📱 **Client API (Public)**

### 1. Get Materials by Topic
```http
GET /api/v1/hubs/legal-education/topics/{topic_slug}/materials/
```

**Query Parameters:**
- `language` (optional): `en` | `sw` - Default: `en`
- `ordering` (optional): `-created_at` | `created_at` | `-views` | `title`
- `page` (optional): Page number - Default: `1`
- `page_size` (optional): Items per page - Default: `20`
- `search` (optional): Search in title/description

**Example:**
```bash
GET /api/v1/hubs/legal-education/topics/constitutional-law/materials/?language=en&ordering=-created_at&page=1&page_size=20
```

**Response:**
```json
{
  "count": 25,
  "next": "https://api.pola.co.tz/api/v1/hubs/legal-education/topics/constitutional-law/materials/?page=2",
  "previous": null,
  "results": [
    {
      "id": 123,
      "title": "Constitutional Law Guide",
      "description": "Comprehensive guide to constitutional law",
      "content_type": "document",
      "language": "en",
      "price": 5000,
      "is_free": false,
      "is_downloadable": true,
      "topic": {
        "id": 1,
        "name": "Constitutional Law",
        "name_sw": "Sheria ya Katiba",
        "slug": "constitutional-law"
      },
      "subtopic": null,  // Legacy - will be null
      "uploader": {
        "id": 5,
        "full_name": "John Doe",
        "user_role": "advocate"
      },
      "created_at": "2024-03-19T10:00:00Z",
      "updated_at": "2024-03-19T10:00:00Z",
      "views": 1250,
      "downloads": 89,
      "likes": 45,
      "file_url": "/media/learning_materials/abc123.pdf"
    }
  ]
}
```

### 2. Get Single Material
```http
GET /api/v1/hubs/legal-education/materials/{id}/
```

**Response:** Same structure as above but single object.

---

## 🔧 **Admin API (Full CRUD)**

### 1. Create Material (Direct to Topic)
```http
POST /api/v1/admin/hub-content/
```

**Headers:**
```
Authorization: Bearer ADMIN_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
  "title": "Constitutional Law Guide",
  "description": "Comprehensive guide to constitutional law",
  "content_type": "document",  // Required: discussion, question, article, news, announcement, document, notes, past_papers, assignments, research, case_study, tutorial, hub_content, other
  "hub_type": "legal_ed",     // Required: advocates, students, forum, legal_ed
  "topic": 1,                 // Required: Topic ID (no subtopic needed)
  "subtopic": null,            // Optional: Legacy support
  "language": "en",            // Required: en | sw
  "is_approved": true,         // Admin bypass approval
  "is_active": true,
  "is_downloadable": true,
  "price": 0,                 // 0 for free, or amount in TZS
  "content": "<h1>HTML Content</h1>",  // Optional: HTML content
  "file": "data:application/pdf;base64,JVBERi0xLjQK...",  // Optional: Base64 file
  "tags": ["constitutional", "law"],  // Optional: Tags array
  "is_featured": false
}
```

**Response:**
```json
{
  "message": "Content created successfully",
  "data": {
    "id": 123,
    "title": "Constitutional Law Guide",
    "topic": {
      "id": 1,
      "name": "Constitutional Law",
      "slug": "constitutional-law"
    },
    "subtopic": null,
    "content_type": "document",
    "language": "en",
    "is_approved": true,
    "created_at": "2024-03-19T10:00:00Z"
  }
}
```

### 2. Get Materials (Admin)
```http
GET /api/v1/admin/hub-content/
```

**Query Parameters:**
- `topic`: Filter by topic ID
- `hub_type`: Filter by hub type
- `content_type`: Filter by content type
- `language`: Filter by language
- `is_approved`: Filter by approval status
- `search`: Search in title/description
- `ordering`: Sort order
- `page`: Page number
- `page_size`: Items per page

**Examples:**
```bash
# Materials for specific topic
GET /api/v1/admin/hub-content/?topic=1&language=en&ordering=-created_at

# All legal education materials
GET /api/v1/admin/hub-content/?hub_type=legal_ed&is_approved=true

# Search materials
GET /api/v1/admin/hub-content/?search=constitutional&language=en
```

### 3. Update Material
```http
PUT /api/v1/admin/hub-content/{id}/
PATCH /api/v1/admin/hub-content/{id}/
```

**Request Body (PUT - Full Update):**
```json
{
  "title": "Updated Constitutional Law Guide",
  "description": "Updated description",
  "topic": 1,  // Can change topic
  "price": 5000,
  "is_approved": true
}
```

**Request Body (PATCH - Partial Update):**
```json
{
  "title": "New Title Only"
}
```

### 4. Delete Material
```http
DELETE /api/v1/admin/hub-content/{id}/
```

**Response:**
```json
{
  "message": "Content deleted successfully"
}
```

### 5. Get Single Material (Admin)
```http
GET /api/v1/admin/hub-content/{id}/
```

**Response:** Full admin details with all fields.

---

## 🏷️ **Topic Management (Admin)**

### 1. Get Topics
```http
GET /api/v1/admin/topics/
```

**Response:**
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "name": "Constitutional Law",
      "name_sw": "Sheria ya Katiba",
      "slug": "constitutional-law",
      "description": "Study of constitutional law principles",
      "description_sw": "Uchunguzi wa misingi ya sheria ya katiba",
      "display_order": 1,
      "is_active": true,
      "materials_count": 25,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 2. Create Topic
```http
POST /api/v1/admin/topics/
```

**Request Body:**
```json
{
  "name": "New Legal Topic",
  "name_sw": "Mada Mpya ya Sheria",
  "description": "Topic description",
  "description_sw": "Maelezo ya mada",
  "display_order": 10,
  "is_active": true
}
```

### 3. Update Topic
```http
PUT /api/v1/admin/topics/{id}/
```

### 4. Delete Topic
```http
DELETE /api/v1/admin/topics/{id}/
```

---

## 📊 **Analytics & Statistics (Admin)**

### 1. Material Statistics
```http
GET /api/v1/admin/hub-content/{id}/stats/
```

**Response:**
```json
{
  "material_id": 123,
  "views": 1250,
  "downloads": 89,
  "likes": 45,
  "comments": 12,
  "purchases": 23,
  "revenue": 115000,
  "rating": 4.5,
  "created_at": "2024-03-19T10:00:00Z"
}
```

### 2. Topic Statistics
```http
GET /api/v1/admin/hub-content/stats-by-topic/?topic=1
```

**Response:**
```json
{
  "topic_id": 1,
  "topic_name": "Constitutional Law",
  "total_materials": 25,
  "total_views": 15000,
  "total_downloads": 890,
  "total_revenue": 250000,
  "approved_count": 23,
  "pending_count": 2
}
```

---

## 🔄 **Bulk Operations (Admin)**

### 1. Bulk Action
```http
POST /api/v1/admin/hub-content/bulk-action/
```

**Request Body:**
```json
{
  "action": "approve",  // approve, reject, delete, feature, pin
  "item_ids": [1, 2, 3, 4, 5],
  "action_data": {
    "is_featured": true,
    "featured_until": "2024-12-31T23:59:59Z"
  }
}
```

**Available Actions:**
- `approve`: Approve pending materials
- `reject`: Reject materials
- `delete`: Delete materials
- `feature`: Feature materials
- `pin`: Pin materials to top
- `activate`: Activate materials
- `deactivate`: Deactivate materials

---

## 📁 **File Upload**

### 1. Base64 Upload (Recommended)
```json
{
  "file": "data:application/pdf;base64,JVBERi0xLjQK...",
  "title": "Material with File",
  "content_type": "document"
}
```

### 2. Multipart Form Upload
```http
POST /api/v1/admin/hub-content/
Content-Type: multipart/form-data
```

**Form Fields:**
- `title`: Material title
- `topic`: Topic ID
- `content_type`: Content type
- `file`: File object
- `language`: Language

---

## 🔍 **Search & Filtering**

### 1. Content Types
```json
[
  "discussion", "question", "article", "news", "announcement",
  "document", "notes", "past_papers", "assignments", 
  "research", "case_study", "tutorial", "hub_content", "other"
]
```

### 2. Hub Types
```json
[
  "advocates", "students", "forum", "legal_ed"
]
```

### 3. Languages
```json
[
  "en",  // English
  "sw"   // Swahili
]
```

---

## 🚫 **Deprecation Notice**

### Subtopic Logic (Legacy)
- **Status**: Deprecated but maintained for backward compatibility
- **New Approach**: Direct topic assignment
- **Migration**: Existing subtopic materials still accessible via topic APIs
- **Frontend**: Remove subtopic selection UI components

### UI Changes Required
1. **Remove**: Subtopic selection/dropdown components
2. **Update**: Material creation forms (topic only)
3. **Modify**: Material listing (topic → materials flow)
4. **Update**: Navigation breadcrumbs (topic → materials)

---

## 🔐 **Authentication**

### Client API
- **Required**: User authentication
- **Permission**: Based on user role and hub access

### Admin API
- **Required**: Admin authentication
- **Permission**: `is_staff = true`
- **Header**: `Authorization: Bearer ADMIN_TOKEN`

---

## 📱 **Frontend Implementation Guide**

### 1. Topic List Component
```javascript
// Get topics
const getTopics = async () => {
  const response = await fetch('/api/v1/admin/topics/');
  return response.json();
};
```

### 2. Materials List Component
```javascript
// Get materials for topic
const getTopicMaterials = async (topicSlug, language = 'en') => {
  const response = await fetch(
    `/api/v1/hubs/legal-education/topics/${topicSlug}/materials/?language=${language}&ordering=-created_at`
  );
  return response.json();
};
```

### 3. Create Material Component
```javascript
// Create material (admin)
const createMaterial = async (materialData) => {
  const response = await fetch('/api/v1/admin/hub-content/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${adminToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(materialData)
  });
  return response.json();
};
```

### 4. Update Material Component
```javascript
// Update material (admin)
const updateMaterial = async (id, materialData) => {
  const response = await fetch(`/api/v1/admin/hub-content/${id}/`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${adminToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(materialData)
  });
  return response.json();
};
```

---

## 📋 **Error Handling**

### Common Error Responses
```json
{
  "error": "Authentication required",
  "code": "authentication_required"
}

{
  "error": "Topic not found",
  "code": "topic_not_found"
}

{
  "error": "Permission denied",
  "code": "permission_denied"
}

{
  "error": "Validation failed",
  "details": {
    "title": ["This field is required."],
    "topic": ["Invalid topic ID."]
  }
}
```

---

## 🔄 **Migration Steps**

### For Frontend Team
1. ✅ **Remove** subtopic selection UI components
2. ✅ **Update** material creation forms (topic dropdown only)
3. ✅ **Modify** navigation: Topic → Materials (no subtopic level)
4. ✅ **Update** API calls to use topic-based endpoints
5. ✅ **Test** with both English and Swahili
6. ✅ **Handle** legacy subtopic data (show as null)

### API Endpoint Changes
- **Keep**: `/api/v1/hubs/legal-education/topics/{slug}/materials/` ✅
- **Keep**: `/api/v1/admin/hub-content/` ✅
- **Keep**: `/api/v1/admin/topics/` ✅
- **Legacy**: `/api/v1/hubs/legal-education/subtopics/{id}/materials/` (maintained)

---

## 📞 **Support**

For API issues or questions:
- Check authentication headers
- Verify topic IDs exist
- Ensure proper content types
- Validate file formats
- Check admin permissions

**API Base URL**: `https://api.pola.co.tz/api/v1/`
**Documentation Version**: 1.0
**Last Updated**: March 19, 2024
