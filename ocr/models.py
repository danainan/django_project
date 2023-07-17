from django.db import models

# Create your models here.

class Document(models.Model):
    firstname = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    line_id = models.CharField(max_length=100)
    room_num = models.CharField(max_length=100)

 


