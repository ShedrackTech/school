import json

import firebase_admin
import requests
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import HttpResponseRedirect, get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import UpdateView
from django.utils import timezone
from decouple import config
from firebase_admin import credentials, messaging
from django.core.paginator import Paginator
from django.db.models import Count, Q
from datetime import datetime
from .forms import *
from .models import *

if not firebase_admin._apps:
    cred = credentials.Certificate(config('FIREBASE_SERVICE_ACCOUNT_PATH'))
    firebase_admin.initialize_app(cred)


def admin_home(request):
    total_staff = Staff.objects.all().count()
    total_students = Student.objects.all().count()
    subjects = Subject.objects.all()
    total_subject = subjects.count()
    total_course = Course.objects.all().count()
    attendance_list = Attendance.objects.filter(subject__in=subjects)
    total_attendance = attendance_list.count()
    attendance_list = []
    subject_list = []
    for subject in subjects:
        attendance_count = Attendance.objects.filter(subject=subject).count()
        subject_list.append(subject.name[:7])
        attendance_list.append(attendance_count)

    students = Student.objects.select_related('admin', 'course', 'session').order_by('-id')

    today = timezone.localdate()

    # Student attendance summary
    todays_reports = AttendanceReport.objects.filter(attendance__date=today)
    if todays_reports.exists():
        attendance_date = today
        attendance_is_today = True
        reports = todays_reports
    else:
        latest_attendance = Attendance.objects.order_by('-date').first()
        if latest_attendance:
            attendance_date = latest_attendance.date
            attendance_is_today = False
            reports = AttendanceReport.objects.filter(attendance__date=attendance_date)
        else:
            attendance_date = None
            attendance_is_today = False
            reports = AttendanceReport.objects.none()

    attendance_total = reports.count()
    attendance_present = reports.filter(status=True).count()
    attendance_absent = attendance_total - attendance_present

    # Staff attendance summary
    todays_staff = StaffAttendance.objects.filter(date=today)
    if todays_staff.exists():
        staff_att_date = today
        staff_att_is_today = True
        staff_records = todays_staff
    else:
        latest_staff = StaffAttendance.objects.order_by('-date').first()
        if latest_staff:
            staff_att_date = latest_staff.date
            staff_att_is_today = False
            staff_records = StaffAttendance.objects.filter(date=staff_att_date)
        else:
            staff_att_date = None
            staff_att_is_today = False
            staff_records = StaffAttendance.objects.none()

    staff_att_total = staff_records.count()
    staff_att_present = staff_records.filter(status=True).count()
    staff_att_absent = staff_att_total - staff_att_present

    context = {
        'portal_name': 'Administrator',
        'page_title': "Administrative Dashboard",
        'total_students': total_students,
        'total_staff': total_staff,
        'total_course': total_course,
        'total_subject': total_subject,
        'subject_list': subject_list,
        'attendance_list': attendance_list,
        'students': students,
        'attendance_present': attendance_present,
        'attendance_absent': attendance_absent,
        'attendance_total': attendance_total,
        'attendance_date': attendance_date,
        'attendance_is_today': attendance_is_today,
        'staff_att_present': staff_att_present,
        'staff_att_absent': staff_att_absent,
        'staff_att_total': staff_att_total,
        'staff_att_date': staff_att_date,
        'staff_att_is_today': staff_att_is_today,
    }
    return render(request, 'main_app/hod_template/admin_home.html', context)

def add_staff(request):
    form = StaffForm(request.POST or None, request.FILES or None)
    context = {
        'form': form,
        'page_title': 'Add Staff',
        'courses': Course.objects.all(),
    }
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password')
            course = form.cleaned_data.get('course')
            passport = request.FILES.get('profile_pic')
            try:
                user = CustomUser.objects.create_user(
                    email=email,
                    password=password,
                    user_type=2,
                    first_name=first_name,
                    last_name=last_name,
                    profile_pic=passport
                )
                user.gender = gender
                user.address = address
                user.save()

                staff = Staff.objects.get(admin=user)
                staff.course = course
                staff.save()

                messages.success(request, "Successfully Added")
                return redirect(reverse('add_staff'))
            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Please fulfil all requirements: " + str(form.errors))

    return render(request, 'main_app/hod_template/add_staff.html', context)


def add_student(request):
    student_form = StudentForm(request.POST or None, request.FILES or None)
    context = {
        'form': student_form,
        'page_title': 'Add Student',
        'courses': Course.objects.all(),
        'sessions': Session.objects.all(),
        'departments': Department.objects.all(),
    }
    if request.method == 'POST':
        if student_form.is_valid():
            first_name = student_form.cleaned_data.get('first_name')
            last_name = student_form.cleaned_data.get('last_name')
            address = student_form.cleaned_data.get('address')
            email = student_form.cleaned_data.get('email')
            gender = student_form.cleaned_data.get('gender')
            password = student_form.cleaned_data.get('password')
            course = student_form.cleaned_data.get('course')
            session = student_form.cleaned_data.get('session')
            passport = request.FILES.get('profile_pic')
            try:
                user = CustomUser.objects.create_user(
                    email=email,
                    password=password,
                    user_type=3,
                    first_name=first_name,
                    last_name=last_name,
                    profile_pic=passport
                )
                user.gender = gender
                user.address = address
                user.save()

                student = Student.objects.get(admin=user)
                student.course = course
                student.department = student_form.cleaned_data.get('department')
                student.session = session
                student.save()

                messages.success(request, "Successfully Added")
                return redirect(reverse('add_student'))
            except Exception as e:
                messages.error(request, "Could Not Add: " + str(e))
        else:
            messages.error(request, "Could Not Add: " + str(student_form.errors))
    return render(request, 'main_app/hod_template/add_student.html', context)


def add_course(request):
    form = CourseForm(request.POST or None)
    context = {
        'form': form,
        'page_title': 'Add Course',
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            try:
                course = Course()
                course.name = name
                course.has_departments = form.cleaned_data.get('has_departments')
                course.save()

                messages.success(request, "Successfully Added")
                return redirect(reverse('add_course'))
            except Exception:
                messages.error(request, "Could Not Add")
        else:
            messages.error(request, "Could Not Add")
    return render(request, 'main_app/hod_template/add_course.html', context)


def add_subject(request):
    form = SubjectForm(request.POST or None)
    context = {
        'form': form,
        'page_title': 'Add Subject',
        'courses': Course.objects.all(),
        'staffs': Staff.objects.all(),
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            course = form.cleaned_data.get('course')
            staff = form.cleaned_data.get('staff')
            try:
                subject = Subject()
                subject.name = name
                subject.staff = staff
                subject.course = course
                subject.department = form.cleaned_data.get('department')
                subject.save()

                messages.success(request, "Successfully Added")
                return redirect(reverse('add_subject'))
            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")

    return render(request, 'main_app/hod_template/add_subject.html', context)


def manage_staff(request):
    staffs = Staff.objects.select_related('admin', 'course').all()
    context = {
        'staffs': staffs,
        'page_title': 'Manage Staff'
    }
    return render(request, "main_app/hod_template/manage_staff.html", context)


def manage_student(request):
    students = Student.objects.select_related('admin', 'course', 'session').all()
    context = {
        'students': students,
        'page_title': 'Manage Students'
    }
    return render(request, "main_app/hod_template/manage_student.html", context)


def manage_course(request):
    courses = Course.objects.all()
    context = {
        'courses': courses,
        'page_title': 'Manage Courses'
    }
    return render(request, "main_app/hod_template/manage_course.html", context)


def manage_subject(request):
    subjects = Subject.objects.all()
    context = {
        'subjects': subjects,
        'page_title': 'Manage Subjects'
    }
    return render(request, "main_app/hod_template/manage_subject.html", context)


def edit_staff(request, staff_id):
    staff = get_object_or_404(Staff, id=staff_id)
    form = StaffForm(request.POST or None, instance=staff)
    context = {
        'form': form,
        'staff_id': staff_id,
        'page_title': 'Edit Staff'
    }
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password') or None
            course = form.cleaned_data.get('course')
            passport = request.FILES.get('profile_pic') or None
            try:
                user = CustomUser.objects.get(id=staff.admin.id)
                user.email = email
                if password is not None:
                    user.set_password(password)
                if passport is not None:
                    user.profile_pic = passport
                user.first_name = first_name
                user.last_name = last_name
                user.gender = gender
                user.address = address
                user.save()

                staff.course = course
                staff.save()

                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_staff', args=[staff_id]))
            except Exception as e:
                messages.error(request, "Could Not Update " + str(e))
        else:
            messages.error(request, "Please fill form properly: " + str(form.errors))
    else:
        user = CustomUser.objects.get(id=staff_id)
        staff = Staff.objects.get(id=user.id)
        return render(request, "main_app/hod_template/edit_staff.html", context)

    return render(request, "main_app/hod_template/edit_staff.html", context)


def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    form = StudentForm(request.POST or None, instance=student)
    context = {
        'form': form,
        'student_id': student_id,
        'page_title': 'Edit Student',
        'departments': Department.objects.all(),
    }
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password') or None
            course = form.cleaned_data.get('course')
            session = form.cleaned_data.get('session')
            passport = request.FILES.get('profile_pic') or None
            try:
                user = CustomUser.objects.get(id=student.admin.id)
                if passport is not None:
                    user.profile_pic = passport
                user.email = email
                if password is not None:
                    user.set_password(password)
                user.first_name = first_name
                user.last_name = last_name
                user.gender = gender
                user.address = address
                user.save()

                student.course = course
                student.department = form.cleaned_data.get('department')
                student.session = session
                student.save()

                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_student', args=[student_id]))
            except Exception as e:
                messages.error(request, "Could Not Update " + str(e))
        else:
            messages.error(request, "Please Fill Form Properly! " + str(form.errors))
    return render(request, "main_app/hod_template/edit_student.html", context)


def edit_course(request, course_id):
    instance = get_object_or_404(Course, id=course_id)
    form = CourseForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'course_id': course_id,
        'page_title': 'Edit Course'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            try:
                course = Course.objects.get(id=course_id)
                course.name = name
                course.has_departments = form.cleaned_data.get('has_departments')
                course.save()

                messages.success(request, "Successfully Updated")
            except Exception:
                messages.error(request, "Could Not Update")
        else:
            messages.error(request, "Could Not Update")

    return render(request, 'main_app/hod_template/edit_course.html', context)


def edit_subject(request, subject_id):
    instance = get_object_or_404(Subject, id=subject_id)
    form = SubjectForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'subject_id': subject_id,
        'page_title': 'Edit Subject'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            course = form.cleaned_data.get('course')
            staff = form.cleaned_data.get('staff')
            try:
                subject = Subject.objects.get(id=subject_id)
                subject.name = name
                subject.staff = staff
                subject.course = course
                subject.department = form.cleaned_data.get('department')
                subject.save()

                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_subject', args=[subject_id]))
            except Exception as e:
                messages.error(request, "Could Not Update " + str(e))
        else:
            messages.error(request, "Fill Form Properly")
    return render(request, 'main_app/hod_template/edit_subject.html', context)


def add_session(request):
    form = SessionForm(request.POST or None)
    context = {'form': form, 'page_title': 'Add Session'}
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Session Created")
                return redirect(reverse('add_session'))
            except Exception as e:
                messages.error(request, 'Could Not Add ' + str(e))
        else:
            messages.error(request, 'Fill Form Properly ')
    return render(request, "main_app/hod_template/add_session.html", context)


def manage_session(request):
    sessions = Session.objects.all()
    context = {'sessions': sessions, 'page_title': 'Manage Sessions'}
    return render(request, "main_app/hod_template/manage_session.html", context)


def edit_session(request, session_id):
    instance = get_object_or_404(Session, id=session_id)
    form = SessionForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'session_id': session_id,
        'page_title': 'Edit Session'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Session Updated")
                return redirect(reverse('edit_session', args=[session_id]))
            except Exception as e:
                messages.error(request, "Session Could Not Be Updated " + str(e))
                return render(request, "main_app/hod_template/edit_session.html", context)
        else:
            messages.error(request, "Invalid Form Submitted ")
            return render(request, "main_app/hod_template/edit_session.html", context)
    else:
        return render(request, "main_app/hod_template/edit_session.html", context)


def check_email_availability(request):
    email = request.POST.get("email")
    try:
        user = CustomUser.objects.filter(email=email).exists()
        if user:
            return HttpResponse(True)
        return HttpResponse(False)
    except Exception:
        return HttpResponse(False)


def student_feedback_message(request):
    if request.method != 'POST':
        feedbacks = FeedbackStudent.objects.all()
        context = {
            'feedbacks': feedbacks,
            'page_title': 'Student Feedback Messages'
        }
        return render(request, 'main_app/hod_template/student_feedback_message.html', context)
    else:
        feedback_id = request.POST.get('id')
        try:
            feedback = get_object_or_404(FeedbackStudent, id=feedback_id)
            reply = request.POST.get('reply')
            feedback.reply = reply
            feedback.save()
            return HttpResponse(True)
        except Exception:
            return HttpResponse(False)


def staff_feedback_message(request):
    if request.method != 'POST':
        feedbacks = FeedbackStaff.objects.all()
        context = {
            'feedbacks': feedbacks,
            'page_title': 'Staff Feedback Messages'
        }
        return render(request, 'main_app/hod_template/staff_feedback_message.html', context)
    else:
        feedback_id = request.POST.get('id')
        try:
            feedback = get_object_or_404(FeedbackStaff, id=feedback_id)
            reply = request.POST.get('reply')
            feedback.reply = reply
            feedback.save()
            return HttpResponse(True)
        except Exception:
            return HttpResponse(False)


def view_staff_leave(request):
    if request.method != 'POST':
        leaves = LeaveReportStaff.objects.select_related('staff', 'staff__admin').all()
        context = {
            'leaves': leaves,
            'page_title': 'Leave Applications From Staff'
        }
        return render(request, "main_app/hod_template/view_staff_leave.html", context)
    else:
        id = request.POST.get('id')
        status = request.POST.get('status')
        if status == '1':
            status = 1
        else:
            status = -1
        try:
            leave = get_object_or_404(LeaveReportStaff, id=id)
            leave.status = status
            leave.save()

            if status == 1:
                msg = f"Your leave request for {leave.date} has been approved."
            else:
                msg = f"Your leave request for {leave.date} has been rejected."
            NotificationStaff.objects.create(staff=leave.staff, message=msg, link='staff_apply_leave')

            return HttpResponse(True)
        except Exception:
            return HttpResponse("False")


def view_student_leave(request):
    if request.method != 'POST':
        leaves = LeaveReportStudent.objects.select_related('student', 'student__admin').all()
        context = {
            'leaves': leaves,
            'page_title': 'Leave Applications From Students'
        }
        return render(request, "main_app/hod_template/view_student_leave.html", context)
    else:
        id = request.POST.get('id')
        status = request.POST.get('status')
        if status == '1':
            status = 1
        else:
            status = -1
        try:
            leave = get_object_or_404(LeaveReportStudent, id=id)
            leave.status = status
            leave.save()

            if status == 1:
                msg = f"Your leave request for {leave.date} has been approved."
            else:
                msg = f"Your leave request for {leave.date} has been rejected."
            NotificationStudent.objects.create(student=leave.student, message=msg, link='student_apply_leave')

            return HttpResponse(True)
        except Exception:
            return HttpResponse("False")


def admin_view_attendance(request):
    staffs = Staff.objects.select_related('admin', 'course').all()
    sessions = Session.objects.all()
    context = {
        'staffs': staffs,
        'sessions': sessions,
        'page_title': 'View Attendance'
    }
    return render(request, "main_app/hod_template/admin_view_attendance.html", context)


def get_staff_subjects(request):
    """AJAX: return subjects taught by a given staff member, for the
    Staff -> Subject cascade on the admin View Attendance page."""
    staff_id = request.GET.get('staff_id')
    try:
        staff = get_object_or_404(Staff, id=staff_id)
        subjects = Subject.objects.filter(staff=staff)
        data = [{"id": s.id, "name": s.name} for s in subjects]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def get_attendance_dates(request):
    """AJAX: return the attendance records (id + date) taken for a given
    subject + session, for the Subject/Session -> Date cascade."""
    subject_id = request.GET.get('subject_id')
    session_id = request.GET.get('session_id')
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        session = get_object_or_404(Session, id=session_id)
        records = Attendance.objects.filter(
            subject=subject, session=session
        ).order_by('-date')
        data = [{"id": a.id, "date": str(a.date)} for a in records]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def get_admin_attendance(request):
    """AJAX: return each student's attendance status for a specific,
    already-taken attendance record (chosen via get_attendance_dates)."""
    attendance_id = request.GET.get('attendance_id')
    try:
        attendance = get_object_or_404(Attendance, id=attendance_id)
        attendance_reports = AttendanceReport.objects.filter(
            attendance=attendance
        ).select_related('student', 'student__admin')
        json_data = []
        for report in attendance_reports:
            data = {
                "status": bool(report.status),
                "name": str(report.student)
            }
            json_data.append(data)
        return JsonResponse(json_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def admin_view_profile(request):
    admin = get_object_or_404(Admin, admin=request.user)
    form = AdminForm(request.POST or None, request.FILES or None, instance=admin)
    context = {
        'form': form,
        'page_title': 'View/Edit Profile'
    }
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                passport = request.FILES.get('profile_pic') or None
                custom_user = admin.admin
                if password != None:
                    custom_user.set_password(password)
                if passport != None:
                    custom_user.profile_pic = passport
                custom_user.first_name = first_name
                custom_user.last_name = last_name
                custom_user.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('admin_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
        except Exception as e:
            messages.error(request, "Error Occured While Updating Profile " + str(e))
    return render(request, "main_app/hod_template/admin_view_profile.html", context)


def admin_notify_staff(request):
    staff = CustomUser.objects.filter(user_type=2)
    context = {
        'page_title': "Send Notifications To Staff",
        'allStaff': staff
    }
    return render(request, "main_app/hod_template/admin_notify_staff.html", context)


def admin_notify_student(request):
    student = CustomUser.objects.filter(user_type=3)
    context = {
        'page_title': "Send Notifications To Students",
        'students': student
    }
    return render(request, "main_app/hod_template/admin_notify_student.html", context)


def send_student_notification(request):
    id = request.POST.get('id')
    message = request.POST.get('message')
    student = get_object_or_404(Student, admin_id=id)

    try:
        notification = NotificationStudent(student=student, message=message, link='student_home')
        notification.save()
    except Exception:
        return HttpResponse("False")

    # Push notification is best-effort: a missing/stale fcm_token should not
    # count as a failed send, since the in-app notification above is what
    # the student actually sees when they open the app.
    token = student.admin.fcm_token
    if token:
        try:
            msg = messaging.Message(
                notification=messaging.Notification(
                    title="Student Management System",
                    body=message,
                ),
                token=token,
            )
            messaging.send(msg)
        except Exception:
            pass

    return HttpResponse("True")


def send_staff_notification(request):
    id = request.POST.get('id')
    message = request.POST.get('message')
    staff = get_object_or_404(Staff, admin_id=id)

    try:
        notification = NotificationStaff(staff=staff, message=message, link='staff_home')
        notification.save()
    except Exception:
        return HttpResponse("False")

    token = staff.admin.fcm_token
    if token:
        try:
            msg = messaging.Message(
                notification=messaging.Notification(
                    title="Student Management System",
                    body=message,
                ),
                token=token,
            )
            messaging.send(msg)
        except Exception:
            pass

    return HttpResponse("True")


def delete_staff(request, staff_id):
    staff = get_object_or_404(CustomUser, staff__id=staff_id)
    staff.delete()
    messages.success(request, "Staff deleted successfully!")
    return redirect(reverse('manage_staff'))


def delete_student(request, student_id):
    student = get_object_or_404(CustomUser, student__id=student_id)
    student.delete()
    messages.success(request, "Student deleted successfully!")
    return redirect(reverse('manage_student'))


def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    try:
        course.delete()
        messages.success(request, "Course deleted successfully!")
    except Exception:
        messages.error(
            request,
            "Sorry, some students are assigned to this course already. Kindly change the affected student course and try again"
        )
    return redirect(reverse('manage_course'))


def delete_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    subject.delete()
    messages.success(request, "Subject deleted successfully!")
    return redirect(reverse('manage_subject'))


def delete_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    try:
        session.delete()
        messages.success(request, "Session deleted successfully!")
    except Exception:
        messages.error(
            request,
            "There are students assigned to this session. Please move them to another session."
        )
    return redirect(reverse('manage_session'))


def profile_change_requests(request):
    requests_qs = ProfileChangeRequest.objects.select_related('user').filter(status='pending').order_by('-created_at')
    context = {
        'requests': requests_qs,
        'page_title': 'Profile Change Requests',
    }
    return render(request, 'main_app/hod_template/profile_change_requests.html', context)


def review_profile_change(request, request_id):
    change_request = get_object_or_404(ProfileChangeRequest, id=request_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        user = change_request.user

        if action == 'approve':
            if change_request.first_name:
                user.first_name = change_request.first_name
            if change_request.last_name:
                user.last_name = change_request.last_name
            if change_request.email:
                user.email = change_request.email
            if change_request.gender:
                user.gender = change_request.gender
            if change_request.address:
                user.address = change_request.address
            if change_request.profile_pic:
                user.profile_pic = change_request.profile_pic
            user.save()

            change_request.status = 'approved'
            change_request.reviewed_at = timezone.now()
            change_request.reviewed_by = request.user
            change_request.save()

            if user.user_type == '3':
                NotificationStudent.objects.create(
                    student=user.student, message="Your profile change request was approved.", link='student_view_profile'
                )
            elif user.user_type == '2':
                NotificationStaff.objects.create(
                    staff=user.staff, message="Your profile change request was approved.", link='staff_view_profile'
                )

            messages.success(request, "Change request approved and applied.")

        elif action == 'reject':
            note = request.POST.get('admin_note', '')
            change_request.status = 'rejected'
            change_request.admin_note = note
            change_request.reviewed_at = timezone.now()
            change_request.reviewed_by = request.user
            change_request.save()

            if user.user_type == '3':
                NotificationStudent.objects.create(
                    student=user.student, message="Your profile change request was rejected." + (f" Reason: {note}" if note else ""), link='student_view_profile'
                )
            elif user.user_type == '2':
                NotificationStaff.objects.create(
                    staff=user.staff, message="Your profile change request was rejected." + (f" Reason: {note}" if note else ""), link='staff_view_profile'
                )

            messages.success(request, "Change request rejected.")

    return redirect(reverse('profile_change_requests'))

def admin_take_staff_attendance(request):
    date_str = request.GET.get('date') or request.POST.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.localdate()
    else:
        selected_date = timezone.localdate()

    staffs = Staff.objects.select_related('admin', 'course').order_by(
        'admin__first_name', 'admin__last_name'
    )
    existing = {
        r.staff_id: r.status
        for r in StaffAttendance.objects.filter(date=selected_date)
    }

    if request.method == 'POST':
        for staff in staffs:
            status = request.POST.get(f'status_{staff.id}') == 'present'
            StaffAttendance.objects.update_or_create(
                staff=staff, date=selected_date,
                defaults={'status': status, 'marked_by': request.user}
            )
        messages.success(request, f"Staff attendance saved for {selected_date}")
        return redirect(reverse('admin_take_staff_attendance') + f'?date={selected_date}')

    # Build (staff, is_present, has_record) tuples so the template needs
    # no dict lookups — has_record distinguishes "not marked yet" (default
    # to Present, since that's the more common case each morning) from
    # "explicitly marked Absent" on a re-visit to an already-taken date.
    staff_rows = [
        (staff, existing.get(staff.id, True), staff.id in existing)
        for staff in staffs
    ]

    context = {
        'staff_rows': staff_rows,
        'selected_date': selected_date,
        'page_title': 'Take Staff Attendance',
    }
    return render(request, 'main_app/hod_template/admin_take_staff_attendance.html', context)

def admin_staff_attendance_list(request):
    query = request.GET.get('q', '').strip()
    staffs = Staff.objects.select_related('admin', 'course').annotate(
        total_marked=Count('staffattendance'),
        total_present=Count('staffattendance', filter=Q(staffattendance__status=True)),
    ).order_by('admin__first_name', 'admin__last_name')

    if query:
        staffs = staffs.filter(
            Q(admin__first_name__icontains=query) | Q(admin__last_name__icontains=query)
        )

    paginator = Paginator(staffs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'query': query,
        'page_title': 'Staff Attendance',
    }
    return render(request, 'main_app/hod_template/admin_staff_attendance_list.html', context)


def admin_staff_attendance_detail(request, staff_id):
    staff = get_object_or_404(Staff.objects.select_related('admin', 'course'), id=staff_id)
    records = StaffAttendance.objects.filter(staff=staff).order_by('-date')

    total = records.count()
    present = records.filter(status=True).count()
    absent = total - present
    rate = round((present / total) * 100, 1) if total else None

    context = {
        'staff': staff,
        'records': records,
        'total': total,
        'present': present,
        'absent': absent,
        'rate': rate,
        'page_title': f"{staff.admin.first_name} {staff.admin.last_name} — Attendance",
    }
    return render(request, 'main_app/hod_template/admin_staff_attendance_detail.html', context)


def admin_student_attendance_list(request):
    query = request.GET.get('q', '').strip()
    students = Student.objects.select_related('admin', 'course', 'session').annotate(
        total_marked=Count('attendancereport'),
        total_present=Count('attendancereport', filter=Q(attendancereport__status=True)),
    ).order_by('admin__first_name', 'admin__last_name')

    if query:
        students = students.filter(
            Q(admin__first_name__icontains=query) | Q(admin__last_name__icontains=query)
        )

    paginator = Paginator(students, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'query': query,
        'page_title': 'Student Attendance',
    }
    return render(request, 'main_app/hod_template/admin_student_attendance_list.html', context)


def admin_student_attendance_detail(request, student_id):
    student = get_object_or_404(
        Student.objects.select_related('admin', 'course', 'session'), id=student_id
    )
    reports = AttendanceReport.objects.filter(student=student).select_related(
        'attendance', 'attendance__subject'
    ).order_by('-attendance__date')

    total = reports.count()
    present = reports.filter(status=True).count()
    absent = total - present
    rate = round((present / total) * 100, 1) if total else None

    context = {
        'student': student,
        'reports': reports,
        'total': total,
        'present': present,
        'absent': absent,
        'rate': rate,
        'page_title': f"{student.admin.first_name} {student.admin.last_name} — Attendance",
    }
    return render(request, 'main_app/hod_template/admin_student_attendance_detail.html', context)

def manage_timetable(request):
    course_id = request.GET.get('course')
    session_id = request.GET.get('session')

    slots = TimetableSlot.objects.select_related('course', 'subject', 'subject__staff', 'subject__staff__admin', 'session')
    if course_id:
        slots = slots.filter(course_id=course_id)
    if session_id:
        slots = slots.filter(session_id=session_id)

    form = TimetableSlotForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Timetable slot added")
                return redirect(reverse('manage_timetable'))
            except Exception as e:
                messages.error(request, "Could Not Add: " + str(e))
        else:
            messages.error(request, "Could Not Add: " + str(form.errors))

    DAY_NAMES = dict(TimetableSlot.DAYS)
    grouped = {}
    for slot in slots:
        grouped.setdefault(slot.day_of_week, []).append(slot)
    days_grouped = [(DAY_NAMES[d], grouped[d]) for d in sorted(grouped)]

    context = {
        'form': form,
        'days_grouped': days_grouped,
        'courses': Course.objects.all(),
        'sessions': Session.objects.all(),
        'selected_course': course_id,
        'selected_session': session_id,
        'page_title': 'Manage Timetable',
    }
    return render(request, 'main_app/hod_template/manage_timetable.html', context)


def edit_timetable_slot(request, slot_id):
    slot = get_object_or_404(TimetableSlot, id=slot_id)
    form = TimetableSlotForm(request.POST or None, instance=slot)
    context = {
        'form': form,
        'slot_id': slot_id,
        'page_title': 'Edit Timetable Slot'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Slot Updated")
                return redirect(reverse('edit_timetable_slot', args=[slot_id]))
            except Exception as e:
                messages.error(request, "Could Not Update " + str(e))
        else:
            messages.error(request, "Could Not Update: " + str(form.errors))
    return render(request, 'main_app/hod_template/edit_timetable_slot.html', context)


def delete_timetable_slot(request, slot_id):
    slot = get_object_or_404(TimetableSlot, id=slot_id)
    slot.delete()
    messages.success(request, "Timetable slot deleted successfully!")
    return redirect(reverse('manage_timetable'))

def add_department(request):
    form = DepartmentForm(request.POST or None)
    context = {'form': form, 'page_title': 'Add Department'}
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_department'))
            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Could Not Add")
    return render(request, 'main_app/hod_template/add_department.html', context)


def manage_department(request):
    departments = Department.objects.all()
    context = {'departments': departments, 'page_title': 'Manage Departments'}
    return render(request, "main_app/hod_template/manage_department.html", context)


def edit_department(request, department_id):
    instance = get_object_or_404(Department, id=department_id)
    form = DepartmentForm(request.POST or None, instance=instance)
    context = {'form': form, 'department_id': department_id, 'page_title': 'Edit Department'}
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Successfully Updated")
            except Exception:
                messages.error(request, "Could Not Update")
        else:
            messages.error(request, "Could Not Update")
    return render(request, 'main_app/hod_template/edit_department.html', context)


def delete_department(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    try:
        department.delete()
        messages.success(request, "Department deleted successfully!")
    except Exception:
        messages.error(request, "Sorry, some students/subjects are assigned to this department already.")
    return redirect(reverse('manage_department'))