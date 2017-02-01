from __future__ import unicode_literals

from django import forms
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.http import JsonResponse
from mezzanine.pages.page_processors import processor_for
from mezzanine.accounts.models import *
from .models import *
from mez.settings import *
from django.contrib.auth.decorators import login_required, user_passes_test
import logging
logger = logging.getLogger('django')
import os
import json
import templatetags.gntm_tags
import datetime
import calendar

def getUser(user):
    groups = user.groups.all().values_list('name', flat=True)
    if not "gntm" in groups:
        return {}
    gntmUser = GntmUser.objects.get(user=user)
    UserThumbWebPath = gntmUser.thumbnail.url
    UserThumbWebPath.replace(MEDIA_ROOT, MEDIA_URL)
    return {"obj": gntmUser,
            "data": {'name': user.first_name,
                    'aktien': gntmUser.getAktien(),
                    'thumb' : UserThumbWebPath,
                    'money': "{:10.2f}".format(gntmUser.money)}
            }
def modelList(request):
    user = getUser(request.user)

    models = GntmModel.objects.all().order_by("FirstName")
    modelData = []
    for model in models:
        ThumbWebPath = model.thumbnail.url
        ThumbWebPath.replace(MEDIA_ROOT, MEDIA_URL)
        mainowner = model.getMainOwner()
        if mainowner["user"] > 0:
            modelUser = GntmUser.objects.get(id=mainowner["user"])
            OwnerThumbWebPath = modelUser.thumbnail.url
            OwnerThumbWebPath.replace(MEDIA_ROOT, MEDIA_URL)
            owner = {'user': modelUser, 'thumb': OwnerThumbWebPath}
        else:
            owner = None

        modelData.append({
            "name": model.FirstName,
            "id": model.id,
            "thumbPath": ThumbWebPath,
            "aktien": model.getAktien(),
            "aktiv": int(model.aktiv),
            "wert": "{:10.2f}".format(model.getValue()),
            "owner": owner,
        })
    # json.dumps(modelData, sort_keys=True, indent=4, separators=(',', ': ')
    return TemplateResponse(request, 'gntm/modellist.html', {'view': {'list':True},
            'models': modelData,
            'debug': '',
            'user': user["data"]
    })

def modelDetail(request, modelId):
    user = getUser(request.user)
    userObj = user["obj"]
    model = GntmModel.objects.get(pk=int(modelId))

    prevModel = GntmModel.objects.filter(pk__lt=model.id).order_by("-id")[:1]
    nextModel = GntmModel.objects.filter(pk__gt=model.id).order_by("id")[:1]
    if not prevModel:
        prevModel = GntmModel.objects.all().order_by("-id")[0]
    else:
        prevModel = prevModel[0]
    if not nextModel:
        nextModel = GntmModel.objects.all().order_by("id")[0]
    else:
        nextModel = nextModel[0]

    transactions = []
    for t in GntmTransaction.objects.filter(model=model.id).order_by('-time'):
        timestamp = calendar.timegm(t.time.timetuple())
        transactions.append({'time': timestamp, 'aktien': t.aktien})

    data = {'name': model.FirstName,
            'id': model.id,
            'description': model.Description,
            'picture': model.Picture,
            'wert': "{:10.2f}".format(model.getValue()),
            'buyValue': "{:10.2f}".format(model.getBuyValue(10)['summe']),
            'userAktien': userObj.getAktienOfModel(model.id),
            }

    if request.method == 'POST':
        if 'kickSubmit' in request.POST:
            logger.info(request.POST)
            if request.user.id == 1:
                logger.info(request.user.id)
                model.aktiv = not model.aktiv
                model.save()
        if ('sellButton' in request.POST) or ('buyButton' in request.POST):
            form = TransactionForm(request.POST)
            if (form.is_valid()):
                logger.info("Valid")
                if ('sellButton' in request.POST):
                    aktien = -form.aktien_data
                    aktienValue = - model.getBuyValue(aktien)['summe']
                else:
                    aktien = form.aktien_data
                    aktienValue = model.getBuyValue(aktien)['summe']
                if userObj.money >= aktienValue or aktien < 0:
                    logger.info("Genug Geld oder Verkauf")
                    if model.aktiv == False and aktien > 0:
                        data["change"] = {'error': True, 'message': 'Model nicht aktiv'}
                    elif data["userAktien"] < form.aktien_data and aktien < 0:
                        data["change"] = {'error': True, 'message': 'Nicht genug Aktien'}
                    else:
                        userObj.money -= aktienValue
                        t = GntmTransaction(model=model,
                                            user=userObj,
                                            aktien=aktien,
                                            value=model.getValue(),
                                            depotValue=userObj.getValue())
                        t.save()
                        userObj.save()
                        timestamp = calendar.timegm(t.time.timetuple())
                        transactions.insert(0, {'time': timestamp, 'aktien': t.aktien})
                        data["userAktien"] += aktien
                        if aktien > 0:
                            data.update({"change": {'success': True, 'message': 'Kauf erfolgreich'}})
                        else:
                            data.update({"change": {'success': True, 'message': 'Verkauf erfolgreich'}})
                else:
                    data["change"] = {'error': True, 'message': 'Nicht genug Geld.'}
            else:
                logger.info(form.errors)
                data["change"] = {'error': True, 'message': 'Eingabedaten sind nicht korrekt.'}
    mainowner = model.getMainOwner()
    if mainowner["user"] > 0:
        ownerName = GntmUser.objects.get(id=mainowner["user"])
    else:
        ownerName = "Kein Haupteigner"

    if data['userAktien'] > 0:
        data['sell'] = {
            'aktiv': True,
            'value': "{:10.2f}".format(model.getBuyValue(-data['userAktien'])['summe'])
        }
    else:
        data['sell'] = {'aktiv': False}
    data['modelAktien'] = model.getAktien()
    data['mainowner'] = ownerName
    data['transactions'] = transactions
    data['prevModel'] = prevModel.id
    data['nextModel'] = nextModel.id
    if model.aktiv:
        data['aktiv'] = model.aktiv,

    return TemplateResponse(request, 'gntm/modeldetail.html',
            {'view': {'model': True},
            'model': data,
            'user':  user["data"]
            })

def ajaxPrice(request):
    form = AjaxForm(request.GET)
    if form.is_valid():
        return JsonResponse({'price': model.getBuyValue(form.aktien_data)})
    else:
        return JsonResponse({'error': "wrong Input"})

def userList(request):
    return TemplateResponse({})

def userDetail(request):
    return TemplateResponse({})