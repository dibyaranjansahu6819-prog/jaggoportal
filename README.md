# Jaago Portal

Jaago Portal is a full-stack role-based portal for volunteer registration, student records, attendance, assignments, and educational operations.

![Node.js](https://img.shields.io/badge/Node.js-18%2B-339933)
![Python](https://img.shields.io/badge/Python-3.10--3.12-3776AB)
![Django](https://img.shields.io/badge/Django-6.1.1-092E20)
![React](https://img.shields.io/badge/React-19.2.0-61DAFB)
![TanStack Start](https://img.shields.io/badge/TanStack%20Start-1.168.32-FF4154)

## About

Jaago Portal manages the daily and administrative workflows of the Jaago teaching program. It connects Admin 1, Admin 2, volunteers, and student information in one Django REST and React application. Volunteers register and can record teaching or homework-checking work, while Admin 1 manages attendance. Admin 2 manages school-day status, holidays, assignments, volunteer records, XP, cautions, removals, and access requests.

## Features

### Admin 1

- Sign in with a Django username and password
- Start and end timed attendance sessions
- Record student attendance by class group
- Record assigned or substitute volunteer attendance
- View today’s attendance summary and history

### Admin 2

- Set regular class, playing day, or holiday status
- Create and update holidays
- Register assignments for teaching, checking, or invigilating
- Attach lesson or homework files and send assignment emails
- Export daily assignment reports as PNG or Excel
- View student and volunteer totals and present lists
- Manage volunteer XP, cautions, removal status, and access requests

### Volunteer

- Register with course, subject, joining year, email, WhatsApp number, and available days
- Sign in with a generated volunteer user ID and password
- View today’s assignment
- Start and end work sessions
- Record student progress or homework checking
- Select authorized special-added work
- Submit a re-access request if removed

### Student

- Register through the volunteer-facing student flow
- Receive an automatically generated roll number
- Record homework completion and earn XP
- View XP and leaderboard information

## Tech Stack

| Area | Technology | Version |
|---|---|---|
| Frontend | React, TanStack Start, TanStack Router | React `19.2.0`, TanStack Start `1.168.32`, TanStack Router `1.170.18` |
| Frontend tooling | Vite, TypeScript, Tailwind CSS | Vite `8.1.5`, TypeScript `5.8.3`, Tailwind CSS `4.2.1` |
| Frontend state/network | TanStack React Query, Axios | React Query `5.101.1`, Axios `1.20.0` |
| Backend | Django, Django REST Framework | Django `6.1.1`, DRF `3.18.1` |
| Authentication | djangorestframework-simplejwt, PyJWT | SimpleJWT `5.5.1`, PyJWT `2.14.0` |
| Database | PostgreSQL or SQLite | PostgreSQL by default; SQLite via `USE_SQLITE=true` |

## Project Structure

```text
.
├── frontend/                 # TanStack Start React application
│   ├── src/routes/           # File-based frontend routes
│   ├── src/services/api.js   # Axios client and JWT session storage
│   └── package.json          # Frontend dependencies and npm scripts
├── backend/                  # Django REST API
│   ├── config/               # Django settings and root URL configuration
│   ├── accounts/             # Authentication, profiles, demo login and seed commands
│   ├── teachers/             # Volunteer registration and work workflows
│   ├── students/             # Student registration, XP and homework
│   ├── attendance/           # Attendance sessions and records
│   ├── admin2/               # Admin 2 operations and reporting
│   ├── courses/              # Courses and subjects
│   ├── timetable/            # Installed Django app placeholder
│   ├── manage.py             # Django command entry point
│   └── requirements.txt      # Python dependencies
├── Reference/                # Product requirements PDFs
├── SETUP_GUIDE.md            # Windows and macOS/Linux setup instructions
└── ARCHITECTURE.md           # Detailed system architecture
```

## Prerequisites

- Node.js **18 or higher**
- Python **3.10, 3.11, or 3.12** recommended
- PostgreSQL if `USE_SQLITE=false` or omitted
- npm

## Quick Start

Run from the project root in two Windows PowerShell terminals.

1. Start the frontend:

```powershell
cd frontend
npm install
npm run dev
```

The frontend is available at `http://localhost:8080`.

2. Start the backend in a second terminal:

```powershell
cd backend
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Create backend/.env before starting Django.
# SECRET_KEY and database settings are required as applicable.
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```

The backend is available at `http://127.0.0.1:8000/`.

`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` is only needed if PowerShell blocks virtual-environment activation.

## Demo Accounts and Sign-in URLs

`python manage.py seed_demo_data` creates or updates these accounts:

| Role | Sign-in URL | Credentials |
|---|---|---|
| Admin 1 | `http://localhost:8080/admin1/signin` | Username: `admin1`; Password: `admin123` |
| Admin 2 | `http://localhost:8080/admin2/signin` | Username: `admin2`; Password: `admin123` |
| Volunteer | `http://localhost:8080/teacher/signin` | The seed creates a demo volunteer with a generated `VOLD###`-style user ID and an unusable password; use one-click demo sign-in when `DEMO_MODE=true` |

The seed command creates Admin 1 and Admin 2 accounts using `ADMIN1_USERNAME`/`ADMIN1_PASSWORD` and `ADMIN2_USERNAME`/`ADMIN2_PASSWORD` environment variables, falling back to `admin1`/`admin123` and `admin2`/`admin123`.

Registration pages:

- Volunteer: `http://localhost:8080/teacher/signup`
- Student: `http://localhost:8080/student/signup`

## Environment Variables

No `.env.example` file was found in the repository. The following variables are read by code:

| Variable | Purpose | Default |
|---|---|---|
| `SECRET_KEY` | Django signing secret | No default; required |
| `DEBUG` | Enable Django debug behavior | `False` |
| `DEMO_MODE` | Enable one-click demo login | `False` |
| `ALLOWED_HOSTS` | Comma-separated Django allowed hosts | Empty |
| `USE_SQLITE` | Use SQLite instead of PostgreSQL | `False` |
| `DB_NAME` | PostgreSQL database name | `jaago_portal` |
| `DB_USER` | PostgreSQL username | `postgres` |
| `DB_PASSWORD` | PostgreSQL password | Empty |
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `JAAGO_EMAIL_USER` | Gmail SMTP sender | `abhyudayiter@gmail.com` |
| `JAAGO_EMAIL_PASSWORD` | Gmail SMTP password | Empty |
| `CORS_ALLOWED_ORIGINS` | Comma-separated frontend origins | `http://localhost:8080` |
| `JAAGO_FRONTEND_RESET_URL` | Frontend password-reset base URL | `http://localhost:8080/reset-password` |
| `ADMIN1_USERNAME` | Seed/Bootstrap Admin 1 username | `admin1` in `seed_demo_data` |
| `ADMIN1_PASSWORD` | Seed/Bootstrap Admin 1 password | `admin123` in `seed_demo_data` |
| `ADMIN2_USERNAME` | Seed/Bootstrap Admin 2 username | `admin2` in `seed_demo_data` |
| `ADMIN2_PASSWORD` | Seed/Bootstrap Admin 2 password | `admin123` in `seed_demo_data` |
| `SUPERUSER_USERNAME` | Django superuser username | No default |
| `SUPERUSER_EMAIL` | Django superuser email | Empty |
| `SUPERUSER_PASSWORD` | Django superuser password | No default |
| `RESEND_API_KEY` | Resend email API key | No default found |
| `RESEND_FROM_EMAIL` | Resend sender address | No default found |
| `VITE_BACKEND_URL` | Frontend Django origin | `http://127.0.0.1:8000` |
| `VITE_API_BASE_URL` | Frontend API base URL | `${VITE_BACKEND_URL}/api` |

Create `backend/.env` manually. For the frontend, use an optional `.env` in `frontend/` if overriding the Vite variables.

## Available Scripts and Commands

### Frontend scripts

Run these in `frontend/`:

| Command | Purpose |
|---|---|
| `npm run dev` | Start the Vite development server |
| `npm run build` | Build the application |
| `npm run build:dev` | Build with development mode |
| `npm run preview` | Preview the built application |
| `npm run lint` | Run ESLint |
| `npm run format` | Format files with Prettier |

### Django commands

Run these in `backend/`:

| Command | Purpose |
|---|---|
| `python manage.py migrate` | Apply database migrations |
| `python manage.py runserver` | Start the Django development server |
| `python manage.py seed_demo_data` | Seed courses, subjects, Admin 1/2 accounts and a demo volunteer |
| `python manage.py bootstrap_admins` | Create or update Admin 1 and Admin 2 from environment variables |
| `python manage.py bootstrap_superuser` | Create or update the Django superuser from environment variables |
| `python manage.py test_real_email` | Send a real Gmail SMTP test email |

## API Overview

The REST API is mounted under `/api/`:

- `/api/auth/` — login, demo login, password reset, and current user
- `/api/courses/` — courses and subjects
- `/api/teachers/` — volunteer registration, login, dashboard, work, progress, checking and special-added work
- `/api/students/` — student registration, XP, homework and history
- `/api/attendance/` — attendance sessions, student and volunteer attendance
- `/api/admin2/` — school status, holidays, assignments, reports, XP, cautions and access requests
- `/admin/` — Django administration

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the complete endpoint and route reference.

## Troubleshooting

- **PowerShell blocks virtual-environment activation:** Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate `.\venv\Scripts\Activate.ps1`.
- **`SECRET_KEY is not configured`:** Create `backend/.env` and set `SECRET_KEY` to a local secret value.
- **Port 8080 or 8000 is already in use:** Stop the existing process, then restart `npm run dev` or `python manage.py runserver`.
- **Migration errors:** Run `python manage.py migrate` after installing dependencies and selecting a valid database.
- **PostgreSQL connection failure:** Set `DB_HOST`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD`, or set `USE_SQLITE=true` for local SQLite.
- **CORS or blocked API requests:** Keep the frontend at `http://localhost:8080` or set `CORS_ALLOWED_ORIGINS` to the actual frontend origin.
- **Demo login returns unavailable:** Set `DEMO_MODE=true` in `backend/.env`, restart Django, and run `python manage.py seed_demo_data`.
- **Email or attachment failures:** Configure `JAAGO_EMAIL_PASSWORD`, `RESEND_API_KEY`, or `RESEND_FROM_EMAIL` where the relevant delivery path requires them.

## Documentation Links

- [ARCHITECTURE.md](./ARCHITECTURE.md) — detailed architecture, routes, models, API reference, security, and deployment notes
- `CHANGES.md` — not found in the repository
