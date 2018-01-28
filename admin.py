from django.contrib import admin
from .models import *
from imagekit.admin import AdminThumbnail

class GntmModelAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'FirstName', 'LastName', "Aktiv", 'TeamString', 'admin_thumbnail')
    admin_thumbnail = AdminThumbnail(image_field='Thumbnail')

class GntmUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'Money', 'admin_thumbnail')
    admin_thumbnail = AdminThumbnail(image_field='Thumbnail')

class GntmChallengeAdmin(admin.ModelAdmin):
    list_display = ('Id', 'Model', 'Name', 'Company')

admin.site.register(GntmModel, GntmModelAdmin)
admin.site.register(GntmUser, GntmUserAdmin)
admin.site.register(GntmChallenge, GntmChallengeAdmin)
