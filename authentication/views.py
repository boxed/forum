from secrets import token_hex

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse
from tri_form import Field
from tri_form.compat import ValidationError
from tri_portal import HtmlPageContent, Page

from .models import ResetCode


def forgot_password(request):
    def parse(string_value, **_):
        try:
            return User.objects.get(Q(username=string_value) | Q(email=string_value))
        except User.DoesNotExist:
            raise ValidationError('Unknown username or email')

    def on_valid_post(form, **_):
        user = form.fields_by_name.username_or_email.value
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

    return Page.form_page(
        title='Forgot password',
        contents__form__on_valid__POST=on_valid_post,
        contents__form__request=request,  # TODO: this shouldn't be neccessary, fix later
        contents__form__fields=[
            Field(
                name='username_or_email',
                is_valid=lambda parsed_data, **_: (parsed_data is not None, 'Unknown username or email'),
                parse=parse,
            ),
        ],
        contents__form__actions__submit__title='Send reset email',
    ).respond_or_render(request)


def reset_password(request):
    def on_valid_post(form, **_):
        reset_code = form.fields_by_name.reset_code.value
        reset_code.user.set_password(form.fields_by_name.new_password.value)
        login(request, reset_code.user)
        reset_code.delete()
        return HttpResponseRedirect('/')

    return Page.form_page(
        title='Reset password',
        contents__form__fields=[
            Field(name='reset_code'),
            Field.password(name='new_password'),
            Field.password(name='confirm_password'),
        ],
        contents__form__actions__submit__title='Set password',
        contents__form__on_valid__POST=on_valid_post,
        contents__email_sent_message=HtmlPageContent(
            after=-1,
            html='E-mail sent! Please check your inbox for the reset code.',
        ),
    ).respond_or_render(request)
