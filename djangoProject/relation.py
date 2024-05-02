from django.shortcuts import render, redirect
from django.http import FileResponse, HttpResponseNotFound
from .decorators import login_required
from django.db import connection
from django.conf import settings
import os
from .query import find_block_by_id
from django.utils import timezone


@login_required
def relation(request):
    uid = request.session.get('uid')
    if request.method == 'GET':
        # Firstly find all neighbors for this specific user
        with connection.cursor() as cursor:
            cursor.execute("""
            SELECT r.rid, r.touserid, u.username, u.photo
            FROM relationship r, users u
            WHERE r.touserid = u.userid and r.fromuserid = %s and r.relation_type = %s and r.status = %s
            """, [uid, 'Neighbor', 'Approved'])
            neighbors = cursor.fetchall()

            # Then find all friends for this speific user. Be aware that the friend relationship is mutual.
            cursor.execute("""
            (SELECT r.rid, r.touserid, u.username, u.photo
            FROM relationship r, users u
            WHERE r.touserid = u.userid and r.relation_type = %s and r.status = %s and r.fromuserid = %s)
            UNION
            (SELECT r.rid, r.fromuserid, u.username, u.photo
            FROM relationship r, users u
            WHERE r.fromuserid = u.userid and r.relation_type = %s and r.status = %s and r.touserid = %s)
            """, ['Friend', 'Approved', uid, 'Friend', 'Approved', uid])
            friends = cursor.fetchall()

            # Then find all pending friends application to this specific user
            cursor.execute("""
            SELECT r.rid, r.fromuserid, u.username, u.photo
            FROM relationship r, users u
            WHERE r.fromuserid = u.userid and r.relation_type = %s and r.status = %s and r.touserid = %s
            """, ['Friend', 'Pending', uid])
            applications = cursor.fetchall()
            print(applications)

            # Then find all pending friends application from this spefic user
            cursor.execute("""
            SELECT r.rid, r.touserid, u.username, u.photo
            FROM relationship r, users u 
            WHERE r.touserid = u.userid and r.relation_type = %s and r.status = %s and r.fromuserid = %s
            """, ['Friend', 'Pending', uid])
            to_applications = cursor.fetchall()

        content = {
            'neighbors': neighbors,
            'friends': friends,
            'applications': applications,
            'to_applications': to_applications,
        }
        return render(request, 'relation.html', content)


@login_required
def neighbor_relation(request):
    uid = request.session.get('uid')
    if request.method == 'POST':
        rid = request.POST.get('rid')
        value = request.POST.get('neighbor_relation')
        if value == 'neighbor':
            # Add the neighbor relation
            touid = request.POST.get('touid')
            with connection.cursor() as cursor:
                cursor.execute("""
                INSERT INTO relationship (fromuserid, touserid, relation_type, status)
                VALUES (%s, %s, %s, %s)
                """, [uid, touid, 'Neighbor', 'Approved'])
            return redirect('profile', uid=touid)

        else:
            # Cancel the neighbor relation
            with connection.cursor() as cursor:
                cursor.execute("""
                UPDATE relationship SET status = %s 
                WHERE rid = %s
                """, ['Canceled', rid])
            return redirect('relation')


@login_required
def friend_relation(request):
    uid = request.session.get('uid')
    if request.method == 'POST':
        rid = request.POST.get('rid')
        value = request.POST.get('friend_relation')
        if value == 'friend':
            # Add the friend relation with status 'Pending'
            touid = request.POST.get('touid')
            with connection.cursor() as cursor:
                cursor.execute("""
                INSERT INTO relationship (fromuserid, touserid, relation_type, status)
                VALUES (%s, %s, %s, %s)
                """, [uid, touid, 'Friend', 'Pending'])
            return redirect('profile', uid=touid)

        else:
            # Cancel the friend relation
            with connection.cursor() as cursor:
                cursor.execute("""
                UPDATE relationship SET status = %s 
                WHERE rid = %s
                """, ['Canceled', rid])

            return redirect('relation')


@login_required
def cancel_application(request):
    if request.method == 'POST':
        rid = request.POST.get('rid')
        with connection.cursor() as cursor:
            cursor.execute("""
            UPDATE relationship SET status = %s 
            WHERE rid = %s
            """, ['Canceled', rid])

        return redirect('relation')


@login_required
def approve_friend(request):
    if request.method == 'POST':
        rid = request.POST.get('rid')
        with connection.cursor() as cursor:
            cursor.execute("""
            UPDATE relationship SET status = %s 
            WHERE rid = %s
            """, ['Approved', rid])

        return redirect('relation')

