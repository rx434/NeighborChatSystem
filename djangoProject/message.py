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

            cursor.execute("""
            SELECT u.userid, b.blockid, b.nid
            FROM users u left outer join block b 
            ON u.blockid = b.blockid
            WHERE u.userid = %s
            """, [uid])
            thisuserid, thisblockid, thisnid = cursor.fetchone()

            cursor.execute("""
            SELECT userid
            FROM send_to_user
            WHERE mid=%s
            """, [mid])
            send_to_user = cursor.fetchone()
            if send_to_user:
                send_to_user = send_to_user[0]

            cursor.execute("""
            SELECT blockid
            FROM send_to_block
            WHERE mid=%s
            """, [mid])
            send_to_block = cursor.fetchone()
            if send_to_block:
                send_to_block = send_to_block[0]

            cursor.execute("""
            SELECT nid
            FROM send_to_neighbor
            WHERE mid=%s
            """, [mid])
            send_to_neighbor = cursor.fetchone()
            if send_to_neighbor:
                send_to_neighbor = send_to_neighbor[0]

        if (thisuserid == send_to_user) or (thisblockid is not None and thisblockid == send_to_block) or (thisnid is not None and thisnid == send_to_neighbor):
            reply_button = 'show'
        else:
            reply_button = 'not show'


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
            'reply_button': reply_button
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


@login_required
def view_message(request):
    uid = request.session.get('uid')
    # Firstly find the block and the neighbor this user belongs to
    with connection.cursor() as cursor:
        cursor.execute("""
        SELECT b.blockid, b.nid
        FROM users u, block b
        WHERE u.blockid = b.blockid and u.userid = %s
        """, [uid])
        res = cursor.fetchone()
        if res:
            bid, nid = res
        else:
            bid = None
            nid = None

    with connection.cursor() as cursor:
        # Then er try to find all corresponding messages
        with connection.cursor() as cursor:
            # All messages from neighbors
            cursor.execute("""
            SELECT *
            FROM send_to_user_messages
            WHERE receiver_id = %s and ownerid in (
            SELECT touserid
            FROM relationship
            WHERE fromuserid = %s and relation_type = %s and status = %s)
            """, [uid, uid, 'Neighbor', 'Approved'])
            all_messages_from_neighbors = cursor.fetchall()

            # New messages from neighbors
            cursor.execute("""
            SELECT *
            FROM send_to_user_messages
            WHERE (send_to_user_messages.receiver_id, send_to_user_messages.mid) in 
            (SELECT v.receiver_id, v.mid
            FROM send_to_user_messages_latest_view v, send_to_user_messages_latest_reply r
            WHERE send_to_user_messages.receiver_id = %s and v.receiver_id = r.receiver_id and v.mid = r.mid and 
            (v.latest_view is NULL or r.latest_reply > v.latest_view))
            and ownerid in (
            SELECT touserid
            FROM relationship
            WHERE fromuserid = %s and relation_type = %s and status = %s 
            )
            """, [uid, uid, 'Neighbor', 'Approved'])
            all_messages_new_from_neighbors = cursor.fetchall()

            # All messages from friends
            cursor.execute("""
            SELECT *
            FROM send_to_user_messages
            WHERE receiver_id = %s and ownerid in (
            (SELECT touserid
            FROM relationship
            WHERE fromuserid = %s and relation_type = %s and status = %s)
            UNION
            (SELECT fromuserid
            FROM relationship
            WHERE touserid = %s and relation_type = %s and status = %s)
            )""", [uid, uid, 'Friend', 'Approved', uid, 'Friend', 'Approved'])
            all_messages_from_friends = cursor.fetchall()

            # New messages from friends
            cursor.execute("""
            SELECT *
            FROM send_to_user_messages
            WHERE (send_to_user_messages.receiver_id, send_to_user_messages.mid) in 
            (SELECT v.receiver_id, v.mid
            FROM send_to_user_messages_latest_view v, send_to_user_messages_latest_reply r
            WHERE send_to_user_messages.receiver_id = %s and v.receiver_id = r.receiver_id and v.mid = r.mid and 
            (v.latest_view is NULL or r.latest_reply > v.latest_view))
            and ownerid in (
            (SELECT touserid
            FROM relationship
            WHERE fromuserid = %s and relation_type = %s and status = %s)
            UNION
            (SELECT fromuserid
            FROM relationship
            WHERE touserid = %s and relation_type = %s and status = %s)
            )
            """, [uid, uid, 'Friend', 'Approved', uid, 'Friend', 'Approved'])
            all_messages_new_from_friends = cursor.fetchall()

            # All messages from the block
            cursor.execute("""
            SELECT *
            FROM send_to_block_messages
            WHERE receiver_id = %s
            """, [uid])
            all_messages_from_block = cursor.fetchall()

            # New messages from the block
            cursor.execute("""
            SELECT *
            FROM send_to_block_messages
            WHERE (send_to_block_messages.receiver_id, send_to_block_messages.mid) in 
            (SELECT v.receiver_id, v.mid
            FROM send_to_block_messages_latest_view v, send_to_block_messages_latest_reply r
            WHERE send_to_block_messages.receiver_id = %s and v.receiver_id = r.receiver_id and v.mid = r.mid and 
            (v.latest_view is NULL or r.latest_reply > v.latest_view))
            """, [uid])
            new_messages_from_block = cursor.fetchall()

            # All messages from the neighborhood
            cursor.execute("""
            SELECT *
            FROM send_to_neighbor_messages
            WHERE receiver_id = %s
            """, [uid])
            all_messages_from_neighborhood = cursor.fetchall()

            # New messages from the neighborhood
            cursor.execute("""
            SELECT *
            FROM send_to_neighbor_messages
            WHERE (send_to_neighbor_messages.receiver_id, send_to_neighbor_messages.mid) in 
            (SELECT v.receiver_id, v.mid
            FROM send_to_neighbor_messages_latest_view v, send_to_neighbor_messages_latest_reply r
            WHERE send_to_neighbor_messages.receiver_id = %s and v.receiver_id = r.receiver_id and v.mid = r.mid and 
            (v.latest_view is NULL or r.latest_reply > v.latest_view))
            """, [uid])
            new_messages_from_neighborhood = cursor.fetchall()

        content = {
            'bid': bid,
            'nid': nid,
            'all_messages_from_neighbors': all_messages_from_neighbors,
            'all_messages_new_from_neighbors': all_messages_new_from_neighbors,
            'all_messages_from_friends': all_messages_from_friends,
            'all_messages_new_from_friends': all_messages_new_from_friends,
            'all_messages_from_block': all_messages_from_block,
            'new_messages_from_block': new_messages_from_block,
            'all_messages_from_neighborhood': all_messages_from_neighborhood,
            'new_messages_from_neighborhood': new_messages_from_neighborhood,
        }
        return render(request, 'view_message.html', content)


