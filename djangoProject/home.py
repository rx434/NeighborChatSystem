from django.shortcuts import render, redirect
from .decorators import login_required


@login_required
def home(request):
    uid = request.session.get('uid', 'Not set')
    uname = request.session.get('uname', 'Not set')
    cookie = request.COOKIES
    return render(request, 'home.html', {'cookies': cookie, 'uid': uid, 'uname': uname})  # Render the home page if logged in
