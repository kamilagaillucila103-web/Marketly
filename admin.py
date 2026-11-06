
from django.contrib import admin
from .models import (
    Vendor,
    Section,
    Stall,
    Lease,
    Payment,
    SignupRequest,
    VendorPayment,
    PaymentChannel,
)


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_email', 'phone_number')
    search_fields = ('name', 'contact_email')


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(Stall)
class StallAdmin(admin.ModelAdmin):
    list_display = ('number', 'section', 'size_sqft', 'is_occupied')
    list_filter = ('is_occupied', 'section')


@admin.register(Lease)
class LeaseAdmin(admin.ModelAdmin):
    list_display = (
        'vendor',
        'stall',
        'monthly_rent',
        'due_day',
        'start_date',
        'end_date',
        'is_active',
        'is_delinquent',
    )
    list_filter = ('is_active', 'is_delinquent')
    search_fields = ('vendor__name', 'stall__number')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('lease', 'amount', 'payment_date', 'is_successful')
    list_filter = ('is_successful', 'payment_date')


@admin.register(SignupRequest)
class SignupRequestAdmin(admin.ModelAdmin):
    list_display = ('vendor_name', 'email', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('vendor_name', 'email')


@admin.register(VendorPayment)
class VendorPaymentAdmin(admin.ModelAdmin):
    list_display = (
        'vendor',
        'amount',
        'payment_type',
        'status',
        'created_at',
    )
    list_filter = ('payment_type', 'status', 'created_at')
    search_fields = ('vendor__name',)


@admin.register(PaymentChannel)
class PaymentChannelAdmin(admin.ModelAdmin):
    list_display = (
        'method',
        'account_name',
        'account_number',
        'is_active',
    )
    list_filter = ('method', 'is_active')
    search_fields = ('account_name', 'account_number')
