from secrets import token_hex

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from iommi import Form, Field

from .models import ResetCode


def forgot_password(request):
    def parse(string_value, **_):
        try:
            return User.objects.get(Q(username=string_value) | Q(email=string_value))
        except User.DoesNotExist:
            return None

    class ForgotPasswordForm(Form):
        username_or_email = Field(is_valid=lambda parsed_data, **_: (parsed_data is not None, 'Unknown username or email'), parse=parse)

        class Meta:
            title = 'Password reset'
            actions__submit__display_name = 'Send reset email'

            def actions__submit__post_handler(form, **_):
                if not form.is_valid():
                    return
                user = form.fields.username_or_email.value
                code = token_hex(64)
                ResetCode.objects.filter(user=user).delete()
                ResetCode.objects.create(user=user, code=code)

                send_mail(
                    subject=f'{settings.INSTALLATION_NAME} password reset',
                    message=f"Your reset code is: \n{code}",
                    from_email=settings.NO_REPLY_EMAIL,
                    recipient_list=[user.email],
                )
                return HttpResponseRedirect(reverse(reset_password))

    return ForgotPasswordForm()


def reset_password(request):
    def parse(string_value, **_):
        try:
            return ResetCode.objects.get(code=string_value)
        except User.DoesNotExist:
            return None

    class ResetPasswordForm(Form):
        reset_code = Field(is_valid=lambda parsed_data, **_: (parsed_data is not None, 'Invalid reset password code'), parse=parse)
        new_password = Field.password()
        confirm_password = Field.password(is_valid=lambda parsed_data, **_: (parsed_data == request.POST.get('new_password'), 'Passwords do not match'))

    form = ResetPasswordForm(request=request)

    if request.POST and form.is_valid():
        reset_code = form.fields.reset_code.value
        reset_code.user.set_password(form.fields.new_password.value)
        login(request, reset_code.user)
        reset_code.delete()
        return HttpResponseRedirect('/')

    return render(request, template_name='auth/reset_password.html', context=dict(form=form))
