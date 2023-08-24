from django.db import models

# Create your models here.
class Users(models.Model):
    firstname = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    line_id = models.CharField(max_length=50)
    room_num = models.CharField(max_length=255)

class Rooms(models.Model):
    room_number = models.CharField(max_length=3, unique=True)
    room_capacity = models.CharField(max_length=1)

class Token(models.Model):
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)