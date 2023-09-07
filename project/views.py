from django.shortcuts import render,redirect,get_object_or_404
from .models import Users,Rooms,Token
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
import os
from PIL import Image, ImageDraw, ImageFont
import requests
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.font_manager import FontProperties
from matplotlib.table import Table
import datetime
from django.http import JsonResponse
from django.conf import settings
from urllib.parse import unquote
from operator import attrgetter
from django.db import DatabaseError





def line_login(request):
    client_id = "Ya8jHK3niGm0PXaTNCl7N1"
    callback_url = "http://127.0.0.1:8000/project/summary/"
    client_secret = "5SNI3j70vtuaiYq35ClPsYwcQSXjkrRpqR0IbJvSlYz"
    
    line_login_url = f"https://notify-bot.line.me/oauth/authorize?response_type=code&client_id={client_id}&redirect_uri={callback_url}&scope=notify&state={client_secret}"
    
    return redirect(line_login_url)
    
def exchange_code_for_access_token(code):
    token_url = "https://notify-bot.line.me/oauth/token"

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "http://127.0.0.1:8000/project/summary/",
        "client_id": "Ya8jHK3niGm0PXaTNCl7N1",
        "client_secret": "5SNI3j70vtuaiYq35ClPsYwcQSXjkrRpqR0IbJvSlYz"
    }

    response = requests.post(token_url, data=payload)
    
    if response.status_code == 200:
        access_token = response.json().get('access_token')
        Token.objects.create(token=access_token, created_at=datetime.datetime.now())
        
        
        
        return access_token
    else:
        return None

def select_columns(collection):
    plt.rcParams['font.family'] = 'Angsana New'
    df = pd.DataFrame(list(collection.find()))
    selected_columns = ['firstname', 'last_name', 'room_num', 'status', 'date']
    df_selected = df[selected_columns]
    # เลือกแถวที่มีสถานะเป็น 'ยังไม่ได้รับ'
    df_selected = df_selected[df_selected['status'] == 'ยังไม่ได้รับ']
    # เปลี่ยนชื่อคอลัมน์
    df_selected.columns = ['ชื่อ', 'นามสกุล', 'ห้อง', 'สถานะ', 'วันที่']
    df_selected = df_selected.sort_values(by='ห้อง', ascending=True)
    df_selected = df_selected.groupby(['ห้อง', 'ชื่อ', 'นามสกุล', 'วันที่', 'สถานะ']).size().reset_index(name='จำนวนพัสดุ(ชิ้น)')
    df_selected['วันที่'] = pd.to_datetime(df_selected['วันที่']).dt.date
    
    return df_selected

def create_and_save_table_plot(df, title, filename):
    path = os.path.join(settings.MEDIA_PROJECT)
    if os.path.exists(path + '/' + filename):
        os.remove(path + '/' + filename)
        matplotlib.use('Agg')
        plt.title(title)
        table = plt.table(
            cellText=df.values,
            colLabels=df.columns,
            cellLoc='center',
            loc='center'
        )
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.5, 1.5)  
        plt.axis('off')
        plt.savefig(path + '/' + filename, bbox_inches='tight', dpi=500)
        plt.close()

    else:
        matplotlib.use('Agg')
        plt.title(title)
        table = plt.table(
            cellText=df.values,
            colLabels=df.columns,
            cellLoc='center',
            loc='center'
        )
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.5, 1.5)  
        plt.axis('off')
        plt.savefig(path + '/' + filename, bbox_inches='tight', dpi=500)
        plt.close()



def save_img(request):
    client = MongoClient('mongodb+srv://authachaizzz:1234@cluster0.xf2c6og.mongodb.net/?retryWrites=true&w=majority')
    db = client['finaldatabase']
    collection = db['ocr_document']


    dateToday = datetime.datetime.now().date()
    all_data = select_columns(collection)

    df_selected_today = all_data[all_data['วันที่'] == dateToday]
    df_selected_today = df_selected_today.groupby(['ห้อง', 'ชื่อ', 'นามสกุล']).agg({'จำนวนพัสดุ(ชิ้น)': 'sum'}).reset_index()
    df_selected_other = all_data[all_data['วันที่'] != dateToday]
    df_selected_other = df_selected_other.groupby(['ห้อง', 'ชื่อ', 'นามสกุล']).agg({'จำนวนพัสดุ(ชิ้น)': 'sum'}).reset_index()


    today_title = f'รายการพัสดุที่ยังไม่ได้รับวันนี้'+str(dateToday)
    other_title = f'รายการพัสดุที่ยังค้างรับ'

    
    
    token = Token.objects.all()
    if not token:
        return redirect('line_login')
    else:
        if not df_selected_today.empty:
            create_and_save_table_plot(df_selected_today, today_title, 'วันนี้.png')
            line_notify(today_title,dateToday)
        else:
            line_notify('ไม่มีพัสดุสำหรับวันนี้',dateToday)

        if not df_selected_other.empty:
            create_and_save_table_plot(df_selected_other, other_title, 'วันอื่นๆ.png')
            line_notify(other_title,dateToday)
        else:
            line_notify('ไม่มีพัสดุค้างรับ',dateToday)


    # line_notify_token = "CCDXvamsMK3Cgcnu3k2sW5MdWgdLUvGbR7YtqteeH7W"

    
    client.close()

    #remove all file
    path = os.path.join(settings.MEDIA_PROJECT)
    for file in os.listdir(path):
        os.remove(os.path.join(path, file))


    messages.success(request, f'ส่งการเเจ้งเตือนเเล้ว')
    return redirect('summary')

def line_notify(messeageLine, dateToday):
   
    
    tokens = Token.objects.all()


    token = max(tokens, key=attrgetter('created_at'))

    
    line_notify_token = token.token
    print('Lasted Token line notify ====>>>>>> ',line_notify_token)
    line_notify_api_url = "https://notify-api.line.me/api/notify"
    headers = {
         "Authorization": f"Bearer {line_notify_token}"
    }
    
    path = os.path.join(settings.MEDIA_PROJECT)
    image_files = {
        f'รายการพัสดุที่ยังไม่ได้รับวันนี้{dateToday}': 'วันนี้.png',
        'รายการพัสดุที่ยังค้างรับ': 'วันอื่นๆ.png'
    }
    
    if messeageLine in image_files:
        image_file_name = image_files[messeageLine]
        image_path = os.path.join(path, image_file_name)
        if os.path.exists(image_path):
            files = {'imageFile': open(image_path, "rb")}
            data = {'message': f'{messeageLine}'}
            requests.post(line_notify_api_url, headers=headers, data=data, files=files)
    
    elif messeageLine == 'ไม่มีพัสดุสำหรับวันนี้':
        data = {'message': f'{messeageLine} {dateToday}'}
        requests.post(line_notify_api_url, headers=headers, data=data)
    
    elif messeageLine == 'ไม่มีพัสดุค้างรับ':
        data = {'message': f'{messeageLine}'}
        requests.post(line_notify_api_url, headers=headers, data=data)

    

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
            ).order_by('room_num','-date')

    else:
        documents = Document.objects.all().order_by('room_num','-date')
        
    
    received_documents = [doc for doc in documents if doc.status == 'รับแล้ว']

    documents = [doc for doc in documents if doc not in received_documents]

    
    code = request.GET.get('code')
    if code:
        access_token = exchange_code_for_access_token(code)

        print(access_token)

    sort_order = request.GET.get('sort')
    if sort_order == 'asc':
        documents = sorted(documents, key=lambda doc: doc.date)
    elif sort_order == 'desc':
        documents = sorted(documents, key=lambda doc: doc.date, reverse=True)
    
    new_sort_order = 'asc' if sort_order == 'desc' else 'desc'

    sort_room_order = request.GET.get('sort_room')
    if sort_room_order == 'asc':
        documents = sorted(documents, key=lambda doc: doc.room_num)
        new_sort_room_order = 'desc'
    elif sort_room_order == 'desc':
        documents = sorted(documents, key=lambda doc: doc.room_num, reverse=True)
        new_sort_room_order = 'asc'

    new_sort_room_order = 'asc' if sort_room_order == 'desc' else 'desc'

    sort_name_order = request.GET.get('sort_name')
    new_sort_name_order = 'asc'
    if sort_name_order == 'asc':
        documents = sorted(documents, key=lambda doc: doc.firstname)
        new_sort_name_order = 'desc'
    elif sort_name_order == 'desc':
        documents = sorted(documents, key=lambda doc: doc.firstname, reverse=True)
        new_sort_name_order = 'asc'

    new_sort_name_order = 'asc' if sort_name_order == 'desc' else 'desc'

    
    return render(request, 'std/summary.html', {'documents': documents, 'received_documents': received_documents, 'sort_order': new_sort_order, 'sort_room_order': new_sort_room_order, 'sort_name_order': new_sort_name_order})


def save_status(request):
    if request.method == 'POST':
    
        remaining_documents = Document.objects.exclude(status='รับแล้ว')

        for document in remaining_documents:
            status = request.POST.get(f"status_{document.pk}")
            if status:
                document.status = status
                document.save()
        return redirect('summary')

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

        if not projects_firstname or not projects_last_name or not projects_line_id or not projects_room_num:
            messages.warning(request, 'กรุณากรอกข้อมูลให้ครบถ้วน')
            return redirect("/project/add-users")

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
        room_status = f"{room.room_number} ({current_occupancy}/{room.room_capacity} คน) (ห้องเต็ม)" if current_occupancy >= int(room.room_capacity) else f"{room.room_number} ({current_occupancy}/{room.room_capacity} คน)"
        room_options.append((room.room_number, room_status))

    #sort room_options by room number
    room_options.sort(key=lambda x: x[0])

    return render(request, 'std/add_u.html', {'room_options': room_options})

def users_delete(request,roll):
    u=Users.objects.get(pk=roll)
    fname = u.firstname
    lname = u.last_name
    u.delete()

    messages.success(request, f"ลบ {fname} {lname} เรียบร้อย")

    return redirect("/project/home")

def users_update(request, roll):
    project = Users.objects.get(pk=roll)
    rooms = Rooms.objects.all()

    room_data = []
    for room in rooms:
        current_occupancy = Users.objects.filter(room_num=room.room_number).exclude(pk=roll).count()
        room_status = f"{room.room_number} ({current_occupancy}/{room.room_capacity} คน) (ห้องเต็ม)" if current_occupancy >= int(room.room_capacity) else f"{room.room_number} ({current_occupancy}/{room.room_capacity} คน)"
        room_data.append((room.room_number, room_status))

    #sort room_data by room number
    room_data.sort(key=lambda x: x[0])

    


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
        messages.success(request, f'แก้ไขข้อมูล {project_firstname} {project_last_name} เรียบร้อย')

        return redirect("/project/home")

@login_required(login_url='/login/')
def room_add(request):
    if request.method == 'POST':
        room_number = request.POST.get("room_number")
        room_capacity = request.POST.get("room_capacity")

        if not room_number:
            return render(request, 'std/add_room.html', {'error': 'กรุณากรอกข้อมูลหมายเลขห้องพัก'})

        if Rooms.objects.filter(room_number=room_number).count() > 0:
            return render(request, 'std/add_room.html', {'error': 'ห้องพักนี้มีอยู่เเล้ว กรุณากรอกหมายเลขห้องพักอื่น'})
        else:
            r = Rooms()
            r.room_number = room_number
            r.room_capacity = room_capacity
            r.save()
            messages.success(request, f'เพิ่มห้องพักหมายเลข {room_number} เรียบร้อย')
            return redirect("/project/home")

    return render(request, 'std/add_room.html', {})

@login_required(login_url='/login/')
def rooms_list(request):
    rooms = Rooms.objects.all().order_by('room_number')
    return render(request, 'std/rooms_list.html', {'rooms': rooms})




# def delete_room(request, room_id):
#     room = get_object_or_404(Rooms, id=room_id)

#     if request.method == 'POST':
#         room.delete()
#         return redirect('rooms_list')

#     return render(request, 'std/delete_room.html', {'room': room})




def delete_room(request, room_id):
    try:
        room = Rooms.objects.filter(id=room_id).first()
        
        if room is None:
            messages.error(request, "ไม่พบห้องที่ต้องการลบ")
        elif Users.objects.filter(room_num=room.room_number).exists():
            messages.warning(request, "มีผู้เข้าพักอยู่ในห้องนี้ ไม่สามารถลบห้องนี้ได้")
        else:
            deleted_room_number = room.room_number
            room.delete()
            messages.success(request, f"ลบห้องพักหมายเลข {deleted_room_number} เรียบร้อยแล้ว")
        
    except DatabaseError as e:
        messages.error(request, f"มีผู้เข้าพักอยู่ในห้องนี้ ไม่สามารถลบห้องนี้ได้ {e}")
    
    return redirect('rooms_list')



# @login_required(login_url='/login/')
# def update_room(request, room_id):
#     room = get_object_or_404(Rooms, id=room_id)
#     rooms = Rooms.objects.all()
#     room_data = []

#     for r in rooms:
#         occupancy = Users.objects.filter(room_num=r.room_number).exclude(pk=room_id).count()
#         room_status = f"{r.room_number} (ห้องพักเต็มแล้ว)" if occupancy >= int(r.room_capacity) else r.room_number
#         room_data.append((r.room_number, room_status))
    
#     if request.method == 'POST':
#         new_room_number = request.POST.get("room_number")
#         new_room_capacity = request.POST.get("room_capacity")
        
#         # Update the room details
#         room.room_number = new_room_number
#         room.room_capacity = new_room_capacity
#         room.save()
        
#         return redirect('rooms_list')
    
#     return render(request, 'std/update_room.html', {'room': room, 'room_data': room_data})


@login_required(login_url='/login/')
def update_room(request, room_id):
    room = get_object_or_404(Rooms, id=room_id)
    rooms = Rooms.objects.all()
    room_data = []

    for r in rooms:
        occupancy = Users.objects.filter(room_num=r.room_number).exclude(pk=room_id).count()
        room_status = f"{r.room_number} (ห้องพักเต็มแล้ว)" if occupancy >= int(r.room_capacity) else r.room_number
        room_data.append((r.room_number, room_status))
    
    if request.method == 'POST':
        new_room_number = request.POST.get("room_number")
        new_room_capacity = request.POST.get("room_capacity")
        
        # Check if there are occupants in the room
        occupancy = Users.objects.filter(room_num=room.room_number).count()
        
        if occupancy > 0:
            # If there are occupants, the new capacity must be greater than or equal to the current occupancy
            if int(new_room_capacity) < occupancy:
                error_message = "จำนวนผู้พักอาศัยในห้องต้องไม่น้อยกว่าจำนวนผู้พักอาศัยเดิมในห้อง"
                return render(request, 'std/update_room.html', {'room': room, 'room_data': room_data, 'error_message': error_message})
        
        # Update the room details
        room.room_number = new_room_number
        room.room_capacity = new_room_capacity
        room.save()
        messages.success(request, f'แก้ไขข้อมูลห้องพักหมายเลข {new_room_number} เรียบร้อย')
        
        return redirect('rooms_list')
    
    return render(request, 'std/update_room.html', {'room': room, 'room_data': room_data})