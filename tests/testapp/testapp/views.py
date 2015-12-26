# -*- coding: utf-8 -*-

from django.http import HttpResponse

from . import models


def one_to_one(request):
    occupations = list(models.Occupation.objects.all())
    return HttpResponse(occupations[0].user.id)


def one_to_one_first(request):
    occupation = models.Occupation.objects.first()
    return HttpResponse(occupation.user.id)


def one_to_many(request):
    users = models.User.objects.all().prefetch_related('addresses')
    return HttpResponse(users[0].addresses.all())


def many_to_many(request):
    users = list(models.User.objects.all())
    return HttpResponse(users[0].hobbies.all())


def prefetch_one_to_one(request):
    users = models.User.objects.all().select_related('occupation')
    return HttpResponse(users[0].occupation)


def prefetch_one_to_one_unused(request):
    users = models.User.objects.all().prefetch_related('occupation')
    return HttpResponse(users[0])


def prefetch_many_to_many(request):
    users = models.User.objects.all().prefetch_related('hobbies')
    return HttpResponse(users[0].hobbies.all())


def prefetch_many_to_many_unused(request):
    users = models.User.objects.all().prefetch_related('addresses')
    return HttpResponse(users[0])


def prefetch_many_to_many_single(request):
    users = models.User.objects.all().prefetch_related('hobbies')
    return HttpResponse(users[0].hobbies.all()[0])


def select_one_to_one(request):
    users = models.User.objects.all().select_related('occupation')
    return HttpResponse(users[0].occupation)


def select_one_to_one_unused(request):
    users = models.User.objects.all().select_related('occupation')
    return HttpResponse(users[0])
