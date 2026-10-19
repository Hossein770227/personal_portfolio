
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.contrib import messages
from django.views import View

from utils import send_otp_code
from .forms import (
    ForgotPasswordForm,
    PhoneLoginForm,
    ResetPasswordForm,
    UserRegisterForm,
    VerifyCodeForm,
)
from .models import OtpCode

User = get_user_model()

OTP_MAX_ATTEMPTS = 5
OTP_RESEND_SECONDS = 120
OTP_SESSION_SECONDS = 300


def create_otp(phone_number, purpose):
    now = timezone.now()

    recent_otp = OtpCode.objects.filter(
        phone_number=phone_number,
        purpose=purpose,
        date_time_created__gte=now - timedelta(seconds=OTP_RESEND_SECONDS),
    ).exists()

    if recent_otp:
        return False

    code = f"{secrets.randbelow(9000) + 1000}"

    otp = OtpCode.objects.create(
        phone_number=phone_number,
        purpose=purpose,
        code=make_password(code),
    )

    try:
        send_otp_code(phone_number, code)
    except Exception:
        otp.delete()
        raise

    return True


def get_valid_otp(phone_number, purpose):
    otp = (
        OtpCode.objects.filter(
            phone_number=phone_number,
            purpose=purpose,
        )
        .order_by("-date_time_created")
        .first()
    )

    if otp and otp.is_expired:
        otp.delete()
        return None

    return otp


def verify_otp(otp, submitted_code):
    if otp is None or otp.is_expired or otp.attempts >= OTP_MAX_ATTEMPTS:
        return False

    with transaction.atomic():
        locked_otp = OtpCode.objects.select_for_update().filter(pk=otp.pk).first()

        if (
            locked_otp is None
            or locked_otp.is_expired
            or locked_otp.attempts >= OTP_MAX_ATTEMPTS
        ):
            return False

        if check_password(str(submitted_code), locked_otp.code):
            return True

        OtpCode.objects.filter(pk=locked_otp.pk).update(
            attempts=F("attempts") + 1
        )
        return False


def safe_next_url(request):
    candidate = request.POST.get("next") or request.GET.get("next")

    if candidate and url_has_allowed_host_and_scheme(
        candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return candidate

    return reverse("website:home")


class UserRegisterView(View):
    form_class = UserRegisterForm
    template_name = "accounts/user_register.html"

    def get(self, request):
        return render(request, self.template_name, {"form": self.form_class()})

    def post(self, request):
        form = self.form_class(request.POST)

        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        phone = form.cleaned_data["phone"]

        if User.objects.filter(phone_number=phone).exists():
            form.add_error("phone", _("This phone number already exists."))
            return render(request, self.template_name, {"form": form})

        if get_valid_otp(phone, "registration"):
            messages.error(request, _("A code was already sent. Please wait."))
            return redirect("accounts:verify_code")

        try:
            sent = create_otp(phone, "registration")
        except Exception:
            messages.error(request, _("Could not send the verification code."))
            return render(request, self.template_name, {"form": form})

        if not sent:
            messages.error(request, _("Please wait before requesting another code."))
            return redirect("accounts:user_register")

        request.session["user_registration_info"] = {
            "phone_number": phone,
            "full_name": form.cleaned_data["full_name"],
            "password_hash": make_password(form.cleaned_data["password2"]),
        }
        request.session.set_expiry(OTP_SESSION_SECONDS)

        messages.success(request, _("Verification code sent successfully."))
        return redirect("accounts:verify_code")


class UserRegisterCodeView(View):
    form_class = VerifyCodeForm
    template_name = "accounts/verify_code.html"

    def get(self, request):
        if not request.session.get("user_registration_info"):
            return redirect("accounts:user_register")

        return render(request, self.template_name, {"form": self.form_class()})

    def post(self, request):
        data = request.session.get("user_registration_info")
        if not data:
            messages.error(request, _("Registration session expired."))
            return redirect("accounts:user_register")

        form = self.form_class(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        with transaction.atomic():
            otp = get_valid_otp(data["phone_number"], "registration")

            if not verify_otp(otp, form.cleaned_data["code"]):
                messages.error(request, _("Invalid or expired code."))
                return redirect("accounts:verify_code")

            if User.objects.filter(phone_number=data["phone_number"]).exists():
                messages.error(request, _("This phone number already exists."))
                return redirect("accounts:user_register")

            user = User(
                phone_number=data["phone_number"],
                full_name=data["full_name"],
            )
            user.password = data["password_hash"]
            user.save()

            otp.delete()

        request.session.pop("user_registration_info", None)
        login(request, user)

        messages.success(request, _("Registration completed successfully."))
        return redirect("website:home")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("website:home")

    form = PhoneLoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        messages.success(request, _("You have successfully logged in."))
        return redirect(safe_next_url(request))

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, _("You have successfully logged out."))

    return redirect("website:home")


@login_required
def password_change_view(request):
    form = PasswordChangeForm(user=request.user, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, _("Password changed successfully."))
        return redirect("website:home")

    return render(request, "accounts/password_change.html", {"form": form})


def forgot_password(request):
    form = ForgotPasswordForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        phone = form.cleaned_data["phone_number"]

        if not User.objects.filter(phone_number=phone).exists():
            messages.success(
                request,
                _("If the account exists, a verification code will be sent."),
            )
            return render(request, "accounts/forgot_password.html", {"form": form})

        if get_valid_otp(phone, "password_reset"):
            messages.error(request, _("A code was already sent. Please wait."))
            return render(request, "accounts/forgot_password.html", {"form": form})

        try:
            sent = create_otp(phone, "password_reset")
        except Exception:
            messages.error(request, _("Could not send the verification code."))
            return render(request, "accounts/forgot_password.html", {"form": form})

        if not sent:
            messages.error(request, _("Please wait before requesting another code."))
            return render(request, "accounts/forgot_password.html", {"form": form})

        request.session["reset_phone"] = phone
        request.session.pop("reset_password_verified", None)
        request.session.set_expiry(OTP_SESSION_SECONDS)

        return redirect("accounts:verify_code_forgot_password")

    return render(request, "accounts/forgot_password.html", {"form": form})


def verify_code_forgot_password(request):
    phone = request.session.get("reset_phone")

    if not phone:
        messages.error(request, _("Session expired. Please start again."))
        return redirect("accounts:forgot_password")

    form = VerifyCodeForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            otp = get_valid_otp(phone, "password_reset")

            if not verify_otp(otp, form.cleaned_data["code"]):
                messages.error(request, _("Invalid or expired code."))
                return redirect("accounts:verify_code_forgot_password")

            otp.delete()

        request.session["reset_password_verified"] = True
        request.session["reset_verified_at"] = timezone.now().timestamp()
        return redirect("accounts:reset_password")

    return render(
        request,
        "accounts/verify_code_forgot_password.html",
        {"form": form},
    )


def reset_password(request):
    phone = request.session.get("reset_phone")
    verified = request.session.get("reset_password_verified")
    verified_at = request.session.get("reset_verified_at", 0)

    if (
        not phone
        or not verified
        or timezone.now().timestamp() - verified_at > OTP_SESSION_SECONDS
    ):
        request.session.pop("reset_password_verified", None)
        messages.error(request, _("Please verify your phone number again."))
        return redirect("accounts:forgot_password")

    form = ResetPasswordForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = User.objects.filter(phone_number=phone).first()

        if user is None:
            request.session.flush()
            return redirect("accounts:forgot_password")

        user.set_password(form.cleaned_data["new_password1"])
        user.save(update_fields=["password"])

        request.session.pop("reset_phone", None)
        request.session.pop("reset_password_verified", None)
        request.session.pop("reset_verified_at", None)

        messages.success(request, _("Password changed successfully."))
        return redirect("accounts:login")

    return render(request, "accounts/reset_password.html", {"form": form})
