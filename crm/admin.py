from django.contrib import admin
from .models import Product, Lead, Account, Opportunity, Quote, QuoteLineItem


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'base_price', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'sku']
    ordering = ['-created_at']


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['reference_number', 'first_name', 'last_name', 'email', 'company_name', 'status', 'created_at']
    list_filter = ['status', 'source', 'created_at']
    search_fields = ['reference_number', 'email', 'company_name']
    readonly_fields = ['reference_number', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'contact_person_name', 'email', 'phone', 'created_at']
    list_filter = ['created_at']
    search_fields = ['company_name', 'email']
    ordering = ['company_name']


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ['name', 'account', 'stage', 'status', 'expected_close_date', 'created_at']
    list_filter = ['stage', 'status', 'created_at']
    search_fields = ['name', 'account__company_name']
    ordering = ['-created_at']


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ['number', 'opportunity', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['number', 'opportunity__name']
    readonly_fields = ['number', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(QuoteLineItem)
class QuoteLineItemAdmin(admin.ModelAdmin):
    list_display = ['product', 'quote', 'quantity', 'unit_price', 'discount', 'created_at']
    list_filter = ['created_at']
    search_fields = ['product__name', 'quote__number']
    ordering = ['-created_at']

