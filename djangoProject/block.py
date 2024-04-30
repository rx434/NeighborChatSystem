from django.shortcuts import render, redirect
from .decorators import login_required
from django.db import connection
from .settings import MEDIA_ROOT


@login_required
def block(request, bid):
    if request.method == 'GET':
        with connection.cursor() as cursor:
            cursor.execute("""
            SELECT b.name, n.nid, b.center_latitude, b.center_longitude, b.radius, n.name
            FROM block as b, neighborhood as n
            WHERE b.nid = n.nid and b.blockid = %s
            """, [bid])
            bname, nid, latitude, longitude, radius, neighbor = cursor.fetchone()

            cursor.execute("""
            SELECT users.photo, users.userid, users.username
            FROM block, users
            WHERE block.blockid = users.blockid and block.blockid = %s
            """, [bid])
            members = cursor.fetchall()

        context = {
            'bname': bname,
            'neighbor': neighbor,
            'nid': nid,
            'latitude': latitude,
            'longitude': longitude,
            'radius': radius,
            'members': members,
            'MEDIA_ROOT': MEDIA_ROOT
        }

        return render(request, 'block.html', context)


@login_required
def neighbor(request, nid):
    if request.method == 'GET':
        with connection.cursor() as cursor:
            cursor.execute("""
            SELECT name, description
            FROM neighborhood
            WHERE nid = %s
            """, [nid])
            name, description = cursor.fetchone()

            cursor.execute("""
            SELECT blockid, name
            FROM block
            WHERE nid = %s
            """, [nid])
            members = cursor.fetchall()

        context = {
            'nname': name,
            'description': description,
            'nid': nid,
            'members': members,
        }

        return render(request, 'neighbor.html', context)
