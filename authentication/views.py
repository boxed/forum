from secrets import token_hex

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from tri_declarative import dispatch, EMPTY
from tri_form import Form, Field

from .models import ResetCode


class Page:
    @dispatch(
        content=EMPTY,
    )
    def __init__(self, request, content):
        self.request = request
        self.content = content

    class Meta:
        base_template = 'forum/base.html'


class FormPage(Page):
    pass


## start forgot password page
def parse(string_value, **_):
    try:
        return User.objects.get(Q(username=string_value) | Q(email=string_value))
    except User.DoesNotExist:
        return None


class ForgotPasswordForm(Form):
    username_or_email = Field(
        is_valid=lambda parsed_data, **_: (parsed_data is not None, 'Unknown username or email'),
        parse=parse,
    )

class ForgotPasswordPage(FormPage):
    pass


ForgotPasswordPage.as_view


# start reset password page

def forgot_password(request):
    def parse(string_value, **_):
        try:
            return User.objects.get(Q(username=string_value) | Q(email=string_value))
        except User.DoesNotExist:
            return None

    class ForgotPasswordForm(Form):
        username_or_email = Field(
            is_valid=lambda parsed_data, **_: (parsed_data is not None, 'Unknown username or email'),
            parse=parse,
        )

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

    return Page(
        request,
        content__form__call_target=ForgotPasswordForm.post_view,
        content__form__on_valid_post=on_valid_post,
    )


def reset_password(request):
    class ResetPasswordForm(Form):
        reset_code = Field()
        new_password = Field.password()
        confirm_password = Field.password()

    form = ResetPasswordForm(request=request)

    if request.POST and form.is_valid():


        return HttpResponseRedirect('/')

    return render(request, template_name='auth/reset_password.html', context=dict(base_template=settings.BASE_TEMPLATE, form=form))
