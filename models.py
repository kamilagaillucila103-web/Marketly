
from django.db import models
from django.contrib.auth.models import User
from cryptography.fernet import Fernet
from django.conf import settings


class Vendor(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='vendor_profile'
    )
    name = models.CharField(max_length=200)
    contact_email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name


class Section(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Stall(models.Model):
    number = models.CharField(max_length=50)
    section = models.ForeignKey(
        Section,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    size_sqft = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00
    )
    is_occupied = models.BooleanField(default=False)

    def __str__(self):
        return f"Stall {self.number}"


class Lease(models.Model):
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='leases'
    )
    stall = models.ForeignKey(
        Stall,
        on_delete=models.CASCADE,
        related_name='leases'
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    monthly_rent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    due_day = models.PositiveSmallIntegerField(
        default=5,
        help_text="Day of the month when rent is due (1-28 recommended)."
    )

    is_active = models.BooleanField(default=True)
    is_delinquent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.vendor.name} - {self.stall}"


class Payment(models.Model):
    lease = models.ForeignKey(
        Lease,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    is_successful = models.BooleanField(default=True)

    def __str__(self):
        return f"₱{self.amount} - {self.lease.vendor.name}"


class SignupRequest(models.Model):
    PENDING = 'PENDING'

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        # Keep the other existing choices
    ]
    vendor_name = models.CharField(max_length=200)
    email = models.EmailField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vendor_name} ({self.status})"


class SecureDataModel(models.Model):
    encrypted_field = models.TextField()

    def set_secure_data(self, raw_data):
        key = (
            settings.ENCRYPTION_KEY
            if hasattr(settings, 'ENCRYPTION_KEY')
            else Fernet.generate_key()
        )
        f = Fernet(key)
        self.encrypted_field = f.encrypt(raw_data.encode()).decode()

    def get_secure_data(self):
        try:
            key = (
                settings.ENCRYPTION_KEY
                if hasattr(settings, 'ENCRYPTION_KEY')
                else Fernet.generate_key()
            )
            f = Fernet(key)
            return f.decrypt(self.encrypted_field.encode()).decode()
        except Exception:
            return "[Encrypted Data]"


class VendorPayment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]

    PAYMENT_TYPE_CHOICES = [
        ('GCASH', 'GCash'),
        ('MAYA', 'Maya'),
        ('BANK', 'Bank Transfer'),
        ('CASH', 'Cash Payment'),
    ]

    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='vendor_payments'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        default='GCASH'
    )

    receipt_image = models.ImageField(
        upload_to='receipts/',
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    rejection_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.vendor.name} - ₱{self.amount} "
            f"({self.status.capitalize()})"
        )


class PaymentChannel(models.Model):
    PAYMENT_METHODS = [
        ('GCASH', 'GCash'),
        ('MAYA', 'Maya'),
        ('BANK', 'Bank Transfer'),
        ('CASH', 'Cash Payment'),
    ]

    method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        unique=True
    )
    account_name = models.CharField(max_length=150, blank=True)
    account_number = models.CharField(max_length=100, blank=True)
    instructions = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['method']

    def __str__(self):
        return self.get_method_display()
