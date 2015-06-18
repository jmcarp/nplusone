# -*- coding: utf-8 -*-

from django.http import HttpResponse

from . import models


def one_to_one(request):
    occupation = models.Occupation.objects.first()
    return HttpResponse(occupation.user.id)


def many_to_many(request):
    users = models.User.objects.all()
    return HttpResponse(users[0].hobbies.all())


def eager(request):
    users = models.User.objects.all().prefetch_related('hobbies')
    return HttpResponse(users[0].hobbies.all())
