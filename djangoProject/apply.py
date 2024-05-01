from django.shortcuts import render, redirect
from django.http import FileResponse, HttpResponseNotFound
from .decorators import login_required
from django.db import connection
from django.conf import settings
import os
from .query import find_block_by_id
from django.utils import timezone


@login_required
def apply(request):
    uid = request.session.get('uid', None)
    if request.method == 'GET':
        with connection.cursor() as cursor:
            cursor.execute("""
            SELECT blockid
            FROM users 
            WHERE userid = %s
            """, [uid])
            blockid = cursor.fetchone()[0]

        if blockid is None:
            # Showing the application in progress for this user
            with connection.cursor() as cursor:
                cursor.execute("""
                SELECT aid, blockid, approval_count, timestamp
                FROM apply
                WHERE userid = %s and status = %s
                """, [uid, 'Pending'])
                res = cursor.fetchone()
                if res is not None:
                    aid, apply_blockid, count, t = res
                    apply_blockname = find_block_by_id(apply_blockid)
                else:
                    aid, apply_blockid, count, t, apply_blockname = (None, None, None, None, None)

            # Because each block has its center latitude and center longitude, this part of code will display the block
            # that the user belongs to according to the user's address.
            with connection.cursor() as cursor:
                cursor.execute("""
                SELECT b.blockid, b.name
                FROM block b, users u
                WHERE u.userid = %s 
                AND SQRT(POWER((b.center_latitude - u.address_latitude) * 69, 2) + POWER((b.center_longitude - u.address_longitude) * 69, 2)) <= b.radius;
                """, [uid])
                recommend_blocks = cursor.fetchall()

            # The third part is to list all blocks that stored in this system.
            with connection.cursor() as cursor:
                cursor.execute("""
                SELECT blockid, name
                FROM block
                """)
                all_blocks = cursor.fetchall()

            content = {
                'blockid': blockid,
                'aid': aid,
                'apply_blockid': apply_blockid,
                'count': count,
                't': t,
                'apply_blockname': apply_blockname,
                'recommend_blocks': recommend_blocks,
                'all_blocks': all_blocks
            }

            return render(request, 'apply.html', content)

        else:
            blockname = find_block_by_id(blockid)

            with connection.cursor() as cursor:
                cursor.execute("""
                (SELECT aid, users.userid, approval_count, username, photo
                FROM apply, users
                WHERE apply.userid = users.userid and apply.blockid = %s and apply.status = %s)
                EXCEPT
                (SELECT apply.aid, users.userid, approval_count, username, photo
                FROM apply, users, approve
                WHERE apply.userid = users.userid and apply.aid = approve.aid and approve.userid = %s)
                """, [blockid, 'Pending', uid])
                apply_users = cursor.fetchall()

            content = {
                'blockid': blockid,
                'blockname': blockname,
                'apply_users': apply_users,
            }
            return render(request, 'apply.html', content)

    elif request.method == 'POST':
        apply_for = request.POST.get('bid')
        # Firstly, check the number of members for this specific block
        with connection.cursor() as cursor:
            cursor.execute("""
            SELECT b.blockid, b.name, COUNT(u.userid)
            FROM block b LEFT JOIN users u ON b.blockid = u.blockid
            WHERE b.blockid = %s
            GROUP BY b.blockid, b.name
            """, [apply_for])
            apply_for_bid, apply_for_name, number = cursor.fetchone()

        if number == 0:
            # In this case, we let the user directly be a member of this block.
            current_time = timezone.now().replace(tzinfo=None)
            with connection.cursor() as cursor:
                cursor.execute("""
                UPDATE users SET blockid = %s, membership_date = %s
                WHERE userid = %s
                """, [apply_for_bid, current_time, uid])

                # In addition, by default, when a user becomes a member of a block, the user will automatically follow
                # this block
                cursor.execute("""
                INSERT INTO follow (userid, blockid)
                VALUES (%s, %s)
                """, [uid, apply_for])

            return redirect('apply')

        else:
            # Else, we insert this application information into the table apply
            current_time = timezone.now().replace(tzinfo=None)
            with connection.cursor() as cursor:
                cursor.execute("""
                INSERT INTO apply (userid, blockid, status, timestamp)
                VALUES (%s, %s, %s, %s)
                """, [uid, apply_for, 'Pending', current_time])

            return redirect('apply')


@login_required
def approve(request):
    uid = request.session.get('uid')
    if request.method == 'POST':
        aid = request.POST.get('aid')
        with connection.cursor() as cursor:
            cursor.execute("""
            INSERT INTO approve (userid, aid)
            VALUES (%s, %s)
            """, [uid, aid])

            cursor.execute("""
            UPDATE apply SET approval_count = approval_count + 1
            WHERE aid = %s
            """, [aid])

        return redirect('apply')


@login_required
def cancel(request):
    uid = request.session.get('uid')
    if request.method == 'POST':
        aid = request.POST.get('aid')
        with connection.cursor() as cursor:
            cursor.execute("""
            UPDATE apply SET status = %s 
            WHERE aid = %s
            """, ['Canceled', aid])

        return redirect('apply')


@login_required
def leave(request):
    uid = request.session.get('uid')
    if request.method == 'POST':
        bid = request.POST.get('bid')
        with connection.cursor() as cursor:
            cursor.execute("""
            UPDATE users SET blockid = %s, membership_date = %s
            WHERE userid = %s
            """, [None, None, uid])

            cursor.execute("""
            DELETE FROM follow
            WHERE userid = %s and blockid = %s
            """, [uid, bid])

        return redirect('apply')