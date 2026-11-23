# Jaago Portal — Setup & Run Guide

Follow these steps to run both the Frontend and Backend on your local machine using VS Code.

---

## Prerequisites
Make sure you have installed:
1. **Node.js** (v18 or higher) — [Download](https://nodejs.org/)
2. **Python** (3.10, 3.11, or 3.12 recommended) — [Download](https://www.python.org/)

---

## Step 1: Open Project in VS Code
1. Extract the zip file to your preferred folder.
2. Open VS Code, go to **File -> Open Folder...**, and select the extracted folder (`jaggoportal`).

---

## Step 2: Open Split Terminals in VS Code
1. Open the terminal panel by pressing ``Ctrl + ` `` (or **Terminal -> New Terminal**).
2. Click the **Split Terminal** icon (or press `Ctrl + Shift + 5`) so you have 2 terminals side by side:
   - In **Terminal 1** (Left): Navigate to frontend
     ```powershell
     cd frontend
     ```
   - In **Terminal 2** (Right): Navigate to backend
     ```powershell
     cd backend
     ```

---

## Step 3: Terminal 1 — Frontend Setup
In the **frontend** terminal, run:

```powershell
# 1. Install frontend packages
npm install

# 2. Start the Vite dev server
npm run dev
```

The frontend will start at **`http://localhost:8080`**.

---

## Step 4: Terminal 2 — Backend Setup
In the **backend** terminal, run:

### Windows (PowerShell):
```powershell
# 1. Create a virtual environment
python -m venv venv

# 2. Activate the virtual environment
# (If you get a script execution policy error, first run: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass)
.\venv\Scripts\activate

# 3. Install backend dependencies
pip install -r requirements.txt

# 4. If .env does not exist, copy from .env.example:
# Copy-Item .env.example .env

# 5. Apply database migrations
python manage.py migrate

# 6. Seed demo data (courses, subjects, admins, demo volunteer)
python manage.py seed_demo_data

# 7. Start the Django backend server
python manage.py runserver
```

### Mac / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```

The backend server will start at **`http://127.0.0.1:8000/`**.

---

## Step 5: Open Browser & Test Login
Open **`http://localhost:8080`** in your browser. Both servers must remain running.

### Available Logins & Roles:

| Role | Sign-in URL | Credentials | Quick One-Click Demo |
| :--- | :--- | :--- | :--- |
| **Admin 1** | `http://localhost:8080/admin1/signin` | **Username:** `admin1`<br>**Password:** `admin123` | Click **"Sign in as Demo Admin 1"** |
| **Admin 2** | `http://localhost:8080/admin2/signin` | **Username:** `admin2`<br>**Password:** `admin123` | Click **"Sign in as Demo Admin 2"** |
| **Volunteer** | `http://localhost:8080/teacher/signin` | **User ID:** `VOLD001`<br>*(or register a new one)* | Click **"Sign in as Demo Volunteer"** |
| **Teacher Signup** | `http://localhost:8080/teacher/signup` | Register new volunteers | — |
| **Student Signup** | `http://localhost:8080/student/signup` | Register new students | — |
