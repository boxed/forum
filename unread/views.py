import json

from django.contrib.auth import authenticate
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from unread import unread_items


def start(request, system, data):
    # TODO:
    #  - ask for active or passive
    #  - implement

    pass


def stop(request, system, data):
    # TODO:
    #  - ask for confirmation
    #  - implement
    pass


@csrf_exempt
def api_unread_simple(request):
    data = request.POST if request.method == 'POST' else request.GET
    if request.user.is_authenticated or authenticate(request=request, username=data['username'], password=data['password']):
        unread = unread_items(user=request.user)
        if unread:
            return HttpResponse(f'{len(unread)}')
        else:
            return HttpResponse(status=204)
    else:
        return HttpResponse('Failed to log in', status=403)


def api_unread(request):
    return HttpResponse(json.dumps(unread_items(user=request.user)), content_type='application/json')
