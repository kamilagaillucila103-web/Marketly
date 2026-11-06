from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import FormView, ListView, TemplateView
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import Lease, Payment, SignupRequest, Vendor
from .signup_forms import ApproveSignupForm, SignupForm


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect("market:portal")
        return super().handle_no_permission()


class SignupView(FormView):
    template_name = "market/signup.html"
    form_class = SignupForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("market:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        data = form.cleaned_data
        User = get_user_model()
        with transaction.atomic():
            user = User.objects.create_user(
                username=data["username"], email=data["email"],
                password=data["password1"], first_name=data["first_name"],
                last_name=data["last_name"], is_active=False,
            )
            SignupRequest.objects.create(
                vendor_name=(data["business_name"] or f'{data["first_name"]} {data["last_name"]}').strip(),
                email=data["email"], user=user, first_name=data["first_name"],
                last_name=data["last_name"], business_name=data["business_name"],
                contact_number=data["contact_number"], address=data["address"],
            )
        messages.success(self.request, "Your request was submitted. You can sign in after an administrator approves it.")
        return redirect("market:signup_done")


class SignupDoneView(TemplateView):
    template_name = "market/signup_done.html"


class SignupListView(StaffRequiredMixin, ListView):
    model = SignupRequest
    context_object_name = "signups"
    template_name = "market/signup_list.html"
    queryset = SignupRequest.objects.all().order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pending_count"] = SignupRequest.objects.filter(status=SignupRequest.PENDING).count()
        return context


class SignupApproveView(StaffRequiredMixin, FormView):
    template_name = "market/signup_approve.html"
    form_class = ApproveSignupForm

    def dispatch(self, request, *args, **kwargs):
        self.signup = get_object_or_404(SignupRequest, pk=kwargs["pk"], status=SignupRequest.PENDING)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["signup"] = self.signup
        return context

    def form_valid(self, form):
        signup = self.signup
        user = signup.user
        if user is None:
            form.add_error(None, "This request has no linked login account. Reject it and ask the vendor to register again.")
            return self.form_invalid(form)

        with transaction.atomic():
            vendor = form.cleaned_data["vendor"]
            if vendor is None:
                vendor = Vendor.objects.create(
                    name=(signup.business_name or signup.full_name)[:200],
                    contact_email=signup.email,
                    phone_number=signup.contact_number,
                    user=user,
                )
            else:
                if Vendor.objects.filter(contact_email=signup.email).exclude(pk=vendor.pk).exists():
                    form.add_error("vendor", "Another vendor record already uses this email.")
                    return self.form_invalid(form)
                vendor.contact_email = signup.email
                vendor.phone_number = signup.contact_number
                vendor.user = user
                vendor.save(update_fields=["contact_email", "phone_number", "user"])

            user.is_active = True
            user.save(update_fields=["is_active"])
            signup.status = SignupRequest.APPROVED
            signup.reviewed_at = timezone.now()
            signup.save(update_fields=["status", "reviewed_at"])

        messages.success(self.request, f"{user.username} has been approved and can now sign in.")
        return redirect("market:signup_list")


class SignupRejectView(StaffRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk):
        signup = get_object_or_404(SignupRequest, pk=pk, status=SignupRequest.PENDING)
        with transaction.atomic():
            if signup.user_id:
                signup.user.is_active = False
                signup.user.save(update_fields=["is_active"])
            signup.status = SignupRequest.REJECTED
            signup.reviewed_at = timezone.now()
            signup.save(update_fields=["status", "reviewed_at"])
        messages.success(request, "The signup request was rejected.")
        return redirect("market:signup_list")


@login_required
def vendor_portal_view(request):
    if request.user.is_staff:
        return redirect("market:dashboard")
    vendor = Vendor.objects.filter(user=request.user).first()
    leases = Lease.objects.filter(vendor=vendor).select_related("stall", "stall__section") if vendor else Lease.objects.none()
    payments = Payment.objects.filter(lease__vendor=vendor).select_related("lease", "lease__stall").order_by("-payment_date") if vendor else Payment.objects.none()
    total_paid = sum((p.amount for p in payments if p.is_successful), start=0)
    return render(request, "market/vendor_portal.html", {
        "vendor": vendor, "leases": leases, "payments": payments,
        "total_paid": total_paid,
    })


def signup_view(request):
    return SignupView.as_view()(request)


def signup_done_view(request):
    return SignupDoneView.as_view()(request)


def signup_list_view(request):
    return SignupListView.as_view()(request)