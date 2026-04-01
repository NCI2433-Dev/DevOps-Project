"""Tests for the CRM application."""
from datetime import timedelta

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from .models import Product, Lead, Account, Opportunity, Quote, QuoteLineItem
from .forms import (
    RequestQuoteForm, RegistrationForm, LeadForm,
    OpportunityForm, QuoteForm
)


class ProductModelTests(TestCase):
    """Tests for Product model."""

    def setUp(self):
        """Create test product."""
        self.product = Product.objects.create(
            name="Test Product",
            sku="TEST001",
            base_price=100.00,
            description="Test Description"
        )

    def test_product_creation(self):
        """Test product creation."""
        self.assertEqual(self.product.name, "Test Product")
        self.assertEqual(self.product.sku, "TEST001")
        self.assertEqual(self.product.base_price, 100.00)

    def test_product_str(self):
        """Test product string representation."""
        self.assertEqual(str(self.product), "Test Product (TEST001)")

    def test_product_is_active_default(self):
        """Test product is active by default."""
        self.assertTrue(self.product.is_active)

    def test_product_unique_name(self):
        """Test product name must be unique."""
        with self.assertRaises(Exception):
            Product.objects.create(
                name="Test Product",
                sku="TEST002",
                base_price=50.00
            )

    def test_product_unique_sku(self):
        """Test product SKU must be unique."""
        with self.assertRaises(Exception):
            Product.objects.create(
                name="Another Product",
                sku="TEST001",
                base_price=50.00
            )


class LeadModelTests(TestCase):
    """Tests for Lead model."""

    def setUp(self):
        """Create test lead."""
        self.lead = Lead.objects.create(
            email="test@example.com",
            company_name="Test Company",
            status="New"
        )

    def test_lead_creation(self):
        """Test lead creation."""
        self.assertEqual(self.lead.email, "test@example.com")
        self.assertEqual(self.lead.status, "New")

    def test_lead_reference_number_generated(self):
        """Test lead reference number is auto-generated."""
        self.assertIsNotNone(self.lead.reference_number)
        self.assertTrue(self.lead.reference_number.startswith("LD-"))

    def test_lead_str(self):
        """Test lead string representation."""
        expected = f"{self.lead.reference_number} - test@example.com"
        self.assertEqual(str(self.lead), expected)

    def test_lead_status_choices(self):
        """Test lead status choices."""
        self.assertEqual(self.lead.status, "New")
        self.lead.status = "Qualified"
        self.lead.save()
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.status, "Qualified")


class AccountModelTests(TestCase):
    """Tests for Account model."""

    def setUp(self):
        """Create test account."""
        self.account = Account.objects.create(
            company_name="Test Company",
            contact_person_name="John Doe",
            email="contact@example.com",
            phone="555-1234"
        )

    def test_account_creation(self):
        """Test account creation."""
        self.assertEqual(self.account.company_name, "Test Company")
        self.assertEqual(self.account.contact_person_name, "John Doe")

    def test_account_str(self):
        """Test account string representation."""
        self.assertEqual(str(self.account), "Test Company")


class OpportunityModelTests(TestCase):
    """Tests for Opportunity model."""

    def setUp(self):
        """Create test opportunity."""
        self.account = Account.objects.create(
            company_name="Test Company",
            contact_person_name="John Doe",
            email="contact@example.com",
            phone="555-1234"
        )
        self.opportunity = Opportunity.objects.create(
            account=self.account,
            name="Test Deal",
            status="Open",
            stage="Qualification",
            expected_close_date=timezone.now().date() + timedelta(days=30)
        )

    def test_opportunity_creation(self):
        """Test opportunity creation."""
        self.assertEqual(self.opportunity.name, "Test Deal")
        self.assertEqual(self.opportunity.status, "Open")
        self.assertEqual(self.opportunity.stage, "Qualification")

    def test_opportunity_str(self):
        """Test opportunity string representation."""
        self.assertEqual(str(self.opportunity), "Test Deal")


class QuoteModelTests(TestCase):
    """Tests for Quote model."""

    def setUp(self):
        """Create test quote with line items."""
        self.product = Product.objects.create(
            name="Test Product",
            sku="TEST001",
            base_price=100.00
        )
        self.account = Account.objects.create(
            company_name="Test Company",
            contact_person_name="John Doe",
            email="contact@example.com",
            phone="555-1234"
        )
        self.opportunity = Opportunity.objects.create(
            account=self.account,
            name="Test Deal",
            status="Open",
            stage="Qualification",
            expected_close_date=timezone.now().date() + timedelta(days=30)
        )
        self.quote = Quote.objects.create(
            opportunity=self.opportunity,
            status="Draft",
            discount=10
        )
        self.line_item = QuoteLineItem.objects.create(
            quote=self.quote,
            product=self.product,
            quantity=2,
            unit_price=100.00
        )

    def test_quote_creation(self):
        """Test quote creation."""
        self.assertEqual(self.quote.status, "Draft")
        self.assertEqual(self.quote.discount, 10)

    def test_quote_number_generated(self):
        """Test quote number is auto-generated."""
        self.assertIsNotNone(self.quote.number)
        self.assertTrue(self.quote.number.startswith("QT-"))

    def test_quote_str(self):
        """Test quote string representation."""
        expected = f"{self.quote.number} - Test Deal"
        self.assertEqual(str(self.quote), expected)

    def test_quote_get_subtotal(self):
        """Test quote subtotal calculation."""
        subtotal = self.quote.get_subtotal()
        self.assertEqual(subtotal, 200.00)  # 2 * 100

    def test_quote_get_discount_amount(self):
        """Test quote discount amount calculation."""
        discount_amount = self.quote.get_discount_amount()
        self.assertEqual(discount_amount, 20.00)  # 200 * 10%

    def test_quote_get_total(self):
        """Test quote total calculation."""
        total = self.quote.get_total()
        self.assertEqual(total, 180.00)  # 200 - 20

    def test_quote_can_edit_draft(self):
        """Test quote can be edited when draft."""
        self.assertTrue(self.quote.can_edit())

    def test_quote_cannot_edit_submitted(self):
        """Test quote cannot be edited when submitted."""
        self.quote.status = "Submitted"
        self.assertFalse(self.quote.can_edit())


class RequestQuoteFormTests(TestCase):
    """Tests for RequestQuoteForm."""

    def setUp(self):
        """Create test product."""
        self.product = Product.objects.create(
            name="Test Product",
            sku="TEST001",
            base_price=100.00
        )

    def test_valid_form(self):
        """Test valid request quote form."""
        form_data = {
            'email': 'guest@example.com',
            'product_interested': self.product.id,
            'quantity': 10
        }
        form = RequestQuoteForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_email_required(self):
        """Test email is required."""
        form_data = {
            'email': '',
            'product_interested': self.product.id,
            'quantity': 10
        }
        form = RequestQuoteForm(data=form_data)
        self.assertFalse(form.is_valid())


class RegistrationFormTests(TestCase):
    """Tests for RegistrationForm."""

    def test_valid_registration_form(self):
        """Test valid registration form."""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'company_name': 'Test Company',
            'password1': 'SecurePassword123!',
            'password2': 'SecurePassword123!'
        }
        form = RegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_duplicate_username(self):
        """Test duplicate username validation."""
        User.objects.create_user(
            username='testuser',
            email='existing@example.com',
            password='password'
        )
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'company_name': 'Test Company',
            'password1': 'SecurePassword123!',
            'password2': 'SecurePassword123!'
        }
        form = RegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_duplicate_email(self):
        """Test duplicate email validation."""
        User.objects.create_user(
            username='existing',
            email='test@example.com',
            password='password'
        )
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'company_name': 'Test Company',
            'password1': 'SecurePassword123!',
            'password2': 'SecurePassword123!'
        }
        form = RegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())


class LeadFormTests(TestCase):
    """Tests for LeadForm."""

    def test_valid_lead_form(self):
        """Test valid lead form."""
        form_data = {
            'email': 'test@example.com',
            'company_name': 'Test Company',
            'status': 'New'
        }
        form = LeadForm(data=form_data)
        self.assertTrue(form.is_valid())


class OpportunityFormTests(TestCase):
    """Tests for OpportunityForm."""

    def setUp(self):
        """Create test account."""
        self.account = Account.objects.create(
            company_name="Test Company",
            contact_person_name="John Doe",
            email="contact@example.com",
            phone="555-1234"
        )

    def test_valid_opportunity_form(self):
        """Test valid opportunity form."""
        future_date = timezone.now().date() + timedelta(days=30)
        form_data = {
            'account': self.account.id,
            'name': 'Test Deal',
            'description': 'Test Description',
            'status': 'Open',
            'stage': 'Qualification',
            'expected_close_date': future_date
        }
        form = OpportunityForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_past_close_date_invalid(self):
        """Test past close date is invalid."""
        past_date = timezone.now().date() - timedelta(days=1)
        form_data = {
            'account': self.account.id,
            'name': 'Test Deal',
            'description': 'Test Description',
            'status': 'Open',
            'stage': 'Qualification',
            'expected_close_date': past_date
        }
        form = OpportunityForm(data=form_data)
        self.assertFalse(form.is_valid())


class QuoteFormTests(TestCase):
    """Tests for QuoteForm."""

    def setUp(self):
        """Create test opportunity."""
        self.account = Account.objects.create(
            company_name="Test Company",
            contact_person_name="John Doe",
            email="contact@example.com",
            phone="555-1234"
        )
        self.opportunity = Opportunity.objects.create(
            account=self.account,
            name="Test Deal",
            status="Open",
            stage="Qualification",
            expected_close_date=timezone.now().date() + timedelta(days=30)
        )

    def test_valid_quote_form(self):
        """Test valid quote form."""
        form_data = {
            'opportunity': self.opportunity.id,
            'discount': 10,
            'notes': 'Test Notes'
        }
        form = QuoteForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_discount(self):
        """Test invalid discount validation."""
        form_data = {
            'opportunity': self.opportunity.id,
            'discount': 150,  # > 100
            'notes': 'Test Notes'
        }
        form = QuoteForm(data=form_data)
        self.assertFalse(form.is_valid())


class ViewsAuthenticationTests(TestCase):
    """Tests for views authentication."""

    def setUp(self):
        """Set up test client and user."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )

    def test_home_view(self):
        """Test home page is accessible."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_product_list_view(self):
        """Test product list is accessible."""
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)

    def test_request_quote_view(self):
        """Test request quote view is accessible."""
        response = self.client.get(reverse('request_quote'))
        self.assertEqual(response.status_code, 200)

    def test_sales_dashboard_requires_staff(self):
        """Test sales dashboard requires staff permission."""
        response = self.client.get(reverse('sales_dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_lead_list_requires_staff(self):
        """Test lead list requires staff permission."""
        response = self.client.get(reverse('lead_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_staff_can_access_dashboard(self):
        """Test staff user can access dashboard."""
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get(reverse('sales_dashboard'))
        self.assertEqual(response.status_code, 200)


class RegisterViewTests(TestCase):
    """Tests for registration view."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_registration_page_loads(self):
        """Test registration page loads."""
        response = self.client.get(reverse('registration'))
        self.assertEqual(response.status_code, 200)

    def test_successful_registration(self):
        """Test successful user registration."""
        response = self.client.post(reverse('registration'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'company_name': 'New Company',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(User.objects.filter(username='newuser').exists())


class LeadViewTests(TestCase):
    """Tests for lead views."""

    def setUp(self):
        """Set up test staff user and lead."""
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        self.product = Product.objects.create(
            name="Test Product",
            sku="TEST001",
            base_price=100.00
        )
        self.lead = Lead.objects.create(
            email="lead@example.com",
            company_name="Lead Company",
            status="New"
        )
        self.client.login(username='staffuser', password='testpass123')

    def test_lead_list_view(self):
        """Test lead list view."""
        response = self.client.get(reverse('lead_list'))
        self.assertEqual(response.status_code, 200)

    def test_lead_detail_view(self):
        """Test lead detail view."""
        response = self.client.get(reverse('lead_detail', args=[self.lead.id]))
        self.assertEqual(response.status_code, 200)

    def test_lead_create_view(self):
        """Test lead create view."""
        response = self.client.get(reverse('lead_create'))
        self.assertEqual(response.status_code, 200)

    def test_lead_create_post(self):
        """Test create lead via POST."""
        response = self.client.post(reverse('lead_create'), {
            'email': 'new@example.com',
            'company_name': 'New Lead Company',
            'status': 'New'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Lead.objects.filter(email='new@example.com').exists())

    def test_lead_update_view(self):
        """Test lead update view."""
        response = self.client.get(reverse('lead_update', args=[self.lead.id]))
        self.assertEqual(response.status_code, 200)

    def test_lead_delete_view(self):
        """Test lead delete view."""
        response = self.client.get(reverse('lead_delete', args=[self.lead.id]))
        self.assertEqual(response.status_code, 200)


class UserLogoutTests(TestCase):
    """Tests for user logout."""

    def setUp(self):
        """Set up test client and user."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_user_logout(self):
        """Test user logout."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
