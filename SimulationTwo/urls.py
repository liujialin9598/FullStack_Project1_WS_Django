from django.urls import path

from . import views

urlpatterns = [
    path("", views.index),
    path("setdef/", views.setDefault),
    path("onesim/", views.OneSimresult),
    path("multisim/", views.MultiSimresult),
]
