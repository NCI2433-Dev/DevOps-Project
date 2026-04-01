"""Views for the CRM application."""

from datetime import timedelta
from functools import wraps

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import (
    AccountForm,
    LeadForm,
    OpportunityForm,
    QuoteForm,
    QuoteLineItemFormSet,
    RegistrationForm,
    RequestQuoteForm,
)
from .models import Account, Lead, Opportunity, Product, Quote

stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def create_checkout_session(request, quote_id):
    """Create Stripe Checkout Session for a quote."""
    quote = get_object_or_404(Quote, id=quote_id)

    # Provide the standard Stripe checkout session config
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': f"Quote #{quote.number}",
                    'description': "💳 Test Card: 4242 4242 4242 4242 (Any Exp/CVC)"
                },
                'unit_amount': int(quote.get_total() * 100),
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri(reverse('payment_success', args=[quote.id])),
        cancel_url=request.build_absolute_uri(reverse('payment_cancel', args=[quote.id])),
        custom_text={
            'submit': {
                'message': "Test Mode: Use card 4242 4242 4242 4242",
            }
        }
    )
    return redirect(session.url, code=303)


@login_required
def payment_success(request, quote_id):
    """Handle successful payment."""
    quote = get_object_or_404(Quote, id=quote_id)
    quote.status = 'Paid'
    quote.save()
    messages.success(request, f"Payment successful for Quote #{quote.number}!")
    return redirect('my_orders')


@login_required
def payment_cancel(request, quote_id):
    """Handle cancelled payment."""
    quote = get_object_or_404(Quote, id=quote_id)
    messages.warning(request, f"Payment cancelled for Quote #{quote.number}.")
    return redirect('my_orders')


def staff_required(view_func):
    """Decorator to check if user is staff."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            messages.error(
                request, "You don't have permission to access this page.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper



# ==================== GUEST VIEWS ====================

def home(request):
    """Home page."""
    return render(request, 'home.html')


def product_list(request):
    """Product catalog (public, read-only)."""
    products = Product.objects.filter(is_active=True)
    return render(request, 'product_list.html', {'products': products})


def product_detail(request, pk):
    """Product detail view."""
    product = get_object_or_404(Product, id=pk)
    return render(request, 'product_detail.html', {'product': product})


def request_quote(request):
    """Quote request form — works for both guests and logged-in users."""
    # If product_id is in query string, pre-select it
    product_id = request.GET.get('product_id')
    initial_data = {}
    if product_id:
        try:
            product = Product.objects.get(id=product_id)
            initial_data['product_interested'] = product
        except ObjectDoesNotExist:
            pass

    if request.method == 'POST':
        # For authenticated users, inject their email so the form validates
        post_data = request.POST.copy()
        if request.user.is_authenticated and not post_data.get('email'):
            post_data['email'] = request.user.email

        form = RequestQuoteForm(post_data)
        if form.is_valid():
            lead = form.save(commit=False)
            lead.status = 'New'
            if request.user.is_authenticated:
                lead.company_name = 'Registered User'
            else:
                lead.company_name = 'Not Provided'
            lead.save()
            return redirect('quote_request_success', ref_num=lead.reference_number)
    else:
        form = RequestQuoteForm(initial=initial_data)
    return render(request, 'request_quote.html', {'form': form})


def registration(request):
    """User registration form."""
    prefill_email = request.GET.get('email', '')
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('login')
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    else:
        initial = {'email': prefill_email} if prefill_email else {}
        form = RegistrationForm(initial=initial)

    return render(request, 'registration.html', {'form': form, 'prefill_email': prefill_email})


def user_logout(request):
    """Custom logout view - logs out user and redirects to home."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


def quote_request_success(request, ref_num):
    """Quote request success page (shows only reference number for privacy)."""
    lead = get_object_or_404(Lead, reference_number=ref_num)
    return render(request, 'quote_request_success.html', {
        'reference_number': ref_num,
        'guest_email': lead.email,
    })


@login_required
def my_orders(request):
    """Authenticated user's order/quote status and payment tracking."""
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
        'approved_count': all_quotes.filter(status='Approved').count(),
        'in_progress_count': all_quotes.filter(status__in=['Draft', 'Submitted']).count(),
    }
    return render(request, 'my_orders.html', context)


# ==================== SALES VIEWS ====================

@login_required
@staff_required
def sales_dashboard(request):
    """Sales dashboard with KPIs."""
    leads_new = Lead.objects.filter(status='New').count()
    leads_qualified = Lead.objects.filter(status='Qualified').count()
    leads_converted = Lead.objects.filter(status='Converted').count()
    opportunities_open = Opportunity.objects.filter(status='Open').count()
    quotes_draft = Quote.objects.filter(status='Draft').count()
    quotes_approved = Quote.objects.filter(status='Approved').count()

    context = {
        'leads_new': leads_new,
        'leads_qualified': leads_qualified,
        'leads_converted': leads_converted,
        'opportunities_open': opportunities_open,
        'quotes_draft': quotes_draft,
        'quotes_approved': quotes_approved,
    }
    return render(request, 'sales_dashboard.html', context)


# ==================== LEAD VIEWS ====================

@login_required
@staff_required
def lead_list(request):
    """Lead list with filtering."""
    status_filter = request.GET.get('status', '')

    leads = Lead.objects.all()
    if status_filter:
        leads = leads.filter(status=status_filter)

    # Pagination
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
def lead_detail(request, pk):
    """Lead detail view."""
    lead = get_object_or_404(Lead, id=pk)
    return render(request, 'lead_detail.html', {'lead': lead})


@login_required
@staff_required
def lead_create(request):
    """Create new lead."""
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            lead = form.save()
            messages.success(request,
                             f"Lead {lead.reference_number} created successfully.")
            return redirect('lead_detail', pk=lead.id)
    else:
        form = LeadForm()
    return render(request, 'lead_form.html',
                  {'form': form, 'title': 'Create Lead'})


@login_required
@staff_required
def lead_update(request, pk):
    """Edit lead."""
    lead = get_object_or_404(Lead, id=pk)
    if request.method == 'POST':
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            lead = form.save()
            messages.success(request, "Lead updated successfully.")
            return redirect('lead_detail', pk=lead.id)
    else:
        form = LeadForm(instance=lead)
    return render(request, 'lead_form.html',
                  {'form': form, 'title': 'Edit Lead', 'lead': lead})


@login_required
@staff_required
def lead_delete(request, pk):
    """Soft-delete lead (mark as Rejected)."""
    lead = get_object_or_404(Lead, id=pk)
    if request.method == 'POST':
        lead.status = 'Rejected'
        lead.save()
        messages.success(request,
                         f"Lead {lead.reference_number} has been rejected.")
        return redirect('lead_list')
    return render(request, 'confirm_delete.html', {'object': lead, 'type': 'Lead'})


@login_required
@staff_required
def lead_convert(request, pk):
    """Convert lead to Account + Opportunity."""
    lead = get_object_or_404(Lead, id=pk)

    if lead.converted_to_acct_id:
        messages.warning(request, "This lead has already been converted.")
        return redirect('lead_detail', pk=pk)

    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            # Create Account
            account = form.save()

            # Create Opportunity
            opp = Opportunity.objects.create(
                account=account,
                name=f"{lead.company_name} - "
                     f"{timezone.now().strftime('%B %Y')}",
                description=form.cleaned_data.get('opportunity_notes', ''),
                status='Open',
                stage='Qualification',
                expected_close_date=timezone.now().date() + timedelta(days=30)
            )

            # Update Lead
            lead.status = 'Converted'
            lead.converted_to_acct_id = account
            lead.save()

            messages.success(request, "Lead converted. Account created:"
                                      f" {account.company_name}")
            return redirect('opportunity_detail', pk=opp.id)
    else:
        # Pre-fill form with lead data
        form = AccountForm(initial={
            'company_name': lead.company_name,
            'email': lead.email,
        })

    return render(request, 'lead_convert.html',
                  {'form': form, 'lead': lead})


# ==================== OPPORTUNITY VIEWS ====================

@login_required
@staff_required
def opportunity_create_quote(request, pk):  # pylint: disable=unused-argument
    """Shortcut: redirect to quote_create with the opportunity ID in the URL."""
    opp = get_object_or_404(Opportunity, id=pk)
    return redirect(reverse('quote_create', args=[opp.id]))


@login_required
@staff_required
def opportunity_list(request):
    """Opportunity list with filtering."""
    status_filter = request.GET.get('status', '')
    stage_filter = request.GET.get('stage', '')

    opportunities = Opportunity.objects.all()
    if status_filter:
        opportunities = opportunities.filter(status=status_filter)
    if stage_filter:
        opportunities = opportunities.filter(stage=stage_filter)

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
def opportunity_detail(request, pk):
    """Opportunity detail view."""
    opp = get_object_or_404(Opportunity, id=pk)
    quotes = opp.quotes.all()
    return render(request, 'opportunity_detail.html',
                  {'opportunity': opp, 'quotes': quotes})


@login_required
@staff_required
def opportunity_create(request):
    """Create new opportunity."""
    if request.method == 'POST':
        form = OpportunityForm(request.POST)
        if form.is_valid():
            opp = form.save()
            messages.success(request, "Opportunity created successfully.")
            return redirect('opportunity_detail', pk=opp.id)
    else:
        form = OpportunityForm()
    return render(request, 'opportunity_form.html',
                  {'form': form, 'title': 'Create Opportunity'})


@login_required
@staff_required
def opportunity_update(request, pk):
    """Edit opportunity."""
    opp = get_object_or_404(Opportunity, id=pk)
    if request.method == 'POST':
        form = OpportunityForm(request.POST, instance=opp)
        if form.is_valid():
            opp = form.save()
            messages.success(request, "Opportunity updated successfully.")
            return redirect('opportunity_detail', pk=opp.id)
    else:
        form = OpportunityForm(instance=opp)
    return render(request, 'opportunity_form.html',
                  {'form': form, 'title': 'Edit Opportunity', 'opportunity': opp})


@login_required
@staff_required
def opportunity_delete(request, pk):
    """Soft-delete opportunity (mark as Closed)."""
    opp = get_object_or_404(Opportunity, id=pk)
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
    """Quote list with filtering."""
    status_filter = request.GET.get('status', '')

    quotes = Quote.objects.all()
    if status_filter:
        quotes = quotes.filter(status=status_filter)

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
def quote_create(request, opp_id=None):
    """Create new quote with line items."""
    opp = None
    if opp_id:
        opp = get_object_or_404(Opportunity, id=opp_id)

    if request.method == 'POST':
        form = QuoteForm(request.POST)
        formset = QuoteLineItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            quote = form.save()
            formset.instance = quote
            formset.save()

            messages.success(request, f"Quote {quote.number} created successfully.")
            return redirect('quote_detail', pk=quote.id)
    else:
        initial_data = {}
        if opp:
            initial_data['opportunity'] = opp

        form = QuoteForm(initial=initial_data)
        formset = QuoteLineItemFormSet()

    context = {
        'form': form,
        'formset': formset,
        'title': 'Create Quote',
        'opportunity': opp,
    }
    return render(request, 'quote_form.html', context)


@login_required
@staff_required
def quote_detail(request, pk):
    """Quote detail view."""
    quote = get_object_or_404(Quote, id=pk)
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
def quote_update(request, pk):
    """Edit quote (Draft only)."""
    quote = get_object_or_404(Quote, id=pk)

    if not quote.can_edit():
        messages.error(request, "Only draft quotes can be edited.")
        return redirect('quote_detail', pk=pk)

    if request.method == 'POST':
        form = QuoteForm(request.POST, instance=quote)
        formset = QuoteLineItemFormSet(request.POST, instance=quote)

        if form.is_valid() and formset.is_valid():
            quote = form.save()
            formset.save()
            messages.success(request, "Quote updated successfully.")
            return redirect('quote_detail', pk=quote.id)
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
def quote_delete(request, pk):
    """Delete quote (Draft only)."""
    quote = get_object_or_404(Quote, id=pk)

    if quote.status != 'Draft':
        messages.error(request, "Only draft quotes can be deleted.")
        return redirect('quote_detail', pk=pk)

    if request.method == 'POST':
        quote.delete()
        messages.success(request, "Quote deleted successfully.")
        return redirect('quote_list')

    return render(request, 'confirm_delete.html', {'object': quote, 'type': 'Quote'})


@login_required
@staff_required
def quote_update_status(request, pk):
    """Update quote status."""
    quote = get_object_or_404(Quote, id=pk)

    if request.method == 'POST':
        new_status = request.POST.get('status')

        # Validate status transition - disallow reverting to draft
        if new_status == 'Draft':
            messages.error(request, "Cannot revert to Draft status.")
            return redirect('quote_detail', pk=pk)

        if new_status == 'Submitted' and quote.status == 'Draft':
            if not quote.line_items.exists():
                messages.error(request, "Cannot submit quote without line items.")
                return redirect('quote_detail', pk=pk)
            quote.status = 'Submitted'
        elif new_status in ['Approved', 'Rejected'] and quote.status == 'Submitted':
            quote.status = new_status
        else:
            messages.error(
                request,
                f"Cannot change status from {quote.status} to {new_status}."
            )
            return redirect('quote_detail', pk=pk)

        quote.save()
        messages.success(request, f"Quote status updated to {quote.status}.")

    return redirect('quote_detail', pk=pk)
