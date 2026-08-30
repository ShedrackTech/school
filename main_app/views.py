import json
import requests
from decouple import config
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse

from .EmailBackend import EmailBackend
from .models import Attendance, Session, Subject


def login_page(request):
    if request.user.is_authenticated:
        if request.user.user_type == '1':
            return redirect(reverse("admin_home"))
        elif request.user.user_type == '2':
            return redirect(reverse("staff_home"))
        else:
            return redirect(reverse("student_home"))
    context = {'recaptcha_site_key': config('RECAPTCHA_SITE_KEY')}
    return render(request, 'main_app/login.html', context)

def doLogin(request, **kwargs):
    if request.method != 'POST':
        return HttpResponse("<h4>Denied</h4>")
    else:
        # Google recaptcha
        captcha_token = request.POST.get('g-recaptcha-response')
        captcha_url = "https://www.google.com/recaptcha/api/siteverify"
        captcha_key = config('RECAPTCHA_SECRET_KEY')
        data = {
            'secret': captcha_key,
            'response': captcha_token
        }
        try:
            captcha_server = requests.post(url=captcha_url, data=data)
            response = json.loads(captcha_server.text)
            if response['success'] == False:
                messages.error(request, 'Invalid Captcha. Try Again')
                return redirect('/')
        except:
            messages.error(request, 'Captcha could not be verified. Try Again')
            return redirect('/')

        # Authenticate
        user = authenticate(request, username=request.POST.get('email'), password=request.POST.get('password'))
        if user != None:
            login(request, user)
            if user.user_type == '1':
                return redirect(reverse("admin_home"))
            elif user.user_type == '2':
                return redirect(reverse("staff_home"))
            else:
                return redirect(reverse("student_home"))
        else:
            messages.error(request, "Invalid details")
            return redirect("/")


def logout_user(request):
    logout(request)
    return redirect("/")


def get_attendance(request):
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        session = get_object_or_404(Session, id=session_id)
        attendance = Attendance.objects.filter(subject=subject, session=session)
        attendance_list = []
        for attd in attendance:
            data = {
                    "id": attd.id,
                    "attendance_date": str(attd.date),
                    "session": attd.session.id
                    }
            attendance_list.append(data)
        return JsonResponse(json.dumps(attendance_list), safe=False)
    except Exception as e:
        return None


def showFirebaseJS(request):
    data = f"""
    importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-app.js');
    importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-messaging.js');

    firebase.initializeApp({{
        apiKey: "{config('FIREBASE_API_KEY')}",
        authDomain: "{config('FIREBASE_AUTH_DOMAIN')}",
        projectId: "{config('FIREBASE_PROJECT_ID')}",
        storageBucket: "{config('FIREBASE_STORAGE_BUCKET')}",
        messagingSenderId: "{config('FIREBASE_MESSAGING_SENDER_ID')}",
        appId: "{config('FIREBASE_APP_ID')}"
    }});

    const messaging = firebase.messaging();
    messaging.setBackgroundMessageHandler(function (payload) {{
        const notification = JSON.parse(payload);
        const notificationOption = {{
            body: notification.body,
            icon: notification.icon
        }};
        return self.registration.showNotification(payload.notification.title, notificationOption);
    }});
    """
    return HttpResponse(data, content_type='application/javascript')