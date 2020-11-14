from django.test import RequestFactory
from tri_struct import Struct


def req(method, **data):
    return getattr(RequestFactory(HTTP_REFERER='/'), method.lower())('/', data=data)


def user_req(method, **data):
    request = req(method, **data)
    request.user = Struct(is_staff=False)
    return request


def staff_req(method, **data):
    request = req(method, **data)
    request.user = Struct(is_staff=True)
    return request
