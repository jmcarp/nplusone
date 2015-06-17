# -*- coding: utf-8 -*-

from django.db import models


class User(models.Model):
    hobbies = models.ManyToManyField('Hobby', related_name='users')


class Occupation(models.Model):
    user = models.OneToOneField('User', related_name='occupation')


class Address(models.Model):
    user = models.ForeignKey('User', related_name='addresses')


class Hobby(models.Model):
    pass
