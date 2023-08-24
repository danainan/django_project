from django.urls import path
from .views import *
from django.contrib import admin

urlpatterns = [
    path("", login),
    path("home/", home),
    path("add-users/", users_add),
    path("delete-users/<int:roll>", users_delete),
    path("update-users/<int:roll>", users_update),
    path("doupdate-users/<int:roll>", do_users_update),
    path("login/", login, name="login"), 
    path("logout/", logout),
    path("add-rooms/", room_add),
    path("rooms-list/", rooms_list, name="rooms_list"),
    path('update-room/<int:room_id>/', update_room, name='update_room'),
    path("delete-room/<int:room_id>", delete_room, name="delete_room"),
    path("summary/", summary, name='summary'),
    path("save-img/", save_img, name="save_img"),
    path("linelogin/", line_login, name="line_login"),
    path("save_status", save_status, name="save_status"),
    
]