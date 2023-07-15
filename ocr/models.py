from django.db import models

# Create your models here.

class Tag(models.Model):
    tag = models.CharField(max_length=100)

 


