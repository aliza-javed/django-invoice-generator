from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import Client, Invoice, InvoiceItem
from .forms import ClientForm, InvoiceForm, InvoiceItemFormSet
from .utils import render_to_pdf


# ==================== Dashboard ====================
@login_required
def dashboard(request):
    user = request.user
    invoices = Invoice.objects.filter(user=user)
    
    total_invoices = invoices.count()
    paid_invoices = invoices.filter(status='paid').count()
    pending_invoices = invoices.filter(status__in=['draft', 'sent']).count()
    overdue_invoices = invoices.filter(status='overdue').count()
    
    total_revenue = invoices.filter(status='paid').aggregate(
        total=Sum('items__quantity' * 'items__unit_price')
    )['total'] or 0
    
    recent_invoices = invoices.select_related('client')[:5]
    clients_count = Client.objects.filter(user=user).count()
    
    context = {
        'total_invoices': total_invoices,
        'paid_invoices': paid_invoices,
        'pending_invoices': pending_invoices,
        'overdue_invoices': overdue_invoices,
        'total_revenue': total_revenue,
        'recent_invoices': recent_invoices,
        'clients_count': clients_count,
    }
    return render(request, 'invoices/dashboard.html', context)


# ==================== Client Views ====================
class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = 'invoices/client_list.html'
    context_object_name = 'clients'
    paginate_by = 10

    def get_queryset(self):
        return Client.objects.filter(user=self.request.user)


class ClientDetailView(LoginRequiredMixin, DetailView):
    model = Client
    template_name = 'invoices/client_detail.html'

    def get_queryset(self):
        return Client.objects.filter(user=self.request.user)


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'invoices/client_form.html'
    success_url = reverse_lazy('client-list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class ClientUpdateView(LoginRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'invoices/client_form.html'
    success_url = reverse_lazy('client-list')

    def get_queryset(self):
        return Client.objects.filter(user=self.request.user)


class ClientDeleteView(LoginRequiredMixin, DeleteView):
    model = Client
    template_name = 'invoices/client_confirm_delete.html'
    success_url = reverse_lazy('client-list')

    def get_queryset(self):
        return Client.objects.filter(user=self.request.user)


# ==================== Invoice Views ====================
class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'invoices/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 10

    def get_queryset(self):
        queryset = Invoice.objects.filter(user=self.request.user).select_related('client')
        
        status = self.request.GET.get('status')
        search = self.request.GET.get('search')
        
        if status:
            queryset = queryset.filter(status=status)
        if search:
            queryset = queryset.filter(
                Q(invoice_number__icontains=search) |
                Q(client__name__icontains=search)
            )
        
        return queryset


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'invoices/invoice_detail.html'

    def get_queryset(self):
        return Invoice.objects.filter(user=self.request.user).select_related('client').prefetch_related('items')


class InvoiceCreateView(LoginRequiredMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoices/invoice_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['items_formset'] = InvoiceItemFormSet(self.request.POST)
        else:
            context['items_formset'] = InvoiceItemFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        items_formset = context['items_formset']
        
        if items_formset.is_valid():
            form.instance.user = self.request.user
            self.object = form.save()
            items_formset.instance = self.object
            items_formset.save()
            return redirect(self.object.get_absolute_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))


class InvoiceUpdateView(LoginRequiredMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoices/invoice_form.html'

    def get_queryset(self):
        return Invoice.objects.filter(user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['items_formset'] = InvoiceItemFormSet(self.request.POST, instance=self.object)
        else:
            context['items_formset'] = InvoiceItemFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        items_formset = context['items_formset']
        
        if items_formset.is_valid():
            self.object = form.save()
            items_formset.instance = self.object
            items_formset.save()
            return redirect(self.object.get_absolute_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))


class InvoiceDeleteView(LoginRequiredMixin, DeleteView):
    model = Invoice
    template_name = 'invoices/invoice_confirm_delete.html'
    success_url = reverse_lazy('invoice-list')

    def get_queryset(self):
        return Invoice.objects.filter(user=self.request.user)


# ==================== PDF Generation ====================
@login_required
def generate_pdf(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    
    context = {
        'invoice': invoice,
        'company_name': request.settings.COMPANY_NAME if hasattr(request, 'settings') else 'Your Company',
    }
    
    pdf = render_to_pdf('invoices/invoice_pdf.html', context)
    
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Invoice_{invoice.invoice_number}.pdf"
        content = f"attachment; filename={filename}"
        response['Content-Disposition'] = content
        return response
    return HttpResponse("Error generating PDF", status=400)