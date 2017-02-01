from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^models/$', views.modelList, name="Modellist"),
    url(r'^models/(?P<modelId>[0-9]+)/$', views.modelDetail, name="Modeldetails"),
    url(r'^users/$', views.userList, name="Userlist"),
    url(r'^users/(?P<userId>[0-9]+)/$', views.userDetail, name="UserDetails"),
]