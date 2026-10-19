import random

from django.contrib import messages
from django.contrib.auth import (
    get_user_model,
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
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


def create_otp(phone_number):
    """
    Delete old OTPs, create a new one and send it.
    """
    OtpCode.objects.filter(phone_number=phone_number).delete()

    code = random.randint(1000, 9999)

    send_otp_code(phone_number, code)

    return OtpCode.objects.create(
        phone_number=phone_number,
        code=code,
    )


def get_valid_otp(phone_number):

    otp = (
        OtpCode.objects
        .filter(phone_number=phone_number)
        .order_by("-date_time_created")
        .first()
    )

    if otp and otp.is_expired:
        otp.delete()
        return None

    return otp


class UserRegisterView(View):
    form_class = UserRegisterForm
    template_name = "accounts/user_register.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {"form": self.form_class()},
        )

    def post(self, request):
        form = self.form_class(request.POST)

        if not form.is_valid():
            return render(
                request,
                self.template_name,
                {"form": form},
            )

        phone = form.cleaned_data["phone"]

        if get_valid_otp(phone):
            messages.error(
                request,
                _("We already sent you a code. Please wait."),
            )
            return redirect("accounts:verify_code")

        create_otp(phone)

        request.session["user_registration_info"] = {
            "phone_number": phone,
            "full_name": form.cleaned_data["full_name"],
            "password": form.cleaned_data["password2"],
        }

        messages.success(
            request,
            _("Verification code sent successfully."),
        )

        return redirect("accounts:verify_code")


class UserRegisterCodeView(View):
    form_class = VerifyCodeForm
    template_name = "accounts/verify_code.html"

    def get(self, request):
        if "user_registration_info" not in request.session:
            messages.error(
                request,
                _("Registration information not found."),
            )
            return redirect("accounts:user_register")

        return render(
            request,
            self.template_name,
            {"form": self.form_class()},
        )

    def post(self, request):
        user_data = request.session.get("user_registration_info")

        if not user_data:
            messages.error(
                request,
                _("Registration information not found."),
            )
            return redirect("accounts:user_register")

        form = self.form_class(request.POST)

        if not form.is_valid():
            return render(
                request,
                self.template_name,
                {"form": form},
            )

        otp = get_valid_otp(user_data["phone_number"])

        if otp is None:
            messages.error(
                request,
                _("The OTP code has expired."),
            )
            return redirect("accounts:user_register")

        if str(form.cleaned_data["code"]) != str(otp.code):
            messages.error(
                request,
                _("The entered code is incorrect."),
            )
            return redirect("accounts:verify_code")

        user = User.objects.create_user(
            phone_number=user_data["phone_number"],
            full_name=user_data["full_name"],
            password=user_data["password"],
        )

        otp.delete()

        request.session.pop("user_registration_info", None)

        login(request, user)

        messages.success(
            request,
            _("You have successfully registered."),
        )

        return redirect("website:home")

def login_view(request):
    if request.user.is_authenticated:
        return redirect("website:home")

    form = PhoneLoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())

        messages.success(
            request,
            _("You have successfully logged in."),
        )

        next_url = request.GET.get("next")
        return redirect(next_url or "website:home")

    return render(
        request,
        "accounts/login.html",
        {"form": form},
    )


def logout_view(request):
    if request.method == "POST":
        logout(request)

        messages.success(
            request,
            _("You have successfully logged out."),
        )

    return redirect("website:home")


@login_required
def password_change_view(request):
    form = PasswordChangeForm(
        user=request.user,
        data=request.POST or None,
    )

    if request.method == "POST":
        if form.is_valid():
            user = form.save()

            update_session_auth_hash(request, user)

            messages.success(
                request,
                _("Your password was changed successfully."),
            )

            return redirect("website:home")

        messages.error(
            request,
            _("Please correct the errors below."),
        )

    return render(
        request,
        "accounts/password_change.html",
        {"form": form},
    )


def forgot_password(request):
    form = ForgotPasswordForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        phone_number = form.cleaned_data["phone_number"]

        latest_otp = (
            OtpCode.objects.filter(phone_number=phone_number)
            .order_by("-date_time_created")
            .first()
        )

        if (
            latest_otp
            and (
                timezone.now() - latest_otp.date_time_created
            ).total_seconds() < 120
        ):
            messages.error(
                request,
                _("Please wait a moment before requesting a new OTP."),
            )

            return render(
                request,
                "accounts/forgot_password.html",
                {"form": form},
            )

        create_otp(phone_number)

        request.session["reset_phone"] = phone_number

        messages.success(
            request,
            _("A verification code has been sent to your phone number."),
        )

        return redirect(
            reverse("accounts:verify_code_forgot_password")
        )

    return render(
        request,
        "accounts/forgot_password.html",
        {"form": form},
    )

User = get_user_model()


def verify_code_forgot_password(request):
    reset_phone = request.session.get("reset_phone")

    if not reset_phone:
        messages.error(
            request,
            _("Session expired. Please start over."),
        )
        return redirect("accounts:forgot_password")

    form = VerifyCodeForm(request.POST or None)

    if request.method == "POST" and form.is_valid():

        otp = get_valid_otp(reset_phone)

        if otp is None:
            messages.error(
                request,
                _("The OTP code has expired. Please request a new one."),
            )
            return redirect("accounts:forgot_password")

        if str(form.cleaned_data["code"]) != str(otp.code):
            messages.error(
                request,
                _("The entered code is incorrect."),
            )
            return redirect("accounts:verify_code_forgot_password")

        otp.delete()

        request.session["reset_password_verified"] = True

        messages.success(
            request,
            _("Code verified successfully."),
        )

        return redirect("accounts:reset_password")

    return render(
        request,
        "accounts/verify_code_forgot_password.html",
        {"form": form},
    )


def reset_password(request):
    reset_phone = request.session.get("reset_phone")
    verified = request.session.get("reset_password_verified")

    if not reset_phone or not verified:
        messages.error(
            request,
            _("Please start from the password recovery step."),
        )
        return redirect("accounts:forgot_password")

    form = ResetPasswordForm(request.POST or None)

    if request.method == "POST" and form.is_valid():

        try:
            user = User.objects.get(phone_number=reset_phone)
        except User.DoesNotExist:
            messages.error(
                request,
                _("User not found."),
            )
            return redirect("accounts:forgot_password")

        user.set_password(
            form.cleaned_data["new_password1"]
        )
        user.save(update_fields=["password"])

        request.session.pop("reset_phone", None)
        request.session.pop("reset_password_verified", None)

        messages.success(
            request,
            _("Your password has been successfully changed."),
        )

        return redirect("accounts:login")

    return render(
        request,
        "accounts/reset_password.html",
        {"form": form},
    )