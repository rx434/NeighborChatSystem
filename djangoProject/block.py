from django.shortcuts import render, redirect
from .decorators import login_required
from django.db import connection


@login_required
def block(request, bid):
    if request.method == 'GET':
        pass


@login_required
def neighbor(request, nid):
    if request.method == 'GET':
        pass

