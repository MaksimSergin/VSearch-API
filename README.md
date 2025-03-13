# VacancySearch

VacancySearch is a private Django project that processes job vacancies using AI, detects duplicate postings, and integrates with Telegram for real-time job updates. The project uses Django with a REST API, Celery for background processing, and OpenAI’s ChatGPT for analyzing vacancy data.

## Features

- **Vacancy Processing:** Extracts and analyzes job vacancy details using a ChatGPT prompt.
- **Duplicate Detection:** Uses TF-IDF and cosine similarity to avoid duplicate job entries.
- **REST API:** Exposes endpoints for creating vacancies.
- **Background Tasks:** Processes vacancies in batches with Celery.
- **Telegram Integration:** A Telethon-based bot collects job posts from groups/channels and sends them to the API.
- **Dockerized Deployment:** Uses Docker Compose with PostgreSQL and Redis for easy setup.

## Setup

1. **Configure Environment:**
   - Copy `.env.example` to `.env` and update the required environment variables (e.g., Django settings, DB credentials, OpenAI and Telegram keys).

2. **Install Dependencies:**
   - Install project dependencies using Poetry:
     ```bash
     poetry install
     ```

3. **Database Setup:**
   - Run Django migrations:
     ```bash
     python manage.py migrate
     ```

4. **Run the Application with Docker:**
   - Build and start the containers:
     ```bash
     docker-compose up --build
     ```
   - The web server will be available on [http://localhost:8000](http://localhost:8000).


