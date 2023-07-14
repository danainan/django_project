from django.db import models

# Create your models here.
class Users(models.Model):
    firstname = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=100)
    room_num = models.CharField(max_length=255)

class Rooms(models.Model):
    room_number = models.CharField(max_length=3)
    room_capacity = models.CharField(max_length=1)


