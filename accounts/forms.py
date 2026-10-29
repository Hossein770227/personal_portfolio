
from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import (
    ReadOnlyPasswordHashField,
    UserChangeForm as BaseUserChangeForm,
    UserCreationForm as BaseUserCreationForm,
)
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from accounts.models import MyUser

from .validator import validate_iranian_phone

User = get_user_model()


class UserCreationForm(BaseUserCreationForm):
    """Django Admin user creation form."""

    class Meta:
        model = MyUser
        fields = ("phone_number", "full_name")

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if not password1 or not password2:
            return password2

        if password1 != password2:
            raise ValidationError(_("Passwords do not match."))

        validate_password(password2, self.instance)
        return password2


class UserChangeForm(BaseUserChangeForm):
    """Django Admin user change form."""

    password = ReadOnlyPasswordHashField(
        help_text=_(
            "You can change the password using the password change form."
        )
    )

    class Meta:
        model = MyUser
        fields = (
            "phone_number",
            "full_name",
            "password",
            "last_login",
            "is_active",
            "is_staff",
        )

    def clean_phone_number(self):
        phone_number = self.cleaned_data["phone_number"]

        if (
            MyUser.objects.filter(phone_number=phone_number)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise ValidationError(_("This phone number already exists."))

        return phone_number


class UserRegisterForm(forms.Form):
    full_name = forms.CharField(
        label=_("Full name"),
        max_length=100,
        strip=True,
    )

    phone = forms.CharField(
        label=_("Phone number"),
        max_length=13,
        validators=[validate_iranian_phone],
    )

    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput,
    )

    password2 = forms.CharField(
        label=_("Confirm password"),
        strip=False,
        widget=forms.PasswordInput,
    )

    def clean_phone(self):
        phone = self.cleaned_data["phone"]

        if User.objects.filter(phone_number=phone).exists():
            raise ValidationError(_("This phone number already exists."))

        return phone

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if not password1 or not password2:
            return password2

        if password1 != password2:
            raise ValidationError(_("Passwords do not match."))

        validate_password(password2)
        return password2


class VerifyCodeForm(forms.Form):
    code = forms.CharField(
        label=_("Verification code"),
        min_length=4,
        max_length=4,
        strip=True,
        validators=[
            RegexValidator(
                regex=r"^\d{4}$",
                message=_("Enter a valid four-digit verification code."),
            )
        ],
        widget=forms.TextInput(
            attrs={
                "inputmode": "numeric",
                "autocomplete": "one-time-code",
                "maxlength": "4",
            }
        ),
    )


class ForgotPasswordForm(forms.Form):
    phone_number = forms.CharField(
        label=_("Phone number"),
        max_length=13,
        validators=[validate_iranian_phone],
    )


class ResetPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label=_("New password"),
        strip=False,
        widget=forms.PasswordInput,
    )

    new_password2 = forms.CharField(
        label=_("Confirm new password"),
        strip=False,
        widget=forms.PasswordInput,
    )

    def clean(self):
        cleaned_data = super().clean()

        password1 = cleaned_data.get("new_password1")
        password2 = cleaned_data.get("new_password2")

        if not password1 or not password2:
            return cleaned_data

        if password1 != password2:
            self.add_error(
                "new_password2",
                _("The passwords must match."),
            )
            return cleaned_data

        validate_password(password1)
        return cleaned_data


class PhoneLoginForm(forms.Form):
    phone_number = forms.CharField(
        label=_("Phone number"),
        max_length=13,
        validators=[validate_iranian_phone],
    )

    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput,
    )

    def clean(self):
        cleaned_data = super().clean()

        phone_number = cleaned_data.get("phone_number")
        password = cleaned_data.get("password")

        if phone_number and password:
            self.user_cache = authenticate(
                self.request,
                phone_number=phone_number,
                password=password,
            )

            if self.user_cache is None:
                raise ValidationError(
                    _("Invalid phone number or password.")
                )

        return cleaned_data

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def get_user(self):
        return self.user_cache
