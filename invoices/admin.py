from django.contrib import admin
from .models import Client, Invoice, InvoiceItem


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'company_name', 'created_at']
    search_fields = ['name', 'email', 'company_name']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'client', 'status', 'total', 'issue_date', 'due_date']
    list_filter = ['status', 'issue_date']
    search_fields = ['invoice_number', 'client__name']
    inlines = [InvoiceItemInline]
    readonly_fields = ['invoice_number', 'created_at', 'updated_at']