# Pola Backend

> 🎓 Comprehensive Legal Education & Professional Networking Platform API

[![Django](https://img.shields.io/badge/Django-5.2.7-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.16.1-red.svg)](https://www.django-rest-framework.org/)
[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)

## ✨ Features

### 🎯 Core Functionality
- **Multi-Hub System**: Advocates Hub, Students Hub, Forum Hub, Legal Education Hub
- **User Authentication**: JWT-based authentication with email verification
- **Content Management**: Upload, share, and manage legal documents and posts
- **Engagement**: Comments, likes, bookmarks, ratings
- **Monetization**: Paid content with purchase tracking and revenue management

### 🛠️ Admin Features
- **Complete Content Management**: CRUD operations across all hubs
- **Moderation Tools**: Pin, toggle active, bulk operations
- **Analytics Dashboard**: 
  - 📊 Trending content tracking
  - 📈 Engagement trends over time
  - 👥 Top contributors ranking
  - 📉 Performance metrics per content
- **Export Functionality**:
  - 💾 CSV export for content and engagement data
  - 📊 Excel export with formatted sheets
  - 🔍 Filtered exports with custom parameters
- **Engagement Viewing**:
  - 💬 View all comments with pagination
  - ❤️ View all likes with user details
  - 🔖 View all bookmarks
  - 📋 Comprehensive engagement summaries

### 🔧 Technical Features
- RESTful API with Django REST Framework
- Swagger/OpenAPI documentation
- PostgreSQL database
- JWT authentication
- Comprehensive test coverage
- Export to CSV/Excel
- Advanced analytics and reporting

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.13+
PostgreSQL
Virtual Environment
```

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/jenadiusnicholaus/pola-backend.git
cd pola-backend
```

2. **Create virtual environment**
```bash
python3.13 -m venv env
source env/bin/activate  # macOS/Linux
# env\Scripts\activate  # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Run migrations**
```bash
python manage.py migrate
```

6. **Create superuser**
```bash
python manage.py createsuperuser
```

7. **Start development server**
```bash
python manage.py runserver 0.0.0.0:8000
```

8. **Access API documentation**
```
Swagger UI: http://localhost:8000/swagger/
ReDoc: http://localhost:8000/redoc/
Admin Panel: http://localhost:8000/admin/
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [API Documentation](docs/ADMIN_HUB_API.md) | Complete API reference with examples |
| [Frontend Guide](docs/ADMIN_FRONTEND_GUIDE.md) | Integration guide for frontend developers |
| [Developer Guide](docs/DEVELOPER_GUIDE.md) | Development workflow and best practices |
| [Features Quick Reference](docs/FEATURES_QUICKREF.md) | Quick reference for new features |

## 🔌 API Endpoints

### Authentication
```http
POST /api/v1/auth/register/          # User registration
POST /api/v1/auth/login/             # User login
POST /api/v1/auth/token/refresh/     # Refresh JWT token
```

### Admin Hub Management
```http
# Content Management
GET    /api/v1/admin/hubs/hub-content/
POST   /api/v1/admin/hubs/hub-content/
GET    /api/v1/admin/hubs/hub-content/{id}/
PUT    /api/v1/admin/hubs/hub-content/{id}/
DELETE /api/v1/admin/hubs/hub-content/{id}/

# Moderation
POST   /api/v1/admin/hubs/hub-content/{id}/pin/
POST   /api/v1/admin/hubs/hub-content/{id}/unpin/
POST   /api/v1/admin/hubs/hub-content/{id}/toggle_active/

# Bulk Actions
POST   /api/v1/admin/hubs/hub-content/bulk_delete/
POST   /api/v1/admin/hubs/hub-content/bulk_toggle_active/
POST   /api/v1/admin/hubs/hub-content/bulk_pin/

# Engagement Viewing ✨ NEW
GET    /api/v1/admin/hubs/hub-content/{id}/comments/
GET    /api/v1/admin/hubs/hub-content/{id}/likes/
GET    /api/v1/admin/hubs/hub-content/{id}/bookmarks/
GET    /api/v1/admin/hubs/hub-content/{id}/engagement/

# Export ✨ NEW
GET    /api/v1/admin/hubs/hub-content/export/
GET    /api/v1/admin/hubs/hub-content/{id}/export_engagement/

# Analytics ✨ NEW
GET    /api/v1/admin/hubs/hub-content/statistics/
GET    /api/v1/admin/hubs/hub-content/top_content/
GET    /api/v1/admin/hubs/hub-content/trending/
GET    /api/v1/admin/hubs/hub-content/engagement_trends/
GET    /api/v1/admin/hubs/hub-content/top_contributors/
GET    /api/v1/admin/hubs/hub-content/{id}/performance_metrics/
```

**Total Endpoints**: 26+ (See [API Documentation](docs/ADMIN_HUB_API.md) for details)

## 🧪 Testing

### Run Tests
```bash
# All tests
python manage.py test

# Specific app
python manage.py test hubs

# With coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Test Coverage
- ✅ Engagement viewing endpoints
- ✅ Content management operations
- ✅ Bulk actions
- ✅ Permission checks
- ✅ Error handling
- ✅ Edge cases

## 🔐 Authentication

All admin endpoints require:
```http
Authorization: Bearer <your-jwt-token>
```

Get token:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "password"}'
```

## 📊 Analytics Examples

### Get Trending Content
```bash
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/admin/hubs/hub-content/trending/?days=7&limit=10"
```

### Export to Excel
```bash
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/admin/hubs/hub-content/export/?format=excel&hub_type=students" \
  --output content.xlsx
```

### Get Performance Metrics
```bash
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/admin/hubs/hub-content/123/performance_metrics/"
```

## 🚢 Deployment

### Docker
```bash
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

### Production Checklist
- [ ] Set `DEBUG=False`
- [ ] Configure strong `SECRET_KEY`
- [ ] Set up PostgreSQL
- [ ] Configure ALLOWED_HOSTS
- [ ] Set up HTTPS
- [ ] Configure static files
- [ ] Set up logging
- [ ] Configure backups

See [Developer Guide](docs/DEVELOPER_GUIDE.md) for detailed deployment instructions.

## 🛠️ Tech Stack

- **Backend**: Django 5.2.7
- **API**: Django REST Framework 3.16.1
- **Database**: PostgreSQL (psycopg2)
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Documentation**: drf-yasg (Swagger/OpenAPI)
- **Export**: openpyxl (Excel), csv
- **Python**: 3.13

## 📦 Project Structure

```
pola-backend/
├── authentication/           # User auth & JWT
├── hubs/                    # Hub content management
│   ├── admin_hub_views.py  # Admin API
│   ├── models.py           # Data models
│   ├── serializers.py      # DRF serializers
│   ├── tests.py            # Test suite
│   └── urls.py             # URL routing
├── documents/              # Learning materials
├── subscriptions/          # Subscription management
├── pola_settings/          # Django settings
├── docs/                   # Documentation
│   ├── ADMIN_HUB_API.md
│   ├── ADMIN_FRONTEND_GUIDE.md
│   ├── DEVELOPER_GUIDE.md
│   └── FEATURES_QUICKREF.md
├── requirements.txt        # Dependencies
├── manage.py              # Django management
└── README.md              # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

See [Developer Guide](docs/DEVELOPER_GUIDE.md) for coding standards and workflow.

## 📝 Changelog

### Version 2.0.0 (October 22, 2025)
- ✨ Added engagement viewing endpoints
- 💾 Added CSV/Excel export functionality
- 📈 Added enhanced analytics features
- 🧪 Added comprehensive test suite
- 📚 Added complete documentation

### Version 1.0.0
- Initial release with core functionality

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Team

- **Jenadius Nicholaus** - [GitHub](https://github.com/jenadiusnicholaus)

## 📞 Support

For issues or questions:
- Create an issue on [GitHub](https://github.com/jenadiusnicholaus/pola-backend/issues)
- Check [Documentation](docs/)
- Contact the development team

---

**Built with ❤️ using Django and Django REST Framework**

