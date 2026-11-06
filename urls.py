from django.urls import path
from . import views
from . import signup_views

app_name = "market"

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("vendors/", views.vendor_list_view, name="vendor_list"),
    path("vendors/add/", views.vendor_create_view, name="vendor_create"),
    path("stalls/", views.stall_list_view, name="stall_list"),
    path("stalls/add/", views.stall_create_view, name="stall_create"),
    path("leases/", views.lease_list_view, name="lease_list"),
    path("leases/add/", views.lease_create_view, name="lease_create"),
    path("payments/add/", views.payment_create_view, name="payment_create"),
    path("signups/", signup_views.SignupListView.as_view(), name="signup_list"),
    path("signups/<int:pk>/approve/", signup_views.SignupApproveView.as_view(), name="signup_approve"),
    path("signups/<int:pk>/reject/", signup_views.SignupRejectView.as_view(), name="signup_reject"),
    path("signup/", signup_views.SignupView.as_view(), name="signup"),
    path("signup/done/", signup_views.SignupDoneView.as_view(), name="signup_done"),
    
    # Vendor Portal
    path("vendor/portal/", views.vendor_portal_view, name="portal"),
    path("vendor/payment/", views.vendor_payment_view, name="vendor_payment"),
    path("vendor/logout/", views.vendor_logout_view, name="vendor_logout"),
    
    # Reports & Security
    path("reports/daily/", views.daily_report_view, name="daily_report"),
    path("reports/delinquents/", views.delinquent_report_view, name="delinquent_report"),
    path("secure/list/", views.secure_data_list_view, name="secure_list"),
    path("secure/add/", views.add_secure_data_view, name="secure_add"),
    
    # Market Admin Payment Verification URLs
    path("market-admin/dashboard/verifications/", views.admin_verification_list, name="admin_verification_list"),
    path("market-admin/verify-payment/<int:payment_id>/", views.verify_payment, name="verify_payment"),
    path("market-admin/reject-payment/<int:payment_id>/", views.reject_payment, name="reject_payment"),
]
