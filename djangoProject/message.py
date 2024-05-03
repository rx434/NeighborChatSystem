from django.shortcuts import render, redirect
from django.http import FileResponse, HttpResponseNotFound
from .decorators import login_required
from django.db import connection
from django.conf import settings
import os
from .query import find_block_by_id
from django.utils import timezone


@login_required
def message(request, mid):
    uid = request.session.get('uid')
    if request.method == 'GET':
        with connection.cursor() as cursor:
            cursor.execute("""
            SELECT *
            FROM message
            WHERE mid=%s
            """, [mid])
            mid, ownerid, subject, body, timestamp, latitude, longitude = cursor.fetchone()

            cursor.execute("""
            SELECT username, photo
            FROM users
            WHERE userid=%s
            """, [ownerid])
            username, photo = cursor.fetchone()

        with connection.cursor() as cursor:
            cursor.execute("""
            SELECT r.replyid, u.userid, r.mid, r.body, r.timestamp, u.username, u.photo
            FROM reply r, users u
            WHERE r.userid = u.userid and mid=%s
            """, [mid])
            replies = cursor.fetchall()

            cursor.execute("""
            INSERT INTO view (userid, mid)
            VALUES (%s, %s)
            """, [uid, mid])

        content = {
            'mid': mid,
            'ownerid': ownerid,
            'username': username,
            'photo': photo,
            'subject': subject,
            'body': body,
            'timestamp': timestamp,
            'latitude': latitude,
            'longitude': longitude,
            'replies': replies,
        }
        return render(request, 'message.html', content)

    elif request.method == 'POST':
        body = request.POST.get('reply_body')
        with connection.cursor() as cursor:
            cursor.execute("""
            INSERT INTO reply (userid, mid, body)
            VALUES (%s, %s, %s)
            """, [uid, mid, body])

        return redirect('message', mid=mid)
