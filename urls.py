from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index, name="Modellist"),
    url(r'^ajax/$', views.ajaxModel, name="AjaxRequests"),
    url(r'^ajax/price/(?P<aktien>[0-9]+)/$', views.ajaxPrice, name="AjaxPreis"),
    url(r'^ajax/buy/(?P<aktien>[0-9]+)/(?P<buy>-?[0-9]+)/$', views.ajaxBuy, name="AjaxBuy"),
    url(r'^ajax/diffList/$', views.diffList, name="AjaxDiffList"),
    url(r'^models/$', views.modelList, name="Modellist"),
    url(r'^models/(?P<modelId>[0-9]+)/$', views.modelDetail, name="Modeldetails"),
    url(r'^users/$', views.userList, name="Userlist"),
    url(r'^users/(?P<userId>[0-9]+)/$', views.userDetail, name="UserDetails"),
    url(r'^result/$', views.result, name="GntmResult"),
]