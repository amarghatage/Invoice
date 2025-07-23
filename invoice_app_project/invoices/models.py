# Create your models here.
from decimal import Decimal
from django.db import models
from django.urls import reverse
import uuid # For unique invoice numbers

class Customer(models.Model):
    """Represents a customer who receives invoices."""
    name = models.CharField(max_length=200, unique=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.name

class Invoice(models.Model):
    """Represents an invoice issued to a customer."""
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Sent', 'Sent'),
        ('Paid', 'Paid'),
        ('Overdue', 'Overdue'),
        ('Cancelled', 'Cancelled'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='invoices')
    invoice_number = models.CharField(max_length=50, unique=True, blank=True)
    issue_date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Draft')
    notes = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Generate a unique invoice number if not provided
            # You might want a more structured numbering system (e.g., INV-YYYYMMDD-XXXX)
            self.invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def total_amount(self):
        """Calculates the total amount of the invoice from its items."""
        return sum(item.line_total for item in self.items.all())

    def get_absolute_url(self):
        """Returns the URL to display the invoice detail."""
        return reverse('invoice_detail', kwargs={'pk': self.pk})

    def __str__(self):
        return f"Invoice {self.invoice_number} for {self.customer.name}"

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0) # <--- Check this line
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0) # <--- Check this line
# class InvoiceItem(models.Model):
#     """Represents a single line item within an invoice."""
#     invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
#     description = models.CharField(max_length=255)
#     quantity = models.DecimalField(max_digits=10, decimal_places=2)
#     unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    # @property
    # def line_total(self):
    #     """Calculates the total for this line item."""
    #     return self.quantity * self.unit_price
    @property
    def line_total(self):
    # Ensure quantity and unit_price are not None before multiplication
        quantity = self.quantity if self.quantity is not None else Decimal('0.00')
        unit_price = self.unit_price if self.unit_price is not None else Decimal('0.00')
        return quantity * unit_price

    def __str__(self):
        return f"{self.description} ({self.invoice.invoice_number})"