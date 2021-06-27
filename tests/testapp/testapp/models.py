# -*- coding: utf-8 -*-

from django.db import models


class User(models.Model):
    hobbies = models.ManyToManyField('Hobby', related_name='users')


class Pet(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)


class Allergy(models.Model):
    pets = models.ManyToManyField('Pet')


class Occupation(models.Model):
    user = models.OneToOneField(
        'User', on_delete=models.CASCADE, related_name='occupation')


class Address(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='addresses')


class Hobby(models.Model):
    pass


class Medicine(models.Model):
    name = models.CharField(max_length=20)
    prescription = models.BooleanField(default=False)
