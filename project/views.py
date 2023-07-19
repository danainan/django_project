from django.shortcuts import render,redirect
from .models import Users
from django.contrib.auth.models import User 
from .models import Rooms
from django.contrib.auth import authenticate, login as auth_login 
from django.contrib.auth import logout as auth_logout
from django.http import HttpResponse ,HttpResponseBadRequest
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q


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

    return render(request, 'std/home.html', {'users': users})



@login_required(login_url='/login/')
def users_add(request):
    if request.method == 'POST':
        print("Completed")
        projects_firstname = request.POST.get("project_firstname")
        projects_last_name = request.POST.get("project_last_name")
        projects_line_id = request.POST.get("project_line_id")
        projects_room_num = request.POST.get("project_room_num")

        room = Rooms.objects.get(room_number=projects_room_num)
        current_occupancy = Users.objects.filter(room_num=projects_room_num).count()
        if current_occupancy >= int(room.room_capacity):
            room_full = True
        else:
            room_full = False

        if room_full:
            rooms = Rooms.objects.all()
            room_options = [(room.room_number, f"{room.room_number} (ห้องพักเต็มเเล้ว)") if current_occupancy >= int(room.room_capacity) else (room.room_number, room.room_number) for room in rooms]
            return render(request, 'std/add_u.html', {'room_options': room_options, 'room_full': room_full})

        # create an object for models
        u = Users()
        u.firstname = projects_firstname
        u.last_name = projects_last_name
        u.line_id = projects_line_id  
        u.room_num = projects_room_num

        u.save()
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
        room_status = f"{room.room_number} (ห้องพักเต็มแล้ว)" if current_occupancy >= int(room.room_capacity) else room.room_number
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