# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.http import JsonResponse
from mezzanine.pages.page_processors import processor_for
from mezzanine.accounts.models import *
from django.contrib.auth.models import User
from .models import *
from mez.settings import *
from django.contrib.auth.decorators import login_required, user_passes_test
import logging
logger = logging.getLogger('django')
import os
import gntm.templatetags.gntm_tags
import datetime

dividende = 2.0
dividendeT10 = 4.0

CURRENCY_STRING = '<span style="letter-spacing: -5px;">SM</span>'
utctz = pytz.timezone("UTC")

def getUser(request):
    groups = request.user.groups.all().values_list('name', flat=True)
    if not "gntm" in groups:
        return {}
    gntmUser = GntmUser.objects.get(user=request.user)

    if gntmUser.Admin == True:
        if request.method == 'POST':
            if 'lockButton' in request.POST:
                System.Locked = not System.Locked

            if 'nextRoundButton' in request.POST and System.Locked:
                for u in GntmUser.objects.all():
                    aktien =u.AktienAktiv
                    if GntmModel.objects.filter(Aktiv=True).count()<10:
                        d = dividendeT10
                    else:
                        d = dividende
                    u.Money += d*aktien
                    u.save()
    return gntmUser

def modelList(request):

    user = getUser(request)
    if user == None:
        return TemplateResponse(request, 'gntm/modellist.html', {})
    modelDataAktiv = []
    for m in GntmModel.objects.filter(Aktiv=True).order_by("FirstName"):
        modelDataAktiv.append(System.getDiagramModelData(user, m))

    modelDataInaktiv = []
    for m in GntmModel.objects.filter(Aktiv=False).order_by("FirstName"):
        modelDataInaktiv.append(System.getDiagramModelData(user, m))

    # json.dumps(modelData, sort_keys=True, indent=4, separators=(',', ': ')
    return TemplateResponse(request, 'gntm/modellist.html', {
            'modelsAktiv': modelDataAktiv,
            'modelsInaktiv': modelDataInaktiv,
            'debug': '',
            'user': user,
            'system': System,
            "currency": CURRENCY_STRING,
    })
@login_required
def modelDetail(request, modelId):
    user = getUser(request)
    if user == None:
        return TemplateResponse(request, 'gntm/modeldetail.html', {})

    model = GntmModel.objects.get(pk=int(modelId))

    prevModel = GntmModel.objects.filter(pk__lt=model.id).order_by("-FirstName")[:1]
    nextModel = GntmModel.objects.filter(pk__gt=model.id).order_by("FirstName")[:1]
    if not prevModel:
        prevModel = GntmModel.objects.all().order_by("-id")[0]
    else:
        prevModel = prevModel[0]
    if not nextModel:
        nextModel = GntmModel.objects.all().order_by("id")[0]
    else:
        nextModel = nextModel[0]

    data = System.getDiagramModelData(user, model)
    data["buyValue"] = "{:10.2f}".format(model.getBuyValue(10)['summe'])
    if data["userAktien"]>0:
        data["sellValue"] = "{:10.2f}".format(model.getBuyValue(-data["userAktien"])['summe'])
    else:
        data["sellValue"] = "0.00"
    logger.info(data)
    if request.method == 'POST':
        if 'kickSubmit' in request.POST:
            logger.info(request.POST)
            if user.Admin:
                logger.info(request.user.id)
                model.Aktiv = not model.Aktiv
                model.KickDateTime = utctz.localize(datetime.datetime.now())
                model.save()
        if 'challengeSubmit' in request.POST:
            logger.info(request.POST)
            if user.Admin:
                form = ChallengeForm(request.POST)
                if form.is_valid():
                    model = GntmModel.objects.get(id=form.model_data)
                    System.handleChallenge(model=model, name=form.challenge_data, company=form.company_data)
                    data.update({"change": {'success': True, 'message': 'Challenge eingereicht'}})
        if ('sellButton' in request.POST or 'buyButton' in request.POST) and not System.Locked:
            form = TransactionForm(request.POST)
            if (form.is_valid() and form.aktien_data > 0):

                if form.modelAktien_data == model.Aktien:

                    if ('sellButton' in request.POST):
                        aktien = -form.aktien_data
                        aktienValue = - model.getBuyValue(aktien)['summe']
                    else:
                        aktien = form.aktien_data
                        aktienValue = model.getBuyValue(aktien)['summe']

                    if user.Money >= aktienValue or aktien < 0:
                        if model.Aktiv == False and aktien > 0:
                            data["change"] = {'error': True, 'message': 'Model nicht aktiv'}
                        elif data["userAktien"] < form.aktien_data and aktien < 0:
                            data["change"] = {'error': True, 'message': 'Nicht genug Aktien'}
                        else:
                            user.Money -= aktienValue

                            t = GntmTransaction(model=model,
                                                user=user,
                                                aktien=aktien,
                                                modelAktienBefore=model.Aktien,
                                                value=model.Value,
                                                depotValue=user.Value,
                                                time=timezone.now(),
                                                userMoney=aktienValue)
                            t.save()
                            user.save()
                            data['transactions'].pop()
                            data['transactions'].append({
                                "time": t.Timestamp,
                                "val": System.getAktienValue(t.modelAktienBefore+t.aktien)
                            })
                            data["userAktien"] += aktien
                            if aktien > 0:
                                data.update({"change": {'success': True, 'message': 'Kauf erfolgreich'}})
                            else:
                                data.update({"change": {'success': True, 'message': 'Verkauf erfolgreich'}})
                    else:
                        data["change"] = {'error': True, 'message': 'Nicht genug Geld.'}
                else:
                    data["change"] = {'error': True, 'message': 'Aktienpreis hat sich geändert'}
            else:
                logger.info(form.errors)
                data["change"] = {'error': True, 'message': 'Eingabedaten sind nicht korrekt.'}
        elif System.Locked:
            data["change"] = {'error': True, 'message': 'Kaufen/Verkaufen ist gesperrt.'}

    data['prevModel'] = prevModel.id
    data['nextModel'] = nextModel.id
    if model.Aktiv:
        data['aktiv'] = model.Aktiv,

    return TemplateResponse(request, 'gntm/modeldetail.html',
            {'view': {'model': True},
            'model': data,
            'user':  user,
            'system': System,
            "currency": CURRENCY_STRING,
            })

def ajaxModel(request):
    form = AjaxForm(request.GET)
    if form.is_valid():
        model = GntmModel.objects.get(pk=int(form.model_data))
        return JsonResponse({'price': model.getBuyValue(form.aktien_data)})
    else:
        return JsonResponse({'error': "wrong Input"})

def ajaxPrice(request, aktien):
    return JsonResponse({'price': System.getAktienValue(int(aktien))})

def ajaxBuy(request, aktien, buy):
    sum = 0.0
    aktien = int(aktien)
    buy = int(buy)
    return JsonResponse({'Summe': System.getBuyValue(aktien, buy)})
def diffList(request):
    diffs = []
    for i in range(3000):
        val = (System.getBuyValue(i,1)-System.getBuyValue(i,-1))/System.getBuyValue(i,1)
        diffs.append([i, val])
    return JsonResponse({"values": diffs})

@login_required
def userList(request):
    user = getUser(request)
    if user == None:
        return TemplateResponse(request, 'gntm/userlist.html', {})
    users = []
    for u in GntmUser.objects.filter(Spectator=False):
        users.append(u)
    return TemplateResponse(request, 'gntm/userlist.html',
                            {"users" : users, 'user':  user, 'system': System,})
@login_required
def userDetail(request, userId):

    user = getUser(request)
    if user == None:
        return TemplateResponse(request, 'gntm/userdetail.html', {})
    detailUser = GntmUser.objects.get(user=int(userId))
    ownModels = []
    for model in GntmModel.objects.all():
        owner, aktien =model.MainOwnerIdAndAktien
        if owner == detailUser.id:
            ownModels.append(model)
    return TemplateResponse(request, 'gntm/userdetail.html',
                            {"detailUser" : detailUser,
                             "ownModels": ownModels,
                             'user':  user,
                             "currency": CURRENCY_STRING,
                             'system': System,})

def index(request):
    user = getUser(request)
    return TemplateResponse(request, 'gntm/gntm.html',{'user':  user, 'system': System,})

@login_required
def result(request):
    user = getUser(request)
    if user == None:
        return TemplateResponse(request, 'gntm/result.html', {})
    users = []
    usermatrix = []
    for u in GntmUser.objects.filter(Spectator=False):
        weeklist = []
        for d in gntmDates:
            weekaktien = System.getUserAktienAtTime(u, d)
            weekmodels = []
            for weekaktie in weekaktien:
                if weekaktie['aktien'] > 0:
                    model = GntmModel.objects.get(pk=weekaktie['model'])
                    owner = System.getMainOwnerAtTime(d, model)
                    weekmodels.append({'model' : model, 'aktien': weekaktie['aktien'], 'owner': owner==u})
            weeklist.append(weekmodels)
        usermatrix.append({'user':u, 'weeklist': weeklist})
        usermatrix = sorted(usermatrix, key=lambda row: -row['user'].Points)
    return TemplateResponse(request, 'gntm/result.html',
                            {"matrix" : usermatrix, 'user':  user, 'system': System, 'weeknumbers' : range(1,len(gntmDates)+1),} )