# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-12-07 13:27
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('talk', '0020_auto_20171013_1825'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='talk',
            name='event',
        ),
    ]
