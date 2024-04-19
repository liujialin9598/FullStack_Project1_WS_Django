from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("default/", views.default, name="default"),
    path("result/", views.result, name="result"),
]