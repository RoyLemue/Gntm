# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from gntm.models import *
from django.core.files import File
import PIL.ExifTags
import PIL.Image
import os, sys
import glob
from io import BytesIO
from mez.settings import *
from django.forms import ImageField
from django.utils.encoding import smart_text


class Command(BaseCommand):
    def handle(self, *args, **options):
        GntmTransaction.objects.all().delete()
        for u in GntmUser.objects.all():
            u.money := 1000.0;
            u.save()