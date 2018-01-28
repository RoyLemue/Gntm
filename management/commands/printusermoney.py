# -*- coding: utf-8 -*-
from __future__ import unicode_literals
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
from django.db.models.aggregates import Sum
from django.db.models import Q
import datetime, time
import pytz

from datetime import *

from gntm.dates import *

class Command(BaseCommand):
    def handle(self, *args, **options):
        #UserList = [GntmUser.objects.get(user=1)]
        UserList = GntmUser.objects.filter(Spectator=False)
        """
        for m in GntmModel.objects.filter(Aktiv=False):
            print("----------------")
            print(m.FirstName+" "+str(m.KickDateTime))
            for t in GntmTransaction.objects.filter(model=m, aktien__lt=0):
                print(str(t.time)+" "+str(t.aktien)+" "+t.MoneyString)
        """
        for u in UserList:
            print("----------------")
            print(u.user.first_name+" "+str(u.id)+" "+str(u.user.id))
            money = 1200.0
            for i in range(len(gntmDates)):
                d = gntmDates[i]
                if(i==0):
                    weekSum = GntmTransaction.objects.filter(user=u, time__lt=d).aggregate(Sum('userMoney'))["userMoney__sum"]
                else:
                    weekSum = GntmTransaction.objects.filter(user=u, time__lt=d, time__gte=gntmDates[i-1]).aggregate(Sum('userMoney'))["userMoney__sum"]

                if weekSum:
                    print("{:10.2f}".format(-weekSum))
                    money -= weekSum
                blubb = GntmChapterLog.objects.filter(User=u, WeekNumber=i+1)
                dividende = GntmChapterLog.objects.filter(User=u, WeekNumber=i+1).aggregate(Sum('Money'))["Money__sum"]
                if dividende:
                    money += dividende
                    print("{:10.2f}".format(dividende))
                weekChallenges = u.getWeekChallenges(i)
                if weekChallenges:
                    challengeSum = 0.0
                    for c in weekChallenges:
                        challengeSum += c.Money
                    print("{:10.2f}".format(challengeSum))
                    money+=challengeSum
            lastweekSum = GntmTransaction.objects.filter(user=u, time__gte=gntmDates[len(gntmDates)-1]).aggregate(Sum('userMoney'))["userMoney__sum"]
            if lastweekSum:
                money -= lastweekSum
                print("{:10.2f}".format(-lastweekSum))
            print("{:10.2f}".format(u.Money)+" = "+"{:10.2f}".format(money))
            #u.Money = money
            #u.save()
