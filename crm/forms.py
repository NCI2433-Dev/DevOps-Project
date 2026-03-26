"""Forms for the CRM application."""
from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
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
                'class': 'form-input', 'placeholder': 'Qty (kg/tons/units)',
                'type': 'number', 'min': '1'
            }),
        }
        labels = {
            'product_interested': 'Food Product',
            'quantity': 'Quantity (kg/tons/units)',
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



class LeadForm(forms.ModelForm):
    """Sales lead form for create/edit"""
    class Meta:  # pylint: disable=too-few-public-methods
        """Metadata for LeadForm."""
        model = Lead
        fields = ['email', 'company_name', 'status']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'company_name': forms.TextInput(attrs={'class': 'form-input'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'company_name': 'Company / Restaurant Name',
        }


class AccountForm(forms.ModelForm):
    """Account form for lead conversion"""
    opportunity_notes = forms.CharField(
        required=False,
        label='Opportunity Notes',
        widget=forms.Textarea(attrs={
            'class': 'form-textarea',
            'rows': 3,
            'placeholder': 'E.g. delivery requirements, preferred schedule, product quantities…'
        })
    )

    class Meta:  # pylint: disable=too-few-public-methods
        """Metadata for AccountForm."""
        model = Account
        fields = ['company_name', 'email']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
        }


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
        labels = {
            'name': 'Deal Name (e.g. March Poultry Supply)',
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
                'class': 'form-input', 'min': '0', 'max': '100', 'step': '0.01',
                'placeholder': '0'
            }),
            'notes': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3,
                                            'placeholder': 'Internal notes (optional)'}),
        }
        labels = {
            'opportunity': 'Linked Deal / Customer'
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
        labels = {
            'product': 'Food Product',
            'quantity': 'Quantity (kg/tons/units)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].empty_label = None
        
        # Attempt to prefill unit_price if this is a new empty form
        first_product = self.fields['product'].queryset.first()
        if not self.initial.get('unit_price') and first_product:
            self.initial['unit_price'] = first_product.base_price
            
        if not self.initial.get('quantity'):
            self.initial['quantity'] = 1
        if not self.initial.get('discount'):
            self.initial['discount'] = 0

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
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class CustomAuthForm(AuthenticationForm):
    """Custom auth form that allows log in with username or email."""
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username is not None and password:
            user_model = get_user_model()
            # If the value entered exists as an email, use their actual username
            try:
                user_match = user_model.objects.get(email__iexact=username)
                username_to_auth = user_match.username
            except (user_model.DoesNotExist, user_model.MultipleObjectsReturned):
                username_to_auth = username

            self.user_cache = authenticate(self.request, username=username_to_auth, password=password)
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
