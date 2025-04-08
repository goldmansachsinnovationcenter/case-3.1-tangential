# HackerNews Viewer Backend

Backend service for the HackerNews Viewer application, built with FastAPI and SQLite.

## Features

- FastAPI REST API
- SQLite database with star schema
- HackerNews API integration
- Hourly data refresh via cron
- Automated database backups

## Setup

1. Install Poetry:
   ```
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Install dependencies:
   ```
   cd backend
   poetry install
   ```

3. Run the application:
   ```
   poetry run uvicorn app.main:app --reload --env-file ../.env
   ```

4. Access the API documentation:
   ```
   http://localhost:8000/docs
   ```

## Project Structure

- `app/`: Main application package
  - `api/`: API endpoints
  - `core/`: Core functionality (config, database)
  - `db/`: Database models and operations
  - `services/`: External services integration
  - `utils/`: Utility functions
- `scripts/`: Scripts for cron jobs and backups
- `tests/`: Unit tests

## Testing

Run tests with pytest:
```
poetry run pytest
```

Generate coverage report:
```
poetry run pytest --cov=app --cov-report=html
```
