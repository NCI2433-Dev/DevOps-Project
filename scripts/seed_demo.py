"""Seed script to create demo data for the CRM CPQ project.

Run with: `python manage.py runscript seed_demo` or `python scripts/seed_demo.py` (activate Django settings first).
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cpq_project.settings')
django.setup()

from decimal import Decimal
from django.contrib.auth import get_user_model

from crm.models import Product, Lead


def run():
    print('Seeding demo data...')

    # Create products
    products = [
        {'name': 'Basic Widget', 'sku': 'BW-001', 'base_price': Decimal('49.99')},
        {'name': 'Pro Widget', 'sku': 'PW-002', 'base_price': Decimal('199.99')},
    ]

    for p in products:
        prod, _ = Product.objects.get_or_create(name=p['name'], sku=p['sku'], defaults={'base_price': p['base_price']})
        print('Product:', prod)

    # Create a guest lead
    lead, _ = Lead.objects.get_or_create(
        email='guest@example.com',
        defaults={'first_name': 'Guest', 'last_name': 'User', 'company_name': 'DemoCo'}
    )
    print('Lead:', lead)

    # Create a staff user if not exists
    User = get_user_model()
    if not User.objects.filter(username='staff').exists():
        staff = User.objects.create_user('staff', email='staff@example.com', password='password')
        staff.is_staff = True
        staff.save()
        print('Created staff user: staff / password')
    else:
        print('Staff user already exists')

    print('Demo data seeded.')


if __name__ == '__main__':
    run()
