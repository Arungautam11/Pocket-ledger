from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import MultipleObjectsReturned


class EmailBackend(ModelBackend):
    """Authenticate the existing Django user model with its email address."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        email = kwargs.get("email") or username
        if not email or password is None:
            return None
        UserModel = get_user_model()
        try:
            user = UserModel._default_manager.get(email__iexact=email)
        except (UserModel.DoesNotExist, MultipleObjectsReturned):
            # Perform a password hash to reduce timing differences for unknown emails.
            UserModel().set_password(password)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
