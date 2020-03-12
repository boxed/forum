import json

from django.contrib.auth import authenticate
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from iommi import Form, Field

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

        class Meta:
            title = 'Change subscription'

            def actions__submit__post_handler(form, **_):
                if form.fields.choices.value == 'Subscribe':
                    Subscription.objects.update_or_create(
                        user=request.user,
                        identifier=identifier_,
                        defaults=dict(subscription_type='passive' if form.fields.passive.value else 'active')
                    )
                else:
                    subscription.delete()

    form = ChangeSubscriptionForm()

    return form


@csrf_exempt
def api_unread_simple(request):
    data = request.POST if request.method == 'POST' else request.GET
    if not request.user.is_authenticated:
        u = authenticate(request=request, username=data['username'], password=data['password'])
        if u:
            request.user = u
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
