POLA API - USER REGISTRATION & AUTHENTICATION
==============================================

BASE URL: http://localhost:8000/api/v1/authentication/

API DOCUMENTATION
-----------------
Swagger UI: http://localhost:8000/swagger/
ReDoc: http://localhost:8000/redoc/

AVAILABLE ENDPOINTS
-------------------

1. AUTHENTICATION
   POST /register/          - Register a new user
   POST /login/             - Login and get JWT tokens
   POST /token/refresh/     - Refresh access token
   POST /token/verify/      - Verify token validity

2. USER PROFILE
   GET    /profile/         - Get current user profile
   PUT    /profile/         - Update user profile
   PATCH  /profile/         - Partially update user profile

3. LOOKUP ENDPOINTS (for dropdown data)
   GET /roles/              - List all user roles
   GET /regions/            - List all regions
   GET /districts/          - List all districts (filter by ?region=<id>)
   GET /specializations/    - List all legal specializations
   GET /places-of-work/     - List all place of work options
   GET /academic-roles/     - List all academic roles


USER REGISTRATION EXAMPLE
--------------------------

STEP 1: Get User Roles
GET /api/v1/authentication/roles/

Response:
[
  {"id": 1, "role_name": "lawyer", "get_role_display": "Lawyer / Mwanasheria"},
  {"id": 2, "role_name": "advocate", "get_role_display": "Advocate / Wakili"},
  {"id": 3, "role_name": "citizen", "get_role_display": "Citizen / Mwananchi"}
]

STEP 2: Register User (Example for Citizen)
POST /api/v1/authentication/register/

Request Body:
{
  "email": "john.doe@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1990-01-15",
  "agreed_to_Terms": true,
  "user_role": 3,
  "gender": "M",
  "phone_number": "+255712345678",
  "region": 1,
  "district": 2,
  "id_number": "19900115-12345-00001-12"
}

Response (201 Created):
{
  "message": "User registered successfully. Please verify your account.",
  "user": {
    "id": 1,
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    ...
  }
}

STEP 3: Login
POST /api/v1/authentication/login/

Request Body:
{
  "email": "john.doe@example.com",
  "password": "SecurePass123!"
}

Response:
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

STEP 4: Access Protected Endpoints
GET /api/v1/authentication/profile/
Headers:
  Authorization: Bearer <access_token>


ROLE-SPECIFIC REGISTRATION EXAMPLES
------------------------------------

ADVOCATE:
{
  "email": "advocate@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "first_name": "Jane",
  "last_name": "Smith",
  "date_of_birth": "1985-05-20",
  "agreed_to_Terms": true,
  "user_role": 2,
  "gender": "F",
  "roll_number": "ADV-2010-12345",
  "practice_status": "active",
  "year_established": 2010,
  "phone_number": "+255712345679",
  "region": 1,
  "district": 2,
  "office_address": "123 Legal Street, Dar es Salaam",
  "operating_regions": [1, 2],
  "specializations": [1, 2]
}

LAWYER:
{
  "email": "lawyer@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "first_name": "Michael",
  "last_name": "Johnson",
  "date_of_birth": "1988-03-10",
  "agreed_to_Terms": true,
  "user_role": 1,
  "gender": "M",
  "bar_membership_number": "BAR-2015-67890",
  "years_of_experience": 8,
  "place_of_work": 1,
  "phone_number": "+255712345680",
  "region": 1,
  "district": 2,
  "operating_regions": [1],
  "operating_districts": [2, 3]
}

LAW FIRM:
{
  "email": "info@lawfirm.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "first_name": "Smith",
  "last_name": "Associates",
  "date_of_birth": "2000-01-01",
  "agreed_to_Terms": true,
  "user_role": 5,
  "firm_name": "Smith & Associates Law Firm",
  "number_of_lawyers": 15,
  "year_established": 2000,
  "phone_number": "+255712345681",
  "website": "https://smithlaw.co.tz",
  "region": 1,
  "district": 2,
  "office_address": "456 Corporate Plaza, Dar es Salaam",
  "specializations": [1, 2, 3]
}

LAW STUDENT:
{
  "email": "student@university.ac.tz",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "first_name": "Alice",
  "last_name": "Williams",
  "date_of_birth": "2000-08-15",
  "agreed_to_Terms": true,
  "user_role": 4,
  "gender": "F",
  "university_name": "University of Dar es Salaam",
  "academic_role": 1,
  "year_of_study": 3,
  "phone_number": "+255712345682"
}


AUTHENTICATION FLOW
-------------------
1. Register user -> Receive user data
2. Login -> Receive access & refresh tokens
3. Use access token for API calls
4. When access token expires, use refresh token to get new access token
5. When refresh token expires, login again


TOKEN USAGE
-----------
Include in all protected endpoint requests:
Headers:
  Authorization: Bearer <your_access_token>

Access Token Lifetime: 60 minutes (configurable)
Refresh Token Lifetime: 24 hours (configurable)


ERROR RESPONSES
---------------
400 Bad Request - Validation errors
{
  "field_name": ["Error message"]
}

401 Unauthorized - Invalid or missing token
{
  "detail": "Authentication credentials were not provided."
}

403 Forbidden - Insufficient permissions
{
  "detail": "You do not have permission to perform this action."
}


TESTING WITH CURL
-----------------
# Register
curl -X POST http://localhost:8000/api/v1/authentication/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SecurePass123!","password_confirm":"SecurePass123!","first_name":"Test","last_name":"User","date_of_birth":"1990-01-01","agreed_to_Terms":true,"user_role":3,"gender":"M"}'

# Login
curl -X POST http://localhost:8000/api/v1/authentication/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SecurePass123!"}'

# Get Profile
curl -X GET http://localhost:8000/api/v1/authentication/profile/ \
  -H "Authorization: Bearer <your_access_token>"
