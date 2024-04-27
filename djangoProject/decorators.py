from django.http import HttpResponseRedirect


def login_required(function):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('uid'):
            return HttpResponseRedirect('/login/')  # Redirect to login if no user_id in session
        return function(request, *args, **kwargs)
    return wrapper
