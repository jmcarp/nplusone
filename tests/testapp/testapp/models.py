# -*- coding: utf-8 -*-

from django.db import models


class User(models.Model):
    hobbies = models.ManyToManyField('Hobby', related_name='users')
    goods = models.ManyToManyField('Good', related_name='owners',
                                   through='Purchase')


class Pet(models.Model):
    user = models.ForeignKey('User')


class Allergy(models.Model):
    pets = models.ManyToManyField('Pet')


class Occupation(models.Model):
    user = models.OneToOneField('User', related_name='occupation')


class Address(models.Model):
    user = models.ForeignKey('User', related_name='addresses')


class Hobby(models.Model):
    pass


class Good(models.Model):
    pass


class Purchase(models.Model):
    user = models.ForeignKey(User, related_name='purchases')
    good = models.ForeignKey(Good)
    purchased_at = models.DateTimeField(auto_now_add=True)
