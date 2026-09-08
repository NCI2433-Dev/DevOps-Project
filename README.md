# Cloud-Based CRM & CPQ Management System

## Overview
This is a portfolio Django project implementing a lightweight CRM and CPQ (Configure-Price-Quote) system. It was developed as an academic project and demonstrates key sales workflows: lead capture, lead conversion to accounts and opportunities, and quote generation with line-item pricing and discounts.

Do not publish real credentials — see `.env.example` for required environment variables.

## Features
- Role-based access: Guest, Sales (staff), Admin (superuser)
- Lead management (create, update, convert)
- Opportunity management (stages, expected close date)
- Quote creation with line items, subtotal/discount/total calculations
- Product catalog
- CI pipeline with linting, tests, SonarCloud scan, and Elastic Beanstalk deploy

## Tech Stack
- Python 3.9
- Django 4.2
- SQLite for local development
- GitHub Actions for CI
- Elastic Beanstalk for deployment (deployment steps present)

## Architecture
User → Django templates / views → Django models → Database

## Local setup
1. Create a virtual environment and activate it:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and set `SECRET_KEY`:

```bash
cp .env.example .env
# edit .env and set SECRET_KEY
```

4. Run migrations and start the dev server:

```bash
python manage.py migrate
python manage.py runserver
```

## Seed demo data

To populate the app with sample data for review, run:

```bash
# Activate virtualenv then
python scripts/seed_demo.py
```

This creates a couple of products, a demo lead, and a staff user (`staff` / `password`).

## Running tests

```bash
python manage.py test
```

## CI/CD
- GitHub Actions runs linting, tests, and SonarCloud analysis. A deployment job uses the AWS EB CLI and the repository's `Procfile` to deploy to Elastic Beanstalk. Configure `AWS_*` and `SONAR_TOKEN` as GitHub Secrets.

## Project structure
- `cpq_project/` — Django project settings
- `crm/` — main app with models, views, forms, tests
- `templates/` — HTML templates
- `static/` — static assets

## Environment variables
See `.env.example`. **Never** commit real secrets.

## Database
- The project uses SQLite for development. Do not commit `db.sqlite3` to the repo. For production, use Postgres or RDS and set config via environment variables.

## Notes for publishing
- Remove `venv/`, `.venv/`, and any environment files before pushing.
- Run a secret scan (gitleaks or truffleHog) and rotate any exposed credentials.

## Academic context
This project was developed during a first-semester academic course. It is presented here as a student portfolio piece — functional and instructive, not a production-grade SaaS.

## Future improvements
- Add more tests (authorization, edge cases)
- Provide Docker support (`Dockerfile` / `docker-compose`)
- Improve UI and responsive styles
