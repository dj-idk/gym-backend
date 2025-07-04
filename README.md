# Gym Backend API

A comprehensive backend system for gym management built with FastAPI, SQLAlchemy, and PostgreSQL.

## Overview

This project provides a robust API for gym management, including user authentication, profile management, coach-client relationships, service management, and a ticketing system. It's designed with scalability and performance in mind, using modern Python async capabilities.

## Tech Stack

- **FastAPI**: High-performance web framework
- **SQLAlchemy**: SQL toolkit and ORM
- **PostgreSQL**: Relational database
- **Redis**: Caching and session management
- **Alembic**: Database migrations
- **Poetry**: Dependency management
- **JWT**: Authentication

## Features

- User authentication and authorization
- Profile and progress tracking
- Service catalog and purchasing
- Coach-client relationship management
- Messaging system
- Ticketing and support system
- Analytics and reporting

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL
- Redis

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/dj-idk/gym-backend.git
   cd gym-backend
   ```

2. Install dependencies:

   ```bash
   poetry install
   ```

3. Set up environment variables:

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Run database migrations:

   ```bash
   alembic upgrade head
   ```

5. Start the development server:

   ```bash
   poetry run uvicorn app.main:app --reload
   ```

   or

   ```bash
   python manage.py runserver --reload
   ```

6. Access the API documentation:
   ```
   http://localhost:8000/docs
   ```

## Project Structure

```
gym-backend/
├── alembic/              # Database migrations
├── app/
│   ├── web/              # API endpoints
│   ├── data/             # Database setup SQLAlchemy models
│   ├── schema/           # Pydantic schemas
│   ├── service/          # Business logic
│   ├── config/           # Project settings
│   ├── middleware/       # Middlewares
│   └── utils/            # Utility functions
├── logs/                 # Application logs
└── tests/                # Test suite
```

## Development

### Running Tests

```bash
poetry run pytest
```

### Creating Migrations

After changing models:

```bash
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```
