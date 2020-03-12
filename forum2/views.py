from _sha1 import sha1
from base64 import b64encode

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.safestring import mark_safe
from iommi import (
    Form,
    Field,
    Page,
    html,
)

from forum.views import subscriptions


def error_test(request):
    asd()


def blank(request):
    return HttpResponse('')


def logout(request):
    from django.contrib.auth import logout
    logout(request)
    return HttpResponseRedirect('/login/')


def welcome(request):
    return render(request, template_name='forum/welcome.html')


def index(request):
    if request.user_agent.is_mobile:
        return subscriptions(request, template_name='forum/index_mobile.html')
    return render(request, template_name='forum/index.html')


def login(request):
    from django.contrib.auth import login

    if request.user.is_authenticated:
        return HttpResponseRedirect(request.GET.get('next', '/'))

    class LoginForm(Form):
        username = Field()
        password = Field.password()
        next = Field.hidden(initial=request.GET.get('next', '/'))

        class Meta:
            title = 'Login'

            def actions__submit__post_handler(form, **_):
                if 'user' in form.extra:
                    login(request, form.extra.user)
                    return HttpResponseRedirect(form.fields['next'].value or '/')

        def is_valid(self):
            if not super(LoginForm, self).is_valid():
                return False

            username = self.fields['username'].value
            password = self.fields['password'].value

            if username and password:
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    return False
                self.extra.user = user
                if authenticate(request=request, username=username, password=password):
                    return True

                try:
                    username = User.objects.get(username=username)
                    if b64encode(sha1(password.encode()).digest()).decode() == user.password:
                        user.set_password(password)  # upgrade password
                        user.save()
                    authenticate(request=request, username=username, password=password)
                except User.DoesNotExist:
                    pass

            return False

    class LoginPage(Page):
        form = LoginForm()

        forgot_passsword = html.a('Forgot your password?', attrs__href='/forgot-password/')
        p = html.p()
        create_account = html.a('Create account', attrs__href='/create-account/')

        set_focus = html.script(mark_safe('document.getElementById("id_username").focus();'))

    return LoginPage()
#    return render(request, 'forum/login.html', context=dict(form=form, url='/'))
