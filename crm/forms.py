"""Forms for the CRM application."""
import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from django.utils import timezone

from .models import Account, Lead, Opportunity, Quote, QuoteLineItem


class RequestQuoteForm(forms.ModelForm):
    """Guest quote request form"""
    class Meta:  # pylint: disable=too-few-public-methods
        """Metadata for RequestQuoteForm."""
        model = Lead
        fields = ['email', 'product_interested', 'quantity']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-input', 'placeholder': 'Email Address'
            }),
            'product_interested': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-input', 'placeholder': 'Number of Products',
                'type': 'number', 'min': '1'
            }),
        }

    def clean_email(self):
        """Validate that email is provided."""
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError("Email is required.")
        return email


User = get_user_model()


class RegistrationForm(UserCreationForm):  # pylint: disable=too-many-ancestors
    """User registration form with username, email and company name"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Username'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email Address'})
    )
    company_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Company Name'})
    )

    class Meta:  # pylint: disable=too-few-public-methods
        """Metadata for RegistrationForm."""
        model = User
        fields = ('username', 'email', 'company_name', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply custom styling to password fields
        self.fields['password1'].widget.attrs.update({'class': 'form-input'})
        self.fields['password2'].widget.attrs.update({'class': 'form-input'})
        self.fields['password1'].label = 'Password'
        self.fields['password2'].label = 'Confirm Password'

    def clean_username(self):
        """Check if username is already taken."""
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        """Check if email is already registered."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        """Save the user instance."""
        user = super().save(commit=True)
        return user


class LeadForm(forms.ModelForm):
    """Sales lead form for create/edit"""
    class Meta:  # pylint: disable=too-few-public-methods
        """Metadata for LeadForm."""
        model = Lead
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'company_name', 'status', 'source', 'notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'company_name': forms.TextInput(attrs={'class': 'form-input'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4}),
        }

    def clean_phone(self):
        """Validate phone number format."""
        phone = self.cleaned_data.get('phone')
        pattern = r'^\+?\d{9,15}$'
        if phone and not re.match(pattern, phone):
            raise ValidationError("Enter a valid phone number (9-15 digits).")
        return phone


class AccountForm(forms.ModelForm):
    """Account form for lead conversion"""
    class Meta:  # pylint: disable=too-few-public-methods
        """Metadata for AccountForm."""
        model = Account
        fields = [
            'company_name', 'industry', 'contact_person_name',
            'email', 'phone', 'address'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-input'}),
            'industry': forms.TextInput(attrs={'class': 'form-input'}),
            'contact_person_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'address': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
        }

    def clean_phone(self):
        """Validate phone number format."""
        phone = self.cleaned_data.get('phone')
        pattern = r'^\+?\d{9,15}$'
        if phone and not re.match(pattern, phone):
            raise ValidationError("Enter a valid phone number (9-15 digits).")
        return phone


class OpportunityForm(forms.ModelForm):
    """Opportunity form for create/edit"""
    class Meta:  # pylint: disable=too-few-public-methods
        """Metadata for OpportunityForm."""
        model = Opportunity
        fields = [
            'account', 'name', 'description', 'status', 'stage', 'expected_close_date'
        ]
        widgets = {
            'account': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'stage': forms.Select(attrs={'class': 'form-select'}),
            'expected_close_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
        }

    def clean_expected_close_date(self):
        """Ensure the expected close date is not in the past."""
        date = self.cleaned_data.get('expected_close_date')
        if date and date < timezone.now().date():
            raise ValidationError("Expected close date must be in the future.")
        return date


class QuoteForm(forms.ModelForm):
    """Quote form for create/edit"""
    class Meta:  # pylint: disable=too-few-public-methods
        """Metadata for QuoteForm."""
        model = Quote
        fields = ['opportunity', 'discount', 'notes']
        widgets = {
            'opportunity': forms.Select(attrs={'class': 'form-select'}),
            'discount': forms.NumberInput(attrs={
                'class': 'form-input', 'min': '0', 'max': '100', 'step': '0.01'
            }),
            'notes': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4}),
        }

    def clean_discount(self):
        """Validate discount percentage."""
        discount = self.cleaned_data.get('discount')
        if discount and (discount < 0 or discount > 100):
            raise ValidationError("Discount must be between 0 and 100.")
        return discount


class QuoteLineItemForm(forms.ModelForm):
    """Quote line item form"""
    class Meta:  # pylint: disable=too-few-public-methods
        """Metadata for QuoteLineItemForm."""
        model = QuoteLineItem
        fields = ['product', 'quantity', 'unit_price', 'discount']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-input', 'min': '1'}),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-input', 'min': '0', 'step': '0.01'
            }),
            'discount': forms.NumberInput(attrs={
                'class': 'form-input', 'min': '0', 'max': '100', 'step': '0.01'
            }),
        }

    def clean_quantity(self):
        """Ensure quantity is at least 1."""
        qty = self.cleaned_data.get('quantity')
        if qty and qty < 1:
            raise ValidationError("Quantity must be at least 1.")
        return qty

    def clean_discount(self):
        """Validate line item discount percentage."""
        discount = self.cleaned_data.get('discount')
        if discount and (discount < 0 or discount > 100):
            raise ValidationError("Discount must be between 0 and 100.")
        return discount


# Formset for inline quote line items
QuoteLineItemFormSet = inlineformset_factory(
    Quote,
    QuoteLineItem,
    form=QuoteLineItemForm,
    extra=3,
    can_delete=True
)
