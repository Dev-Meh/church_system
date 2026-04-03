# PHM-ARCC Iyumbu Church Management System API Documentation

## Base URL
```
http://127.0.0.1:8000/api/
```

## Authentication
The API uses Token Authentication. Include the token in your requests:

```
Authorization: Token your_token_here
```

## Endpoints

### 1. User Registration
**POST** `/api/users/register/`

Request Body:
```json
{
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "password": "securepassword123",
    "password_confirm": "securepassword123",
    "phone_number": "+255123456789",
    "address": "123 Main St, Dodoma",
    "city": "Dodoma",
    "country": "Tanzania"
}
```

Response:
```json
{
    "token": "abc123def456...",
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "+255123456789",
        "address": "123 Main St, Dodoma",
        "city": "Dodoma",
        "country": "Tanzania",
        "membership_date": "2026-03-18",
        "role": "member",
        "date_joined": "2026-03-18T22:15:00Z"
    }
}
```

### 2. User Login
**POST** `/api/users/login/`

Request Body:
```json
{
    "username": "john_doe",
    "password": "securepassword123"
}
```

Response:
```json
{
    "token": "abc123def456...",
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe"
    }
}
```

### 3. User Logout
**POST** `/api/users/logout/`

Headers:
```
Authorization: Token your_token_here
```

Response:
```json
{
    "message": "Logged out successfully"
}
```

### 4. Get Current User Profile
**GET** `/api/users/me/`

Headers:
```
Authorization: Token your_token_here
```

Response:
```json
{
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+255123456789",
    "address": "123 Main St, Dodoma",
    "city": "Dodoma",
    "country": "Tanzania",
    "membership_date": "2026-03-18",
    "role": "member",
    "is_active_member": true,
    "date_joined": "2026-03-18T22:15:00Z",
    "last_login": "2026-03-18T22:20:00Z"
}
```

### 5. Get User List (Admin Only)
**GET** `/api/users/`

Headers:
```
Authorization: Token your_token_here
```

Response:
```json
[
    {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "membership_date": "2026-03-18",
        "role": "member",
        "is_active_member": true
    }
]
```

### 6. Get User Details
**GET** `/api/users/{id}/`

Headers:
```
Authorization: Token your_token_here
```

### 7. Update User Profile
**PUT** `/api/users/{id}/`

Headers:
```
Authorization: Token your_token_here
```

Request Body:
```json
{
    "first_name": "John Updated",
    "last_name": "Doe Updated",
    "phone_number": "+255987654321",
    "address": "456 New St, Dodoma"
}
```

## Error Responses

### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 400 Bad Request
```json
{
    "password": ["Passwords don't match"],
    "username": ["This username is already taken."]
}
```

## Testing with cURL

### Register a new user:
```bash
curl -X POST http://127.0.0.1:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "password": "password123",
    "password_confirm": "password123"
  }'
```

### Login:
```bash
curl -X POST http://127.0.0.1:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

### Get profile:
```bash
curl -X GET http://127.0.0.1:8000/api/users/me/ \
  -H "Authorization: Token your_token_here"
```

## Frontend Integration

You can now use these API endpoints with any frontend framework:

### React Example:
```javascript
// Login
const login = async (username, password) => {
    const response = await fetch('/api/users/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    const data = await response.json();
    localStorage.setItem('token', data.token);
    return data.user;
};

// Get profile
const getProfile = async () => {
    const token = localStorage.getItem('token');
    const response = await fetch('/api/users/me/', {
        headers: { 'Authorization': `Token ${token}` }
    });
    return await response.json();
};
```

## Current System Status

✅ **Your existing Django templates still work exactly the same**
✅ **New API endpoints are available for frontend development**
✅ **No breaking changes to current functionality**
✅ **Ready for gradual frontend migration**
