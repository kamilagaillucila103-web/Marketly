from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import SignupRequest, Vendor


class VendorSignupWorkflowTests(TestCase):
    def setUp(self):
        self.signup_data = {
            "first_name": "Jamie",
            "last_name": "Santos",
            "business_name": "Jamie's Store",
            "contact_number": "09171234567",
            "address": "Batangas City",
            "email": "jamie@example.com",
            "username": "jamiesantos",
            "password1": "SafeTestPass123!",
            "password2": "SafeTestPass123!",
        }

    def test_signup_creates_inactive_user_and_pending_request(self):
        response = self.client.post(reverse("market:signup"), self.signup_data)
        self.assertRedirects(response, reverse("market:signup_done"))
        user = get_user_model().objects.get(username="jamiesantos")
        self.assertFalse(user.is_active)
        self.assertTrue(SignupRequest.objects.filter(user=user, status=SignupRequest.PENDING).exists())
        self.assertFalse(Vendor.objects.filter(user=user).exists())

    def test_staff_can_approve_and_activate_vendor(self):
        self.client.post(reverse("market:signup"), self.signup_data)
        request = SignupRequest.objects.get(email="jamie@example.com")
        admin = get_user_model().objects.create_user(username="admin", password="AdminPass123!", is_staff=True)
        self.client.force_login(admin)
        response = self.client.post(reverse("market:signup_approve", args=[request.pk]), {"vendor": ""})
        self.assertRedirects(response, reverse("market:signup_list"))
        request.refresh_from_db()
        request.user.refresh_from_db()
        self.assertEqual(request.status, SignupRequest.APPROVED)
        self.assertTrue(request.user.is_active)
        self.assertTrue(Vendor.objects.filter(user=request.user, contact_email="jamie@example.com").exists())

    def test_staff_can_reject_without_deleting_request(self):
        self.client.post(reverse("market:signup"), self.signup_data)
        request = SignupRequest.objects.get(email="jamie@example.com")
        admin = get_user_model().objects.create_user(username="admin", password="AdminPass123!", is_staff=True)
        self.client.force_login(admin)
        response = self.client.post(reverse("market:signup_reject", args=[request.pk]))
        self.assertRedirects(response, reverse("market:signup_list"))
        request.refresh_from_db()
        request.user.refresh_from_db()
        self.assertEqual(request.status, SignupRequest.REJECTED)
        self.assertFalse(request.user.is_active)
