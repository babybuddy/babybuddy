# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.core.management.commands import migrate


class Command(migrate.Command):
    help = 'Creates an initial User (admin/admin) for Baby Buddy.'

    def handle(self, *args, **kwargs):
        super(Command, self).handle(*args, **kwargs)

        superusers = User.objects.filter(is_superuser=True)
        if len(superusers) == 0:
            default_user = User.objects.create_user('admin', password='admin')
            default_user.is_superuser = True
            default_user.is_staff = True
            default_user.save()
