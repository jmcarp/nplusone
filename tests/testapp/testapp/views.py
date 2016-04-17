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
    pets = list(models.Pet.objects.all().prefetch_related('user'))
    # Touch class-level descriptors to exercise `None` instance checks
    print(models.Occupation.user)
    print(models.User.occupation)
    return HttpResponse(str(pet.user) for pet in pets)


def prefetch_many_to_many_unused(request):
    users = models.User.objects.all().prefetch_related('addresses')
    return HttpResponse(users[0])


def prefetch_many_to_many_single(request):
    hobbies = models.Hobby.objects.all().prefetch_related('users')
    return HttpResponse(hobbies[0].users.all()[0])


def prefetch_many_to_many_no_related(request):
    pets = models.Pet.objects.all().prefetch_related('allergy_set')
    return HttpResponse(pets[0].allergy_set.all()[0])


def select_one_to_one(request):
    users = models.User.objects.all().select_related('occupation')
    return HttpResponse(users[0].occupation)


def select_one_to_one_unused(request):
    users = models.User.objects.all().select_related('occupation')
    return HttpResponse(users[0])


def select_many_to_one(request):
    pets = list(models.Pet.objects.all().select_related('user'))
    return HttpResponse(pets[0].user if pets else None)


def select_many_to_one_unused(request):
    pets = list(models.Pet.objects.all().select_related('user'))
    return HttpResponse(pets[0])


def prefetch_nested(request):
    pets = list(models.Pet.objects.all().select_related('user__occupation'))
    return HttpResponse(pets[0].user.occupation)


def prefetch_nested_unused(request):
    pets = list(models.Pet.objects.all().select_related('user__occupation'))
    return HttpResponse(pets[0])
