from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class RegistrationForm(forms.Form):
    full_name = forms.CharField(max_length=150, label="Full name")
    email = forms.EmailField(max_length=150, label="Email address")
    password1 = forms.CharField(
        label="Password", strip=False, widget=forms.PasswordInput,
    )
    password2 = forms.CharField(
        label="Confirm password", strip=False, widget=forms.PasswordInput,
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        User = get_user_model()
        if User._default_manager.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "The passwords do not match.")
        if password1:
            User = get_user_model()
            candidate = User(
                email=cleaned.get("email", ""),
                first_name=(cleaned.get("full_name", "").strip().split(" ", 1) or [""])[0],
            )
            try:
                validate_password(password1, user=candidate)
            except ValidationError as error:
                self.add_error("password1", error)
        return cleaned

    def save(self):
        User = get_user_model()
        full_name = self.cleaned_data["full_name"].strip()
        email = User.objects.normalize_email(self.cleaned_data["email"].strip())
        user = User(
            username=email,
            email=email,
            first_name=full_name[:150],
        )
        user.set_password(self.cleaned_data["password1"])
        user.save()
        return user


class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email address", widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    remember_me = forms.BooleanField(required=False, label="Remember me")


class ProfileForm(forms.Form):
    full_name = forms.CharField(max_length=150, label="Full name")
    email = forms.EmailField(max_length=150, label="Email address")

    def __init__(self, *args, user, **kwargs):
        self.user = user
        initial = kwargs.pop("initial", {})
        initial.setdefault("full_name", user.first_name or user.get_full_name())
        initial.setdefault("email", user.email)
        super().__init__(*args, initial=initial, **kwargs)

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        User = get_user_model()
        if User._default_manager.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def save(self):
        full_name = self.cleaned_data["full_name"].strip()
        email = get_user_model().objects.normalize_email(self.cleaned_data["email"].strip())
        self.user.username = email
        self.user.email = email
        self.user.first_name = full_name
        self.user.last_name = ""
        self.user.save(update_fields=["username", "email", "first_name", "last_name"])
        return self.user
