# -*- coding: utf-8 -*-

from django.db.models import Prefetch
from django.http import HttpResponse

from . import models


def one_to_one(request):
    occupation = models.Occupation.objects.first()
    return HttpResponse(occupation.user.id)


def many_to_many(request):
    users = models.User.objects.all()
    return HttpResponse(users[0].hobbies.all())


def many_to_many_through(request):
    users = models.User.objects.prefetch_related(Prefetch('purchases'))
    return HttpResponse(users[0].purchases.all())


def eager_prefetch(request):
    users = models.User.objects.all().prefetch_related('hobbies')
    return HttpResponse(users[0].hobbies.all())


def eager_prefetch_item(request):
    users = models.User.objects.all().prefetch_related('hobbies')
    return HttpResponse(users[0].hobbies.all()[0])


def eager_select(request):
    users = models.User.objects.all().select_related('occupation')
    return HttpResponse(users[0].occupation)


def eager_select_unused(request):
    users = models.User.objects.all().select_related('occupation')
    return HttpResponse(users[0])


def eager_prefetch_scalar(request):
    users = models.User.objects.all().select_related('occupation')
    return HttpResponse(users[0].occupation)


def eager_prefetch_scalar_unused(request):
    users = models.User.objects.all().prefetch_related('occupation')
    return HttpResponse(users[0])
