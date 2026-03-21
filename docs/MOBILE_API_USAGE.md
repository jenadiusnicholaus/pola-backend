# 📱 Mobile API Usage Guide

## 🎯 **Public API for Mobile App**

Complete API reference for mobile app educational content access.

---

## 🔐 **Authentication**

### **Login**

- **Method**: POST
- **URL**: `/api/v1/authentication/login/`
- **Headers**: `Content-Type: application/json`
- **Body**: Email and password credentials
- **Response**: Access token, refresh token, and user data

### **Required Headers**

All authenticated requests require:

- `Authorization: Bearer {access_token}`
- `Content-Type: application/json`

---

## 📚 **Legal Education Hub**

### **List Topics**

- **Method**: GET
- **URL**: `/api/v1/hubs/legal-education/topics/`
- **Parameters**: page, page_size, search
- **Response**: List of topics with materials count

### **Topic Details**

- **Method**: GET
- **URL**: `/api/v1/hubs/legal-education/topics/{slug}/`
- **Response**: Topic details with subtopics list

### **Topic Materials**

- **Method**: GET
- **URL**: `/api/v1/hubs/legal-education/topics/{slug}/materials/`
- **Parameters**: language, ordering, page, page_size, search
- **Response**: Paginated materials list

### **Subtopic Materials**

- **Method**: GET
- **URL**: `/api/v1/hubs/legal-education/subtopics/{slug}/materials/`
- **Parameters**: language, ordering, page, page_size, search
- **Response**: Paginated materials list

---

## 📄 **Materials Access**

### **Material Details**

- **Method**: GET
- **URL**: `/api/v1/documents/learning-materials/{id}/`
- **Response**: Full material details with content

### **Download Material**

- **Method**: GET
- **URL**: `/api/v1/documents/learning-materials/{id}/download/`
- **Headers**: `Authorization: Bearer {token}`
- **Response**: File download

### **Like Material**

- **Method**: POST
- **URL**: `/api/v1/documents/learning-materials/{id}/like/`
- **Headers**: `Authorization: Bearer {token}`
- **Response**: Like status and count

### **Bookmark Material**

- **Method**: POST
- **URL**: `/api/v1/documents/learning-materials/{id}/bookmark/`
- **Headers**: `Authorization: Bearer {token}`
- **Response**: Bookmark status

---

## 💰 **Purchases & Payments**

### **Purchase Material**

- **Method**: POST
- **URL**: `/api/v1/payments/purchase/`
- **Headers**: `Authorization: Bearer {token}`
- **Body**: material_id, payment_method
- **Response**: Purchase confirmation and payment details

### **User Purchases**

- **Method**: GET
- **URL**: `/api/v1/payments/purchases/`
- **Headers**: `Authorization: Bearer {token}`
- **Parameters**: page, page_size, status
- **Response**: User's purchase history

### **Material Pricing**

- **Method**: GET
- **URL**: `/api/v1/documents/learning-materials/{id}/pricing/`
- **Response**: Pricing information and discounts

---

## 👤 **User Profile**

### **User Details**

- **Method**: GET
- **URL**: `/api/v1/users/profile/`
- **Headers**: `Authorization: Bearer {token}`
- **Response**: User profile information

### **Update Profile**

- **Method**: PATCH
- **URL**: `/api/v1/users/profile/`
- **Headers**: `Authorization: Bearer {token}`
- **Body**: Partial profile data

### **User Stats**

- **Method**: GET
- **URL**: `/api/v1/users/stats/`
- **Headers**: `Authorization: Bearer {token}`
- **Response**: User statistics (downloads, purchases, etc.)

---

## 🔍 **Search & Discovery**

### **Search Materials**

- **Method**: GET
- **URL**: `/api/v1/search/materials/`
- **Parameters**: q, language, content_type, topic, price_min, price_max, page, page_size
- **Response**: Search results with pagination

### **Search Topics**

- **Method**: GET
- **URL**: `/api/v1/search/topics/`
- **Parameters**: q, language, page, page_size
- **Response**: Topic search results

### **Trending Materials**

- **Method**: GET
- **URL**: `/api/v1/trending/materials/`
- **Parameters**: language, time_range, page, page_size
- **Response**: Trending materials list

### **Recommended Materials**

- **Method**: GET
- **URL**: `/api/v1/recommendations/materials/`
- **Headers**: `Authorization: Bearer {token}`
- **Parameters**: language, limit
- **Response**: Personalized recommendations

---

## 💬 **Comments & Reviews**

### **Material Comments**

- **Method**: GET
- **URL**: `/api/v1/documents/learning-materials/{id}/comments/`
- **Parameters**: page, page_size
- **Response**: Comments list

### **Add Comment**

- **Method**: POST
- **URL**: `/api/v1/documents/learning-materials/{id}/comments/`
- **Headers**: `Authorization: Bearer {token}`
- **Body**: comment text

### **Material Reviews**

- **Method**: GET
- **URL**: `/api/v1/documents/learning-materials/{id}/reviews/`
- **Parameters**: page, page_size, rating
- **Response**: Reviews list

### **Add Review**

- **Method**: POST
- **URL**: `/api/v1/documents/learning-materials/{id}/reviews/`
- **Headers**: `Authorization: Bearer {token}`
- **Body**: rating, review_text

---

## 📊 **Analytics & Tracking**

### **Track Material View**

- **Method**: POST
- **URL**: `/api/v1/analytics/view/`
- **Headers**: `Authorization: Bearer {token}`
- **Body**: material_id, duration, device_info

### **Track Download**

- **Method**: POST
- **URL**: `/api/v1/analytics/download/`
- **Headers**: `Authorization: Bearer {token}`
- **Body**: material_id, device_info

### **User Activity**

- **Method**: GET
- **URL**: `/api/v1/users/activity/`
- **Headers**: `Authorization: Bearer {token}`
- **Parameters**: activity_type, date_from, date_to, page, page_size
- **Response**: User activity log

---

## 🚀 **Curl Examples**

### **Authentication**

```bash
curl -X POST "http://localhost:8000/api/v1/authentication/login/" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

### **Browse Topics**

```bash
# List all topics
curl "http://localhost:8000/api/v1/hubs/legal-education/topics/"

# Get topic materials
curl "http://localhost:8000/api/v1/hubs/legal-education/topics/constitutional-law/materials/?language=en&page=1&page_size=20"
```

### **Materials Access**

```bash
# Get material details
curl "http://localhost:8000/api/v1/documents/learning-materials/23/"

# Download material (authenticated)
curl -H "Authorization: Bearer {token}" \
  "http://localhost:8000/api/v1/documents/learning-materials/23/download/"
```

### **Search**

```bash
# Search materials
curl "http://localhost:8000/api/v1/search/materials/?q=constitutional&language=en&page=1&page_size=10"

# Search topics
curl "http://localhost:8000/api/v1/search/topics/?q=law&language=en"
```

### **User Actions**

```bash
# Like material
curl -X POST "http://localhost:8000/api/v1/documents/learning-materials/23/like/" \
  -H "Authorization: Bearer {token}"

# Get user profile
curl -H "Authorization: Bearer {token}" \
  "http://localhost:8000/api/v1/users/profile/"
```

---

## 🔍 **Filtering Parameters**

### **Common Parameters**

- `language=en|sw` - Filter by language
- `page=1&page_size=20` - Pagination
- `search=text` - Search query
- `ordering=-created_at|created_at|title|price` - Sort order

### **Material Filters**

- `content_type=document|article|tutorial|video` - Content type filter
- `topic=slug` - Filter by topic
- `price_min=1000&price_max=10000` - Price range
- `is_free=true|false` - Free vs paid filter
- `rating=1|2|3|4|5` - Minimum rating filter

### **Search Parameters**

- `q=search_term` - Search query
- `fuzzy=true|false` - Fuzzy search
- `highlight=true|false` - Highlight matches

---

## ✅ **Response Codes**

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden (payment required, etc.)
- `404` - Not Found
- `429` - Rate Limited
- `500` - Server Error

---

## 🎯 **Topic → Subtopic → Materials Flow**

### **Step 1: List All Topics**

- **Method**: GET
- **URL**: `/api/v1/hubs/legal-education/topics/`
- **Purpose**: Display main categories to users
- **Response**: List of topics with materials count

### **Step 2: Get Topic Details with Subtopics**

- **Method**: GET
- **URL**: `/api/v1/hubs/legal-education/topics/{slug}/`
- **Purpose**: Show topic details and available subtopics
- **Response**: Topic info + subtopics list

### **Step 3: Get Topic Materials (Direct + Subtopic)**

- **Method**: GET
- **URL**: `/api/v1/hubs/legal-education/topics/{slug}/materials/`
- **Purpose**: Show all materials in topic (both direct and from subtopics)
- **Response**: Combined materials list with source tracking

### **Step 4: Get Specific Subtopic Materials**

- **Method**: GET
- **URL**: `/api/v1/hubs/legal-education/subtopics/{slug}/materials/`
- **Purpose**: Browse materials within specific subtopic
- **Response**: Materials from that subtopic only

### **Step 5: Get Material Details**

- **Method**: GET
- **URL**: `/api/v1/documents/learning-materials/{id}/`
- **Purpose**: Show full material information
- **Response**: Complete material details with pricing

### **Step 6: Download/Purchase Material**

- **Method**: GET/POST
- **URL**: `/api/v1/documents/learning-materials/{id}/download/`
- **Purpose**: Access material content
- **Response**: File download or payment flow

---

## 🚀 **Complete Flow Example**

### **Mobile App User Journey**

```bash
# 1. Get all topics
curl "http://localhost:8000/api/v1/hubs/legal-education/topics/"

# 2. Get topic details with subtopics
curl "http://localhost:8000/api/v1/hubs/legal-education/topics/constitutional-law/"

# 3. Get all materials in topic
curl "http://localhost:8000/api/v1/hubs/legal-education/topics/constitutional-law/materials/?language=en"

# 4. Get specific subtopic materials
curl "http://localhost:8000/api/v1/hubs/legal-education/subtopics/fundamental-rights/materials/?language=en"

# 5. Get material details
curl "http://localhost:8000/api/v1/documents/learning-materials/23/"

# 6. Download material (authenticated)
curl -H "Authorization: Bearer {token}" \
  "http://localhost:8000/api/v1/documents/learning-materials/23/download/"
```

### **Response Structure Flow**

```json
// 1. Topics List
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "name": "Constitutional Law",
      "name_sw": "Sheria ya Katiba",
      "slug": "constitutional-law",
      "materials_count": 12,
      "subtopics_count": 3
    }
  ]
}

// 2. Topic Details with Subtopics
{
  "id": 1,
  "name": "Constitutional Law",
  "subtopics": [
    {
      "id": 1,
      "name": "Fundamental Rights",
      "slug": "fundamental-rights",
      "materials_count": 5
    }
  ]
}

// 3. Topic Materials (Combined)
{
  "count": 12,
  "materials": [
    {
      "id": 23,
      "title": "Constitutional Guide",
      "source": "direct", // or "subtopic"
      "subtopic_name": "Fundamental Rights",
      "price": "5000.00"
    }
  ]
}

// 4. Subtopic Materials Only
{
  "count": 5,
  "materials": [
    {
      "id": 24,
      "title": "Rights Analysis",
      "subtopic": "Fundamental Rights",
      "price": "3000.00"
    }
  ]
}
```

---

## 🎯 **Quick Reference**

### **Base URLs**

- Legal Education: `/api/v1/hubs/legal-education/`
- Materials: `/api/v1/documents/learning-materials/`
- Authentication: `/api/v1/authentication/`
- Users: `/api/v1/users/`
- Search: `/api/v1/search/`
- Payments: `/api/v1/payments/`

### **Key Flow Endpoints**

- Topics List: `GET /hubs/legal-education/topics/`
- Topic Details: `GET /hubs/legal-education/topics/{slug}/`
- Topic Materials: `GET /hubs/legal-education/topics/{slug}/materials/`
- Subtopic Materials: `GET /hubs/legal-education/subtopics/{slug}/materials/`
- Material Details: `GET /documents/learning-materials/{id}/`
- Material Download: `GET /documents/learning-materials/{id}/download/`

### **Mobile App Flow**

1. **Browse Topics** - List all available topics
2. **Select Topic** - View topic details and subtopics
3. **Choose Path** - Either browse all topic materials or specific subtopic
4. **View Materials** - See filtered material lists
5. **Material Details** - Get full information about specific material
6. **Access Content** - Download or purchase material
7. **Engage** - Like, comment, bookmark materials

This API guide provides complete coverage for Topic → Subtopic → Materials flow! 📱🚀
