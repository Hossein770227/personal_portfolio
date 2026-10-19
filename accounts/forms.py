from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import (
    ReadOnlyPasswordHashField,
    UserCreationForm as BaseUserCreationForm,
    UserChangeForm as BaseUserChangeForm,
)

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _

from .validator import validate_iranian_phone

User = get_user_model()


class UserCreationForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = ("phone_number", "full_name")

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError(_("Passwords do not match."))

        validate_password(password2)

        return password2


class UserChangeForm(BaseUserChangeForm):
    password = ReadOnlyPasswordHashField(
        help_text=_(
            "You can change the password using this "
            "<a href='../password/'>form</a>."
        )
    )

    class Meta:
        model = User
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
            User.objects.filter(phone_number=phone_number)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise ValidationError(_("This phone number already exists."))

        return phone_number


class UserRegisterForm(forms.Form):
    full_name = forms.CharField(
        label=_("Full name"),
        max_length=100,
    )

    phone = forms.CharField(
        label=_("Phone number"),
        max_length=11,
        validators=[validate_iranian_phone],
    )

    password1 = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(render_value=False),
    )

    password2 = forms.CharField(
        label=_("Confirm password"),
        widget=forms.PasswordInput(render_value=False),
    )

    def clean_phone(self):
        phone = self.cleaned_data["phone"]

        if User.objects.filter(phone_number=phone).exists():
            raise ValidationError(_("This phone number already exists."))

        return phone

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError(_("Passwords do not match."))

        validate_password(password2)

        return password2


class VerifyCodeForm(forms.Form):
    code = forms.IntegerField(
        label=_("Verification code"),
        validators=[
            MinValueValidator(1000),
            MaxValueValidator(9999),
        ],
    )


class ForgotPasswordForm(forms.Form):
    phone_number = forms.CharField(
        label=_("Phone number"),
        max_length=11,
        validators=[validate_iranian_phone],
    )

    def clean_phone_number(self):
        phone = self.cleaned_data["phone_number"]

        if not User.objects.filter(phone_number=phone).exists():
            raise ValidationError(_("This phone number does not exist."))

        return phone


class ResetPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(render_value=False),
    )

    new_password2 = forms.CharField(
        label=_("Confirm new password"),
        widget=forms.PasswordInput(render_value=False),
    )

    def clean(self):
        cleaned_data = super().clean()

        password1 = cleaned_data.get("new_password1")
        password2 = cleaned_data.get("new_password2")

        if password1 and password2:
            if password1 != password2:
                raise ValidationError(_("The passwords must match."))

            validate_password(password1)

        return cleaned_data


class PhoneLoginForm(forms.Form):
    phone_number = forms.CharField(
        label=_("Phone number"),
        max_length=11,
        validators=[validate_iranian_phone],
    )

    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(render_value=False),
    )

    def clean(self):
        cleaned_data = super().clean()

        phone_number = cleaned_data.get("phone_number")
        password = cleaned_data.get("password")

        if phone_number and password:
            self.user_cache = authenticate(
                phone_number=phone_number,
                password=password,
            )

            if self.user_cache is None:
                raise ValidationError(
                    _("Invalid phone number or password.")
                )

        return cleaned_data

    def get_user(self):
        return self.user_cache