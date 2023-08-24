from django.db import models

class Document(models.Model):
    firstname = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    room_num = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    date = models.DateTimeField()
    
    # image_file = models.FileField(upload_to=media_path)

 


