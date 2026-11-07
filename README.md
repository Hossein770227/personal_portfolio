# Hossein's Personal Portfolio

<p align="center">
  <strong>A Personal Portfolio Website Built with Django</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Django-6.1.2-green?logo=django" alt="Django">
  <img src="https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Docker-Compose-blue?logo=docker" alt="Docker">
</p>

## About The Project

**Personal Portfolio** is a web application developed with Django to introduce my professional background, technical skills, projects, and experience as a Python Backend Developer.

The main goal of this project is to create a professional online presence where visitors can learn more about my work, explore my projects, and get in touch with me.

## Features

- Personal portfolio and professional profile.
- Custom user model and account management.
- Phone number-based authentication.
- OTP verification.
- User-friendly administration panel.
- Database integration with PostgreSQL.
- Localization and translation support.
- Jalali date support.
- Docker and Docker Compose integration.
- Environment-based configuration.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Main programming language |
| Django 6.1.2 | Backend framework |
| PostgreSQL 16 | Database |
| Docker | Containerization |
| Docker Compose | Service management |
| Django Unfold | Admin dashboard |
| Django Rosetta | Translation management |

## Project Structure

```text
personal_portfolio/
│
├── accounts/
│   └── User authentication and account management
│
├── config/
│   └── Django project configuration
│
├── templates/
│   └── HTML templates
│
├── website/
│   └── Portfolio website application
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── manage.py
└── utils.py
```

## Getting Started

### Prerequisites

Make sure you have installed:

- Python 3.12+
- Docker
- Docker Compose

### Installation with Docker

**1. Clone the repository**

```bash
git clone https://github.com/Hossein770227/personal_portfolio.git

cd personal_portfolio
```

**2. Create an environment file**

Create a `.env` file in the project root and configure the required environment variables:

```env
DATABASE_NAME=portfolio
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password
DATABASE_PORT=5432

DOCKER_COMPOSE_DJANGO_SECRET_KEY=your_secret_key
DOCKER_COMPOSE_DJANGO_DEBUG=True

DOCKER_DJANGO_LIMO_SMS_API_KEY=your_sms_api_key
```

**3. Build and run containers**

```bash
docker compose up --build -d
```

**4. Apply database migrations**

```bash
docker compose exec web python manage.py migrate
```

**5. Create a superuser**

```bash
docker compose exec web python manage.py createsuperuser
```

**6. Open the application**

```text
http://localhost:8000/
```

## Development

To stop the containers:

```bash
docker compose down
```

To view application logs:

```bash
docker compose logs -f web
```

## Author

**Hossein**

Python Backend Developer

- GitHub: [@Hossein770227](https://github.com/Hossein770227)
- Portfolio Repository: [Personal Portfolio](https://github.com/Hossein770227/personal_portfolio)

---

<p align="center">
  Built with Python and Django ❤️
</p>
