from django.contrib import messages
from django.core.cache import cache
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth.views import PasswordChangeView, PasswordResetCompleteView, PasswordResetConfirmView
from django.contrib.auth.views import PasswordResetDoneView, PasswordResetView
from django.db import IntegrityError, transaction
from django.urls import reverse_lazy
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
import hashlib

from .forms import EmailLoginForm, ProfileForm, RegistrationForm


@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                form.save()
        except IntegrityError:
            form.add_error("email", "An account with this email address already exists.")
            return render(request, "accounts/register.html", {"form": form})
        messages.success(request, "Your account is ready. Sign in with your email address.")
        return redirect("login")
    return render(request, "accounts/register.html", {"form": form})


class EmailLoginView(LoginView):
    authentication_form = EmailLoginForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    failure_limit = 5
    failure_window = 15 * 60

    def _throttle_keys(self, request):
        email = request.POST.get("username", "").strip().casefold()[:150]
        client_ip = request.META.get("REMOTE_ADDR", "")
        digest = hashlib.sha256(f"{client_ip}\0{email}".encode()).hexdigest()
        return f"login-failures:{digest}", f"login-locked:{digest}"

    def form_valid(self, form):
        failure_key, lock_key = self._throttle_keys(self.request)
        if cache.get(lock_key):
            form.add_error(None, "Too many sign-in attempts. Try again in 15 minutes.")
            return super().form_invalid(form)
        cache.delete(failure_key)
        cache.delete(lock_key)
        response = super().form_valid(form)
        if form.cleaned_data.get("remember_me"):
            self.request.session.set_expiry(60 * 60 * 24 * 14)
        else:
            self.request.session.set_expiry(0)
        return response

    def form_invalid(self, form):
        failure_key, lock_key = self._throttle_keys(self.request)
        if cache.get(lock_key):
            form.add_error(None, "Too many sign-in attempts. Try again in 15 minutes.")
            return super().form_invalid(form)
        cache.add(failure_key, 0, timeout=self.failure_window)
        try:
            failures = cache.incr(failure_key)
        except ValueError:
            cache.set(failure_key, 1, timeout=self.failure_window)
            failures = 1
        if failures >= self.failure_limit:
            cache.set(lock_key, True, timeout=self.failure_window)
            form.add_error(None, "Too many sign-in attempts. Try again in 15 minutes.")
        return super().form_invalid(form)


@login_required
@require_http_methods(["POST"])
def logout_view(request):
    logout(request)
    messages.success(request, "You have been signed out.")
    return redirect("login")


@login_required
@require_http_methods(["GET", "POST"])
def profile(request):
    form = ProfileForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                form.save()
        except IntegrityError:
            form.add_error("email", "An account with this email address already exists.")
        else:
            messages.success(request, "Your profile has been updated.")
            return redirect("profile")
    return render(request, "accounts/profile.html", {"form": form, "account_created": request.user.date_joined})


class AccountPasswordChangeView(PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("profile")

    def form_valid(self, form):
        messages.success(self.request, "Your password has been changed.")
        return super().form_valid(form)


class AccountPasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset_form.html"
    email_template_name = "accounts/password_reset_email.html"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("password_reset_done")


class AccountPasswordResetDoneView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class AccountPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")


class AccountPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"
