# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.core.management.base import BaseCommand, CommandError
from gntm.models import *
from django.db.models.aggregates import Sum
import datetime, time
import pytz

from gntm.dates import *



class Command(BaseCommand):
    """

    """
    def handle(self, *args, **options):
        for d in gntmDates:
            date = d.astimezone(utcTz)
            print(d)
            print(date.astimezone(berlinTz))
        #UserList = [GntmUser.objects.get(user=6)]

        """
        for t in GntmTransaction.objects.all():
            mAktien = System.getModelAktienAtTime(t.time, t.model)
            value = System.getBuyValue(mAktien, t.aktien)
            if t.aktien < 0 and (not t.model.Aktiv):
                #print(str(t.model.KickDateTime) + " " + str(t.time) )
                if t.model.KickDateTime < t.time or \
                (t.time.date() == t.model.KickDateTime.date() and t.time > berlinTz.localize(t.time).replace(hour=21,minute=30)):
                    value = -startwert * t.aktien
                    print(t.user.user.first_name+" "+str(t.model)+": "+str(t.aktien))
            if t.aktien > 0: t.userMoney = value
            else: t.userMoney = -value
            t.modelAktienBefore = mAktien
            t.save()
        """

        GntmChallengeLog.objects.all().delete()

        for u in GntmUser.objects.filter(Spectator=False):
            for c in GntmChallenge.objects.all():
                if c.Time < gntmDates[4]:
                    stoptime = c.Time
                else:
                    stoptime = c.Time.astimezone(berlinTz).replace(hour=20, minute=15, second=0)
                aktSum = GntmTransaction.objects.filter(time__lte=stoptime.astimezone(utcTz), user=u, model=c.Model).aggregate(Sum('aktien'))
                mainOwner = System.getMainOwnerAtTime(stoptime.astimezone(utcTz), c.Model)
                c.MainOwner = mainOwner
                c.save()
                if aktSum["aktien__sum"] == None or aktSum["aktien__sum"] == 0:
                    challengeMoney = 0.0
                else:
                    if c.Company == True:
                        dividende = 2.0
                    else:
                        dividende = 0.1
                    if System.getModelAktivCountAtTime(c.Time) <= 10:
                        dividende = 2.0*dividende
                    if (mainOwner and u.id == mainOwner.id):
                        challengeMoney = 2 * dividende * aktSum["aktien__sum"]
                    else:
                        challengeMoney = dividende * aktSum["aktien__sum"]
                if challengeMoney != 0.0:
                    logEntry = GntmChallengeLog(Challenge=c, User=u, Aktien=aktSum["aktien__sum"], Money=challengeMoney)
                    logEntry.save()

        GntmChapterLog.objects.all().delete()

        for i in range(len(gntmDates)):
            d = gntmDates[i]
            endDate = d.replace(hour=22, minute=30)
            modelCount = System.getModelAktivCountAtTime(endDate.astimezone(utcTz))
            print(d.astimezone(utcTz))
            for u in GntmUser.objects.filter(Spectator=False):
                userAktien = System.getUserAktienAtTime(u, d.astimezone(utcTz))

                for modelItem in userAktien:
                    #more than 10 models left
                    #print(modelItem)
                    if modelItem['aktien'] != 0:
                        m = GntmModel.objects.get(id=modelItem['model'])
                        if m.KickDateTime > endDate:
                            if modelCount <= 10:
                                dividende = 4.0
                            else:
                                dividende = 2.0
                            ch = GntmChapterLog(WeekNumber=i+1, User=u, Model=m, Aktien=modelItem['aktien'], Money=modelItem['aktien']*dividende, Date=d.date())
                            ch.save()
