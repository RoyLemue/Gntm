# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from gntm.models import *
from datetime import *

class Command(BaseCommand):
    def handle(self, *args, **options):
        stoptime = datetime(2017,3,9, 21,00,0,1)
        company = True
        modelId = 22
        model = GntmModel.objects.get(id=modelId)
        mainOwner = model.MainOwner
        user = {}
        for u in GntmUser.objects.all():
            user[u.user.id] = 0
        print(str(stoptime))
        for t in GntmTransaction.objects.filter(time__gte=stoptime, model=model):
                print(str(t.time)+" "+str(t.aktien))
                user[t.user.user.id] -= t.aktien
        if company == True:
            dividende=challengeCompany
        else:
            dividende=challengeInternal

        for u in GntmUser.objects.all():
            if u == mainOwner:
                u.Money += 2 * dividende * user[u.user.id]
            else:
                u.Money += dividende * user[u.user.id]
            u.save()