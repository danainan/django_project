from django.urls import path
from .views import *

urlpatterns = [
        path("", index, name='index'),
        path('livefe',livefe, name='livefe'),
        path('reset_camera', reset_camera, name='reset_camera'),
        path('initialize_camera', initialize_camera, name='initialize_camera'),
        path('display_file_capture', display_file_capture, name='display_file_capture'),
        path('ocr', ocr, name='ocr'),


        


]