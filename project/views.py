from django.shortcuts import render,redirect
from .models import Users
from django.contrib.auth.models import User 
from .models import Rooms
from django.contrib.auth import authenticate, login as auth_login 
from django.contrib.auth import logout as auth_logout
from django.http import HttpResponse ,HttpResponseBadRequest
from django.contrib import messages




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


def home(request):
    project=Users.objects.all()

    return render(request , 'std/home.html', {'project':project})

def users_add(request):
    if request.method == 'POST':
        print("Completed")
        # Retrieve the user inputs
        projects_firstname = request.POST.get("project_firstname")
        projects_last_name = request.POST.get("project_last_name")
        projects_email = request.POST.get("project_email")
        projects_room_num = request.POST.get("project_room_num")

        room = Rooms.objects.get(room_number=projects_room_num)
        current_occupancy = Users.objects.filter(room_num=projects_room_num).count()
        if current_occupancy >= int(room.room_capacity):
            room_full = True
        else:
            room_full = False

        if room_full:
            rooms = Rooms.objects.all()
            return render(request, 'std/add_u.html', {'rooms': rooms, 'room_full': room_full})

        # create an object for models
        u = Users()
        u.firstname = projects_firstname
        u.last_name = projects_last_name
        u.email = projects_email
        u.room_num = projects_room_num

        u.save()
        return redirect("/project/home")

    rooms = Rooms.objects.all()
    return render(request, 'std/add_u.html', {'rooms': rooms})


def users_delete(request,roll):
    u=Users.objects.get(pk=roll)
    u.delete()

    return redirect("/project/home")

def users_update(request,roll):
    project=Users.objects.get(pk=roll)
    return render(request, 'std/update_u.html',{'project':project})

def do_users_update(request,roll):
    project_firstname=request.POST.get("project_firstname")
    project_last_name=request.POST.get("project_last_name")
    project_email=request.POST.get("project_email")
    project_room_num=request.POST.get("project_room_num")

    project=Users.objects.get(pk=roll)

    project.firstname=project_firstname
    project.last_name=project_last_name
    project.email=project_email
    project.room_num=project_room_num

    project.save()
    return redirect("/project/home")

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



    



    

