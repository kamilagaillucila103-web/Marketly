from django import forms
from .models import (
    Vendor, 
    Stall, 
    Lease, 
    Payment, 
    SignupRequest, 
    SecureDataModel, 
    VendorPayment
)


class SecureDataForm(forms.ModelForm):
    class Meta:
        model = SecureDataModel
        fields = ['encrypted_field']
        widgets = {
            'encrypted_field': forms.PasswordInput(attrs={'class': 'field-input', 'placeholder': 'Ilagay ang sensitibong impormasyon dito'}),
        }
        labels = {
            'encrypted_field': 'Sekretong Impormasyon',
        }


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values(): 
            field.widget.attrs.setdefault("class", "field-input")


class VendorForm(StyledModelForm):
    class Meta: 
        model = Vendor
        fields = ["name", "contact_email", "phone_number"]


class StallForm(StyledModelForm):
    class Meta: 
        model = Stall
        fields = ["number", "section", "size_sqft", "is_occupied"]


class LeaseForm(StyledModelForm):
    class Meta:
        model = Lease
        fields = ["vendor", "stall", "start_date", "end_date", "is_active", "is_delinquent"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date", "class": "field-input"}), 
            "end_date": forms.DateInput(attrs={"type": "date", "class": "field-input"})
        }


class PaymentForm(StyledModelForm):
    class Meta: 
        model = Payment
        fields = ["lease", "amount", "is_successful"]


class SignupRequestForm(StyledModelForm):
    class Meta:
        model = SignupRequest
        fields = ["vendor_name", "email"]
        labels = {
            "vendor_name": "Your name or business name", 
            "email": "Contact email"
        }


class VendorPaymentForm(StyledModelForm):
    class Meta:
        model = VendorPayment
        fields = ["amount", "payment_type", "receipt_image"]
        labels = {
            "amount": "Payment Amount (₱)",
            "payment_type": "Type of Payment",
            "receipt_image": "Receipt Image",
        }