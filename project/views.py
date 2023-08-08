from django.shortcuts import render,redirect,get_object_or_404
from .models import Users
from django.contrib.auth.models import User 
from .models import Rooms
from django.contrib.auth import authenticate, login as auth_login 
from django.contrib.auth import logout as auth_logout
from django.http import HttpResponse ,HttpResponseBadRequest
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from ocr.models import Document
import pandas as pd
from pymongo import MongoClient
import openpyxl
import os
from PIL import Image, ImageDraw, ImageFont
import requests
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.font_manager import FontProperties
from matplotlib.table import Table
import datetime
from django.http import JsonResponse
from django.conf import settings



def save_img(request):
    # ส่วนที่ 1
    client = MongoClient('mongodb+srv://authachaizzz:1234@cluster0.xf2c6og.mongodb.net/?retryWrites=true&w=majority')
    db = client['finaldatabase']
    collection = db['ocr_document']

    # เลือกฟิลด์ที่ต้องการใช้งาน
    def select_columns():
        plt.rcParams['font.family'] = 'Angsana New'

        # เชื่อมต่อ MongoDB
        df = pd.DataFrame(list(collection.find()))
        selected_columns = ['firstname', 'last_name', 'room_num', 'status', 'date']
        df_selected = df[selected_columns]

        # เลือกแถวที่มีสถานะเป็น 'ยังไม่ได้รับ'
        df_selected = df_selected[df_selected['status'] == 'ยังไม่ได้รับ']

        # เปลี่ยนชื่อคอลัมน์
        df_selected.columns = ['ชื่อ', 'นามสกุล', 'ห้อง', 'สถานะ', 'วันที่']

        df_selected = df_selected.sort_values(by='ห้อง', ascending=True)

        df_selected = df_selected[['ห้อง' ,'ชื่อ', 'นามสกุล','วันที่' ,'สถานะ']]

        df_selected['วันที่'] = pd.to_datetime(df_selected['วันที่']).dt.date

        return df_selected

    # ส่วนที่ 2
    df_selected = select_columns()

    # ส่วนที่ 3
    dateToday = datetime.datetime.now().date()
    dateMaxData = select_columns()['วันที่'].max()
    df_selected_today = select_columns()
    df_selected_today = df_selected_today[df_selected_today['วันที่'] == dateToday]

    if not df_selected.empty:
        plt.title(f'รายชื่อพัสดุที่ยังไม่ได้รับวันที่ {dateToday}')
        plt.table(cellText=df_selected_today.values,
                colLabels=df_selected_today.columns,
                cellLoc='center', loc='center')
        plt.axis('off')
        plt.savefig('วันนี้.png', bbox_inches='tight', dpi=500)
        plt.close()

    df_selected_other = select_columns()
    df_selected_other = df_selected_other[df_selected_other['วันที่'] != dateToday]

    if not df_selected.empty:
        plt.title(f'รายชื่อพัสดุที่ยังไม่ได้รับวันอื่นๆ')
        plt.table(cellText=df_selected_other.values,
                colLabels=df_selected_other.columns,
                cellLoc='center', loc='center')
        plt.axis('off')
        plt.savefig('วันอื่นๆ.png', bbox_inches='tight', dpi=500)
        plt.close()

    line_notify_token = "CCDXvamsMK3Cgcnu3k2sW5MdWgdLUvGbR7YtqteeH7W"
    line_notify_api_url = "https://notify-api.line.me/api/notify"

    headers = {
        "Authorization": f"Bearer {line_notify_token}"
    }
    data = {
        "message": "รายการพัสดุที่ยังไม่ได้รับวันนี้",
    }
    files = {
        "imageFile": ("วันนี้.png", open("วันนี้.png", "rb"), "image/png")
    }
    response = requests.post(line_notify_api_url, headers=headers, data=data, files=files)

    if response.status_code == 200:
        print("ส่งรูปภาพสำเร็จ")
    else:
        print("เกิดข้อผิดพลาดในการส่งรูปภาพ")
        print(response.text)

    
    data = {
        "message": "รายการพัสดุที่ยังไม่ได้รับวันอื่นๆ",
    }
    files = {
        "imageFile": ("วันอื่นๆ.png", open("วันอื่นๆ.png", "rb"), "image/png")
    }
    response = requests.post(line_notify_api_url, headers=headers, data=data, files=files)
    # ตรวจสอบสถานะการส่ง
    if response.status_code == 200:
        print("ส่งรูปภาพวันอื่นๆสำเร็จ")
    else:
        print("เกิดข้อผิดพลาดในการส่งรูปภาพวันอื่นๆ")
        print(response.text)


    
    # คืนค่าเพื่อบอกว่าฟังก์ชันทำงานเสร็จสิ้น
    return redirect('summary')





@login_required(login_url='/login/')
def summary(request):
    documents = Document.objects.all()
    if request.method == 'GET' and 'search' in request.GET:
        search_query = request.GET.get('search')
        if not search_query:
            messages.warning(request, 'กรุณากรอกข้อมูลที่ถูกต้องเช่น ชื่อ-นามสกุล หรือ หมายเลขห้องพัก')
            documents = Document.objects.all().order_by('room_num')
        else:
            documents = Document.objects.filter(
                Q(firstname__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(room_num__icontains=search_query) 
            ).order_by('room_num')
    else:
        documents = Document.objects.all().order_by('room_num')

    received_documents = [doc for doc in documents if doc.status == 'รับแล้ว']

    documents = [doc for doc in documents if doc not in received_documents]

    if request.method == 'POST':
        for document in documents:
            status = request.POST.get(f"status_{document.pk}", None)
            if status in ['รับแล้ว', 'ยังไม่ได้รับ']:
                document.status = status
                document.save()

    return render(request, 'std/summary.html', {'documents': documents, 'received_documents': received_documents})


# ----------------------------------------------------------------------------------------


# client = MongoClient('mongodb+srv://authachaizzz:1234@cluster0.xf2c6og.mongodb.net/?retryWrites=true&w=majority')
# db = client['finaldatabase']
# collection = db['ocr_document']


# # เลือกฟิลด์ที่ต้องการใช้งาน
# def select_columns():
#     plt.rcParams['font.family'] = 'Angsana New'

#     # เชื่อมต่อ MongoDB
    
#     df = pd.DataFrame(list(collection.find()))
#     selected_columns = ['firstname', 'last_name', 'room_num', 'status', 'date']


#     df_selected = df[selected_columns]

#     # เลือกแถวที่มีสถานะเป็น 'ยังไม่ได้รับ'
#     df_selected = df_selected[df_selected['status'] == 'ยังไม่ได้รับ']

#     # เปลี่ยนชื่อคอลัมน์
#     df_selected.columns = ['ชื่อ', 'นามสกุล', 'ห้อง', 'สถานะ', 'วันที่']

#     # filter ห้องน้อยก่อน
#     df_selected = df_selected.sort_values(by='ห้อง', ascending=True)

#     #สลับคอลัมน์
#     df_selected = df_selected[['ห้อง' ,'ชื่อ', 'นามสกุล','วันที่' ,'สถานะ']]

#     # แปลงคอลัมน์ 'date' ให้เป็นประเภท date
#     df_selected['วันที่'] = pd.to_datetime(df_selected['วันที่']).dt.date
#     return df_selected

# dateToday = datetime.datetime.now().date()
# dateMaxData = select_columns()['วันที่'].max()


# df_selected = select_columns()
# df_selected = df_selected[df_selected['วันที่'] == dateToday]
# plt.title(f'รายชื่อพัสดุที่ยังไม่ได้รับวันที่ {dateToday}')
# plt.table(cellText=df_selected.values,
#         colLabels=df_selected.columns,
#         cellLoc='center', loc='center')
# plt.axis('off')
# plt.savefig('วันนี้.png', bbox_inches='tight', dpi=300)

# plt.close()
# df_selected = select_columns()
# df_selected = df_selected[df_selected['วันที่'] != dateToday]
# plt.title(f'รายชื่อพัสดุที่ยังไม่ได้รับวันอื่นๆ')
# plt.table(cellText=df_selected.values,
#         colLabels=df_selected.columns,
#         cellLoc='center', loc='center')
# plt.axis('off')
# plt.savefig('วันอื่นๆ.png', bbox_inches='tight', dpi=300)





# # ข้อมูลสำหรับเชื่อมต่อกับ Line Notify API
# line_notify_token = "CCDXvamsMK3Cgcnu3k2sW5MdWgdLUvGbR7YtqteeH7W"
# line_notify_api_url = "https://notify-api.line.me/api/notify"

# # ส่งรูปภาพ
# headers = {
#     "Authorization": f"Bearer {line_notify_token}"
# }
# data = {
#     "message": "ข้อความที่คุณต้องการส่ง",
# }
# files = {
#     "imageFile": ("output_image.png", open("output_image.png", "rb"), "image/png")
# }
# response = requests.post(line_notify_api_url, headers=headers, data=data, files=files)

# # ตรวจสอบสถานะการส่ง
# if response.status_code == 200:
#     print("ส่งรูปภาพสำเร็จ")
# else:
#     print("เกิดข้อผิดพลาดในการส่งรูปภาพ")
#     print(response.text)



# ------------------------------------------------------------------------------------





def index(request):
    return render(request, 'std/index.html')


def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('pass')  # แก้ชื่อตัวแปรจาก pass1 เป็น password
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)  # ใช้ชื่อฟังก์ชัน auth_login แทนที่ login
            return redirect("/project/home")
        else:
            return HttpResponse("Username or password is incorrect!!!")
        
    return render(request, 'std/login.html')



def logout(request):
    auth_logout(request)
    return redirect('login')


@login_required(login_url='/login/')
def home(request):
    rooms = Rooms.objects.all()  

    if request.method == 'GET' and 'search' in request.GET:
        search_query = request.GET.get('search')
        if not search_query:
            messages.warning(request, 'กรุณากรอกข้อมูลที่ถูกต้องเช่น ชื่อ-นามสกุล หรือ หมายเลขห้องพัก')
            users = Users.objects.all().order_by('room_num')
        else:
            users = Users.objects.filter(
                Q(firstname__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(room_num__icontains=search_query)
            ).order_by('room_num')
    else:
        users = Users.objects.all().order_by('room_num')

    return render(request, 'std/home.html', {'users': users, 'rooms': rooms})



@login_required(login_url='/login/')
def users_add(request):
    if request.method == 'POST':

        projects_firstname = request.POST.get("project_firstname")
        projects_last_name = request.POST.get("project_last_name")
        projects_line_id = request.POST.get("project_line_id")
        projects_room_num = request.POST.get("project_room_num")

        existing_user = Users.objects.filter(firstname=projects_firstname, last_name=projects_last_name).first()
        
        
        room = Rooms.objects.get(room_number=projects_room_num)
        current_occupancy = Users.objects.filter(room_num=projects_room_num).count()
        if current_occupancy >= int(room.room_capacity):
            room_full = True
        else:
            room_full = False

        if room_full:
            rooms = Rooms.objects.all()
            room_options = [(room.room_number, f"{room.room_number} (ห้องพักเต็มเเล้ว)") if current_occupancy >= int(room.room_capacity) else (room.room_number, room.room_number) for room in rooms]
            # return render(request, 'std/add_u.html', {'room_options': room_options, 'room_full': room_full})
            messages.warning(request, f'ห้องพักเต็มแล้ว')
            return redirect("/project/add-users")
        elif existing_user:
            messages.warning(request, f'ชื่อ {projects_firstname} {projects_last_name} มีอยู่ในระบบแล้ว')
            return redirect("/project/add-users")
        
        else:
            u = Users()
            u.firstname = projects_firstname
            u.last_name = projects_last_name
            u.line_id = projects_line_id  
            u.room_num = projects_room_num
            u.save()
            messages.success(request, f'เพิ่มข้อมูล {projects_firstname} {projects_last_name} เรียบร้อย')
            return redirect("/project/home")        
        

    rooms = Rooms.objects.all()
    # room_options = [(room.room_number, f"{room.room_number} (ห้องพักเต็มเเล้ว)") if Users.objects.filter(room_num=room.room_number).count() >= int(room.room_capacity) else (room.room_number, room.room_number) for room in rooms]

    room_options = []

    for room in rooms:
        current_occupancy = Users.objects.filter(room_num=room.room_number).count()
        room_status = f"{room.room_number} (ห้องพักเต็มแล้ว)" if current_occupancy >= int(room.room_capacity) else f"{room.room_number} ({current_occupancy}/{room.room_capacity} คน)"
        room_options.append((room.room_number, room_status))


    return render(request, 'std/add_u.html', {'room_options': room_options})


def users_delete(request,roll):
    u=Users.objects.get(pk=roll)
    u.delete()

    return redirect("/project/home")


def users_update(request, roll):
    project = Users.objects.get(pk=roll)
    rooms = Rooms.objects.all()
    room_data = []


    for room in rooms:
        current_occupancy = Users.objects.filter(room_num=room.room_number).exclude(pk=roll).count()
        room_status = f"{room.room_number} (ห้องพักเต็มแล้ว)" if current_occupancy >= int(room.room_capacity) else f"{room.room_number} ({current_occupancy}/{room.room_capacity} คน)"
        room_data.append((room.room_number, room_status))

    return render(request, 'std/update_u.html', {'project': project, 'room_data': room_data})


@login_required(login_url='/login/')
def do_users_update(request, roll):
    if request.method == 'POST':
        project_firstname = request.POST.get("project_firstname")
        project_last_name = request.POST.get("project_last_name")
        project_line_id = request.POST.get("project_line_id")
        project_room_num = request.POST.get("project_room_num")

        project = Users.objects.get(pk=roll)
        room = Rooms.objects.get(room_number=project_room_num)

        current_occupancy = Users.objects.filter(room_num=project_room_num).exclude(pk=roll).count()
        if current_occupancy >= int(room.room_capacity):
            rooms = Rooms.objects.all()
            room_data = []

            for r in rooms:
                occupancy = Users.objects.filter(room_num=r.room_number).exclude(pk=roll).count()
                room_status = f"{r.room_number} (ห้องพักเต็มแล้ว)" if occupancy >= int(r.room_capacity) else r.room_number
                room_data.append((r.room_number, room_status))

            return render(request, 'std/update_u.html', {'project': project, 'room_data': room_data, 'room_full': True})

        project.firstname = project_firstname
        project.last_name = project_last_name
        project.line_id = project_line_id
        project.room_num = project_room_num
        project.save()

        return redirect("/project/home")




@login_required(login_url='/login/')
def room_add(request):
    if request.method == 'POST':
        room_number = request.POST.get("room_number")
        room_capacity = request.POST.get("room_capacity")

        if Rooms.objects.filter(room_number=room_number).count() > 0:
            return render(request, 'std/add_room.html', {'error': 'ห้องพักนี้มีอยู่เเล้ว กรุณากรอกหมายเลขห้องพักอื่น'})
        else:
            r = Rooms()
            r.room_number = room_number
            r.room_capacity = room_capacity
            r.save()
            return redirect("/project/home")

    return render(request, 'std/add_room.html', {})



@login_required(login_url='/login/')
def rooms_list(request):
    rooms = Rooms.objects.all()
    return render(request, 'std/rooms_list.html', {'rooms': rooms})



def delete_room(request, room_id):
    room = get_object_or_404(Rooms, id=room_id)

    if request.method == 'POST':
        room.delete()
        return redirect('rooms_list')

    return render(request, 'std/delete_room.html', {'room': room})




