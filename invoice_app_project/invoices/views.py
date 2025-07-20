from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from django.db import transaction
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa # Install xhtml2pdf: pip install xhtml2pdf

from .models import Customer, Invoice, InvoiceItem
from .forms import CustomerForm, InvoiceForm, InvoiceItemForm

# --- Invoice List View ---
def invoice_list(request):
    """Displays a list of all invoices."""
    invoices = Invoice.objects.all().order_by('-issue_date')
    context = {
        'invoices': invoices,
        'page_title': 'All Invoices'
    }
    return render(request, 'invoices/invoice_list.html', context)

# --- Invoice Create/Update View ---
def invoice_create_update(request, pk=None):
    """
    Handles creation of new invoices or updating existing ones.
    Uses formsets for dynamic invoice items.
    """
    invoice = None
    if pk:
        invoice = get_object_or_404(Invoice, pk=pk)
        page_title = f"Edit Invoice {invoice.invoice_number}"
    else:
        page_title = "Create New Invoice"

    # Determine if we are creating a new customer or using an existing one
    customer_form = CustomerForm(request.POST or None, instance=invoice.customer if invoice else None)
    invoice_form = InvoiceForm(request.POST or None, instance=invoice)
    formset = inlineformset_factory(Invoice, InvoiceItem, form=InvoiceItemForm, extra=1, can_delete=True)
    invoice_item_formset = formset(request.POST or None, instance=invoice, prefix='items')

    if request.method == 'POST':
        if 'new_customer_name' in request.POST and request.POST['new_customer_name']:
            # Create a new customer if specified
            new_customer_name = request.POST['new_customer_name']
            new_customer, created = Customer.objects.get_or_create(name=new_customer_name)
            invoice_form.data = invoice_form.data.copy() # Make mutable
            invoice_form.data['customer'] = new_customer.pk # Set the customer field to the new customer's PK

        if invoice_form.is_valid() and invoice_item_formset.is_valid():
            try:
                with transaction.atomic():
                    invoice_instance = invoice_form.save(commit=False)
                    # If a new customer was created, ensure it's linked
                    if 'new_customer_name' in request.POST and request.POST['new_customer_name']:
                        new_customer_name = request.POST['new_customer_name']
                        customer_obj = Customer.objects.get(name=new_customer_name)
                        invoice_instance.customer = customer_obj
                    invoice_instance.save() # Save the invoice first to get an ID

                    # Save invoice items
                    invoice_item_formset.instance = invoice_instance
                    invoice_item_formset.save()

                return redirect('invoice_detail', pk=invoice_instance.pk)
            except Exception as e:
                # Handle potential errors during save
                print(f"Error saving invoice: {e}")
                # You might add a message to the user here
                pass # Re-render form with errors if any

    context = {
        'invoice_form': invoice_form,
        'invoice_item_formset': invoice_item_formset,
        'page_title': page_title,
        'invoice': invoice, # Pass invoice object for editing
        'customers': Customer.objects.all(), # For dropdown
        'customer_form': customer_form, # For new customer creation
    }
    return render(request, 'invoices/invoice_form.html', context)

# --- Invoice Detail View ---
def invoice_detail(request, pk):
    """Displays the details of a single invoice."""
    invoice = get_object_or_404(Invoice, pk=pk)
    context = {
        'invoice': invoice,
        'page_title': f"Invoice {invoice.invoice_number}"
    }
    return render(request, 'invoices/invoice_detail.html', context)

# --- PDF Generation View ---
def invoice_pdf(request, pk):
    """Generates and serves an invoice as a PDF."""
    invoice = get_object_or_404(Invoice, pk=pk)
    template_path = 'invoices/invoice_pdf_template.html'
    context = {'invoice': invoice}

    # Render HTML template with context
    template = get_template(template_path)
    html = template.render(context)

    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    # If you want to download the PDF, uncomment the line below:
    # response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
    # If you want to display the PDF in the browser, use 'inline':
    response['Content-Disposition'] = f'inline; filename="invoice_{invoice.invoice_number}.pdf"'

    # Create PDF
    pisa_status = pisa.CreatePDF(
        html,                # the HTML to convert
        dest=response)       # file handle to receive result

    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response
