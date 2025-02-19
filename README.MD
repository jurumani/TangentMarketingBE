# Tangent Marketing Portal Backend

This is the backend for the Tangent Marketing Portal, built with Django and Django REST Framework. It provides APIs for user management, campaign management, and integration with Synthesia for video creation.

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Authentication](#authentication)
- [Password Reset](#password-reset)
- [Contributing](#contributing)
- [License](#license)

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/yourusername/tangent-marketing-portal.git
    cd tangent-marketing-portal/backend
    ```

2. **Create and activate a virtual environment:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install the dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Apply the migrations:**

    ```bash
    python manage.py migrate
    ```

5. **Create a superuser:**

    ```bash
    python manage.py createsuperuser
    ```

6. **Run the development server:**

    ```bash
    python manage.py runserver
    ```

## Configuration

1. **Environment Variables:**

    Create a `.env` file in the [backend](http://_vscodecontentref_/0) directory and add the following environment variables:

    ```env
    SECRET_KEY=your_secret_key
    DEBUG=True
    ALLOWED_HOSTS=localhost,127.0.0.1
    DATABASE_URL=postgres://user:password@localhost:5432/dbname
    EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
    EMAIL_HOST=smtp.your-email-provider.com
    EMAIL_PORT=587
    EMAIL_USE_TLS=True
    EMAIL_HOST_USER=your-email@example.com
    EMAIL_HOST_PASSWORD=your-email-password
    FRONTEND_URL=http://localhost:8100
    ```

2. **Update [settings.py](http://_vscodecontentref_/1):**

    Ensure that the settings in `backend/settings.py` are configured to use the environment variables.

## Usage

1. **Run the development server:**

    ```bash
    python manage.py runserver
    ```

2. **Access the admin panel:**

    Open your browser and go to `http://localhost:8000/admin`. Log in with the superuser credentials you created earlier.

## API Endpoints

### User Management

- **Login:**
    - `POST /api/users/login/`
    - Request Body: `{ "username": "user", "password": "pass" }`
    - Response: `{ "token": "auth_token", "user_id": 1, "email": "user@example.com" }`

- **Logout:**
    - `POST /api/users/logout/`
    - Response: `{ "detail": "Logout successful" }`

- **List Users:**
    - `GET /api/users/list_users/`
    - Response: `[ { "id": 1, "username": "user", "email": "user@example.com" }, ... ]`

- **Search Users:**
    - `GET /api/users/search_users/?search=query`
    - Response: `[ { "id": 1, "username": "user", "first_name": "First", "last_name": "Last" }, ... ]`

- **Delete User:**
    - `DELETE /api/users/delete_user/{id}/`
    - Response: `{ "detail": "User deleted" }`

### Password Reset

- **Request Password Reset:**
    - `POST /api/users/password_reset/`
    - Request Body: `{ "email": "user@example.com" }`
    - Response: `{ "detail": "Password reset e-mail has been sent." }`

- **Confirm Password Reset:**
    - `POST /api/users/password_reset_confirm/`
    - Request Body: `{ "key": "reset_key", "password": "new_password" }`
    - Response: `{ "detail": "Password has been reset with the new password." }`

## Authentication

This project uses token-based authentication. To access protected endpoints, include the token in the `Authorization` header:

```http
Authorization: Token your_auth_token