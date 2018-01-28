from __future__ import unicode_literals

from django.db import models
from django.db.models.aggregates import Sum
from django.contrib.auth.models import User
from imagekit.models import ImageSpecField
from imagekit.processors import *
from django import forms
from mez.settings import *
from mezzanine.conf import settings
from mezzanine.conf.models import Setting
from mezzanine.core.urls import *
from django.utils import timezone
import calendar
from gntm.dates import *
import os
import logging
import six
logger = logging.getLogger('django')

CONFIG_FILE = os.path.join(PROJECT_ROOT, 'gntm/config.json')

import math

folgen = 13
startAktien = 100
dividende = 1.2 # 5 Aktien generieren eine Neue
startwert = 10.0
aktienScale = 2.0
umbruch = 1000.0
lowdividende = 2.0
highdividende = 4.0
challengeCompany = 2.0
challengeInternal= 0.1
topX = 10

class GntmModel: pass
class GntmUser: pass

class GntmSystem(object):
    def __init__(self):
        self.modelCount = GntmModel.objects.count()
        self.userCount = GntmUser.objects.filter(Spectator=False).count()
        self.aktienMean = self.userCount * startAktien * dividende ** folgen
        self.startTime = calendar.timegm(gntmDates[0].replace(hour=20, minute=15).timetuple()) * 1000

    @property
    def Locked(self):
        return settings.GNTM_LOCKED

    @Locked.setter
    def Locked(self, lock):
        setting_obj, created = Setting.objects.get_or_create(name='GNTM_LOCKED')
        setting_obj.value = lock
        setting_obj.save()
        settings.clear_cache()

    def handleChallenge(self, model, name, company):
        stoptime = berlinTz.localize(datetime.datetime.combine(datetime.date.today(), datetime.time(20,15,0)))

        userList = GntmTransaction.objects.filter(model=model, time__lt = stoptime) \
            .values('user') \
            .annotate(aktien=Sum('aktien')) \
            .order_by('user')
        mainOwner = None
        maxAktien = 0
        for userItem in userList:
            if maxAktien < userItem['aktien']:
                maxAktien= userItem["aktien"]
                mainOwner = userItem["user"]

        if mainOwner:
            mainOwner = GntmUser.objects.get(id=mainOwner)
        c = GntmChallenge(Model=model, Name=name, Company=company, MainOwner=mainOwner)
        c.save()

        if company == True:
            dividende=challengeCompany
        else:
            dividende=challengeInternal

        if GntmModel.objects.filter(Aktiv=True).count() < topX:
            dividende = dividende * 2

        for userItem in userList:
            u = GntmUser.objects.get(id=userItem["user"])
            if(mainOwner and userItem["user"] == mainOwner.id):
                value = 2 * dividende * userItem["aktien"]
                u.Money +=value
            else:
                value = dividende * userItem["aktien"]
                u.Money +=value
            clog = GntmChallengeLog(Challenge=c, User=u, Aktien=userItem["aktien"], Money=value)
            clog.save()
            u.save()

    def __modelValueFirst(self, x):
        return math.exp(x * self.modelCount / (aktienScale * self.aktienMean))

    def __modelValueSecond(self, x):
        return startwert - startwert * math.exp(-x * self.modelCount / (aktienScale * self.aktienMean))

    def getAktienValue(self, x):
        if x < umbruch:
            value = self.__modelValueFirst(x)
        else:
            value = (startwert - self.__modelValueFirst(umbruch)) / (startwert - self.__modelValueSecond(umbruch)) * (
                self.__modelValueSecond(x) - self.__modelValueSecond(umbruch)) + self.__modelValueFirst(umbruch)
        return startwert*value
    def getBuyValue(self, aktien, buy):
        sum = 0
        if buy > 0:
            for i in range(1, buy + 1):
                sum += System.getAktienValue(aktien + i)
        if buy < 0:
            for i in range(1, -buy + 1):
                sum += System.getAktienValue(aktien - i)
        return sum

    def getAktienFromValue(self, x):
        if x < self.getAktienValue(umbruch):
            return int(math.log(x/startwert)*aktienScale*self.aktienMean/self.modelCount)
        else:
            return 0

    def getUserMoney(self, user, datetime):
        money = 1200.0
        transactions = GntmTransaction.objects.filter(user=user, time__lt=datetime)
        if transactions == None:
            return money
        for t in transactions:
            modelAktien = self.getModelAktienAtTime(t.time, t.model)
            if(t.aktien<0):
                if(t.time > t.model.KickDateTime):
                    money+= startwert * t.aktien
                else:
                    money += self.getBuyValue(modelAktien, t.aktien)
            else:
                money -= self.getBuyValue(modelAktien, t.aktien)
        return money

    def getModelAktienAtTime(self, datTime, model):
        modelAktien = GntmTransaction.objects.filter(time__lt=datTime, model=model).aggregate(Sum('aktien'))["aktien__sum"]
        if modelAktien == None:
            return 0
        return modelAktien

    def getModelAktivCountAtTime(self, datTime):
        return GntmModel.objects.filter(KickDateTime__gt=datTime).count()


    def getMainOwnerAtTime(self, datTime, Model):
        userAktien = {}
        for u in GntmUser.objects.all():
            userAktien[u.id] = 0
        for t in GntmTransaction.objects.filter(time__lt=datTime, model=Model):
            userAktien[t.user.id] += t.aktien
        mainUser = 0
        aktien = 0
        for k, v in six.iteritems(userAktien):
            if v > aktien:
                mainUser = k
                aktien = v
            elif v == aktien:
                mainUser = 0
        if mainUser == 0:
            return None
        else:
            return GntmUser.objects.filter(pk=mainUser)[0]

    def getUserAktienAtTime(self, user, time):
        query = GntmTransaction.objects.filter(user=user, time__lt = time) \
            .values('model') \
            .annotate(aktien=Sum('aktien')) \
            .order_by('model')
        return query

    def getDiagramModelData(self, user, model):
        data = []

        #first value
        modelData = {
            "obj" : model,
            "transactions" : [{
                "time" : self.startTime,
                "val" : 10.0
            }],
            "userAktien" : user.getAktienOfModel(model.id)
        }
        for t in GntmTransaction.objects.filter(model=model).order_by('time'):
            modelData["transactions"].append({
                "time": t.Timestamp,
                "val": self.getAktienValue(t.modelAktienBefore+t.aktien)
            })
        #last value
        modelData["transactions"].append({
            "time": calendar.timegm(datetime.datetime.now(tz=berlinTz).timetuple()) * 1000,
            "val": model.Value
        })
        return modelData

    def getWinner(self):
            pass


class GntmTransaction (models.Model):
    model = models.ForeignKey('GntmModel')
    user = models.ForeignKey('GntmUser')
    time = models.DateTimeField(auto_created=True)
    aktien = models.IntegerField()
    modelAktienBefore = models.IntegerField(0)
    value = models.FloatField()
    depotValue = models.FloatField()
    userMoney = models.FloatField(default=0.0)

    @property
    def Timestamp(self):
        return calendar.timegm(self.time.timetuple()) * 1000


    @property
    def MoneyString(self):
        return "{:10.2f}".format(self.userMoney)
    @property
    def TimeString(self):
        return self.time.astimezone(berlinTz).strftime("%d.%m.%Y %H:%M:%S")

    def __str__(self):
        return self.user.user.first_name+" "+self.TimeString+" "+str(self.aktien)

class GntmModel(models.Model):
    id = models.AutoField(primary_key=True)
    FirstName = models.CharField(max_length=255)
    LastName = models.CharField(max_length=255)
    Description = models.TextField()
    Picture = models.ImageField(upload_to="gntm_modelimages", blank=True)
    Thumbnail = ImageSpecField(source='Picture',
                                      processors=[ResizeToFit(300, 300)],
                                      format='JPEG',
                                      options={'quality': 80})
    PictureBw = ImageSpecField(source='Picture',
                                      processors=[ResizeToFit(300, 300), Adjust(color=0.0)],
                                      format='JPEG',
                                      options={'quality': 80})
    ThumbnailBw = ImageSpecField(source='Picture',
                                      processors=[ResizeToFit(300, 300), Adjust(color=0.0)],
                                      format='JPEG',
                                      options={'quality': 80})

    FacePicture = models.ImageField(upload_to="gntm_modelimages_face", blank=True)
    FaceThumbnail = ImageSpecField(source='FacePicture',
                                      processors=[ResizeToFit(300, 300)],
                                      format='JPEG',
                                      options={'quality': 80})

    Transactions = models.ManyToManyField('GntmUser',
                                          through='GntmTransaction',
                                          through_fields=('model', 'user'),
                                          blank=True)
    Aktiv = models.BooleanField(default=True)
    TeamMichael = models.BooleanField(default=False)
    KickDateTime = models.DateTimeField(default=datetime.datetime(2017,6,1,0,0,0))

    @property
    def ThumbPath(self):
        WebPath = self.Thumbnail.url
        WebPath.replace(MEDIA_ROOT, MEDIA_URL)
        return WebPath
    @property
    def BWThumbPath(self):
        WebPath = self.ThumbnailBw.url
        WebPath.replace(MEDIA_ROOT, MEDIA_URL)
        return WebPath

    @property
    def Aktien(self):
        aktien = 0
        if self.Transactions.count() > 0:
            for transaction in GntmTransaction.objects.filter(model=self.id):
                aktien += transaction.aktien
        return aktien

    def __modelValueFirst(self, x, modelCount, userCount):
        aktienMean = userCount * startAktien * dividende ** folgen
        return math.exp(x * modelCount / (aktienScale * aktienMean))

    def __modelValueSecond(self, x, modelCount, userCount):
        aktienMean = userCount * startAktien * dividende ** folgen
        return startwert - startwert * math.exp(-x * modelCount / (aktienScale * aktienMean))

    def __modelValueFunction(self, x, modelCount, userCount):
        if self.Aktiv == False:
            return startwert
        if x < umbruch:
            value = self.__modelValueFirst(x, modelCount, userCount)
        else:
            value = (startwert - self.__modelValueFirst(umbruch, modelCount, userCount)) / (startwert - self.__modelValueSecond(umbruch, modelCount, userCount)) * (
                self.__modelValueSecond(x, modelCount, userCount) - self.__modelValueSecond(umbruch, modelCount, userCount)) + self.__modelValueFirst(umbruch, modelCount, userCount)
        return startwert*value

    @property
    def TeamString(self):
        if self.TeamMichael:
            return "Michael"
        else: return "Thomas"

    @property
    def Value(self):
        if not self.Aktiv:
            return startwert
        aktien = self.Aktien
        modelCount = GntmModel.objects.count()
        userCount = GntmUser.objects.filter(Spectator=False).count()
        return self.__modelValueFunction(aktien, modelCount, userCount)
    @property
    def ValueString(self):
        return "{:10.2f}".format(self.Value)

    def getBuyValue(self, aktien):
        sum = 0
        aktienCount = self.Aktien
        modelCount = GntmModel.objects.count()
        userCount = GntmUser.objects.filter(Spectator=False).count()
        l = System.Locked
        print(l)
        if l == True:
            return {"summe": startwert*abs(aktien), "mean": startwert, "endValue": startwert}
        if aktien > 0:
            for i in range(1,aktien+1):
                sum += self.__modelValueFunction(aktienCount+i, modelCount, userCount)
        if aktien < 0:
            for i in range(1,-aktien+1):
                sum += self.__modelValueFunction(aktienCount - i, modelCount, userCount)
        return {"summe":sum, "mean": sum/aktien, "endValue": self.__modelValueFunction(aktienCount+aktien, modelCount, userCount)}

    @property
    def MainOwnerIdAndAktien(self):
        userAktien = {}
        for u in GntmUser.objects.all():
            userAktien[u.id]= 0
        for t in GntmTransaction.objects.filter(model=self.id):
            userAktien[t.user.id] += t.aktien
        mainUser = 0
        aktien = 0
        for k, v in six.iteritems(userAktien):
            if v > aktien:
                mainUser = k
                aktien = v
            elif v == aktien:
                mainUser = 0
        return mainUser, aktien

    @property
    def MainOwner(self):
        userAktien = {}
        for u in GntmUser.objects.all():
            userAktien[u.id]= 0
        for t in GntmTransaction.objects.filter(model=self.id):
            userAktien[t.user.id] += t.aktien
        mainUser = 0
        aktien = 0
        for k, v in six.iteritems(userAktien):
            if v > aktien:
                mainUser = k
                aktien = v
            elif v == aktien:
                mainUser = 0
        if mainUser == 0:
            return None
        else:
            return GntmUser.objects.filter(pk=mainUser)[0]

    @property
    def Challenges(self):
        return GntmChallenge.objects.filter(Model=self.id)

    @property
    def Position(self):
        if self.Aktiv:
            if self.FirstName == 'Celine':
                return 1
            elif self.FirstName == 'Serlina':
                return 2
            elif self.FirstName == 'Romina':
                return 3
            else: return 4
        return GntmModel.objects.filter(KickDateTime__gt=self.KickDateTime).count()+1


    def __str__(self):
        return self.FirstName+" "+self.LastName

    def __unicode__(self):
        return self.FirstName + " " + self.LastName

class GntmUser(models.Model):
    user = models.OneToOneField(User)
    Picture = models.ImageField(upload_to="gntm_userimages", blank=True)
    Thumbnail = ImageSpecField(source='Picture',
                                      processors=[ResizeToFit(300, 300)],
                                      format='JPEG',
                                      options={'quality': 80})

    Transactions = models.ManyToManyField('GntmModel',
                                          through='GntmTransaction',
                                          through_fields=('user', 'model'),
                                          blank=True)
    Admin = models.BooleanField(default=False)
    Spectator = models.BooleanField(default=False)
    Money = models.FloatField()
    @property
    def MoneyString(self):
        return "{:10.2f}".format(self.Money)
    @property
    def ThumbPath(self):
        UserThumbWebPath = self.Thumbnail.url
        UserThumbWebPath.replace(MEDIA_ROOT, MEDIA_URL)
        return UserThumbWebPath
    @property
    def PicturePath(self):
        UserThumbWebPath = self.Picture.url
        UserThumbWebPath.replace(MEDIA_ROOT, MEDIA_URL)
        return UserThumbWebPath

    @property
    def Value(self):
        modelAktien = {}
        for model in GntmModel.objects.all():
            modelAktien[model.id]=0
        for t in GntmTransaction.objects.filter(user=self.id):
            modelAktien[t.model.id] += t.aktien
        depot=0
        for k,v in six.iteritems(modelAktien):
            depot += v*GntmModel.objects.get(pk=k).Value
        return depot
    @property
    def ValueString(self):
        return "{:10.2f}".format(self.Value)

    @property
    def Aktien(self):
        value = 0
        for t in GntmTransaction.objects.filter(user=self.id):
            value += t.aktien
        return value
    @property
    def AktienAktiv(self):
        value = 0
        for m in GntmModel.objects.filter(Aktiv=True):
            for t in GntmTransaction.objects.filter(user=self.id, model=m.id):
                value += t.aktien
        return value
    @property
    def AktienInaktiv(self):
        return self.Aktien - self.AktienAktiv
    @property
    def UserModels(self):
        models = []
        for model in GntmModel.objects.all():
            modelAktien = self.getAktienOfModel(model.id)
            if modelAktien > 0:
                models.append({"name": model.FirstName, "aktien": modelAktien, "id": model.id})
        return models

    @property
    def Transactions(self):
        return GntmTransaction.objects.filter(user=self).order_by('time')

    @property
    def Challenges(self):
        return GntmChallengeLog.objects.filter(User=self)

    def getWeekChallenges(self, weekNumber):
        gteTime = gntmDates[weekNumber].replace(hour=20,minute=15)
        lteTime = gntmDates[weekNumber].replace(hour=22,minute=30)
        return GntmChallengeLog.objects.filter(User=self, Challenge__Time__gte=gteTime, Challenge__Time__lte=lteTime)

    @property
    def Chapters(self):
        chapterList = GntmChapterLog.objects.filter(User=self) \
            .values("WeekNumber") \
            .annotate(Money=Sum("Money"))
        for c in chapterList:
            s = GntmChapterLog.objects.filter(User=self, WeekNumber=c["WeekNumber"])
            c["Detail"] = s
        return chapterList
    @property
    def CalcMoney(self):
        money = 1200.0
        for t in self.Transactions:
            money -= t.userMoney
        for c in self.Challenges:
            money += c.Money
        for ch in self.Chapters:
            money += ch["Money"]
        return money

    @property
    def Points(self):
        userAktien = System.getUserAktienAtTime(self, gntmDates[len(gntmDates)-1])
        points = 0
        for modelaktien in userAktien:
            if modelaktien['aktien'] > 0:
                model = GntmModel.objects.get(pk=modelaktien['model'])
                pos = model.Position

                if pos == 1: wert = 10
                elif pos == 2: wert = 6
                elif pos == 3: wert = 4
                elif pos <= 10:wert = 2
                else: wert = 1
                points += modelaktien['aktien']*wert
        return points

    def getAktienOfModel(self, modelId):
        aktien = GntmTransaction.objects.filter(user=self.id, model=modelId).aggregate(Sum('aktien'))["aktien__sum"]
        if aktien == None:
            return 0
        else:
            return aktien

    def __str__(self):
        return self.user.first_name

    def __unicode__(self):
        return self.user.first_name

class GntmChallenge(models.Model):
    Id = models.AutoField(primary_key=True)
    Model = models.ForeignKey('GntmModel')
    Name = models.CharField(max_length=255)
    Company = models.BooleanField(default=False)
    Time = models.DateTimeField(default=timezone.now)
    MainOwner = models.ForeignKey('GntmUser', blank=True, null=True)

    @property
    def CompanyString(self):
        if self.Company:
            return "Ja"
        else:
            return "Nein"
    @property
    def TimeString(self):
        return self.Time.astimezone(berlinTz).strftime("%d.%m.%Y %H:%M:%S")


class GntmChallengeLog(models.Model):
    Id = models.AutoField(primary_key=True)
    Challenge = models.ForeignKey('GntmChallenge')
    User = models.ForeignKey('GntmUser')
    Aktien = models.IntegerField()
    Money = models.FloatField()
    @property
    def MoneyString(self):
        return "{:10.2f}".format(self.Money)

class GntmChapterLog(models.Model):
    Id = models.AutoField(primary_key=True)
    WeekNumber = models.IntegerField()
    User = models.ForeignKey('GntmUser')
    Model = models.ForeignKey('GntmModel')
    Aktien = models.IntegerField()
    Money = models.FloatField()
    Date = models.DateField()
    @property
    def MoneyString(self):
        return "{:10.2f}".format(self.Money)
    @property
    def DateString(self):
        return self.Date.strftime("%d.%m.%Y")

class TransactionForm(forms.Form):
    model = forms.IntegerField(min_value=0)
    modelAktien = forms.IntegerField(min_value=0)
    aktien = forms.IntegerField()

    def clean(self):
        cleaned_data = super(TransactionForm, self).clean()
        self.model_data = cleaned_data.get("model")
        self.modelAktien_data = cleaned_data.get("modelAktien")
        self.aktien_data = cleaned_data.get("aktien")

class AjaxForm(forms.Form):
    model = forms.IntegerField(min_value=0)
    aktien = forms.IntegerField()

    def clean(self):
        cleaned_data = super(AjaxForm, self).clean()
        self.model_data = cleaned_data.get("model")
        self.aktien_data = cleaned_data.get("aktien")

class LockForm(forms.Form):
    lock = forms.BooleanField
    def clean(self):
        cleaned_data = super(LockForm, self).clean()
        self.lock_data = cleaned_data.get("lock")

class ChallengeForm(forms.Form):
    model = forms.IntegerField(min_value=0)
    challengeName = forms.CharField()
    company = forms.BooleanField(initial = False, required = False)


    def clean(self):
        cleaned_data = super(ChallengeForm, self).clean()
        self.model_data = cleaned_data.get("model")
        self.challenge_data = cleaned_data.get("challengeName")
        self.company_data = cleaned_data.get("company")


System = GntmSystem()