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
from django.db.models import Max
from django.utils import timezone



class Command(BaseCommand):
    def handle(self, *args, **options):
        if GntmModel.objects.filter(Aktiv=True).count() <= topX:
            dividende=highdividende
        else:
            dividende=lowdividende

        i = GntmChapterLog.objects.all().aggregate(Max("WeekNumber"))["WeekNumber__max"]
        print(i)
        dtime = timezone.now()
        for u in GntmUser.objects.filter(Spectator=False):
            userAktien = System.getUserAktienAtTime(u, dtime.replace(hour=18, minute=15))
            for modelItem in userAktien:
                # more than 10 models left
                logger.debug(modelItem)
                if modelItem['aktien'] != 0:
                    m = GntmModel.objects.get(id=modelItem['model'])
                    if m.KickDateTime > dtime:
                        ch = GntmChapterLog(WeekNumber=i + 1, User=u, Model=m, Aktien=modelItem['aktien'],
                                            Money=modelItem['aktien'] * dividende, Date=dtime.date())
                        ch.save()
                        u.Money += ch.Money
            u.save()