from django.shortcuts import render, redirect
from django.contrib.auth import login, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.db import connection
from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser
import hashlib
import os


def hash_password(password):
    hasher = hashlib.sha256(password.encode('utf-8'))
    hash_value = hasher.digest().hex()
    return hash_value


def verify_password(stored_hash, given_password):
    hasher = hashlib.sha256(given_password.encode('utf-8'))
    return hasher.digest().hex() == stored_hash


def register(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        email = request.POST.get('email')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", [username])
            user_row = cursor.fetchone()
        if user_row is not None:
            error_message = "This username already exists."
            return render(request, 'register.html', {'error_message': error_message})

        if password != password2:
            error_message = "The two passwords don't match"
            return render(request, 'register.html', {'error_message': error_message})

        else:
            query = """
            INSERT INTO users (blockid, username, password, first_name, last_name, email, address_latitude, address_longitude, profile_text, photo) 
            VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, NULL, %s)
            """
            params = (username, hash_password(password), firstname, lastname, email, latitude, longitude, "default.png")
            with connection.cursor() as cursor:
                cursor.execute(query, params)
            return redirect('login')

    #     form = RegisterForm(request.POST)
    #     if form.is_valid():
    #         user = form.save()
    #         login(request, user)
    #         return redirect('login')  # Redirect to a desired page after registration
    # else:
    #     form = RegisterForm()
    return render(request, 'register.html')


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        with connection.cursor() as cursor:
            cursor.execute("SELECT userid, username, password FROM users WHERE username = %s", [username])
            user_row = cursor.fetchone()

        if user_row is None:
            error_message = "Invalid username or password."
            return render(request, 'login.html', {'error_message': error_message})
        else:
            uid, uname, passwd = user_row
            if not verify_password(passwd, password):
                error_message = "Invalid username or password."
                return render(request, 'login.html', {'error_message': error_message})
            else:
                request.session['uid'] = uid
                request.session['uname'] = uname
                return redirect('home')

    else:
        return render(request, 'login.html')


def logout(request):
    request.session.clear()
    return redirect('login')
