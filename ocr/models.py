from django.db import models

# Create your models here.

class Person(models.Model):
    firstname = models.CharField(max_length=100)

 


