import json

from django.contrib.auth import authenticate
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from tri.form import Form, Field

from unread import unread_items
from unread.models import Subscription


def change_subscription(request):
    identifier_ = request.GET['identifier']
    try:
        subscription = Subscription.objects.get(user=request.user, identifier=identifier_)
    except Subscription.DoesNotExist:
        subscription = None

    class ChangeSubscriptionForm(Form):
        choices = Field.radio(choices=['Subscribe', 'Unsubscribe'], initial='Subscribe')
        passive = Field.boolean(display_name='Show only when unread', initial=subscription and subscription.subscription_type == 'passive')
        identifier = Field.hidden(initial=identifier_)

    form = ChangeSubscriptionForm(request)

    if request.method == 'POST':
        if form.fields_by_name.choices.value == 'Subscribe':
            Subscription.objects.update_or_create(user=request.user, identifier=identifier_, defaults=dict(subscription_type='passive' if form.fields_by_name.passive.value else 'active'))
        else:
            subscription.delete()

    return render(
        request,
        template_name='unread/change_subscription.html',
        context=dict(
            form=form,
        )
    )


@csrf_exempt
def api_unread_simple(request):
    data = request.POST if request.method == 'POST' else request.GET
    if not request.user.is_authenticated:
        request.user = authenticate(request=request, username=data['username'], password=data['password'])
    if request.user.is_authenticated:
        unread = [x for x in unread_items(user=request.user).values() if x]
        if unread:
            return HttpResponse(f'{len(unread)}')
        else:
            return HttpResponse(status=204)
    else:
        return HttpResponse('Failed to log in', status=403)


def api_unread(request):
    if not request.user.is_authenticated:
        return HttpResponse('Not logged in', status=401)
    return HttpResponse(json.dumps(unread_items(user=request.user)), content_type='application/json')
