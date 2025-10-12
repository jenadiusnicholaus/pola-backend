# Lookups API Reference

Complete reference for all lookup/reference data endpoints.

## Overview

The Lookups API provides reference data for dropdowns, selections, and form fields. All lookup endpoints are **publicly accessible** (no authentication required).

## Base URL

```
http://localhost:8000/api/v1/lookups/
```

## Endpoints

### 1. User Roles

**GET** `/roles/`

Get all available user roles in the system.

**Authentication:** Not required

**Response:**
```json
{
  "count": 6,
  "results": [
    {
      "id": 1,
      "role_name": "lawyer",
      "get_role_display": "Lawyer / Mwanasheria",
      "description": "Legal professional working in various organizations"
    },
    {
      "id": 2,
      "role_name": "advocate",
      "get_role_display": "Advocate / Wakili",
      "description": "Licensed legal practitioner with roll number"
    },
    {
      "id": 3,
      "role_name": "paralegal",
      "get_role_display": "Paralegal / Msaidizi wa Kisheria",
      "description": "Legal assistant providing support to lawyers and advocates"
    },
    {
      "id": 4,
      "role_name": "law_student",
      "get_role_display": "Law Student / Mwanafunzi wa Sheria/Mhadhiri",
      "description": "Student studying law at a university"
    },
    {
      "id": 5,
      "role_name": "law_firm",
      "get_role_display": "Law Firm / Kampuni ya Wakili",
      "description": "Legal practice organization"
    },
    {
      "id": 6,
      "role_name": "citizen",
      "get_role_display": "Citizen / Mwananchi",
      "description": "General public user seeking legal information or services"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/lookups/roles/
```

---

### 2. Regions

**GET** `/regions/`

Get all regions in Tanzania.

**Authentication:** Not required

**Response:**
```json
{
  "count": 31,
  "results": [
    {
      "id": 1,
      "name": "Arusha"
    },
    {
      "id": 2,
      "name": "Dar es Salaam"
    },
    {
      "id": 3,
      "name": "Dodoma"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/lookups/regions/
```

---

### 3. Districts

**GET** `/districts/`

Get all districts, optionally filtered by region.

**Authentication:** Not required

**Query Parameters:**
- `region` (optional) - Filter districts by region ID

**Response:**
```json
{
  "count": 184,
  "results": [
    {
      "id": 1,
      "name": "Arusha City",
      "region": 1,
      "region_name": "Arusha"
    },
    {
      "id": 2,
      "name": "Arusha",
      "region": 1,
      "region_name": "Arusha"
    }
  ]
}
```

**Examples:**
```bash
# Get all districts
curl http://localhost:8000/api/v1/lookups/districts/

# Get districts in Arusha region (region_id=1)
curl "http://localhost:8000/api/v1/lookups/districts/?region=1"

# Get districts in Dar es Salaam (region_id=2)
curl "http://localhost:8000/api/v1/lookups/districts/?region=2"
```

---

### 4. Legal Specializations

**GET** `/specializations/`

Get all legal practice areas/specializations.

**Authentication:** Not required

**Response:**
```json
{
  "count": 15,
  "results": [
    {
      "id": 1,
      "name_en": "Corporate Law",
      "name_sw": "Sheria za Kampuni",
      "description": "Legal practice focusing on business and corporate matters"
    },
    {
      "id": 2,
      "name_en": "Criminal Law",
      "name_sw": "Sheria za Jinai",
      "description": "Legal practice focusing on criminal cases and defense"
    },
    {
      "id": 3,
      "name_en": "Family Law",
      "name_sw": "Sheria za Familia",
      "description": "Legal practice focusing on family matters, divorce, custody"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/lookups/specializations/
```

---

### 5. Place of Work

**GET** `/places-of-work/`

Get all workplace types for legal professionals.

**Authentication:** Not required

**Response:**
```json
{
  "count": 8,
  "results": [
    {
      "id": 1,
      "code": "law_firm",
      "name_en": "Law Firm",
      "name_sw": "Ofisi ya Mawakili"
    },
    {
      "id": 2,
      "code": "government",
      "name_en": "Government Agency",
      "name_sw": "Idara ya Serikali"
    },
    {
      "id": 3,
      "code": "ngo",
      "name_en": "NGO/Non-Profit",
      "name_sw": "Shirika Lisilo la Faida"
    },
    {
      "id": 4,
      "code": "private_company",
      "name_en": "Private Company",
      "name_sw": "Kampuni Binafsi"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/lookups/places-of-work/
```

---

### 6. Academic Roles

**GET** `/academic-roles/`

Get all academic roles (for law students, lecturers, professors).

**Authentication:** Not required

**Response:**
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "code": "law_student",
      "name_en": "Law Student",
      "name_sw": "Mwanafunzi wa Sheria"
    },
    {
      "id": 8,
      "code": "lecturer",
      "name_en": "Lecturer",
      "name_sw": "Mkufunzi"
    },
    {
      "id": 9,
      "code": "professor",
      "name_en": "Professor",
      "name_sw": "Profesa"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/lookups/academic-roles/
```

---

## Usage in Registration

When registering users, use these lookup endpoints to populate form dropdowns:

### Example Registration Flow

**1. Load User Roles:**
```javascript
fetch('http://localhost:8000/api/v1/lookups/roles/')
  .then(res => res.json())
  .then(data => {
    // Populate role dropdown
    const roles = data.results;
  });
```

**2. Load Regions:**
```javascript
fetch('http://localhost:8000/api/v1/lookups/regions/')
  .then(res => res.json())
  .then(data => {
    // Populate region dropdown
    const regions = data.results;
  });
```

**3. Load Districts (when region selected):**
```javascript
const regionId = 1; // Selected region
fetch(`http://localhost:8000/api/v1/lookups/districts/?region=${regionId}`)
  .then(res => res.json())
  .then(data => {
    // Populate district dropdown
    const districts = data.results;
  });
```

**4. Load Specializations (for lawyers/advocates):**
```javascript
fetch('http://localhost:8000/api/v1/lookups/specializations/')
  .then(res => res.json())
  .then(data => {
    // Populate specializations multi-select
    const specializations = data.results;
  });
```

---

## Response Format

All lookup endpoints return paginated responses:

```json
{
  "count": 100,
  "next": "http://localhost:8000/api/v1/lookups/endpoint/?page=2",
  "previous": null,
  "results": [...]
}
```

**Fields:**
- `count` - Total number of items
- `next` - URL to next page (null if last page)
- `previous` - URL to previous page (null if first page)
- `results` - Array of items

---

## Pagination

Default page size is **10 items**. You can customize pagination:

```bash
# Get 50 items per page
curl "http://localhost:8000/api/v1/lookups/districts/?page_size=50"

# Get page 2
curl "http://localhost:8000/api/v1/lookups/districts/?page=2"

# Combine parameters
curl "http://localhost:8000/api/v1/lookups/districts/?region=1&page_size=20"
```

---

## CORS

All lookup endpoints support CORS for the following origins:
- http://localhost:3000
- http://localhost:5173
- http://127.0.0.1:3000
- http://127.0.0.1:5173

---

## Caching

Lookup data is relatively static. Consider caching responses on the client side:

```javascript
// Cache for 1 hour
const CACHE_DURATION = 3600000;

async function getCachedLookup(endpoint) {
  const cacheKey = `lookup_${endpoint}`;
  const cached = localStorage.getItem(cacheKey);
  
  if (cached) {
    const { data, timestamp } = JSON.parse(cached);
    if (Date.now() - timestamp < CACHE_DURATION) {
      return data;
    }
  }
  
  const response = await fetch(`http://localhost:8000/api/v1/lookups/${endpoint}/`);
  const data = await response.json();
  
  localStorage.setItem(cacheKey, JSON.stringify({
    data,
    timestamp: Date.now()
  }));
  
  return data;
}

// Usage
const roles = await getCachedLookup('roles');
const regions = await getCachedLookup('regions');
```

---

## Complete Example: Dynamic Form

```html
<!DOCTYPE html>
<html>
<head>
  <title>User Registration</title>
</head>
<body>
  <form id="registrationForm">
    <select id="userRole" required>
      <option value="">Select Role</option>
    </select>
    
    <select id="region" required>
      <option value="">Select Region</option>
    </select>
    
    <select id="district" required>
      <option value="">Select District</option>
    </select>
    
    <select id="specializations" multiple>
      <!-- For lawyers/advocates -->
    </select>
    
    <button type="submit">Register</button>
  </form>
  
  <script>
    const API_BASE = 'http://localhost:8000/api/v1/lookups';
    
    // Load user roles
    fetch(`${API_BASE}/roles/`)
      .then(res => res.json())
      .then(data => {
        const select = document.getElementById('userRole');
        data.results.forEach(role => {
          const option = document.createElement('option');
          option.value = role.id;
          option.textContent = role.get_role_display;
          select.appendChild(option);
        });
      });
    
    // Load regions
    fetch(`${API_BASE}/regions/`)
      .then(res => res.json())
      .then(data => {
        const select = document.getElementById('region');
        data.results.forEach(region => {
          const option = document.createElement('option');
          option.value = region.id;
          option.textContent = region.name;
          select.appendChild(option);
        });
      });
    
    // Load districts when region changes
    document.getElementById('region').addEventListener('change', (e) => {
      const regionId = e.target.value;
      const districtSelect = document.getElementById('district');
      districtSelect.innerHTML = '<option value="">Select District</option>';
      
      if (regionId) {
        fetch(`${API_BASE}/districts/?region=${regionId}`)
          .then(res => res.json())
          .then(data => {
            data.results.forEach(district => {
              const option = document.createElement('option');
              option.value = district.id;
              option.textContent = district.name;
              districtSelect.appendChild(option);
            });
          });
      }
    });
    
    // Load specializations
    fetch(`${API_BASE}/specializations/`)
      .then(res => res.json())
      .then(data => {
        const select = document.getElementById('specializations');
        data.results.forEach(spec => {
          const option = document.createElement('option');
          option.value = spec.id;
          option.textContent = spec.name_en;
          select.appendChild(option);
        });
      });
  </script>
</body>
</html>
```

---

## Summary

| Endpoint | Purpose | Filter Parameters |
|----------|---------|-------------------|
| `/roles/` | User roles | None |
| `/regions/` | Tanzania regions | None |
| `/districts/` | Districts | `?region=<id>` |
| `/specializations/` | Legal practice areas | None |
| `/places-of-work/` | Workplace types | None |
| `/academic-roles/` | Academic roles | None |

All endpoints:
- ✅ No authentication required
- ✅ Support pagination
- ✅ Return English and Swahili names (where applicable)
- ✅ CORS enabled
- ✅ Documented in Swagger UI

---

## See Also

- [Registration Guide](03-REGISTRATION-GUIDE.md)
- [API Endpoints](08-API-ENDPOINTS.md)
- [Swagger UI](http://localhost:8000/swagger/)
