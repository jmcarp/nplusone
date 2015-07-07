# -*- coding: utf-8 -*-

from __future__ import absolute_import

from peewee import RelationDescriptor
from peewee import ReverseRelationDescriptor

try:
    from playhouse import fields
except ImportError:  # pragma: no cover
    from playhouse import shortcuts as fields

from nplusone.core import signals


def parse_get_object(args, kwargs, context):
    descriptor = args[0]
    return descriptor.field.model_class, descriptor.field.name


def parse_reverse_get(args, kwargs, context):
    descriptor = args[0]
    return descriptor.field.rel_model, descriptor.field.related_name


def get_object_or_id(self, instance):
    rel_id = instance._data.get(self.att_name)
    if rel_id is not None or self.att_name in instance._obj_cache:
        if self.att_name not in instance._obj_cache:
            signals.lazy_load.send(None, args=(self, instance), parser=parse_get_object)
            obj = self.rel_model.get(self.field.to_field == rel_id)
            instance._obj_cache[self.att_name] = obj
        return instance._obj_cache[self.att_name]
    elif not self.field.null:  # pragma: no cover; pasted from peewee
        raise self.rel_model.DoesNotExist
    return rel_id  # pragma: no cover; pasted from peewee
RelationDescriptor.get_object_or_id = get_object_or_id


def reverse_get(self, instance, instance_type=None):
    if instance is not None:
        signals.lazy_load.send(
            None,
            args=(self, instance),
            kwargs={'instance_type': instance_type},
            parser=parse_reverse_get,
        )
        return self.rel_model.select().where(
            self.field == getattr(instance, self.field.to_field.name))
    return self  # pragma: no cover; pasted from peewee
ReverseRelationDescriptor.__get__ = reverse_get


def reverse_get_many(self, instance, instance_type=None):
    if instance is not None:
        signals.lazy_load.send(
            None,
            args=(self, instance),
            kwargs={'instance_type': instance_type},
            parser=parse_get_object,
        )
        return (fields.ManyToManyQuery(instance, self, self.rel_model)
                .select()
                .join(self.through_model)
                .join(self.model_class)
                .where(self.src_fk == instance))
    return self.field
fields.ManyToManyFieldDescriptor.__get__ = reverse_get_many
