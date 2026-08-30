import json

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import HttpResponseRedirect, get_object_or_404, redirect, render
from django.urls import reverse

from .forms import *
from .models import *


def staff_home(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff=staff)
    subject_count = subjects.count()
    student_count = Student.objects.filter(course=staff.course).count()
    results_count = StudentResult.objects.filter(subject__in=subjects).count()
    attendance_count = Attendance.objects.filter(subject__in=subjects).count()

    # attach a per-subject student count so the dashboard table can show it
    subject_rows = []
    for s in subjects:
        s.student_count = Student.objects.filter(course=s.course).count()
        subject_rows.append(s)

    context = {
        'portal_name': 'Staff',
        'page_title': 'Staff Panel',
        'subject_count': subject_count,
        'student_count': student_count,
        'results_count': results_count,
        'attendance_count': attendance_count,
        'subjects': subject_rows,
    }
    return render(request, 'main_app/staff_template/staff_home.html', context)


def staff_take_attendance(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff_id=staff)
    sessions = Session.objects.all()
    context = {
        'subjects': subjects,
        'sessions': sessions,
        'page_title': 'Take Attendance'
    }

    return render(request, 'main_app/staff_template/staff_take_attendance.html', context)


def get_students(request):
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    try:
        staff = get_object_or_404(Staff, admin=request.user)
        subject = get_object_or_404(Subject, id=subject_id)
        if subject.staff != staff:  # ownership check
            return JsonResponse({'error': 'Not permitted'}, status=403)
        session = get_object_or_404(Session, id=session_id)
        students = Student.objects.filter(
            course_id=subject.course.id, session=session)
        student_data = []
        for student in students:
            data = {
                "id": student.id,
                "name": student.admin.last_name + " " + student.admin.first_name
            }
            student_data.append(data)
        return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def save_attendance(request):
    student_data = request.POST.get('student_ids')
    date = request.POST.get('date')
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    students = json.loads(student_data)
    try:
        staff = get_object_or_404(Staff, admin=request.user)
        session = get_object_or_404(Session, id=session_id)
        subject = get_object_or_404(Subject, id=subject_id)
        if subject.staff != staff:  # ownership check
            return HttpResponse("False")

        # Check if an attendance object already exists for the given date and session
        attendance, created = Attendance.objects.get_or_create(
            session=session, subject=subject, date=date)

        for student_dict in students:
            student = get_object_or_404(Student, id=student_dict.get('id'))
            # update_or_create so re-submitting corrected statuses works
            AttendanceReport.objects.update_or_create(
                student=student,
                attendance=attendance,
                defaults={'status': student_dict.get('status')}
            )
    except Exception:
        return HttpResponse("False")

    return HttpResponse("OK")


def staff_update_attendance(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff_id=staff)
    sessions = Session.objects.all()
    context = {
        'subjects': subjects,
        'sessions': sessions,
        'page_title': 'Update Attendance'
    }

    return render(request, 'main_app/staff_template/staff_update_attendance.html', context)


def get_student_attendance(request):
    subject_id = request.GET.get('subject_id')
    session_id = request.GET.get('session_id')
    date = request.GET.get('date')
    try:
        staff = get_object_or_404(Staff, admin=request.user)
        subject = get_object_or_404(Subject, id=subject_id)
        if subject.staff != staff:  # ownership check
            return JsonResponse({'error': 'Not permitted'}, status=403)
        session = get_object_or_404(Session, id=session_id)
        attendance = Attendance.objects.filter(
            subject=subject, session=session, date=date).first()
        student_data = []
        if attendance:
            students = Student.objects.filter(
                course_id=subject.course.id, session=session)
            for student in students:
                report = AttendanceReport.objects.filter(
                    student=student, attendance=attendance).first()
                student_data.append({
                    "id": student.id,
                    "name": student.admin.last_name + " " + student.admin.first_name,
                    "email": student.admin.email,
                    "status": bool(report.status) if report else False,
                })
        return JsonResponse({"students": student_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def update_attendance(request):
    try:
        staff = get_object_or_404(Staff, admin=request.user)
        payload = json.loads(request.body)
        subject = get_object_or_404(Subject, id=payload.get('subject_id'))
        if subject.staff != staff:  # ownership check
            return JsonResponse({'status': 'error', 'message': 'Not permitted'})
        session = get_object_or_404(Session, id=payload.get('session_id'))
        date = payload.get('date')
        attendance, _ = Attendance.objects.get_or_create(
            subject=subject, session=session, date=date)
        for item in payload.get('attendance', []):
            student = get_object_or_404(Student, id=item.get('student_id'))
            status = item.get('status') in (True, 'true', 1, '1')
            AttendanceReport.objects.update_or_create(
                student=student, attendance=attendance,
                defaults={'status': status})
        return JsonResponse({'status': 'success', 'message': 'Attendance updated successfully'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def staff_apply_leave(request):
    form = LeaveReportStaffForm(request.POST or None)
    staff = get_object_or_404(Staff, admin_id=request.user.id)
    context = {
        'form': form,
        'leave_history': LeaveReportStaff.objects.filter(staff=staff),
        'page_title': 'Apply for Leave'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.staff = staff
                obj.save()
                messages.success(
                    request, "Application for leave has been submitted for review")
                return redirect(reverse('staff_apply_leave'))
            except Exception:
                messages.error(request, "Could not apply!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "main_app/staff_template/staff_apply_leave.html", context)


def staff_feedback(request):
    form = FeedbackStaffForm(request.POST or None)
    staff = get_object_or_404(Staff, admin_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackStaff.objects.filter(staff=staff),
        'page_title': 'Add Feedback'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.staff = staff
                obj.save()
                messages.success(request, "Feedback submitted for review")
                return redirect(reverse('staff_feedback'))
            except Exception:
                messages.error(request, "Could not Submit!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "main_app/staff_template/staff_feedback.html", context)


def staff_view_profile(request):
    staff = get_object_or_404(Staff, admin=request.user)
    admin = staff.admin

    pending = ProfileChangeRequest.objects.filter(user=admin, status='pending').first()

    context = {
        'page_title': 'View/Edit Profile',
        'pending': pending,
    }

    if request.method == 'POST':
        if pending:
            messages.error(request, "You already have a pending change request awaiting admin approval.")
            return redirect(reverse('staff_view_profile'))

        form = ProfileChangeRequestForm(request.POST, request.FILES)
        if form.is_valid():
            req = form.save(commit=False)
            req.user = admin
            req.status = 'pending'
            req.save()
            messages.success(request, "Your changes have been submitted for admin approval.")
            return redirect(reverse('staff_view_profile'))
        else:
            messages.error(request, "Please correct the errors below.")
            context['form'] = form
            return render(request, "main_app/staff_template/staff_view_profile.html", context)

    context['form'] = ProfileChangeRequestForm()
    return render(request, "main_app/staff_template/staff_view_profile.html", context)


def staff_fcmtoken(request):
    token = request.POST.get('token')
    try:
        staff_user = get_object_or_404(CustomUser, id=request.user.id)
        staff_user.fcm_token = token
        staff_user.save()
        return HttpResponse("True")
    except Exception:
        return HttpResponse("False")


def staff_view_notification(request):
    staff = get_object_or_404(Staff, admin=request.user)
    notifications = NotificationStaff.objects.filter(staff=staff)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "main_app/staff_template/staff_view_notification.html", context)


def staff_add_result(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff=staff)
    sessions = Session.objects.all()
    context = {
        'page_title': 'Result Upload',
        'subjects': subjects,
        'sessions': sessions
    }
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student_list')
            subject_id = request.POST.get('subject')
            test = request.POST.get('test')
            exam = request.POST.get('exam')
            student = get_object_or_404(Student, id=student_id)
            subject = get_object_or_404(Subject, id=subject_id)
            if subject.staff != staff:  # ownership check
                raise Exception("You are not assigned to this subject")
            try:
                data = StudentResult.objects.get(
                    student=student, subject=subject)
                data.exam = exam
                data.test = test
                data.save()
                messages.success(request, "Scores Updated")
            except Exception:
                result = StudentResult(student=student, subject=subject, test=test, exam=exam)
                result.save()
                messages.success(request, "Scores Saved")
        except Exception as e:
            messages.warning(request, "Error Occured While Processing Form: " + str(e))
    return render(request, "main_app/staff_template/staff_add_result.html", context)


def fetch_student_result(request):
    try:
        staff = get_object_or_404(Staff, admin=request.user)
        subject_id = request.POST.get('subject')
        student_id = request.POST.get('student')
        student = get_object_or_404(Student, id=student_id)
        subject = get_object_or_404(Subject, id=subject_id)
        if subject.staff != staff:  # ownership check
            return HttpResponse('False')
        result = StudentResult.objects.get(student=student, subject=subject)
        result_data = {
            'exam': result.exam,
            'test': result.test
        }
        return HttpResponse(json.dumps(result_data))
    except Exception:
        return HttpResponse('False')