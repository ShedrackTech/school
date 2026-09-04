import json
import math
from datetime import datetime

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404, redirect, render)
from django.urls import reverse
from django.db.models import Q

from .forms import *
from .models import *


def student_home(request):
    student = get_object_or_404(Student, admin=request.user)
    subjects = Subject.objects.filter(course=student.course).filter(
        Q(department__isnull=True) | Q(department=student.department)
    )
    subject_count = subjects.count()

    # Attendance percentage
    total_attendance = AttendanceReport.objects.filter(student=student).count()
    total_present = AttendanceReport.objects.filter(student=student, status=True).count()
    if total_attendance == 0:
        attendance_pct = 0
    else:
        attendance_pct = round((total_present / total_attendance) * 100)

    # Results: totals and grades computed here (safer than template math)
    results = []
    overall_marks = []
    for r in StudentResult.objects.filter(student=student).select_related('subject'):
        test = float(r.test or 0)
        exam = float(r.exam or 0)
        total = test + exam
        overall_marks.append(total)
        if total >= 80:
            grade = 'A+'
        elif total >= 60:
            grade = 'A'
        elif total >= 40:
            grade = 'B'
        else:
            grade = 'F'
        results.append({
            'subject': r.subject.name,
            'test': test,
            'exam': exam,
            'total': total,
            'grade': grade,
            'passed': total >= 40,
        })

    if overall_marks:
        overall_percentage = round(sum(overall_marks) / len(overall_marks))
    else:
        overall_percentage = 0

    context = {
        'portal_name': 'Student',
        'page_title': 'Student Homepage',
        'subject_count': subject_count,
        'overall_percentage': overall_percentage,
        'results_published': len(results),
        'attendance_pct': attendance_pct,
        'results': results,
    }
    return render(request, 'main_app/student_template/student_home.html', context)


def student_view_attendance(request):
    student = get_object_or_404(Student, admin=request.user)

    # New: AJAX GET path used by student_view_attendance.html's live filter
    if request.method == 'GET' and request.GET.get('ajax') == '1':
        try:
            subject_id = request.GET.get('subject_id')
            reports = AttendanceReport.objects.filter(
                student=student
            ).select_related('attendance', 'attendance__subject')
            if subject_id:
                reports = reports.filter(attendance__subject_id=subject_id)
            json_data = [
                {
                    "date": str(report.attendance.date),
                    "subject": report.attendance.subject.name,
                    "status": report.status,
                }
                for report in reports.order_by('-attendance__date')
            ]
            return JsonResponse(json_data, safe=False)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    # Original page load
    if request.method != 'POST':
        course = get_object_or_404(Course, id=student.course.id)
        context = {
            'subjects': Subject.objects.filter(course=course).filter(
                Q(department__isnull=True) | Q(department=student.department)
            ),
            'page_title': 'View Attendance'
        }
        return render(request, 'main_app/student_template/student_view_attendance.html', context)
    else:
        # Original POST/date-range path, kept as-is in case anything else calls it
        subject_id = request.POST.get('subject')
        start = request.POST.get('start_date')
        end = request.POST.get('end_date')
        try:
            subject = get_object_or_404(Subject, id=subject_id)
            start_date = datetime.strptime(start, "%Y-%m-%d")
            end_date = datetime.strptime(end, "%Y-%m-%d")
            attendance = Attendance.objects.filter(
                date__range=(start_date, end_date), subject=subject)
            attendance_reports = AttendanceReport.objects.filter(
                attendance__in=attendance, student=student)
            json_data = []
            for report in attendance_reports:
                data = {
                    "date": str(report.attendance.date),
                    "status": report.status
                }
                json_data.append(data)
            return JsonResponse(json.dumps(json_data), safe=False)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


def student_apply_leave(request):
    form = LeaveReportStudentForm(request.POST or None)
    student = get_object_or_404(Student, admin_id=request.user.id)
    context = {
        'form': form,
        'leave_history': LeaveReportStudent.objects.filter(student=student),
        'page_title': 'Apply for leave'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.student = student
                obj.save()
                messages.success(
                    request, "Application for leave has been submitted for review")
                return redirect(reverse('student_apply_leave'))
            except Exception:
                messages.error(request, "Could not submit")
        else:
            messages.error(request, "Form has errors: " + str(form.errors))
    return render(request, "main_app/student_template/student_apply_leave.html", context)


def student_feedback(request):
    form = FeedbackStudentForm(request.POST or None)
    student = get_object_or_404(Student, admin_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackStudent.objects.filter(student=student),
        'page_title': 'Student Feedback'

    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.student = student
                obj.save()
                messages.success(
                    request, "Feedback submitted for review")
                return redirect(reverse('student_feedback'))
            except Exception:
                messages.error(request, "Could not Submit!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "main_app/student_template/student_feedback.html", context)


def student_view_profile(request):
    student = get_object_or_404(Student, admin=request.user)
    admin = student.admin

    pending = ProfileChangeRequest.objects.filter(user=admin, status='pending').first()

    context = {
        'page_title': 'View/Edit Profile',
        'pending': pending,
        'student': student,
    }
    if request.method == 'POST':
        if pending:
            messages.error(request, "You already have a pending change request awaiting admin approval.")
            return redirect(reverse('student_view_profile'))

        form = ProfileChangeRequestForm(request.POST, request.FILES)
        if form.is_valid():
            req = form.save(commit=False)
            req.user = admin
            req.status = 'pending'
            req.save()
            messages.success(request, "Your changes have been submitted for admin approval.")
            return redirect(reverse('student_view_profile'))
        else:
            messages.error(request, "Please correct the errors below.")
            context['form'] = form
            return render(request, "main_app/student_template/student_view_profile.html", context)

    context['form'] = ProfileChangeRequestForm()
    return render(request, "main_app/student_template/student_view_profile.html", context)


def student_fcmtoken(request):
    token = request.POST.get('token')
    student_user = get_object_or_404(CustomUser, id=request.user.id)
    try:
        student_user.fcm_token = token
        student_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def student_view_notification(request):
    student = get_object_or_404(Student, admin=request.user)
    notifications = NotificationStudent.objects.filter(student=student)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "main_app/student_template/student_view_notification.html", context)


def student_view_result(request):
    student = get_object_or_404(Student, admin=request.user)
    results = StudentResult.objects.filter(student=student)
    context = {
        'results': results,
        'page_title': "View Results"
    }
    return render(request, "main_app/student_template/student_view_result.html", context)

def student_timetable(request):
    student = get_object_or_404(Student, admin=request.user)
    slots = TimetableSlot.objects.filter(course=student.course).filter(
        Q(subject__department__isnull=True) | Q(subject__department=student.department)
    ).select_related('subject', 'subject__staff', 'subject__staff__admin', 'session')

    DAY_NAMES = dict(TimetableSlot.DAYS)
    grouped = {}
    for slot in slots:
        grouped.setdefault(slot.day_of_week, []).append(slot)
    days_grouped = [(DAY_NAMES[d], grouped[d]) for d in sorted(grouped)]

    context = {
        'days_grouped': days_grouped,
        'page_title': 'My Timetable',
    }
    return render(request, 'main_app/student_template/student_timetable.html', context)