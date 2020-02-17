# -*- coding: utf-8 -*-
import datetime
import importlib
import os
import tablib

from django.core.management import call_command
from django.test import TestCase

from core import admin, models


class ImportTestCase(TestCase):
    base_path = os.path.dirname(__file__) + '/import/'
    admin_module = importlib.import_module('core.admin')
    model_module = importlib.import_module('core.models')

    def setUp(self):
        call_command('migrate', verbosity=0)
        # The data to be imported uses 2020-02-10 as a basis and Child ID 1.
        birth_date = datetime.date(year=2020, month=2, day=10)
        models.Child.objects.create(
            first_name='Child', last_name='One', birth_date=birth_date).save()

    def get_dataset(self, model_name):
        file = open(self.base_path + model_name + '.csv')
        return tablib.Dataset().load(file.read())

    def import_data(self, model, count):
        dataset = self.get_dataset(model._meta.model_name)
        resource_class = getattr(
            self.admin_module, model.__name__ + 'ImportExportResource')
        resource = resource_class()
        result = resource.import_data(dataset, dry_run=False)
        self.assertFalse(result.has_validation_errors())
        self.assertFalse(result.has_errors())
        self.assertEqual(model.objects.count(), count)

    def test_child(self):
        self.import_data(models.Child, 2)

    def test_diaperchange(self):
        self.import_data(models.DiaperChange, 75)

    def test_feeding(self):
        self.import_data(models.Feeding, 40)

    def test_note(self):
        self.import_data(models.Note, 1)

    def test_sleep(self):
        self.import_data(models.Sleep, 39)

    def test_temperature(self):
        self.import_data(models.Temperature, 23)

    def test_tummytime(self):
        self.import_data(models.TummyTime, 36)

    def test_weight(self):
        self.import_data(models.Weight, 5)

    def test_invalid_child(self):
        dataset = self.get_dataset('diaperchange-invalid-child')
        resource = admin.DiaperChangeImportExportResource()
        result = resource.import_data(dataset, dry_run=False)
        self.assertTrue(result.has_validation_errors())
