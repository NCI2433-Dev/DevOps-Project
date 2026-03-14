from django.urls import path
from django.contrib.auth.views import LoginView
from . import views


urlpatterns = [
    # Authentication
    path('accounts/login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('accounts/logout/', views.user_logout, name='logout'),
    
    # Guest views
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/<int:id>/', views.product_detail, name='product_detail'),
    path('quote-request/', views.request_quote, name='request_quote'),
    path('registration/', views.registration, name='registration'),
    path('quote-request/success/<str:ref_num>/', views.quote_request_success, name='quote_request_success'),
    
    # Authenticated user views
    path('my-orders/', views.my_orders, name='my_orders'),
    
    # Sales dashboard
    path('sales/', views.sales_dashboard, name='sales_dashboard'),
    
    # Lead URLs
    path('sales/leads/', views.lead_list, name='lead_list'),
    path('sales/leads/new/', views.lead_create, name='lead_create'),
    path('sales/leads/<int:id>/', views.lead_detail, name='lead_detail'),
    path('sales/leads/<int:id>/edit/', views.lead_update, name='lead_update'),
    path('sales/leads/<int:id>/delete/', views.lead_delete, name='lead_delete'),
    path('sales/leads/<int:id>/convert/', views.lead_convert, name='lead_convert'),
    
    # Opportunity URLs
    path('sales/opportunities/', views.opportunity_list, name='opportunity_list'),
    path('sales/opportunities/new/', views.opportunity_create, name='opportunity_create'),
    path('sales/opportunities/<int:id>/', views.opportunity_detail, name='opportunity_detail'),
    path('sales/opportunities/<int:id>/edit/', views.opportunity_update, name='opportunity_update'),
    path('sales/opportunities/<int:id>/delete/', views.opportunity_delete, name='opportunity_delete'),
    
    # Quote URLs
    path('sales/quotes/', views.quote_list, name='quote_list'),
    path('sales/quotes/new/', views.quote_create, name='quote_create'),
    path('sales/quotes/<int:id>/', views.quote_detail, name='quote_detail'),
    path('sales/quotes/<int:id>/edit/', views.quote_update, name='quote_update'),
    path('sales/quotes/<int:id>/delete/', views.quote_delete, name='quote_delete'),
    path('sales/quotes/<int:id>/update-status/', views.quote_update_status, name='quote_update_status'),
]
