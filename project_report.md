# Cloud-Based CPQ System – Project Report

## 1. Project Overview
This project is a cloud-based Customer Relationship Management (CRM) and Configure, Price, Quote (CPQ) web application built using the Django framework. The system manages the end-to-end sales pipeline, starting from initial lead capture (via web forms or manual entry) through qualification, opportunity management, and final quote generation. It provides a centralized platform for sales teams to track customer interactions, manage product catalogs, and automate the creation of pricing documents with discount calculations.

## 2. System Purpose
In B2B sales, managing customer inquiries, tracking deal progress, and generating accurate pricing quotes are often disjointed processes handled across multiple spreadsheets and emails. This system solves that real-world problem by providing a unified, cloud-accessible platform. It allows businesses to:
- Capture and standardize lead data systematically.
- Transition qualified leads into manageable accounts and sales opportunities.
- Maintain a structured product catalog with base pricing.
- Generate standardized, accurate quotes for customers to ensure pricing consistency and improve sales team efficiency.

## 3. System Architecture
The application follows a traditional multi-tier architectural pattern utilizing the Django MTV (Model-Template-View) framework:

*   **Frontend (Templates, HTML, CSS):** 
    The presentation layer is handled by Django templates (`templates/` directory) supplemented by static assets (`static/` directory). It features distinct views for both guests (product catalog, quote requests, registration) and authenticated sales users (dashboards, CRUD interfaces for leads, opportunities, and quotes).
*   **Backend (Django Views and Logic):** 
    The application logic is primarily contained within the `crm` application. It routes incoming HTTP requests via `urls.py`, processes them in `views.py`, and enforces business rules (such as quote subtotal/discount calculations and automated reference number generation).
*   **Database (Django Models):** 
    The data layer is managed by Django's ORM, mapping Python classes in `models.py` to relational database tables. The system currently utilizes SQLite (`db.sqlite3`) for local development, which is typically replaced by a robust relational database (like PostgreSQL) in production.
*   **Cloud Deployment Concept:** 
    While currently configured for local execution (`django.core.servers.basehttp.WSGIServer` via `manage.py runserver`), the presence of `requirements.txt` and a standard `wsgi.py` (implied by the `cpq_project` structure) indicates the application is packaged for standard cloud PaaS deployment environments (e.g., Heroku, AWS Elastic Beanstalk, or Docker containers). 

## 4. System Modules
Based on the Django application structure (`cpq_project` and `crm`), the system is logically partitioned into the following areas of responsibility:

*   **Authentication & Access Module:** Handles user sessions, login/logout (`accounts/login/`, `accounts/logout/`), and differentiates between guest access and the internal sales dashboard.
*   **Guest/Customer Facing Module:** Manages public-facing views such as the product catalog (`/products/`), lead intake form (`/quote-request/`), and customer registration.
*   **Lead Management Module:** Provides internal tools (`/sales/leads/`) for the sales team to create, track, edit, and convert initial inquiries into established accounts.
*   **Sales Opportunity Module:** Manages the pipeline of active deals (`/sales/opportunities/`), tracking them through stages (Qualification, Proposal, Negotiation, Closure).
*   **Quote & Configuration Module:** Handles the generation and lifecycle of pricing documents (`/sales/quotes/`), linking opportunities to specific products, calculating line-item totals, and managing discounts.

## 5. Database Design
The relational database schema is centered around the sales lifecycle. The main entities (models) include:

*   **Product:** Represents sellable items. 
    *   *Fields:* `name` (unique), `sku` (unique), `base_price`, `is_active`.
*   **Lead:** Represents initial customer inquiries.
    *   *Fields:* `reference_number` (auto-generated), contact info (`first_name`, `email`, etc.), `status` (New, Contacted, Qualified, etc.), `source`.
    *   *Relationships:* Foreign Key to `Product` (interest) and `Account` (if converted).
*   **Account:** Represents established customer organizations.
    *   *Fields:* `company_name`, `industry`, `contact_person_name`, `email`, `address`.
*   **Opportunity:** Represents a specific sales deal tied to an account.
    *   *Fields:* `name`, `status` (Open/Closed), `stage`, `expected_close_date`.
    *   *Relationships:* Foreign Key to `Account`.
*   **Quote:** Represents a pricing proposal generated for an opportunity.
    *   *Fields:* `number` (auto-generated), `status` (Draft, Submitted, Approved, Rejected), `discount`.
    *   *Relationships:* Foreign Key to `Opportunity`. Integrates custom methods for calculating subtotals and final totals.
*   **QuoteLineItem:** Represents the individual products and quantities comprising a quote.
    *   *Fields:* `quantity`, `unit_price`, `discount`.
    *   *Relationships:* Foreign Keys linking resolving the many-to-many relationship between `Quote` and `Product`.

## 6. System Workflow
The typical user interaction flows as follows:

1.  **Guest Intake:** A prospective customer browses the product catalog (`/products/`) and submits a "quote request" (`/quote-request/`). 
2.  **Lead Creation:** The system automatically saves this request as a `Lead` with a "New" status and an auto-generated reference number (e.g., LD-2026-001).
3.  **Sales Review (Login):** An internal sales representative logs into the system (`/accounts/login/`) and accesses the internal sales dashboard (`/sales/`).
4.  **Lead Qualification & Conversion:** The rep reviews the lead (`/sales/leads/`), contacts the customer, updates the status, and upon qualification, converts the lead into an established `Account`.
5.  **Opportunity Tracking:** An `Opportunity` is created under the Account to track the specific deal through its sales stages (Qualification → Negotiation).
6.  **Quote Generation:** The rep generates a `Quote` for the Opportunity, adding specific `Product`s as `QuoteLineItem`s, adjusting quantities, and apply necessary discounts.
7.  **Quote Finalization:** The quote status is updated (Draft → Submitted → Approved) as negotiations conclude, providing the final pricing document for the customer.

## 7. Key Features
Based on the provided models and URL configurations, the system implements the following core functionalities:
*   **Public Product Catalog:** Unauthenticated views for browsing available products and services.
*   **Automated Lead Capture:** Web forms that directly ingest inquiries into the CRM database.
*   **Automated Reference Numbering:** Auto-generation of standardized ID formats for leads (LD-YYYY-001) and quotes (QT-YYYY-001).
*   **Sales Pipeline Management:** CRUD (Create, Read, Update, Delete) interfaces for leads, opportunities, and quotes via a dedicated sales dashboard.
*   **Lead Conversion:** Workflow to graduate a "Lead" into an established "Account".
*   **Dynamic Pricing Calculation:** Built-in model methods (e.g., `get_subtotal()`, `get_total()`) to compute line-item totals, apply percentage discounts, and calculate final quote amounts securely on the backend.
*   **Quote Lifecycle Management:** Tracking quote states (Draft, Submitted, Approved) with enforced editing restrictions based on status.
