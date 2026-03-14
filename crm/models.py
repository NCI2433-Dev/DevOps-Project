from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


def generate_lead_reference():
    """Generate reference number like LD-2026-001"""
    current_year = timezone.now().year
    count = Lead.objects.filter(
        reference_number__startswith=f"LD-{current_year}"
    ).count() + 1
    return f"LD-{current_year}-{count:03d}"


def generate_quote_number():
    """Generate quote number like QT-2026-001"""
    current_year = timezone.now().year
    count = Quote.objects.filter(
        number__startswith=f"QT-{current_year}"
    ).count() + 1
    return f"QT-{current_year}-{count:03d}"


class Product(models.Model):
    """Sellable products"""
    name = models.CharField(max_length=200, unique=True)
    sku = models.CharField(max_length=50, unique=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sku})"


class Lead(models.Model):
    """Initial inquiry from guest or sales"""
    STATUS_CHOICES = [
        ('New', 'New'),
        ('Contacted', 'Contacted'),
        ('Qualified', 'Qualified'),
        ('Converted', 'Converted'),
        ('Rejected', 'Rejected'),
    ]
    
    SOURCE_CHOICES = [
        ('Web Form', 'Web Form'),
        ('Email', 'Email'),
        ('Phone', 'Phone'),
        ('Referral', 'Referral'),
    ]

    reference_number = models.CharField(max_length=20, unique=True, default=generate_lead_reference)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    company_name = models.CharField(max_length=150)
    product_interested = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='New')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='Web Form')
    converted_to_acct_id = models.ForeignKey(
        'Account', on_delete=models.SET_NULL, null=True, blank=True, related_name='leads'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reference_number} - {self.first_name} {self.last_name}"


class Account(models.Model):
    """Customer company/organization"""
    company_name = models.CharField(max_length=150)
    industry = models.CharField(max_length=100, blank=True)
    contact_person_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['company_name']

    def __str__(self):
        return self.company_name


class Opportunity(models.Model):
    """Sales deal/pursuit"""
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Closed', 'Closed'),
    ]
    
    STAGE_CHOICES = [
        ('Qualification', 'Qualification'),
        ('Proposal', 'Proposal'),
        ('Negotiation', 'Negotiation'),
        ('Closure', 'Closure'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='opportunities')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='Qualification')
    expected_close_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Quote(models.Model):
    """Pricing document for an opportunity"""
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Submitted', 'Submitted'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    number = models.CharField(max_length=20, unique=True, default=generate_quote_number)
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name='quotes')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    discount = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.number} - {self.opportunity.name}"

    def get_subtotal(self):
        """Calculate subtotal from line items"""
        items = self.line_items.all()
        total = sum(item.get_line_total() for item in items)
        return round(total, 2)

    def get_discount_amount(self):
        """Calculate discount amount"""
        subtotal = self.get_subtotal()
        discount_amount = subtotal * (self.discount / 100)
        return round(discount_amount, 2)

    def get_total(self):
        """Calculate final total"""
        subtotal = self.get_subtotal()
        discount_amount = self.get_discount_amount()
        return round(subtotal - discount_amount, 2)

    def can_edit(self):
        """Check if quote can be edited"""
        return self.status == 'Draft'


class QuoteLineItem(models.Model):
    """Individual product line in a quote"""
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name='line_items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    discount = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"

    def get_line_total(self):
        """Calculate line item total"""
        base_total = self.unit_price * self.quantity
        discount_amount = base_total * (self.discount / 100)
        return round(base_total - discount_amount, 2)

