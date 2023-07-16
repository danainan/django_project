from django.urls import path
from .views import *
from django.contrib import admin

urlpatterns = [
    path("", index),
    path("home/", home),
    path("add-users/", users_add),
    path("delete-users/<int:roll>", users_delete),
    path("update-users/<int:roll>", users_update),
    path("doupdate-users/<int:roll>", do_users_update),
    path("login/", login, name="login"), 
    path("logout/", logout),
    path("add-rooms/", room_add),
]


