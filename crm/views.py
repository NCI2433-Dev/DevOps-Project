from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import logout
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from functools import wraps
from .models import Lead, Account, Opportunity, Quote, QuoteLineItem, Product
from .forms import (
    RequestQuoteForm, LeadForm, AccountForm, OpportunityForm, 
    QuoteForm, QuoteLineItemFormSet, RegistrationForm
)


def staff_required(view_func):
    """Decorator to check if user is staff"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            messages.error(request, "You don't have permission to access this page.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def superuser_required(view_func):
    """Decorator to check if user is superuser"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            messages.error(request, "Admin access required.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


# ==================== GUEST VIEWS ====================

def home(request):
    """Home page"""
    return render(request, 'home.html')


def product_list(request):
    """Product catalog (public, read-only)"""
    products = Product.objects.filter(is_active=True)
    return render(request, 'product_list.html', {'products': products})


def product_detail(request, id):
    """Product detail view"""
    product = get_object_or_404(Product, id=id)
    return render(request, 'product_detail.html', {'product': product})


def request_quote(request):
    """Guest quote request form"""
    # If product_id is in query string, pre-select it
    product_id = request.GET.get('product_id')
    initial_data = {}
    if product_id:
        try:
            product = Product.objects.get(id=product_id)
            initial_data['product_interested'] = product
        except Product.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = RequestQuoteForm(request.POST)
        if form.is_valid():
            lead = form.save(commit=False)
            # Set default values for fields not in guest form
            lead.first_name = 'Guest'
            lead.last_name = 'Inquiry'
            lead.company_name = 'Not Provided'
            lead.phone = 'N/A'
            lead.status = 'New'
            lead.source = 'Web Form'
            lead.save()
            return redirect('quote_request_success', ref_num=lead.reference_number)
    else:
        form = RequestQuoteForm(initial=initial_data)
    return render(request, 'request_quote.html', {'form': form})

def registration(request):
    """User registration form"""
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create associated Lead record
            lead = Lead.objects.create(
                first_name=form.cleaned_data.get('username', 'User'),
                last_name='',
                email=user.email,
                phone='',
                company_name=form.cleaned_data.get('company_name', ''),
                status='New',
                source='Registration'
            )
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RegistrationForm()
    
    return render(request, 'registration.html', {'form': form})


def user_logout(request):
    """Custom logout view - logs out user and redirects to home"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


def quote_request_success(request, ref_num):
    """Quote request success page (shows only reference number for privacy)"""
    lead = get_object_or_404(Lead, reference_number=ref_num)
    return render(request, 'quote_request_success.html', {'reference_number': ref_num})


@login_required
def my_orders(request):
    """Authenticated user's order/quote status and payment tracking"""
    # Get all leads associated with this user by email
    user_leads = Lead.objects.filter(email=request.user.email)
    
    # Get associated quotes through leads
    user_quotes = Quote.objects.filter(
        opportunity__account__leads__email=request.user.email
    )
    
    # Alternative: If leads are converted to accounts, get quotes
    user_accounts = Account.objects.filter(email=request.user.email)
    account_quotes = Quote.objects.filter(
        opportunity__account__in=user_accounts
    )
    
    # Combine all quotes (remove distinct before combining, then add after)
    all_quotes = (user_quotes | account_quotes).distinct().order_by('-created_at')
    
    context = {
        'leads': user_leads,
        'quotes': all_quotes,
        'orders_count': all_quotes.count(),
    }
    return render(request, 'my_orders.html', context)


# ==================== SALES VIEWS ====================

@login_required
@staff_required
def sales_dashboard(request):
    """Sales dashboard with KPIs"""
    leads_new = Lead.objects.filter(status='New').count()
    leads_contacted = Lead.objects.filter(status='Contacted').count()
    leads_qualified = Lead.objects.filter(status='Qualified').count()
    leads_converted = Lead.objects.filter(status='Converted').count()
    
    opportunities_open = Opportunity.objects.filter(status='Open').count()
    
    quotes_draft = Quote.objects.filter(status='Draft').count()
    quotes_submitted = Quote.objects.filter(status='Submitted').count()
    quotes_approved = Quote.objects.filter(status='Approved').count()
    
    recent_quotes = Quote.objects.all()[:5]
    
    context = {
        'leads_new': leads_new,
        'leads_contacted': leads_contacted,
        'leads_qualified': leads_qualified,
        'leads_converted': leads_converted,
        'opportunities_open': opportunities_open,
        'quotes_draft': quotes_draft,
        'quotes_submitted': quotes_submitted,
        'quotes_approved': quotes_approved,
        'recent_quotes': recent_quotes,
    }
    return render(request, 'sales_dashboard.html', context)


# ==================== LEAD VIEWS ====================

@login_required
@staff_required
def lead_list(request):
    """Lead list with filtering"""
    status_filter = request.GET.get('status', '')
    
    leads = Lead.objects.all()
    if status_filter:
        leads = leads.filter(status=status_filter)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(leads, 10)
    page_num = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_num)
    
    context = {
        'page_obj': page_obj,
        'leads': page_obj.object_list,
        'status_filter': status_filter,
        'status_choices': Lead.STATUS_CHOICES,
    }
    return render(request, 'lead_list.html', context)


@login_required
@staff_required
def lead_detail(request, id):
    """Lead detail view"""
    lead = get_object_or_404(Lead, id=id)
    return render(request, 'lead_detail.html', {'lead': lead})


@login_required
@staff_required
def lead_create(request):
    """Create new lead"""
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            lead = form.save()
            messages.success(request, f"Lead {lead.reference_number} created successfully.")
            return redirect('lead_detail', id=lead.id)
    else:
        form = LeadForm()
    return render(request, 'lead_form.html', {'form': form, 'title': 'Create Lead'})


@login_required
@staff_required
def lead_update(request, id):
    """Edit lead"""
    lead = get_object_or_404(Lead, id=id)
    if request.method == 'POST':
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            lead = form.save()
            messages.success(request, "Lead updated successfully.")
            return redirect('lead_detail', id=lead.id)
    else:
        form = LeadForm(instance=lead)
    return render(request, 'lead_form.html', {'form': form, 'title': 'Edit Lead', 'lead': lead})


@login_required
@staff_required
def lead_delete(request, id):
    """Soft-delete lead (mark as Rejected)"""
    lead = get_object_or_404(Lead, id=id)
    if request.method == 'POST':
        lead.status = 'Rejected'
        lead.save()
        messages.success(request, f"Lead {lead.reference_number} has been rejected.")
        return redirect('lead_list')
    return render(request, 'confirm_delete.html', {'object': lead, 'type': 'Lead'})


@login_required
@staff_required
def lead_convert(request, id):
    """Convert lead to Account + Opportunity"""
    lead = get_object_or_404(Lead, id=id)
    
    if lead.converted_to_acct_id:
        messages.warning(request, "This lead has already been converted.")
        return redirect('lead_detail', id=id)
    
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            # Create Account
            account = form.save()
            
            # Create Opportunity
            opp = Opportunity.objects.create(
                account=account,
                name=f"{lead.company_name} - {timezone.now().strftime('%B %Y')}",
                status='Open',
                stage='Qualification',
                expected_close_date=timezone.now().date() + timedelta(days=30)
            )
            
            # Update Lead
            lead.status = 'Converted'
            lead.converted_to_acct_id = account
            lead.save()
            
            messages.success(request, f"Lead converted. Account created: {account.company_name}")
            return redirect('opportunity_detail', id=opp.id)
    else:
        # Pre-fill form with lead data
        form = AccountForm(initial={
            'company_name': lead.company_name,
            'contact_person_name': f"{lead.first_name} {lead.last_name}",
            'email': lead.email,
            'phone': lead.phone,
        })
    
    return render(request, 'lead_convert.html', {'form': form, 'lead': lead})


# ==================== OPPORTUNITY VIEWS ====================

@login_required
@staff_required
def opportunity_list(request):
    """Opportunity list with filtering"""
    status_filter = request.GET.get('status', '')
    stage_filter = request.GET.get('stage', '')
    
    opportunities = Opportunity.objects.all()
    if status_filter:
        opportunities = opportunities.filter(status=status_filter)
    if stage_filter:
        opportunities = opportunities.filter(stage=stage_filter)
    
    from django.core.paginator import Paginator
    paginator = Paginator(opportunities, 10)
    page_num = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_num)
    
    context = {
        'page_obj': page_obj,
        'opportunities': page_obj.object_list,
        'status_filter': status_filter,
        'stage_filter': stage_filter,
        'status_choices': Opportunity.STATUS_CHOICES,
        'stage_choices': Opportunity.STAGE_CHOICES,
    }
    return render(request, 'opportunity_list.html', context)


@login_required
@staff_required
def opportunity_detail(request, id):
    """Opportunity detail view"""
    opp = get_object_or_404(Opportunity, id=id)
    quotes = opp.quotes.all()
    return render(request, 'opportunity_detail.html', {'opportunity': opp, 'quotes': quotes})


@login_required
@staff_required
def opportunity_create(request):
    """Create new opportunity"""
    if request.method == 'POST':
        form = OpportunityForm(request.POST)
        if form.is_valid():
            opp = form.save()
            messages.success(request, "Opportunity created successfully.")
            return redirect('opportunity_detail', id=opp.id)
    else:
        form = OpportunityForm()
    return render(request, 'opportunity_form.html', {'form': form, 'title': 'Create Opportunity'})


@login_required
@staff_required
def opportunity_update(request, id):
    """Edit opportunity"""
    opp = get_object_or_404(Opportunity, id=id)
    if request.method == 'POST':
        form = OpportunityForm(request.POST, instance=opp)
        if form.is_valid():
            opp = form.save()
            messages.success(request, "Opportunity updated successfully.")
            return redirect('opportunity_detail', id=opp.id)
    else:
        form = OpportunityForm(instance=opp)
    return render(request, 'opportunity_form.html', {'form': form, 'title': 'Edit Opportunity', 'opportunity': opp})


@login_required
@staff_required
def opportunity_delete(request, id):
    """Soft-delete opportunity (mark as Closed)"""
    opp = get_object_or_404(Opportunity, id=id)
    if request.method == 'POST':
        opp.status = 'Closed'
        opp.save()
        messages.success(request, f"Opportunity {opp.name} has been closed.")
        return redirect('opportunity_list')
    return render(request, 'confirm_delete.html', {'object': opp, 'type': 'Opportunity'})


# ==================== QUOTE VIEWS ====================

@login_required
@staff_required
def quote_list(request):
    """Quote list with filtering"""
    status_filter = request.GET.get('status', '')
    
    quotes = Quote.objects.all()
    if status_filter:
        quotes = quotes.filter(status=status_filter)
    
    from django.core.paginator import Paginator
    paginator = Paginator(quotes, 10)
    page_num = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_num)
    
    context = {
        'page_obj': page_obj,
        'quotes': page_obj.object_list,
        'status_filter': status_filter,
        'status_choices': Quote.STATUS_CHOICES,
    }
    return render(request, 'quote_list.html', context)


@login_required
@staff_required
def quote_create(request):
    """Create new quote with line items"""
    if request.method == 'POST':
        form = QuoteForm(request.POST)
        formset = QuoteLineItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            quote = form.save()
            formset.instance = quote
            formset.save()
            
            messages.success(request, f"Quote {quote.number} created successfully.")
            return redirect('quote_detail', id=quote.id)
    else:
        form = QuoteForm()
        formset = QuoteLineItemFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'title': 'Create Quote',
    }
    return render(request, 'quote_form.html', context)


@login_required
@staff_required
def quote_detail(request, id):
    """Quote detail view"""
    quote = get_object_or_404(Quote, id=id)
    line_items = quote.line_items.all()
    
    # Calculate totals
    subtotal = quote.get_subtotal()
    discount_amount = quote.get_discount_amount()
    total = quote.get_total()
    
    context = {
        'quote': quote,
        'line_items': line_items,
        'subtotal': subtotal,
        'discount_amount': discount_amount,
        'total': total,
    }
    return render(request, 'quote_detail.html', context)


@login_required
@staff_required
def quote_update(request, id):
    """Edit quote (Draft only)"""
    quote = get_object_or_404(Quote, id=id)
    
    if not quote.can_edit():
        messages.error(request, "Only draft quotes can be edited.")
        return redirect('quote_detail', id=id)
    
    if request.method == 'POST':
        form = QuoteForm(request.POST, instance=quote)
        formset = QuoteLineItemFormSet(request.POST, instance=quote)
        
        if form.is_valid() and formset.is_valid():
            quote = form.save()
            formset.save()
            messages.success(request, "Quote updated successfully.")
            return redirect('quote_detail', id=quote.id)
    else:
        form = QuoteForm(instance=quote)
        formset = QuoteLineItemFormSet(instance=quote)
    
    context = {
        'form': form,
        'formset': formset,
        'quote': quote,
        'title': 'Edit Quote',
    }
    return render(request, 'quote_form.html', context)


@login_required
@staff_required
def quote_delete(request, id):
    """Delete quote (Draft only)"""
    quote = get_object_or_404(Quote, id=id)
    
    if quote.status != 'Draft':
        messages.error(request, "Only draft quotes can be deleted.")
        return redirect('quote_detail', id=id)
    
    if request.method == 'POST':
        quote.delete()
        messages.success(request, "Quote deleted successfully.")
        return redirect('quote_list')
    
    return render(request, 'confirm_delete.html', {'object': quote, 'type': 'Quote'})


@login_required
@staff_required
def quote_update_status(request, id):
    """Update quote status"""
    quote = get_object_or_404(Quote, id=id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        
        # Validate status transition
        if new_status == 'Draft':
            messages.error(request, "Cannot revert to Draft status.")
            return redirect('quote_detail', id=id)
        
        if new_status == 'Submitted' and quote.status == 'Draft':
            if not quote.line_items.exists():
                messages.error(request, "Cannot submit quote without line items.")
                return redirect('quote_detail', id=id)
            quote.status = 'Submitted'
        elif new_status in ['Approved', 'Rejected'] and quote.status == 'Submitted':
            quote.status = new_status
        else:
            messages.error(request, f"Cannot change status from {quote.status} to {new_status}.")
            return redirect('quote_detail', id=id)
        
        quote.save()
        messages.success(request, f"Quote status updated to {quote.status}.")
    
    return redirect('quote_detail', id=id)

