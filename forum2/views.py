from _sha1 import sha1
from base64 import b64encode

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from tri_form import Form, Field

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

        def is_valid(self):
            if not super(LoginForm, self).is_valid():
                return False

            username = self.fields_by_name['username'].value
            password = self.fields_by_name['password'].value

            if username and password:
                user = User.objects.get(username=username)
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

    form = LoginForm(request)

    if request.method == 'POST' and form.is_valid():
        login(request, form.extra.user)
        return HttpResponseRedirect(form.fields_by_name['next'].value or '/')

    return render(request, 'forum/login.html', context=dict(form=form, url='/'))
