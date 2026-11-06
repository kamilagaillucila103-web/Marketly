from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError

from .models import SignupRequest, Vendor


class SignupForm(forms.Form):
    first_name = forms.CharField(max_length=60, widget=forms.TextInput(attrs={"class": "field-input"}))
    last_name = forms.CharField(max_length=60, widget=forms.TextInput(attrs={"class": "field-input"}))
    business_name = forms.CharField(max_length=120, required=False, label="Business / store name", widget=forms.TextInput(attrs={"class": "field-input"}))
    contact_number = forms.CharField(max_length=30, widget=forms.TextInput(attrs={"class": "field-input"}))
    address = forms.CharField(max_length=200, widget=forms.TextInput(attrs={"class": "field-input"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "field-input"}))
    username = forms.CharField(max_length=150, validators=[UnicodeUsernameValidator()], widget=forms.TextInput(attrs={"class": "field-input"}))
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={"class": "field-input"}))
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput(attrs={"class": "field-input"}))

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        User = get_user_model()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("That username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        User = get_user_model()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with that email already exists.")
        if SignupRequest.objects.filter(email__iexact=email, status=SignupRequest.PENDING).exists():
            raise ValidationError("A signup request with this email is already pending.")
        if Vendor.objects.filter(contact_email__iexact=email).exists():
            raise ValidationError("This email is already connected to a vendor record. Please contact the administrator.")
        return email

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password1")
        confirm = cleaned.get("password2")
        if password and confirm:
            if password != confirm:
                self.add_error("password2", "The passwords do not match.")
            else:
                try:
                    password_validation.validate_password(password)
                except ValidationError as error:
                    self.add_error("password1", error)
        return cleaned


class ApproveSignupForm(forms.Form):
    vendor = forms.ModelChoiceField(
        queryset=Vendor.objects.none(), required=False,
        empty_label="Create a new vendor record",
        label="Existing vendor record (optional)",
        help_text="Select an existing vendor only if this request belongs to that vendor. Otherwise, leave this blank.",
        widget=forms.Select(attrs={"class": "field-input"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vendor"].queryset = Vendor.objects.filter(user__isnull=True)
