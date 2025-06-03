# The Church Manager - Backend

A modern, scalable backend service for The Church Manager application, built with Python and FastAPI.

## 🚀 Features

- **RESTful API** with proper versioning
- **JWT Authentication** with refresh tokens
- **Password Reset** with OTP via email
- **User Management** with role-based access control
- **SQLAlchemy** ORM with async support
- **Pydantic** for data validation
- **Alembic** for database migrations
- **Testing** with pytest
- **Docker** containerization
- **Environment-based** configuration
- **Structured logging**

## 📁 Project Structure

```
.
├── .github/                 # GitHub Actions workflows
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
├── app/
│   ├── api/                 # API endpoints
│   │   └── v1/               # API version 1
│   │       ├── endpoints/     # Route handlers
│   │       ├── dependencies/  # Route dependencies
│   │       └── models/       # Request/Response models
│   ├── core/                 # Core business logic
│   ├── config/               # Configuration management
│   │   ├── settings.py       # App settings
│   │   └── database.py       # Database config
│   ├── models/               # Database models
│   ├── schemas/              # Pydantic schemas
│   ├── services/             # Business logic layer
│   ├── utils/                # Utility functions
│   └── main.py               # Application entry point
├── tests/                    # Test files
│   ├── unit/                 # Unit tests
│   └── integration/          # Integration tests
├── migrations/               # Database migrations
├── scripts/                  # Utility scripts
├── .env.example             # Environment variables example
├── .gitignore
├── pyproject.toml           # Project metadata and dependencies
├── requirements/             # Requirements files
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
└── README.md
```

## 🔐 Authentication Endpoints

The API uses JWT for authentication. Here are the available authentication endpoints:

### 1. Login

```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=yourpassword
```

### 2. Register New User

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "passwordConfirm": "securepassword",
  "firstName": "John",
  "lastName": "Doe"
}
```

### 3. Forgot Password

```http
POST /api/v1/auth/forgot-password
Content-Type: application/json

{
  "email": "user@example.com"
}
```

### 4. Reset Password with OTP

```http
POST /api/v1/auth/reset-password
Content-Type: application/json

{
  "email": "user@example.com",
  "otp": "123456",
  "new_password": "newsecurepassword",
  "new_password_confirm": "newsecurepassword"
}
```

### 5. Change Password (Authenticated)

```http
POST /api/v1/auth/change-password
Authorization: Bearer <your_access_token>
Content-Type: application/json

{
  "current_password": "oldpassword",
  "new_password": "newsecurepassword",
  "new_password_confirm": "newsecurepassword"
}
```

### 6. Get Current User

```http
GET /api/v1/users/me
Authorization: Bearer <your_access_token>
```

## 🔧 Environment Variables

Make sure to set these environment variables in your `.env` file:

```env
# Email Settings
SMTP_TLS=True
SMTP_PORT=587
SMTP_HOST=smtp.example.com
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-email-password
EMAILS_FROM_EMAIL=noreply@yourdomain.com
EMAILS_FROM_NAME="Your App Name"
```

## 🛠️ Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 13+
- Redis (for caching and rate limiting)
- Docker & Docker Compose (optional)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/the-church-manager-backend.git
   cd the-church-manager-backend/python
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements/dev.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Running the Application

#### Development

```bash
uvicorn app.main:app --reload
```

#### Production (with Gunicorn)

```bash
gunicorn -k uvicorn.workers.UvicornWorker app.main:app
```

#### Using Docker

```bash
docker-compose up --build
```

## 🧪 Testing

Run tests with coverage:

```bash
pytest --cov=app tests/
```

## 🔄 Database Migrations

Create a new migration:
```bash
## 📦 Database Migrations

To create a new migration:
```bash
alembic revision --autogenerate -m "Your migration message"
```

Apply migrations:
```bash
docker-compose exec app alembic upgrade head
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [MongoDB](https://www.mongodb.com/)
- [Redis](https://redis.io/)
- [Docker](https://www.docker.com/)
alembic upgrade head
```

## 📚 API Documentation

Once the application is running, you can access the following:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## 🛡️ Security

- JWT Authentication
- Password hashing with Argon2
- CORS enabled
- Rate limiting
- Input validation
- Security headers

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

Your Name - your.email@example.com

Project Link: [https://github.com/your-username/the-church-manager-backend](https://github.com/your-username/the-church-manager-backend)
