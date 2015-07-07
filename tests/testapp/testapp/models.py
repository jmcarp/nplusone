# -*- coding: utf-8 -*-

from django.db import models


class User(models.Model):
    hobbies = models.ManyToManyField('Hobby', related_name='users')


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
