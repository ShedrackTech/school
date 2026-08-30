from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect


class LoginCheckMiddleWare(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        modulename = view_func.__module__
        user = request.user
        
        if user.is_authenticated:
            if user.user_type == '1':
                if modulename == 'main_app.student_views':
                    return redirect('admin_home')
            elif user.user_type == '2':
                if modulename == 'main_app.student_views' or modulename == 'main_app.hod_views':
                    return redirect('staff_home')
            elif user.user_type == '3':
                if modulename == 'main_app.hod_views' or modulename == 'main_app.staff_views':
                    return redirect('student_home')
            else:
                return redirect('/')
        else:
            # Allow these paths without login
            if request.path == '/':
                pass
            elif request.path.startswith('/admin'):
                pass
            elif modulename == 'django.contrib.auth.views':
                pass
            elif request.path == '/doLogin/':
                pass
            else:
                return redirect('/')
        
        return None