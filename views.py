import calendar
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q, Sum
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail
from django.conf import settings

from .forms import VendorForm, StallForm, LeaseForm, PaymentForm, SecureDataForm, VendorPaymentForm
from .models import Vendor, Stall, Lease, SignupRequest, Payment, SecureDataModel, VendorPayment, PaymentChannel


@login_required
@user_passes_test(lambda user: user.is_staff, login_url="market:portal")
def secure_data_list_view(request):
    items = SecureDataModel.objects.all()
    decrypted_items = []
    for item in items:
        decrypted_items.append({
            'id': item.id,
            'original_text': item.get_secure_data()
        })
    return render(request, 'market/secure_list.html', {'items': decrypted_items})


@login_required
@user_passes_test(lambda user: user.is_staff, login_url="market:portal")
def add_secure_data_view(request):
    if request.method == 'POST':
        form = SecureDataForm(request.POST)
        if form.is_valid():
            raw_text = form.cleaned_data['encrypted_field']
            item = SecureDataModel()
            item.set_secure_data(raw_text)
            item.save()
            return redirect('market:secure_list') 
    else:
        form = SecureDataForm()
    return render(request, 'market/secure_form.html', {'form': form})


@login_required
def dashboard_view(request):
    if not request.user.is_staff:
        return redirect("market:portal")
    total_stalls = Stall.objects.count()
    occupied_stalls = Stall.objects.filter(is_occupied=True).count()
    return render(request, "market/dashboard.html", {
        "total_vendors": Vendor.objects.count(), 
        "total_stalls": total_stalls, 
        "occupied_stalls": occupied_stalls, 
        "occupancy_rate": round((occupied_stalls / total_stalls) * 100) if total_stalls else 0, 
        "active_leases": Lease.objects.filter(is_active=True).count(), 
        "pending_signups": SignupRequest.objects.filter(status="PENDING").count(), 
        "recent_leases": Lease.objects.select_related("vendor", "stall").order_by("-id")[:6], 
        "recent_payments": Payment.objects.select_related("lease__vendor", "lease__stall").order_by("-payment_date", "-id")[:5], 
        "collection_total": Payment.objects.filter(is_successful=True).aggregate(total=Sum("amount"))["total"] or 0
    })


def _create(request, form_class, title, subtitle, back_url, success_message, after="market:dashboard"):
    form = form_class(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        if isinstance(obj, Lease) and obj.is_active:
            obj.stall.is_occupied = True
            obj.stall.save(update_fields=["is_occupied"])
        messages.success(request, success_message)
        return redirect(after)
    return render(request, "market/form.html", {"form": form, "title": title, "subtitle": subtitle, "back_url": back_url})


@login_required
@user_passes_test(lambda user: user.is_staff, login_url="market:portal")
def vendor_create_view(request): 
    return _create(request, VendorForm, "Add vendor", "Create a vendor profile for the market directory.", "market:vendor_list", "Vendor added successfully.")


@login_required
@user_passes_test(lambda user: user.is_staff, login_url="market:portal")
def stall_create_view(request): 
    return _create(request, StallForm, "Add stall", "Register a new space and its section.", "market:stall_list", "Stall added successfully.")


@login_required
@user_passes_test(lambda user: user.is_staff, login_url="market:portal")
def lease_create_view(request): 
    return _create(request, LeaseForm, "Create lease", "Assign a stall to a vendor.", "market:lease_list", "Lease created successfully.")


@login_required
@user_passes_test(lambda user: user.is_staff, login_url="market:portal")
def payment_create_view(request):
    form = PaymentForm(request.POST or None, initial={"lease": request.GET.get("lease")})
    if request.method == "POST" and form.is_valid(): 
        form.save()
        messages.success(request, "Payment recorded successfully.")
        return redirect("market:daily_report")
    return render(request, "market/form.html", {"form": form, "title": "Record payment", "subtitle": "Add a collection entry to the ledger.", "back_url": "market:daily_report"})


@login_required
@user_passes_test(lambda user: user.is_staff, login_url="market:portal")
def vendor_list_view(request):
    query = request.GET.get("q", "").strip()
    vendors = Vendor.objects.all().order_by("name")
    if query: 
        vendors = vendors.filter(Q(name__icontains=query) | Q(contact_email__icontains=query) | Q(phone_number__icontains=query))
    return render(request, "market/vendor_list.html", {"vendors": vendors, "query": query})


@login_required
@user_passes_test(lambda user: user.is_staff, login_url="market:portal")
def stall_list_view(request):
    status = request.GET.get("status", "all")
    stalls = Stall.objects.select_related("section").order_by("number")
    if status == "vacant": 
        stalls = stalls.filter(is_occupied=False)
    elif status == "occupied": 
        stalls = stalls.filter(is_occupied=True)
    return render(request, "market/stall_list.html", {"stalls": stalls, "status": status})


@login_required
@user_passes_test(lambda user: user.is_staff, login_url="market:portal")
def lease_list_view(request): 
    return render(request, "market/lease_list.html", {"leases": Lease.objects.select_related("vendor", "stall", "stall__section").order_by("-is_active", "-start_date")})


@login_required
@user_passes_test(lambda user: user.is_staff, login_url="market:portal")
def daily_report_view(request):
    payments = Payment.objects.select_related("lease__vendor", "lease__stall").order_by("-payment_date", "-id")
    return render(request, "market/daily_report.html", {"payments": payments, "total": payments.filter(is_successful=True).aggregate(total=Sum("amount"))["total"] or 0})


@login_required
@user_passes_test(lambda user: user.is_staff, login_url="market:portal")
def delinquent_report_view(request): 
    return render(request, "market/delinquent_report.html", {"delinquents": Lease.objects.filter(is_delinquent=True).select_related("vendor", "stall")})


# --- VENDOR PORTAL, PAYMENT SUBMISSION & ADMIN VERIFICATION VIEWS ---

def _months_charged(start, end):
    """Bilang ng buwan (kasama ang kasalukuyang buwan) na may singil."""
    if end < start:
        return 0
    return (end.year - start.year) * 12 + (end.month - start.month) + 1


def _due_date_in_month(year, month, due_day):
    last = calendar.monthrange(year, month)[1]
    return date(year, month, min(due_day, last))


def _next_due_date(due_day, today):
    this_month = _due_date_in_month(today.year, today.month, due_day)
    if today <= this_month:
        return this_month
    year, month = (today.year + 1, 1) if today.month == 12 else (today.year, today.month + 1)
    return _due_date_in_month(year, month, due_day)


def _vendor_summary(vendor):
    """Kinukuwenta ang stalls, due date, total na singil, nabayaran at balance."""
    today = date.today()
    leases = (
        Lease.objects.filter(vendor=vendor, is_active=True)
        .select_related("stall", "stall__section")
        .order_by("stall__number")
    )

    rows = []
    total_charged = Decimal("0")
    for lease in leases:
        end = min(lease.end_date, today) if lease.end_date else today
        charged = lease.monthly_rent * _months_charged(lease.start_date, end)
        total_charged += charged
        rows.append({
            "lease": lease,
            "stall": lease.stall,
            "monthly_rent": lease.monthly_rent,
            "due_day": lease.due_day,
            "next_due": _next_due_date(lease.due_day, today),
        })

    # Bayad na bilang: mga naka-record ng admin + mga resibong na-verify na
    ledger_paid = (
        Payment.objects.filter(lease__vendor=vendor, is_successful=True)
        .aggregate(t=Sum("amount"))["t"] or Decimal("0")
    )
    verified_paid = (
        VendorPayment.objects.filter(vendor=vendor, status="verified")
        .aggregate(t=Sum("amount"))["t"] or Decimal("0")
    )
    total_paid = ledger_paid + verified_paid
    balance = max(total_charged - total_paid, Decimal("0"))

    return {
        "rows": rows,
        "total_charged": total_charged,
        "total_paid": total_paid,
        "balance": balance,
        "next_due": min((r["next_due"] for r in rows), default=None),
        "monthly_total": sum((r["monthly_rent"] for r in rows), Decimal("0")),
    }


def vendor_logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect(settings.LOGIN_URL)


# ---------------- DASHBOARD (market:portal) ----------------
@login_required
def vendor_portal_view(request):
    if request.user.is_staff:
        return redirect("market:dashboard")

    vendor = Vendor.objects.filter(user=request.user).first()
    summary = _vendor_summary(vendor) if vendor else None

    return render(request, "market/vendor_portal.html", {
        "vendor": vendor,
        "summary": summary,
    })


# ---------------- PAYMENT PAGE (market:vendor_payment) ----------------
@login_required
def vendor_payment_view(request):
    if request.user.is_staff:
        return redirect("market:dashboard")

    vendor = Vendor.objects.filter(user=request.user).first()
    if vendor is None:
        messages.error(request, "Walang vendor profile na naka-link sa account na ito.")
        return redirect("market:portal")

    if request.method == "POST":
        form = VendorPaymentForm(request.POST, request.FILES)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.vendor = vendor
            payment.save()
            messages.success(request, "Na-submit na ang iyong resibo para sa pag-verify.")
            return redirect("market:vendor_payment")
    else:
        form = VendorPaymentForm()

    return render(request, "market/vendor_payment.html", {
        "vendor": vendor,
        "summary": _vendor_summary(vendor),
        "channels": PaymentChannel.objects.filter(is_active=True),
        "payments": VendorPayment.objects.filter(vendor=vendor).order_by("-created_at"),
        "form": form,
    })


@staff_member_required
def admin_verification_list(request):
    """View para sa Admin Dashboard upang makita ang listahan ng mga pending payments."""
    pending_payments = VendorPayment.objects.filter(status='pending').order_by('-created_at')
    return render(request, 'market/admin_verification_list.html', {'pending_payments': pending_payments})


@staff_member_required
def verify_payment(request, payment_id):
    """View para i-verify ang bayad."""
    payment = get_object_or_404(VendorPayment, id=payment_id)

    if payment.status == 'pending':
        payment.status = 'verified'
        payment.save()

        if payment.vendor.contact_email:
            subject = 'Your Payment has been Verified!'
            message = (
                f"Hello {payment.vendor.name},\n\n"
                f"Your submitted payment amounting to ₱{payment.amount} has been verified by the admin. "
                f"Thank you!"
            )
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [payment.vendor.contact_email],
                fail_silently=True,
            )
        messages.success(request, f"Payment from {payment.vendor.name} has been verified.")

    return redirect('market:admin_verification_list')


@staff_member_required
def reject_payment(request, payment_id):
    """View para i-reject ang bayad kasama ang dahilan mula sa admin."""
    payment = get_object_or_404(VendorPayment, id=payment_id)

    if payment.status == 'pending' and request.method == 'POST':
        reason = request.POST.get('rejection_reason')
        payment.status = 'rejected'
        payment.rejection_reason = reason
        payment.save()

        if payment.vendor.contact_email:
            subject = 'Sorry: Your Receipt/Payment has been Rejected'
            message = (
                f"Hello {payment.vendor.name},\n\n"
                f"We regret to inform you that your submitted payment amounting to ₱{payment.amount} has been rejected.\n\n"
                f"Reason: {reason}\n\n"
                f"Please review this and resubmit if necessary. Thank you very much."
            )
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [payment.vendor.contact_email],
                fail_silently=True,
            )
        messages.warning(request, f"Payment from {payment.vendor.name} has been rejected.")

    return redirect('market:admin_verification_list')
