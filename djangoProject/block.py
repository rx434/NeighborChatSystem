from django.shortcuts import render, redirect
from .decorators import login_required
from django.db import connection
from .settings import MEDIA_ROOT
from .query import find_block_by_id


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

        uid = request.session.get('uid', None)

        with connection.cursor() as cursor:
            cursor.execute("""
            SELECT *
            FROM follow
            WHERE userid = %s and blockid = %s
            """, [uid, bid])
            follow = cursor.fetchone()


        context = {
            'bid': bid,
            'bname': bname,
            'neighbor': neighbor,
            'nid': nid,
            'latitude': latitude,
            'longitude': longitude,
            'radius': radius,
            'members': members,
            'follow': follow,
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


@login_required
def follow(request):
    uid = request.session.get('uid', None)
    if request.method == 'GET':
        with connection.cursor() as cursor:
            cursor.execute("""
            SELECT block.blockid, block.name
            FROM follow, block
            WHERE follow.blockid = block.blockid and userid = %s
            """, [uid])
            followed_blocks = cursor.fetchall()

        content = {
            'followed_blocks': followed_blocks
        }
        return render(request, 'follow.html', content)

    else:
        follow = request.POST.get('follow')
        print(follow)
        bid = request.POST.get('bid')
        if follow == 'follow':
            with connection.cursor() as cursor:
                cursor.execute("""
                INSERT INTO follow (userid, blockid)
                VALUES (%s, %s)
                """, [uid, bid])
            return redirect('block', bid=bid)

        elif follow == 'unfollow':
            with connection.cursor() as cursor:
                cursor.execute("""
                DELETE FROM follow
                WHERE userid = %s and blockid = %s
                """, [uid, bid])
            return redirect('block', bid=bid)



