from django.shortcuts import render, redirect
from django.http import FileResponse, HttpResponseNotFound
from .decorators import login_required
from django.db import connection
from django.conf import settings
import os
from django.core.files.storage import FileSystemStorage


@login_required
def home(request):
    uid = request.session.get('uid', 'Not set')
    uname = request.session.get('uname', 'Not set')
    request.session['error_message'] = None

    with connection.cursor() as cursor:
        cursor.execute("""
        SELECT photo
        FROM users
        WHERE userid = %s
        """, [uid])
        photo = cursor.fetchone()[0]

    with connection.cursor() as cursor:
        cursor.execute("""
        SELECT block.blockid, block.name, neighborhood.nid, neighborhood.name
        FROM users, block, neighborhood
        WHERE users.blockid = block.blockid and block.nid = neighborhood.nid and userid = %s
        """, [uid])
        row = cursor.fetchone()

    if row is None:
        blockid = None
        nid = None
        block = None
        neighbor = None
    else:
        blockid, block, nid, neighbor = row

    return render(request, 'home.html', {'uid': uid, 'uname': uname, 'blockid': blockid, 'nid': nid,
                                         'block': block, 'neighbor': neighbor, 'photo': photo})


@login_required
def profile(request, uid):
    session_uid = request.session.get('uid', 'Not set')
    error_message = request.session.get('error_message', None)
    if request.method == 'GET':
        with connection.cursor() as cursor:
            cursor.execute("""
            SELECT blockid, username, first_name, last_name, email, address_latitude, address_longitude, profile_text, photo, membership_date
            FROM users 
            WHERE userid = %s
            """, [uid])
            user_row = cursor.fetchone()
            blockid, username, first_name, last_name, email, latitude, longitude, introduction, photo, membership_date = user_row

            if blockid is not None:
                cursor.execute("""
                SELECT name
                FROM block
                WHERE blockid = %s
                """, [blockid])
                block = cursor.fetchone()[0]
            else:
                block = None

        return render(request, 'profile.html', {'blockid': blockid, 'block': block, 'uid': uid,
                                                'session_uid': session_uid,
                                                'uname': username, 'first_name': first_name, 'last_name': last_name,
                                                'email': email, 'latitude': latitude, 'longitude': longitude,
                                                'introduction': introduction, 'photo': photo,
                                                'membership_date': membership_date,
                                                'error_message': error_message})
    elif request.method == 'POST':
        photo = request.FILES.get('photo')
        username = request.POST.get('uname')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        introduction = request.POST.get('introduction')

        if photo:
            extension = os.path.splitext(photo.name)[1]
            filename = f"{uid}{extension}"
            photo_path = os.path.join(settings.MEDIA_ROOT, filename)

            if os.path.exists(photo_path):
                os.remove(photo_path)

            with open(photo_path, 'wb+') as destination:
                for chunk in photo.chunks():
                    destination.write(chunk)

            relative_photo_path = filename
        else:
            with connection.cursor() as cursor:
                cursor.execute("""
                SELECT photo
                FROM users
                WHERE userid = %s
                """, [uid])
                relative_photo_path = cursor.fetchone()[0]

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE users SET username=%s, photo=%s, first_name=%s, last_name=%s, email=%s, profile_text=%s
                    WHERE userid=%s
                    """, [username, relative_photo_path, first_name, last_name, email, introduction, uid])
        except:
            error_message = "This username already exists."
            request.session['error_message'] = error_message
            return redirect('profile', uid=uid)

        request.session['error_message'] = None
        return redirect('profile', uid=uid)


@login_required
def address(request):
    session_uid = request.session.get('uid', 'Not set')
    if request.method == 'GET':
        return render(request, 'address.html', {'uid': session_uid})

    elif request.method == 'POST':
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE users SET address_latitude=%s, address_longitude=%s
                WHERE userid=%s
                """, [latitude, longitude, session_uid])

        return redirect('profile', uid=session_uid)


@login_required
def serve_media(request, path):
    # Construct the full file path
    file_path = os.path.join(settings.MEDIA_ROOT, path)

    # Check if file exists
    if not os.path.exists(file_path):
        return HttpResponseNotFound('The requested file does not exist.')

    # Open the file to serve it
    response = FileResponse(open(file_path, 'rb'))

    # Set the cache-control headers
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response



