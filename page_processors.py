from __future__ import unicode_literals

from django import forms
from django.http import HttpResponseRedirect
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

@processor_for("gntm")
def gntmmodellist(request, page):
    groups = request.user.groups.all().values_list('name', flat=True)
    if not "gntm" in groups:
        return {}
    user = GntmUser.objects.get(user=request.user)
    UserThumbWebPath = user.thumbnail.url
    UserThumbWebPath.replace(MEDIA_ROOT, MEDIA_URL)

    if("model" in request.GET):

        model = GntmModel.objects.get(pk=request.GET["model"])
        prevModel = GntmModel.objects.filter(pk__lt=model.id).order_by("-id")[:1]
        nextModel = GntmModel.objects.filter(pk__gt=model.id).order_by("id")[:1]
        if not prevModel:
            prevModel = GntmModel.objects.all().order_by("-id")[0]
        else:
            prevModel = prevModel[0]
        if not nextModel:
            nextModel = GntmModel.objects.all().order_by("id")[0]
        else :
            nextModel = nextModel[0]

        if ("ajax" in request.GET):
            form = AjaxForm(request.GET)
            if form.is_valid():
                return JsonResponse({'price': model.getBuyValue(form.aktien_data)})
            else:
                return JsonResponse({'error': "wrong Input"})

        transactions = []
        for t in GntmTransaction.objects.filter(model=model.id).order_by('-time'):
            timestamp = calendar.timegm(t.time.timetuple())
            transactions.append({'time': timestamp, 'aktien': t.aktien})

        data = {'name':         model.FirstName,
               'id':            model.id,
               'description':   model.Description,
               'picture':       model.Picture,
                'wert':         "{:10.2f}".format(model.getValue()),
                'buyValue':     "{:10.2f}".format(model.getBuyValue(10)['summe']),
                'userAktien':   user.getAktienOfModel(model.id),
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
                if(form.is_valid()):
                    logger.info("Valid")
                    if( 'sellButton' in request.POST):
                        aktien = -form.aktien_data
                        aktienValue = - model.getBuyValue(aktien)['summe']
                    else:
                        aktien=form.aktien_data
                        aktienValue =   model.getBuyValue(aktien)['summe']
                    if user.money >= aktienValue or aktien < 0:
                        logger.info("Genug Geld oder Verkauf")
                        if model.aktiv == False and aktien > 0:
                            data["change"] = {'error': True, 'message': 'Model nicht aktiv'}
                        elif data["userAktien"] < form.aktien_data and aktien < 0:
                            data["change"] = {'error': True, 'message': 'Nicht genug Aktien'}
                        else:
                            user.money -= aktienValue
                            t = GntmTransaction(model=model,
                                                 user=user,
                                                 aktien=aktien,
                                                 value=model.getValue(),
                                                 depotValue=user.getValue())
                            t.save()
                            user.save()
                            timestamp = calendar.timegm(t.time.timetuple())
                            transactions.insert(0,{'time': timestamp, 'aktien': t.aktien})
                            data["userAktien"] += aktien
                            if aktien > 0:
                                data.update({"change":{'success':True, 'message': 'Kauf erfolgreich'}})
                            else:
                                data.update({"change":{'success':True, 'message': 'Verkauf erfolgreich'}})
                    else:
                        data["change"] = {'error': True, 'message': 'Nicht genug Geld.'}
                else:
                    logger.info(form.errors)
                    data["change"] ={'error':True, 'message': 'Eingabedaten sind nicht korrekt.'}
        mainowner = model.getMainOwner()
        if mainowner["user"] > 0:
            ownerName = GntmUser.objects.get(id=mainowner["user"])
        else:
            ownerName = "Kein Haupteigner"

        if data['userAktien'] >0:
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

        return {'view': {'model':True},
                'model': data,
                'user':{'name': user.user.first_name,
                        'aktien': user.getAktien(),
                        'thumb' : UserThumbWebPath,
                        'money': "{:10.2f}".format(user.money)}
                }
    else:
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
        return {'view': {'list':True},
                'models': modelData,
                'debug': '',
                'user':{'name': user.user.first_name,
                        'aktien': user.getAktien(),
                        'thumb' : UserThumbWebPath,
                        'money': "{:10.2f}".format(user.money)}
        }