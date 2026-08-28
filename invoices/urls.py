from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Clients
    path('clients/', views.ClientListView.as_view(), name='client-list'),
    path('clients/<int:pk>/', views.ClientDetailView.as_view(), name='client-detail'),
    path('clients/create/', views.ClientCreateView.as_view(), name='client-create'),
    path('clients/<int:pk>/update/', views.ClientUpdateView.as_view(), name='client-update'),
    path('clients/<int:pk>/delete/', views.ClientDeleteView.as_view(), name='client-delete'),
    
    # Invoices
    path('invoices/', views.InvoiceListView.as_view(), name='invoice-list'),
    path('invoices/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice-detail'),
    path('invoices/create/', views.InvoiceCreateView.as_view(), name='invoice-create'),
    path('invoices/<int:pk>/update/', views.InvoiceUpdateView.as_view(), name='invoice-update'),
    path('invoices/<int:pk>/delete/', views.InvoiceDeleteView.as_view(), name='invoice-delete'),
    path('invoices/<int:pk>/pdf/', views.generate_pdf, name='invoice-pdf'),
]