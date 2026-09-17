# 🎓 Shedy School Management System

A full-featured school management system built with Django, providing separate portals for admins (HODs), staff, and students to manage attendance, results, timetables, and more.

---

## ✨ Features

- 👥 Three role-based portals: **Admin (HOD)**, **Staff**, and **Student**
- 📋 Attendance tracking — staff take/update attendance per subject and session; students view their own records with live filtering
- 📊 Student results — test/exam score entry with automatic grade bands (A+/A/B/F) and pass/fail status
- 🗓️ Timetable management — admin builds the timetable; staff and students each view their own schedule
- 🏫 Course/department structure with subject filtering by department
- 📝 Leave applications for both staff and students, with admin review
- 💬 Feedback submission for staff and students
- 🔔 Push notifications via Firebase Cloud Messaging (FCM)
- 🙋 Profile change requests requiring admin approval (instead of direct self-editing)
- 🔐 reCAPTCHA-protected authentication
- 🎨 Custom themed UI per role (admin/staff/student), built with a shared CSS design system and Lucide icons

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Django 6 |
| Frontend | HTML5, CSS3 (custom design system), JavaScript |
| Database | SQLite (development) |
| Notifications | Firebase Cloud Messaging |
| Security | Google reCAPTCHA |
| Environment | python-dotenv |
| Version Control | Git & GitHub |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Git
- A Firebase project (for push notifications)
- reCAPTCHA site/secret keys

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ShedrackTech/school.git
   cd school
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Mac/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   Create a `.env` file in the project root:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True

   DJANGO_SUPERUSER_EMAIL=your@email.com
   DJANGO_SUPERUSER_PASSWORD=your-password

   FIREBASE_API_KEY=your-firebase-api-key
   FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
   FIREBASE_PROJECT_ID=your-project-id
   FIREBASE_STORAGE_BUCKET=your-project.firebasestorage.app
   FIREBASE_MESSAGING_SENDER_ID=your-sender-id
   FIREBASE_APP_ID=your-app-id
   FIREBASE_SERVICE_ACCOUNT_PATH=firebase-service-account.json

   RECAPTCHA_SITE_KEY=your-recaptcha-site-key
   RECAPTCHA_SECRET_KEY=your-recaptcha-secret-key
   ```

5. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Visit the app**
   - Site: http://127.0.0.1:8000/
   - Admin: http://127.0.0.1:8000/admin/

---

## 📁 Project Structure

```
school/
├── main_app/                      # Main app
│   ├── hod_views.py                # Admin (HOD) views
│   ├── staff_views.py               # Staff views
│   ├── student_views.py             # Student views
│   ├── models.py
│   ├── forms.py
│   ├── middlewares.py               # Login/role-based access control
│   ├── migrations/
│   ├── static/main_app/             # CSS, JS, icons
│   └── templates/main_app/
│       ├── hod_template/            # Admin portal templates
│       ├── staff_template/          # Staff portal templates
│       └── student_template/        # Student portal templates
├── student_management_system/       # Project settings
│   ├── settings.py
│   └── urls.py
├── manage.py
├── .env                              # Environment variables (not committed)
├── .gitignore
└── requirements.txt
```

---

## 👥 Roles & Portals

### Admin (HOD)
Full oversight across the system — manages courses, departments, subjects, staff and student accounts, timetables, and approves pending profile change requests.

### Staff
Takes and updates attendance for assigned subjects, enters and edits student results, views their timetable, and can apply for leave or submit feedback.

### Student
Views their own attendance, results, and timetable, applies for leave, submits feedback, and requests profile changes (subject to admin approval).

---

## 🔒 Environment Variables

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` for development, `False` for production |
| `DJANGO_SUPERUSER_EMAIL` | Email used when auto-creating a superuser |
| `DJANGO_SUPERUSER_PASSWORD` | Password used when auto-creating a superuser |
| `FIREBASE_API_KEY` | Firebase Web API key |
| `FIREBASE_AUTH_DOMAIN` | Firebase auth domain |
| `FIREBASE_PROJECT_ID` | Firebase project ID |
| `FIREBASE_STORAGE_BUCKET` | Firebase storage bucket |
| `FIREBASE_MESSAGING_SENDER_ID` | Firebase Cloud Messaging sender ID |
| `FIREBASE_APP_ID` | Firebase app ID |
| `FIREBASE_SERVICE_ACCOUNT_PATH` | Path to the Firebase service account JSON |
| `RECAPTCHA_SITE_KEY` | Google reCAPTCHA site key |
| `RECAPTCHA_SECRET_KEY` | Google reCAPTCHA secret key |

---

## 👨‍💻 Author

**Shedrack Ugwu**
GitHub: [@ShedrackTech](https://github.com/ShedrackTech)

---

## 📄 License

This project is for educational and portfolio purposes.
