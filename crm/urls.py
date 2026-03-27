"""URL patterns for the CRM application."""
from django.urls import path
from django.contrib.auth.views import LoginView
from . import views
from .forms import RegistrationForm, CustomAuthForm


class HomeRedirectLoginView(LoginView):  # pylint: disable=too-many-ancestors
    """Login view that always redirects to home after login, ignoring next."""
    template_name = 'login.html'
    form_class = CustomAuthForm

    def get_success_url(self):
        next_url = self.request.POST.get('next') or self.request.GET.get('next')
        if next_url:
            return next_url
        return '/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        prefill_email = self.request.GET.get('email', '')
        initial = {'email': prefill_email} if prefill_email else None
        context['registration_form'] = RegistrationForm(initial=initial)
        context['prefill_email'] = prefill_email
        should_show = self.request.GET.get('register') or prefill_email
        context['show_registration'] = bool(should_show)
        return context


urlpatterns = [
    # Authentication
    path('accounts/login/', HomeRedirectLoginView.as_view(), name='login'),
    path('accounts/logout/', views.user_logout, name='logout'), # Removed trailing whitespace

    # Guest views
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('quote-request/', views.request_quote, name='request_quote'),
    path('registration/', views.registration, name='registration'),
    path('quote-request/success/<str:ref_num>/',
         views.quote_request_success, name='quote_request_success'),

    # Authenticated user views
    path('my-orders/', views.my_orders, name='my_orders'),
    path(
        'my-orders/pay/<int:quote_id>/',
        views.create_checkout_session,
        name='create_checkout_session'
    ),
    path(
        'my-orders/pay/success/<int:quote_id>/',
        views.payment_success,
        name='payment_success'
    ),
    path(
        'my-orders/pay/cancel/<int:quote_id>/',
        views.payment_cancel,
        name='payment_cancel'
    ),

    # Sales dashboard
    path('sales/', views.sales_dashboard, name='sales_dashboard'),

    # Lead URLs
    path('sales/leads/', views.lead_list, name='lead_list'),
    path('sales/leads/new/', views.lead_create, name='lead_create'),
    path('sales/leads/<int:pk>/', views.lead_detail, name='lead_detail'),
    path('sales/leads/<int:pk>/edit/', views.lead_update, name='lead_update'),
    path('sales/leads/<int:pk>/delete/', views.lead_delete, name='lead_delete'),
    path('sales/leads/<int:pk>/convert/', views.lead_convert, name='lead_convert'),

    # Opportunity URLs
    path('sales/opportunities/', views.opportunity_list, name='opportunity_list'),
    path('sales/opportunities/new/', views.opportunity_create, name='opportunity_create'),
    path('sales/opportunities/<int:pk>/', views.opportunity_detail, name='opportunity_detail'),
    path('sales/opportunities/<int:pk>/edit/', views.opportunity_update, name='opportunity_update'),
    path(
        'sales/opportunities/<int:pk>/delete/',
        views.opportunity_delete,
        name='opportunity_delete'
    ),
    path(
        'sales/opportunities/<int:pk>/create-quote/',
        views.opportunity_create_quote,
        name='opportunity_create_quote'
    ),

    # Quote URLs
    path('sales/quotes/', views.quote_list, name='quote_list'),
    path('sales/quotes/new/<int:opp_id>/', views.quote_create, name='quote_create'),
    path('sales/quotes/<int:pk>/', views.quote_detail, name='quote_detail'),
    path('sales/quotes/<int:pk>/edit/', views.quote_update, name='quote_update'),
    path('sales/quotes/<int:pk>/delete/', views.quote_delete, name='quote_delete'),
    path(
        'sales/quotes/<int:pk>/update-status/',
        views.quote_update_status,
        name='quote_update_status'
    ),
]
