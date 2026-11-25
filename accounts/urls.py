from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.EmailLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile, name="profile"),
    path("password-change/", views.AccountPasswordChangeView.as_view(), name="password_change"),
    path("password-reset/", views.AccountPasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", views.AccountPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("password-reset/confirm/<uidb64>/<token>/", views.AccountPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("password-reset/complete/", views.AccountPasswordResetCompleteView.as_view(), name="password_reset_complete"),
    path("register/", views.register, name="register"),
]
