# HackerNews Viewer Frontend

Frontend application for the HackerNews Viewer, built with Streamlit.

## Features

- Display top 5 HackerNews stories
- Show top 10 comment threads for each story
- User profile viewing
- System status monitoring

## Setup

1. Install Poetry:
   ```
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Install dependencies:
   ```
   cd frontend
   poetry install
   ```

3. Set up environment variables:
   ```
   cp .env.example .env
   ```
   Edit the `.env` file to configure the backend API URL.

4. Run the application:
   ```
   poetry run streamlit run app/main.py
   ```

5. Access the application:
   ```
   http://localhost:8501
   ```

## Project Structure

- `app/`: Main application package
  - `main.py`: Main Streamlit application
  - `pages/`: Additional Streamlit pages
  - `components/`: Reusable UI components
  - `utils/`: Utility functions
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
