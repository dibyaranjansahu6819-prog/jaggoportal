import {
    useCallback,
    useEffect,
    useRef,
    useState,
} from "react";

import { Link, useNavigate } from "@tanstack/react-router";

import API from "../services/api";

import "./Admin1Attendance.css";
import JaagoBg from "../admin2/JaagoBg";

/* ============================================================
   This page talks to the real attendance API (attendance.urls):

     POST /attendance/session/start/    - start today's 10-min window
     GET  /attendance/session/current/  - the active session, if any
     POST /attendance/session/end/      - end it early

     GET  /attendance/students/         - today's students + status
     POST /attendance/students/save/    - { student, status }

     GET  /attendance/volunteers/current/ - today's attendance rows
                                            (auto-built from Admin 2's
                                            sent assignments, or from
                                            every active volunteer on
                                            a Playing Day)
     POST /attendance/volunteers/save/    - { volunteer, status, task }
     GET  /attendance/volunteers/         - full non-removed roster,
                                             for "+ Add Volunteer"
     POST /attendance/volunteers/add/     - { volunteer, task } (Special
                                             Added, TEACHING/CHECKING only)

   There is no backend endpoint for removing a volunteer from today's
   attendance and no photo-upload endpoint at all, so those UI pieces
   from the previous version are not wired to anything real and have
   been left out rather than pointed at endpoints that don't exist.
   The daily HOLIDAY / PLAYING_DAY / REGULAR_CLASS status itself is set
   by Admin 2 (admin2.DailySchoolStatusView) — Admin 1 only reads it.
   ============================================================ */

function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${String(minutes).padStart(2, "0")}:${String(remainingSeconds).padStart(2, "0")}`;
}

function getInitials(name) {
    if (!name) return "?";
    const parts = name.trim().split(" ");
    if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function secondsUntil(isoTime) {
    if (!isoTime) return 0;
    const diff = Math.round((new Date(isoTime).getTime() - Date.now()) / 1000);
    return Math.max(diff, 0);
}

function Admin1Attendance() {
    const navigate = useNavigate();

    const [session, setSession] = useState(null);
    const [holiday, setHoliday] = useState(null);
    const [secondsRemaining, setSecondsRemaining] = useState(0);

    const [students, setStudents] = useState([]);
    const [volunteers, setVolunteers] = useState([]);

    const [loading, setLoading] = useState(true);
    const [starting, setStarting] = useState(false);
    const [message, setMessage] = useState("");

    const [showVolunteerModal, setShowVolunteerModal] = useState(false);
    const [availableVolunteers, setAvailableVolunteers] = useState([]);
    const [selectedAvailableId, setSelectedAvailableId] = useState(null);
    const [newVolunteerRole, setNewVolunteerRole] = useState("TEACHING");

    /* ========================================================
       LOAD TODAY'S SESSION-DEPENDENT DATA
       ======================================================== */

    const loadStudentsAndVolunteers = useCallback(async () => {
        try {
            const [studentRes, volunteerRes] = await Promise.all([
                API.get("/attendance/students/"),
                API.get("/attendance/volunteers/current/"),
            ]);

            setStudents(studentRes.data.students || []);
            setVolunteers(volunteerRes.data.volunteers || []);
        } catch (error) {
            setMessage(error?.response?.data?.error || "Unable to load today's attendance data.");
        }
    }, []);

    const loadSession = useCallback(async () => {
        setLoading(true);
        setMessage("");
        try {
            const response = await API.get("/attendance/session/current/");

            if (response.data.holiday) {
                setHoliday(response.data.holiday);
                setSession(null);
            } else {
                setHoliday(null);
                setSession(response.data.session);

                if (response.data.session) {
                    setSecondsRemaining(secondsUntil(response.data.session.expires_at));
                    await loadStudentsAndVolunteers();
                } else {
                    setStudents([]);
                    setVolunteers([]);
                }
            }
        } catch (error) {
            setMessage(error?.response?.data?.error || "Unable to check today's attendance session.");
        } finally {
            setLoading(false);
        }
    }, [loadStudentsAndVolunteers]);

    useEffect(() => {
        loadSession();
    }, [loadSession]);

    /* ========================================================
       SESSION COUNTDOWN — purely a display of expires_at; the
       backend is the source of truth for when a session actually
       closes (get_active_session() closes it server-side once
       has_expired is true).
       ======================================================== */

    useEffect(() => {
        if (!session) return undefined;

        const timer = setInterval(() => {
            setSecondsRemaining((previous) => {
                if (previous <= 1) {
                    clearInterval(timer);
                    loadSession();
                    return 0;
                }
                return previous - 1;
            });
        }, 1000);

        return () => clearInterval(timer);
    }, [session, loadSession]);

    /* ========================================================
       START / END SESSION
       ======================================================== */

    const startSession = async () => {
        setStarting(true);
        setMessage("");
        try {
            const response = await API.post("/attendance/session/start/");
            setSession(response.data.session);
            setSecondsRemaining(secondsUntil(response.data.session.expires_at));
            await loadStudentsAndVolunteers();
        } catch (error) {
            setMessage(error?.response?.data?.error || "Unable to start the attendance session.");
        } finally {
            setStarting(false);
        }
    };

    const endSession = async () => {
        try {
            await API.post("/attendance/session/end/");
        } catch (error) {
            // even if this fails (e.g. already expired), reflect a closed session
        } finally {
            setSession(null);
            setStudents([]);
            setVolunteers([]);
            navigate({ to: "/" });
        }
    };

    /* ========================================================
       STUDENT ATTENDANCE
       ======================================================== */

    const setStudentStatus = async (studentId, newStatus) => {
        setStudents((previous) =>
            previous.map((student) =>
                student.student_id === studentId ? { ...student, status: newStatus } : student,
            ),
        );

        try {
            await API.post("/attendance/students/save/", {
                student: studentId,
                status: newStatus,
            });
        } catch (error) {
            setMessage(error?.response?.data?.error || "Unable to save that student's attendance.");
            loadStudentsAndVolunteers();
        }
    };

    /* ========================================================
       VOLUNTEER ATTENDANCE
       ======================================================== */

    const setVolunteerStatus = async (attendanceId, newStatus, task) => {
        setVolunteers((previous) =>
            previous.map((volunteer) =>
                volunteer.id === attendanceId ? { ...volunteer, status: newStatus } : volunteer,
            ),
        );

        try {
            await API.post("/attendance/volunteers/save/", {
                volunteer: volunteers.find((v) => v.id === attendanceId)?.volunteer,
                status: newStatus,
                task,
            });
        } catch (error) {
            setMessage(error?.response?.data?.error || "Unable to save that volunteer's attendance.");
            loadStudentsAndVolunteers();
        }
    };

    /* ========================================================
       ADD VOLUNTEER (SPECIAL ADDED)
       ======================================================== */

    const openVolunteerModal = async () => {
        setMessage("");
        try {
            const response = await API.get("/attendance/volunteers/");
            const alreadyIn = new Set(volunteers.map((v) => v.volunteer));
            const free = (response.data.volunteers || []).filter((v) => !alreadyIn.has(v.id));

            setAvailableVolunteers(free);
            setSelectedAvailableId(free[0]?.id ?? null);
            setNewVolunteerRole("TEACHING");
            setShowVolunteerModal(true);
        } catch (error) {
            setMessage(error?.response?.data?.error || "Unable to load available volunteers.");
            setAvailableVolunteers([]);
            setSelectedAvailableId(null);
            setShowVolunteerModal(true);
        }
    };

    const addVolunteer = async () => {
        const volunteer = availableVolunteers.find((item) => item.id === selectedAvailableId);
        if (!volunteer) return;

        try {
            const response = await API.post("/attendance/volunteers/add/", {
                volunteer: volunteer.id,
                task: newVolunteerRole,
            });

            setVolunteers((previous) => [...previous, response.data.attendance]);
            setAvailableVolunteers((previous) => previous.filter((item) => item.id !== volunteer.id));
            setShowVolunteerModal(false);
            setMessage(`${volunteer.name} added as Special Added.`);
        } catch (error) {
            setMessage(error?.response?.data?.error || "Unable to add volunteer.");
        }
    };

    /* ========================================================
       RENDER
       ======================================================== */

    if (loading) {
        return (
            <div className="admin-attendance-page">
                <JaagoBg />
                <p className="toolkit-loading">Loading…</p>
            </div>
        );
    }

    if (holiday) {
        return (
            <div className="admin-attendance-page">
                <JaagoBg />
                <div className="holiday-wrap">
                    <div className="holiday-card">
                        <h2>🏖 Today is a holiday</h2>
                        <p>{holiday.name} — {String(holiday.date)}</p>
                        <p>Attendance cannot be taken today.</p>
                        <button className="holiday-home-btn" type="button" onClick={() => navigate({ to: "/" })}>
                            Back to Home
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    if (!session) {
        return (
            <div className="admin-attendance-page">
                <JaagoBg />
                <div className="toolkit-header">
                    <img className="toolkit-logo" src="/jaago-attendance-logo.jpeg" alt="Jaago" />
                    <div>
                        <p className="toolkit-eyebrow">Admin 1</p>
                        <h1 className="toolkit-title">Attendance</h1>
                    </div>
                </div>
                {message && <p className="toolkit-message">{message}</p>}
                <div className="toolkit-panel">
                    <p>No attendance session is active right now. Starting one opens a 10-minute window for marking today's student and volunteer attendance.</p>
                    <button className="add-volunteer-btn" type="button" disabled={starting} onClick={startSession}>
                        {starting ? "Starting…" : "Start Attendance Session"}
                    </button>
                    <Link to="/admin1/history" style={{ marginLeft: 12 }}>View attendance history</Link>
                </div>
            </div>
        );
    }

    return (
        <div className="admin-attendance-page">
            <JaagoBg />

            <div className="toolkit-header">
                <img className="toolkit-logo" src="/jaago-attendance-logo.jpeg" alt="Jaago" />
                <div className="toolkit-brand">
                    <p className="toolkit-eyebrow">Admin 1</p>
                    <h1 className="toolkit-title">Today's Attendance</h1>
                </div>
                <div className="toolkit-session">
                    <span className="session-label">Session ends in</span>
                    <span className="session-timer">{formatTime(secondsRemaining)}</span>
                    <span className="session-date">{String(session.session_date)}</span>
                    <Link to="/admin1/history" className="end-session-btn" style={{ textDecoration: "none", display: "inline-block" }}>
                        History
                    </Link>
                    <button className="end-session-btn" type="button" onClick={endSession}>
                        End Session
                    </button>
                </div>
            </div>

            {message && <p className="toolkit-message">{message}</p>}

            <div className="attendance-toolkit-grid">
                <section className="toolkit-panel">
                    <div className="panel-header">
                        <span className="panel-kicker">Students</span>
                        <span className="panel-count">{students.filter((s) => s.status === "PRESENT").length} / {students.length} present</span>
                    </div>
                    <div className="attendance-list">
                        {students.length === 0 && <div className="list-empty">No students registered yet.</div>}
                        {students.map((student) => (
                            <div className="attendance-row" key={student.student_id}>
                                <div className="person-avatar">{getInitials(student.name)}</div>
                                <div className="person-info">
                                    <strong>{student.name}</strong>
                                    <span>{student.roll_no} · {student.class}</span>
                                </div>
                                <div className="status-buttons">
                                    <button
                                        type="button"
                                        className={`status-btn present ${student.status === "PRESENT" ? "active" : ""}`}
                                        onClick={() => setStudentStatus(student.student_id, "PRESENT")}
                                    >
                                        Present
                                    </button>
                                    <button
                                        type="button"
                                        className={`status-btn absent ${student.status === "ABSENT" ? "active" : ""}`}
                                        onClick={() => setStudentStatus(student.student_id, "ABSENT")}
                                    >
                                        Absent
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </section>

                <section className="toolkit-panel">
                    <div className="panel-header">
                        <span className="panel-kicker">Volunteers</span>
                        <span className="panel-count">{volunteers.filter((v) => v.status === "PRESENT").length} / {volunteers.length} present</span>
                    </div>
                    <div className="attendance-list">
                        {volunteers.length === 0 && (
                            <div className="list-empty">No volunteers to mark yet — assignments are set by Admin 2.</div>
                        )}
                        {volunteers.map((volunteer) => (
                            <div className="attendance-row" key={volunteer.id}>
                                <div className="person-avatar">{getInitials(volunteer.volunteer_name)}</div>
                                <div className="person-info">
                                    <strong>{volunteer.volunteer_name}</strong>
                                    <span>{volunteer.user_id} · {volunteer.subject}</span>
                                    <span className={`source-pill ${volunteer.attendance_source === "SPECIAL_ADDED" ? "source-special" : "source-assigned"}`}>
                                        {volunteer.attendance_source} · {volunteer.task}
                                    </span>
                                </div>
                                <div className="status-buttons">
                                    <button
                                        type="button"
                                        className={`status-btn present ${volunteer.status === "PRESENT" ? "active" : ""}`}
                                        onClick={() => setVolunteerStatus(volunteer.id, "PRESENT", volunteer.task)}
                                    >
                                        Present
                                    </button>
                                    <button
                                        type="button"
                                        className={`status-btn absent ${volunteer.status === "ABSENT" ? "active" : ""}`}
                                        onClick={() => setVolunteerStatus(volunteer.id, "ABSENT", volunteer.task)}
                                    >
                                        Absent
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                    <div className="panel-footer">
                        <button className="add-volunteer-btn" type="button" onClick={openVolunteerModal}>
                            + Add Volunteer (Special Added)
                        </button>
                    </div>
                </section>
            </div>

            {showVolunteerModal && (
                <div className="volunteer-modal-backdrop" role="dialog" aria-modal="true">
                    <div className="volunteer-modal">
                        <div className="modal-header">
                            <div>
                                <span>REGISTERED VOLUNTEERS</span>
                                <h2>Add Volunteer</h2>
                                <p>Select a registered volunteer to add as Special Added for today.</p>
                            </div>
                            <button type="button" className="modal-close" onClick={() => setShowVolunteerModal(false)}>×</button>
                        </div>

                        <div className="available-volunteer-list">
                            {availableVolunteers.length === 0 ? (
                                <div className="modal-empty">
                                    <strong>No volunteers available</strong>
                                    <span>Everyone registered is already in today's attendance list.</span>
                                </div>
                            ) : (
                                <div className="modal-form">
                                    <label className="modal-field">
                                        <span>Volunteer</span>
                                        <select
                                            value={selectedAvailableId ?? ""}
                                            onChange={(event) => setSelectedAvailableId(Number(event.target.value))}
                                        >
                                            {availableVolunteers.map((volunteer) => (
                                                <option key={volunteer.id} value={volunteer.id}>
                                                    {volunteer.user_id} — {volunteer.name}
                                                </option>
                                            ))}
                                        </select>
                                    </label>

                                    <fieldset className="modal-field">
                                        <legend>Task</legend>
                                        <div className="radio-group">
                                            {["TEACHING", "CHECKING"].map((role) => (
                                                <label key={role} className={newVolunteerRole === role ? "radio-option active" : "radio-option"}>
                                                    <input
                                                        type="radio"
                                                        name="volunteer-role"
                                                        checked={newVolunteerRole === role}
                                                        onChange={() => setNewVolunteerRole(role)}
                                                    />
                                                    {role === "TEACHING" ? "Teaching" : "Checking"}
                                                </label>
                                            ))}
                                        </div>
                                    </fieldset>

                                    <button
                                        type="button"
                                        className="modal-add-btn"
                                        onClick={addVolunteer}
                                        disabled={selectedAvailableId === null}
                                    >
                                        Add
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default Admin1Attendance;
