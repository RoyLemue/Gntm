from django.contrib import admin
from .models import *
from imagekit.admin import AdminThumbnail

class GntmModelAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'FirstName', 'LastName', 'admin_thumbnail')
    admin_thumbnail = AdminThumbnail(image_field='thumbnail')

class GntmUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'money', 'admin_thumbnail')
    admin_thumbnail = AdminThumbnail(image_field='thumbnail')

admin.site.register(GntmModel, GntmModelAdmin)
admin.site.register(GntmUser, GntmUserAdmin)