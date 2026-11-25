import re

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone


class RegistrationTests(TestCase):
    def test_registration_creates_user_with_hashed_password(self):
        response = self.client.post(reverse("register"), {
            "full_name": "Taylor Example",
            "email": "taylor@example.com",
            "password1": "A-long-unique-passphrase-928!",
            "password2": "A-long-unique-passphrase-928!",
        })
        self.assertRedirects(response, "/accounts/login/")
        user = get_user_model().objects.get(email="taylor@example.com")
        self.assertEqual(user.first_name, "Taylor Example")
        self.assertNotEqual(user.password, "A-long-unique-passphrase-928!")
        self.assertTrue(user.check_password("A-long-unique-passphrase-928!"))

    def test_duplicate_email_is_rejected_case_insensitively(self):
        User = get_user_model()
        User.objects.create_user(
            username="existing@example.com", email="existing@example.com", password="Already-safe-928!"
        )
        response = self.client.post(reverse("register"), {
            "full_name": "Another User",
            "email": "EXISTING@example.com",
            "password1": "A-long-unique-passphrase-928!",
            "password2": "A-long-unique-passphrase-928!",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")
        self.assertEqual(User.objects.filter(email__iexact="existing@example.com").count(), 1)


class AuthenticationTests(TestCase):
    def setUp(self):
        cache.clear()
        User = get_user_model()
        self.user = User.objects.create_user(
            username="login@example.com",
            email="login@example.com",
            password="A-long-unique-passphrase-928!",
        )

    def test_login_accepts_email_and_password(self):
        response = self.client.post(reverse("login"), {
            "username": "login@example.com",
            "password": "A-long-unique-passphrase-928!",
            "remember_me": "on",
        })
        self.assertRedirects(response, reverse("dashboard"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)
        expiry_seconds = (self.client.session.get_expiry_date() - timezone.now()).total_seconds()
        self.assertGreater(expiry_seconds, 60 * 60 * 24 * 13)
        self.assertLessEqual(expiry_seconds, 60 * 60 * 24 * 14)

    def test_invalid_credentials_are_rejected(self):
        response = self.client.post(reverse("login"), {
            "username": "login@example.com", "password": "wrong-password",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_private_page_requires_authentication(self):
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_logout_requires_post_and_clears_session(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 405)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_is_rate_limited_after_repeated_failures(self):
        for _ in range(5):
            response = self.client.post(reverse("login"), {
                "username": "login@example.com", "password": "incorrect",
            })
        self.assertContains(response, "Too many sign-in attempts")
        response = self.client.post(reverse("login"), {
            "username": "login@example.com", "password": "A-long-unique-passphrase-928!",
        })
        self.assertNotIn("_auth_user_id", self.client.session)


class AccountManagementTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="profile@example.com",
            email="profile@example.com",
            password="A-long-unique-passphrase-928!",
            first_name="Profile User",
        )
        self.client.force_login(self.user)

    def test_profile_updates_only_the_signed_in_user(self):
        response = self.client.post(reverse("profile"), {
            "full_name": "Updated Name", "email": "updated@example.com",
        })
        self.assertRedirects(response, reverse("profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated Name")
        self.assertEqual(self.user.email, "updated@example.com")
        self.assertEqual(self.user.username, "updated@example.com")

    def test_password_change_uses_django_password_validation(self):
        response = self.client.post(reverse("password_change"), {
            "old_password": "A-long-unique-passphrase-928!",
            "new_password1": "A-different-long-passphrase-833!",
            "new_password2": "A-different-long-passphrase-833!",
        })
        self.assertRedirects(response, reverse("profile"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("A-different-long-passphrase-833!"))

    def test_password_reset_sends_single_use_time_limited_link(self):
        self.client.logout()
        response = self.client.post(reverse("password_reset"), {"email": "profile@example.com"})
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        path = re.search(r"https?://[^/]+(/\S+)", mail.outbox[0].body).group(1)
        response = self.client.get(path)
        self.assertEqual(response.status_code, 302)
        response = self.client.post(response.url, {
            "new_password1": "Reset-long-passphrase-733!",
            "new_password2": "Reset-long-passphrase-733!",
        })
        self.assertRedirects(response, reverse("password_reset_complete"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Reset-long-passphrase-733!"))

    def test_password_reset_response_does_not_reveal_unknown_email(self):
        self.client.logout()
        known = self.client.post(reverse("password_reset"), {"email": "profile@example.com"})
        unknown = self.client.post(reverse("password_reset"), {"email": "missing@example.com"})
        self.assertEqual(known.status_code, unknown.status_code)
        self.assertEqual(known.content, unknown.content)


class CsrfProtectionTests(TestCase):
    def test_registration_login_and_logout_reject_missing_csrf_token(self):
        from django.test import Client

        client = Client(enforce_csrf_checks=True)
        User = get_user_model()
        user = User.objects.create_user(
            username="csrf@example.com", email="csrf@example.com", password="A-long-unique-passphrase-928!",
        )
        self.assertEqual(client.post(reverse("register"), {}).status_code, 403)
        self.assertEqual(client.post(reverse("login"), {
            "username": user.email, "password": "A-long-unique-passphrase-928!",
        }).status_code, 403)
        client.force_login(user)
        self.assertEqual(client.post(reverse("logout")).status_code, 403)


class CsrfProtectionTests(TestCase):
    def test_registration_login_and_logout_reject_missing_csrf_token(self):
        from django.test import Client

        client = Client(enforce_csrf_checks=True)
        User = get_user_model()
        user = User.objects.create_user(
            username="csrf@example.com", email="csrf@example.com", password="A-long-unique-passphrase-928!",
        )
        self.assertEqual(client.post(reverse("register"), {}).status_code, 403)
        self.assertEqual(client.post(reverse("login"), {
            "username": user.email, "password": "A-long-unique-passphrase-928!",
        }).status_code, 403)
        client.force_login(user)
        self.assertEqual(client.post(reverse("logout")).status_code, 403)
