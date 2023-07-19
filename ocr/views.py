
from django.shortcuts import render, redirect
from django.http import StreamingHttpResponse, HttpResponse, FileResponse
from django.views.decorators import gzip
import cv2
import threading   
import os
import time
from PIL import Image
from tesserocr import PyTessBaseAPI, RIL, PSM , OEM
from pythainlp.tokenize import word_tokenize
from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch
from pythainlp.tag import named_entity
from pythainlp import *
import requests
import numpy as np
import json
import base64
import keyboard
from django.conf import settings
from django.http import JsonResponse
from bs4 import BeautifulSoup
from .forms import ImageUploadForm
import numpy as np
from django.core.files.storage import FileSystemStorage
import re
from pythainlp.tag import NER, NNER
from pymongo import MongoClient
from django.conf import settings
from .models import *
from fuzzywuzzy import fuzz, process
import datetime
import json
from bson import ObjectId
from .models import *



def index(request, *args, **kwargs):

    image = 'https://baj.by/sites/default/files/event/preview/thumb-padrao-video.png'

    return render(request, 'index.html', {'image': image})
    


status = {"new_image_available": False}
class VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        # self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        # self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        # self.video.set(cv2.CAP_PROP_FPS, 30)
        self.grabbed, self.frame = self.video.read()
        threading.Thread(target=self.update, args=()).start()

    def __del__(self):
        self.video.release()
        cv2.destroyAllWindows()
        
        

    def release_camera(self):
        if self.video is not None:
            self.video.release()
            self.video = None
            self.frame = None
            cv2.destroyAllWindows()
            cv2.waitKey(1)

    def initialize_camera(self):
        self.release_camera()
        # cv2.CAP_DSHOW
        self.video = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    def get_frame(self):
        # image = self.frame
        # _, jpeg = cv2.imencode('.jpg', image)
        # return jpeg.tobytes()
        if self.video is not None:
            self.grabbed, self.frame = self.video.read()
        if self.frame is None:
            return None

        _, jpeg = cv2.imencode('.jpg', self.frame)
        return jpeg.tobytes()
    
    def update(self):
        while True:
            if self.video is None:
                time.sleep(1)  # Delay to wait for camera initialization
                continue
            (self.grabbed, self.frame) = self.video.read()

    def save_img(self):
        media_path = os.path.join(settings.MEDIA_ROOT , 'capture.jpg')
        # os.makedirs(os.path.dirname(media_path), exist_ok=True)
        with open(media_path, 'wb') as f:
            # f.write(self.frame)
            cv2.imwrite(media_path, self.frame)
            # # VideoCamera.__del__(self)
            # self.release_camera()
            
            cv2.waitKey(1)
            cv2.destroyAllWindows()
            status["new_image_available"] = True

    def send_image(self,request):
        media_path = os.path.join(settings.MEDIA_ROOT , 'capture.jpg')
        with open(media_path, 'rb') as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            self.release_camera()
            return render(request, 'index.html', {'encoded_image': encoded_image},{'captured-image': encoded_image})



        
                

def upload_img(request):
    media_path = os.path.join(settings.MEDIA_ROOT, 'capture.jpg')
   

    if request.method == 'POST':
        if os.path.exists(media_path):
            os.remove(media_path)
        upload_image = request.FILES.get('file_image')
    
    
        if upload_image:
            fs = FileSystemStorage()
            filename = fs.save("capture.jpg",upload_image)
            request.session['file_image'] = filename
            with open(media_path, 'rb') as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            return render(request, 'index.html', {'encoded_image': encoded_image})
            

        return render(request, 'index.html')
    
def reset_camera(request):
    if 'camera' in request.session:
        camera = request.session['camera']
        camera.release_camera()
        del request.session['camera']
    return redirect('index')

def gen(camera, request):
    if camera is None:
        camera = VideoCamera()

    while True: 
        frame = camera.get_frame()
        yield(b'--frame\r\n'
              b'Content-Type: image/png\r\n\r\n' + frame + b'\r\n\r\n')
        if  keyboard.is_pressed('q'):
            camera.save_img()
            camera.send_image(request)
            break
        

def capture(request):
    media_path = os.path.join(settings.MEDIA_ROOT , 'capture.jpg')
    if os.path.exists(media_path):
        with open(media_path, 'rb') as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            return render(request, 'index.html', {'encoded_image': encoded_image})
        
    else:
        return render(request, 'index.html')
    


def initialize_camera(request):
    if 'camera' in request.session:
        camera = request.session['camera']
        camera.initialize_camera()
    return HttpResponse(status=200)


    

@gzip.gzip_page
def livefe(request):
    try:
        cam = VideoCamera()
        return StreamingHttpResponse(gen(cam, request),content_type="multipart/x-mixed-replace;boundary=frame")
    except :
        pass




# def ocr(request):
#     media_path = os.path.join(settings.MEDIA_ROOT, 'capture.jpg')
#     ocr_path = os.path.join(settings.OCR_ROOT, 'tessdata_best-main')
#     if os.path.exists(media_path):
#         with PyTessBaseAPI(path=ocr_path,lang='tha+eng') as api:
#             api.SetImageFile(media_path)
#             text = api.GetUTF8Text()
#             conf = api.AllWordConfidences()
#             print(text)
#             name = os.path.join(settings.NER_ROOT, 'thainer-corpus-v2-base-model')
#             tokenizer = AutoTokenizer.from_pretrained(name)
#             model = AutoModelForTokenClassification.from_pretrained(name)

#             if len(text) > 512:
#                 text = text[:512]

    

#             sentence = f'{text}'
            
#             formatted_content = re.sub(r'\s+', ' ', text).strip()

#             print(formatted_content)
        
            

            

#             cut=word_tokenize(formatted_content.replace(" ", "<_>"))
#             inputs=tokenizer(cut,is_split_into_words=True,return_tensors="pt")

#             ids = inputs["input_ids"]
#             mask = inputs["attention_mask"]
#             # forward pass
#             outputs = model(ids, attention_mask=mask)
#             logits = outputs[0]

#             predictions = torch.argmax(logits, dim=2)
#             predicted_token_class = [model.config.id2label[t.item()] for t in predictions[0]]

#             def fix_span_error(words,ner):
#                 _ner = []
#                 _ner=ner
#                 _new_tag=[]
#                 for i,j in zip(words,_ner):
#                     #print(i,j)
#                     i=tokenizer.decode(i)
#                     if i.isspace() and j.startswith("B-"):
#                         j="O"
#                     if i=='' or i=='<s>' or i=='</s>':
#                         continue
#                     if i=="<_>":
#                         i=" "
#                     _new_tag.append((i,j))
#                 return _new_tag

#             ner_tag=fix_span_error(inputs['input_ids'][0],predicted_token_class)
#             print(ner_tag)

#             merged_ner=[]
#             for i in ner_tag:
#                 if i[1].startswith("B-"):
#                     merged_ner.append(i)
#                 elif i[1].startswith("I-"):
#                     merged_ner[-1]=(merged_ner[-1][0]+i[0],merged_ner[-1][1])
#                 else:
#                     merged_ner.append(i)

#             print(merged_ner)

#             #display only entity of person  name
#             person = []
#             _pharse = []
#             for i in merged_ner:
#                 if i[1].startswith("B-PERSON") and i[0] != ' ' and len(i[0]) > 5 :
#                     _pharse.append(i)
#                     person.append(i[0])

#             print(person)
#             print(_pharse)

#             if len(person) == 2:
#                 print('ผู้ส่ง :',person[0]),print('ผู้รับ :',person[1])
#                 return JsonResponse({'tag1': person[0], 'tag': person[1], 'text': formatted_content}, status=200)

#             elif len(person) > 2:
#                 # print('ผู้ส่ง :',person[0]),print('ผู้รับ :',person[1]+person[2])
#                 for i in range(2,len(person)):
#                     person[1] = person[1] + person[i]
#                 print('ผู้ส่ง :',person[0]),print('ผู้รับ :',person[1])
#                 return JsonResponse({'tag1': person[0], 'tag': person[1], 'text': formatted_content}, status=200)
#             else :
#                 return JsonResponse({'tag1': 'ไม่พบข้อมูล', 'tag': 'ไม่พบข้อมูล','tex' : formatted_content}, status=200)
            
            
#     return HttpResponse(status=200)

def ocr(request):
    media_path = os.path.join(settings.MEDIA_ROOT, 'capture.jpg')
    ocr_path = os.path.join(settings.OCR_ROOT, 'tessdata_best-main')
    if os.path.exists(media_path):
        with PyTessBaseAPI(path=ocr_path,lang='tha+eng',oem=OEM.LSTM_ONLY,psm=PSM.AUTO_OSD) as api:
            api.SetImageFile(media_path)
            text = api.GetUTF8Text()
            conf = api.AllWordConfidences()
            formatted_content = re.sub(r'\s+', ' ', text).strip()
            print(formatted_content)

            _engine = NER(engine="thainer-v2",corpus="thainer")
    
            # print(_engine.tag(formatted_content,tag=True))

            person = []

            ner_tag = _engine.tag(formatted_content)


            merged_ner=[]
            for i in ner_tag:
                if i[1].startswith("B-"):
                    merged_ner.append(i)
                elif i[1].startswith("I-"):
                    merged_ner[-1]=(merged_ner[-1][0]+i[0],merged_ner[-1][1])
                else:
                    merged_ner.append(i)

            # print(merged_ner)

            #display only entity of person  name
            person = []
            _pharse = []
            for i in merged_ner:
                if i[1].startswith("B-PERSON") and i[0] != ' ' and len(i[0]) > 5 :
                    _pharse.append(i)
                    person.append(i[0])

            print(person)
            print(_pharse)

            if len(person) == 0:
                return JsonResponse({'tag1': 'ไม่พบข้อมูล', 'tag': 'ไม่พบข้อมูล', 'text': formatted_content}, status=200)

            elif len(person) == 1:
                print('ผู้ส่ง :',person[0]),print('ผู้รับ :',person[0])
                return JsonResponse({'tag1': person[0], 'tag': person[0], 'text': _engine.tag(formatted_content,tag=True)}, status=200)

            elif len(person) == 2:
                print('ผู้ส่ง :',person[0]),print('ผู้รับ :',person[1])
                return JsonResponse({'tag1': person[0], 'tag': person[1], 'text': _engine.tag(formatted_content,tag=True)}, status=200)

            elif len(person) > 2:
                # print('ผู้ส่ง :',person[0]),print('ผู้รับ :',person[1]+person[2])
                for i in range(2,len(person)):
                    person[1] = person[1] + person[i]
                print('ผู้ส่ง :',person[0]),print('ผู้รับ :',person[1])
                return JsonResponse({'tag1': person[0], 'tag': person[1], 'text': _engine.tag(formatted_content,tag=True)}, status=200)
            else :
                return JsonResponse({'tag1': 'ไม่พบข้อมูล', 'tag': 'ไม่พบข้อมูล','tex' : _engine.tag(formatted_content,tag=True)}, status=200)
            
            



            #return JsonResponse({'text': _engine.tag(formatted_content,tag=True)}, status=200)


def search_name(request):
    if request.method == 'POST':
        # firstname = request.POST.get('tag')
        # client = MongoClient(settings.MONGODB_URI)
        # db = client[settings.MONGODB_NAME]

        # result = db['project_users'].find_one({'firstname': {'$regex': firstname}})
        # if result:
        #     return render(request, 'index.html', {'result': result})
        # else:
        #     return render(request, 'index.html', {'result': 'ไม่พบข้อมูล'})

        search_string = request.POST.get('tag')
        search_string_parts = search_string.split(' ')
        if len(search_string_parts) >= 2:
            search_string_firstname = search_string_parts[0]
            search_string_lastname = ' '.join(search_string_parts[1:])
        else:
            search_string_firstname = search_string
            search_string_lastname = ''

        print('fname=>',search_string_firstname)
        print('lname=>',search_string_lastname)






        client = MongoClient(settings.MONGODB_URI)
        db = client[settings.MONGODB_NAME]

        data_firstname = []
        data_lastname = []

        results = db['project_users'].find({})
        
        for document in results:
            data_firstname.append(document['firstname'])
            data_lastname.append(document['last_name'])

        matching_data_firstname = []
        confident = []
        confidence_threshold = 60
        for i in range(len(data_firstname)):
            confidence = fuzz.ratio(search_string_firstname, data_firstname[i])
            
            if confidence >= confidence_threshold:
                # matching_data_firstname.append(db['project_users'].find_one({'firstname': data_firstname[i]}))
                document = db['project_users'].find({'firstname': data_firstname[i]})
                print(document)
  
                for doc in document:
                    matching_data_firstname.append(doc)
                    #append confidence
                    matching_data_firstname[-1]['confidence'] = confidence
                    #remove duplicate
                    matching_data_firstname = list({v['_id']:v for v in matching_data_firstname}.values())
                    #sort with confidence
                    matching_data_firstname.sort(key=lambda x: fuzz.ratio(search_string_firstname, x['firstname']), reverse=True)
                    #matching_data_firstname.sort(key=lambda x: x['firstname'], reverse=True)
                   
                    
                    print(matching_data_firstname,'confidence=>',confidence)

        
        

        if len(matching_data_firstname) == 1:
            client = MongoClient(settings.MONGODB_URI)
            db = client[settings.MONGODB_NAME]
            result = db['project_users'].find_one({'firstname': matching_data_firstname[0]['firstname']})
            print(result)
            # media_path = os.path.join(settings.MEDIA_ROOT, 'capture.jpg')
            # with open(media_path, 'rb') as f:
            #     data = f.read()
            # encoded_string = base64.b64encode(data).decode('utf-8')

            return render(request, 'index.html', {'result_parcels': result,'document':matching_data_firstname,'conf':confidence,'result': matching_data_firstname[0]})
        
        elif len(matching_data_firstname) > 1:
            return render(request, 'index.html', {'result': matching_data_firstname,'document':matching_data_firstname,'conf':confidence})
        else:
            return render(request, 'index.html', {'result': 'ไม่พบข้อมูล','document':' ','conf':'ไม่พบข้อมูล'})
                
                 

        # if len(matching_data_firstname) > 0:
        #     return render(request, 'index.html', {'result': matching_data_firstname,'document':matching_data_firstname})
           
        # else:
        #     return render(request, 'index.html', {'result': 'ไม่พบข้อมูล'})


def get_document_id(request,roll):
    if request.method == 'POST':
        client = MongoClient(settings.MONGODB_URI)
        db = client[settings.MONGODB_NAME]

        result = db['project_users'].find_one({'id': int(roll)})

        getfirstname = result['firstname']
        getlastname = result['last_name']
        getroom = result['room_num']

        media_path = os.path.join(settings.MEDIA_ROOT, 'capture.jpg')
        with open(media_path, 'rb') as f:
            data = f.read()
        encoded_string = base64.b64encode(data).decode('utf-8')


        print(result)
        if result:
            return render(request, 'index.html', {'result_parcels': result,'encoded_string': encoded_string})

            
        else:
            return render(request, 'index.html', {'result': 'ไม่พบข้อมูล'})
        
    return render(request, 'index.html')


def save_document(request):
    if request.method == 'POST':
        firstname = request.POST.get('firstname')
        last_name = request.POST.get('last_name')
        room_num = request.POST.get('room_num')
        status = request.POST.get('status')
        date = request.POST.get('dateInput')

        client = MongoClient(settings.MONGODB_URI)
        db = client[settings.MONGODB_NAME]
        


        d = Document()
        d.firstname = firstname
        d.last_name = last_name
        d.room_num = room_num
        d.status = status
        d.date = date
        d.save()


        

        return render(request, 'index.html', {'result': 'บันทึกข้อมูลเรียบร้อยแล้ว'})

    return render(request, 'index.html')

            

    




    


    
