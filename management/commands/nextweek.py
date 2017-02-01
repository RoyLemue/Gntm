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

lowdividende = 2.0
highdividende = 4.0
topX = 10

class Command(BaseCommand):
    def handle(self, *args, **options):
        if GntmModel.objects.filter(aktiv=True).count() <= topX:
            dividende=highdividende
        else:
            dividende=lowdividende
        for user in GntmUser.objects.all():
            user.money += dividende*user.getAktienAktiv()
            user.save()