# Raw Foods CPQ — Django Web Application

A cloud-based **Configure, Price, Quote (CPQ)** system for a raw food supply company. Built with Django 4.2, featuring complete CRM workflows, quote generation with line items, role-based access, and Stripe payment integration.

---

## Features

- **Guest portal** — public product catalog, quote request form
- **My Orders** — logged-in customers track their quote status and pay online
- **Sales portal** — full lead → account → opportunity → quote → payment workflow
- **Role-based access** — guest / authenticated user / staff / superuser
- **Stripe checkout** — test-mode payment integration
- **Django Admin** — manage all data models

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 4.2 |
| Database | SQLite (dev) |
| Static files | Whitenoise |
| Server | Gunicorn |
| Payments | Stripe v11 |
| Deploy target | AWS Elastic Beanstalk |

---

## Local Setup

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd "Test cloud based cpq"
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Copy the example file and fill in your values:
```bash
cp .env.example .env
```

Edit `.env`:
```
SECRET_KEY=your-long-random-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
```

> ⚠️ **Never commit your `.env` file.** It is already excluded by `.gitignore`.

Then load it before running the server (or use `python-dotenv` — already in requirements):
```bash
export $(cat .env | xargs)      # macOS/Linux
```

### 5. Apply migrations
```bash
python manage.py migrate
```

### 6. Create a superuser (admin)
```bash
python manage.py createsuperuser
```

### 7. Run the development server
```bash
python manage.py runserver
```

Open http://127.0.0.1:8000

---

## User Roles

| Role | Access |
|---|---|
| Guest (not logged in) | Home, product catalog, request quote |
| Authenticated user | My Orders, pay approved quotes |
| Staff (`is_staff=True`) | Sales dashboard, leads, opportunities, quotes |
| Superuser | All of the above + Django Admin (`/admin/`) |

To make a user staff, go to `/admin/` → Users → select user → check `Staff status`.

---

## Stripe Test Payments

This app runs in **Stripe Test Mode**. Use these test card details on the checkout page:

| Field | Value |
|---|---|
| Card Number | `4242 4242 4242 4242` |
| Expiry Date | Any future date (e.g. `12/35`) |
| CVC | Any 3 digits (e.g. `123`) |
| Name / ZIP | Any values |

Get your own Stripe test keys at https://dashboard.stripe.com/apikeys

---

## Key URLs

| URL | Description |
|---|---|
| `/` | Home page |
| `/products/` | Product catalog |
| `/quote-request/` | Guest quote request |
| `/registration/` | New user registration |
| `/my-orders/` | My Orders (login required) |
| `/sales/` | Sales dashboard (staff only) |
| `/sales/leads/` | Lead management |
| `/sales/opportunities/` | Opportunity management |
| `/sales/quotes/` | Quote management |
| `/admin/` | Django admin |

---

## Project Structure

```
cpq_project/       — Django project settings, URLs, wsgi
crm/               — Main app: models, views, forms, admin, URLs
templates/         — All HTML templates
static/css/        — Stylesheet
requirements.txt   — Python dependencies
Procfile           — Gunicorn entry point for deployment
.env.example       — Environment variable template
```
