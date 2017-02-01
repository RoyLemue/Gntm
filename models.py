from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from imagekit.models import ImageSpecField
from imagekit.processors import *
from django import forms

import math

folgen = 13
startAktien = 100
dividende = 1.2 # 5 Aktien generieren eine Neue
startwert = 10.0
aktienScale = 2.0
umbruch = 1400.0

class GntmTransaction (models.Model):
    model = models.ForeignKey('GntmModel')
    user = models.ForeignKey('GntmUser')
    time = models.DateTimeField(auto_now=True)
    aktien = models.IntegerField()
    value = models.FloatField()
    depotValue = models.FloatField()

class GntmModel(models.Model):
    id = models.AutoField(primary_key=True)
    FirstName = models.CharField(max_length=255)
    LastName = models.CharField(max_length=255)
    Description = models.TextField()
    Picture = models.ImageField(upload_to="gntm_modelimages")
    thumbnail = ImageSpecField(source='Picture',
                                      processors=[ResizeToFit(300, 300)],
                                      format='JPEG',
                                      options={'quality': 80})
    transactions = models.ManyToManyField('GntmUser',
                                          through='GntmTransaction',
                                          through_fields=('model', 'user'),
                                          blank=True)
    aktiv = models.BooleanField(default=True)
    def getAktien(self):
        aktien = 0
        if self.transactions.count() > 0:
            for transaction in GntmTransaction.objects.filter(model=self.id):
                aktien += transaction.aktien
        return aktien

    def modelValueFirst(self, x, modelCount, userCount):
        aktienMean = userCount * startAktien * dividende ** folgen
        return math.exp(x * modelCount / (aktienScale * aktienMean))

    def modelValueSecond(self, x, modelCount, userCount):
        aktienMean = userCount * startAktien * dividende ** folgen
        return startwert - startwert * math.exp(-x * modelCount / (aktienScale * aktienMean))

    def modelValueFunction(self, x, modelCount, userCount):
        if self.aktiv == False:
            return startwert
        if x < umbruch:
            value = self.modelValueFirst(x, modelCount, userCount)
        else:
            value = (startwert - self.modelValueFirst(umbruch, modelCount, userCount)) / (startwert - self.modelValueSecond(umbruch, modelCount, userCount)) * (
                self.modelValueSecond(x, modelCount, userCount) - self.modelValueSecond(umbruch, modelCount, userCount)) + self.modelValueFirst(umbruch, modelCount, userCount)
        return startwert*value

    def getValue(self):
        if not self.aktiv:
            return startwert
        aktien = self.getAktien()
        modelCount = GntmModel.objects.count()
        userCount = GntmUser.objects.count()
        return self.modelValueFunction(aktien, modelCount, userCount)

    def getBuyValue(self, aktien):
        sum = 0
        aktienCount = self.getAktien()
        modelCount = GntmModel.objects.count()
        userCount = GntmUser.objects.count()
        if aktien > 0:
            for i in range(1,aktien+1):
                sum += self.modelValueFunction(aktienCount+i, modelCount, userCount)
        if aktien < 0:
            for i in range(1,-aktien+1):
                sum += self.modelValueFunction(aktienCount - i, modelCount, userCount)
        return {"summe":sum, "mean": sum/aktien, "endValue": self.modelValueFunction(aktienCount+aktien, modelCount, userCount)}

    def getMainOwner(self):
        userAktien = {}
        for u in GntmUser.objects.all():
            userAktien[u.id]= 0
        for t in GntmTransaction.objects.filter(model=self.id):
            userAktien[t.user.id] += t.aktien
        mainUser = 0
        aktien = 0
        for k, v in userAktien.iteritems():
            if v > aktien:
                mainUser = k
                aktien = v
            elif v == aktien:
                mainUser = 0
        return {'user': mainUser, 'aktien': aktien}

    def __str__(self):
        return self.FirstName.encode("utf-8")+" "+self.LastName.encode("utf-8")

    def __unicode__(self):
        return self.FirstName + " " + self.LastName

class GntmUser(models.Model):
    user = models.OneToOneField(User)
    Picture = models.ImageField(upload_to="gntm_userimages")
    thumbnail = ImageSpecField(source='Picture',
                                      processors=[ResizeToFit(300, 300)],
                                      format='JPEG',
                                      options={'quality': 80})

    transactions = models.ManyToManyField('GntmModel',
                                          through='GntmTransaction',
                                          through_fields=('user', 'model'),
                                          blank=True)
    money = models.FloatField()

    def getValue(self):
        modelAktien = {}
        for model in GntmModel.objects.all():
            modelAktien[model.id]=0
        for t in GntmTransaction.objects.filter(user=self.id):
            modelAktien[t.model.id] += t.aktien
        depot=0
        for k,v in modelAktien.iteritems():
            depot += v*GntmModel.objects.get(pk=k).getValue()
        return depot
    def getAktienOfModel(self, modelId):
        value = 0
        for t in GntmTransaction.objects.filter(model=modelId, user=self.id):
            value += t.aktien
        return value
    def getAktien(self):
        value = 0
        for t in GntmTransaction.objects.filter(user=self.id):
            value += t.aktien
        return value
    def getAktienAktiv(self):
        value = 0
        for m in GntmModel.objects.filter(aktiv=True):
            for t in GntmTransaction.objects.filter(user=self.id, model=m.id):
                value += t.aktien
        return value
    def __str__(self):
        return self.user.first_name.encode("utf-8")

    def __unicode__(self):
        return self.user.first_name

class TransactionForm(forms.Form):
    model = forms.IntegerField(min_value=0)
    modelAktien = forms.IntegerField(min_value=0)
    aktien = forms.IntegerField()

    def clean(self):
        cleaned_data = super(TransactionForm, self).clean()
        self.model_data = cleaned_data.get("model")
        self.sum_data = cleaned_data.get("sum")
        self.aktien_data = cleaned_data.get("aktien")

class AjaxForm(forms.Form):
    model = forms.IntegerField(min_value=0)
    aktien = forms.IntegerField()

    def clean(self):
        cleaned_data = super(AjaxForm, self).clean()
        self.model_data = cleaned_data.get("model")
        self.aktien_data = cleaned_data.get("aktien")