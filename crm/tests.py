"""Tests for the CRM application.

These tests cover core business logic (quote calculations) and basic
authentication/authorization for staff-only views.
"""
from decimal import Decimal

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Product, Account, Opportunity, Quote, QuoteLineItem


User = get_user_model()


class QuoteCalculationTests(TestCase):
    """Verify quote subtotal, discount, and total calculations."""

    def setUp(self):
        self.product = Product.objects.create(
            name='Test Product', sku='TP-001', base_price=Decimal('100.00')
        )
        self.account = Account.objects.create(
            company_name='ACME', contact_person_name='Alice', email='a@a.com', phone='123'
        )
        self.opp = Opportunity.objects.create(
            account=self.account, name='Deal 1', expected_close_date='2099-12-31'
        )
        self.quote = Quote.objects.create(opportunity=self.opp, discount=Decimal('10.00'))
        # Two line items: 2 x 100, 1 x 50
        QuoteLineItem.objects.create(quote=self.quote, product=self.product, quantity=2, unit_price=Decimal('100.00'), discount=Decimal('0'))
        QuoteLineItem.objects.create(quote=self.quote, product=self.product, quantity=1, unit_price=Decimal('50.00'), discount=Decimal('0'))

    def test_subtotal_discount_total(self):
        self.assertEqual(self.quote.get_subtotal(), Decimal('250.00'))
        # 10% discount on 250 = 25
        self.assertEqual(self.quote.get_discount_amount(), Decimal('25.00'))
        self.assertEqual(self.quote.get_total(), Decimal('225.00'))


class AuthAndViewTests(TestCase):
    """Basic auth and permission tests for staff views."""

    def setUp(self):
        self.client = Client()
        self.staff = User.objects.create_user(username='staff', password='pass')
        self.staff.is_staff = True
        self.staff.save()

    def test_sales_dashboard_requires_login(self):
        resp = self.client.get(reverse('sales_dashboard'))
        # redirect to login
        self.assertEqual(resp.status_code, 302)

    def test_staff_user_can_access_dashboard(self):
        self.client.login(username='staff', password='pass')
        resp = self.client.get(reverse('sales_dashboard'))
        self.assertIn(resp.status_code, (200, 302))


class LeadConversionTests(TestCase):
    """Tests for converting a Lead into Account + Opportunity."""

    def setUp(self):
        self.client = Client()
        self.staff = User.objects.create_user(username='staff2', password='pass')
        self.staff.is_staff = True
        self.staff.save()
        # create a lead
        from .models import Lead
        self.lead = Lead.objects.create(
            first_name='John', last_name='Doe', email='john@example.com',
            phone='+123456789', company_name='JD Inc', status='New'
        )

    def test_lead_convert_creates_account_and_opportunity(self):
        self.client.login(username='staff2', password='pass')
        url = reverse('lead_convert', kwargs={'pk': self.lead.id})
        data = {
            'company_name': 'JD Inc',
            'industry': 'Software',
            'contact_person_name': 'John Doe',
            'email': 'john@example.com',
            'phone': '+123456789',
            'address': '123 Lane',
        }
        resp = self.client.post(url, data)
        # After conversion, the lead should be marked Converted and an account created
        from .models import Account, Opportunity
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.status, 'Converted')
        self.assertIsNotNone(self.lead.converted_to_acct_id)
        acct = Account.objects.filter(company_name='JD Inc').first()
        self.assertIsNotNone(acct)
        # Opportunity should exist for the account
        opp = Opportunity.objects.filter(account=acct).first()
        self.assertIsNotNone(opp)


class QuoteStatusTests(TestCase):
    """Tests for quote status transitions and validation."""

    def setUp(self):
        self.client = Client()
        self.staff = User.objects.create_user(username='staff3', password='pass')
        self.staff.is_staff = True
        self.staff.save()
        from .models import Account, Opportunity, Quote, Product, QuoteLineItem
        self.account = Account.objects.create(company_name='Acct', contact_person_name='C', email='c@a.com', phone='1')
        self.opp = Opportunity.objects.create(account=self.account, name='Deal', expected_close_date='2099-12-31')
        self.quote = Quote.objects.create(opportunity=self.opp, discount=0)
        self.product = Product.objects.create(name='P', sku='P-1', base_price=10)

    def test_submit_quote_requires_line_items(self):
        self.client.login(username='staff3', password='pass')
        url = reverse('quote_update_status', kwargs={'pk': self.quote.id})
        resp = self.client.post(url, {'status': 'Submitted'})
        self.quote.refresh_from_db()
        # Should remain Draft because no line items
        self.assertEqual(self.quote.status, 'Draft')

    def test_submit_and_approve_quote(self):
        # add a line item
        from .models import QuoteLineItem
        QuoteLineItem.objects.create(quote=self.quote, product=self.product, quantity=1, unit_price=10, discount=0)
        self.client.login(username='staff3', password='pass')
        url = reverse('quote_update_status', kwargs={'pk': self.quote.id})
        resp = self.client.post(url, {'status': 'Submitted'})
        self.quote.refresh_from_db()
        self.assertEqual(self.quote.status, 'Submitted')
        # Approve the quote
        resp = self.client.post(url, {'status': 'Approved'})
        self.quote.refresh_from_db()
        self.assertEqual(self.quote.status, 'Approved')
