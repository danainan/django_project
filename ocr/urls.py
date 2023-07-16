from django.urls import path
from .views import *


urlpatterns = [
        path("", index, name='index'),
        path('livefe',livefe, name='livefe'),
        path('initialize_camera', initialize_camera, name='initialize_camera'),
        path('ocr', ocr, name='ocr'),
        path('upload_img', upload_img),
        path('search_name', search_name),



        


]