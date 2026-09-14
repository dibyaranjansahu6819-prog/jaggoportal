import {
    useEffect,
    useRef,
    useState,
} from "react";

import {
    useNavigate,
} from "react-router-dom";

import API, {
    uploadAttendancePhoto,
    getMediaUrl,
} from "../services/api";

import "./Admin1Attendance.css";


const SESSION_SECONDS = 10 * 60;


/* ============================================================
   TODAY
   ============================================================ */

function getToday() {

    const today = new Date();

    const year =
        today.getFullYear();

    const month =
        String(
            today.getMonth() + 1
        ).padStart(2, "0");

    const day =
        String(
            today.getDate()
        ).padStart(2, "0");

    return `${year}-${month}-${day}`;
}


/* ============================================================
   FORMAT TIMER
   ============================================================ */

function formatTime(seconds) {

    const minutes =
        Math.floor(seconds / 60);

    const remainingSeconds =
        seconds % 60;

    return (
        `${String(minutes).padStart(2, "0")}:` +
        `${String(remainingSeconds).padStart(2, "0")}`
    );
}


/* ============================================================
   INITIALS
   ============================================================ */

function getInitials(name) {

    if (!name) {
        return "?";
    }

    const parts =
        name.trim().split(" ");

    if (parts.length === 1) {

        return parts[0]
            .substring(0, 2)
            .toUpperCase();

    }

    return (
        parts[0][0] +
        parts[parts.length - 1][0]
    ).toUpperCase();
}


/* ============================================================
   COMPONENT
   ============================================================ */

function Admin1Attendance() {

    const navigate = useNavigate();


    /* ========================================================
       PHOTO INPUTS
       ======================================================== */

    const studentPhotoInput =
        useRef(null);

    const volunteerPhotoInput =
        useRef(null);


    /* ========================================================
       SESSION
       ======================================================== */

    const [
        secondsRemaining,
        setSecondsRemaining,
    ] = useState(
        SESSION_SECONDS
    );


    /* ========================================================
       DATE
       ======================================================== */

    const [
        selectedDate,
        setSelectedDate,
    ] = useState(
        getToday()
    );


    /* ========================================================
       ATTENDANCE DATA
       ======================================================== */

    const [
        students,
        setStudents,
    ] = useState([]);

    const [
        volunteers,
        setVolunteers,
    ] = useState([]);

    const [
        availableVolunteers,
        setAvailableVolunteers,
    ] = useState([]);


    /* ========================================================
       PHOTOS
       ======================================================== */

    const [
        studentPhotos,
        setStudentPhotos,
    ] = useState([]);

    const [
        volunteerPhotos,
        setVolunteerPhotos,
    ] = useState([]);


    /* ========================================================
       UI
       ======================================================== */

    const [
        loading,
        setLoading,
    ] = useState(true);

    const [
        saving,
        setSaving,
    ] = useState(false);

    const [
        message,
        setMessage,
    ] = useState("");

    const [
        showVolunteerModal,
        setShowVolunteerModal,
    ] = useState(false);

    const [
        uploadingStudentPhoto,
        setUploadingStudentPhoto,
    ] = useState(false);

    const [
        uploadingVolunteerPhoto,
        setUploadingVolunteerPhoto,
    ] = useState(false);


    /* ========================================================
       LOAD ATTENDANCE
       ======================================================== */

    const loadAttendance = async () => {

        try {

            setLoading(true);

            const response =
                await API.get(
                    "/attendance/",
                    {
                        params: {
                            date: selectedDate,
                        },
                    }
                );


            setStudents(
                response.data.students || []
            );


            setVolunteers(
                response.data.volunteers || []
            );


            /*
             * Django may return:
             *
             * student_photos
             * volunteer_photos
             *
             * If they are not returned, use [].
             */

            setStudentPhotos(
                response.data.student_photos || []
            );


            setVolunteerPhotos(
                response.data.volunteer_photos || []
            );


        } catch (error) {

            console.error(
                "Attendance loading error:",
                error
            );

            setMessage(
                "Unable to load attendance data."
            );

        } finally {

            setLoading(false);

        }

    };


    /* ========================================================
       LOAD WHEN DATE CHANGES
       ======================================================== */

    useEffect(() => {

        loadAttendance();

    }, [selectedDate]);


    /* ========================================================
       10 MINUTE SESSION TIMER
       ======================================================== */

    useEffect(() => {

        const timer =
            setInterval(() => {

                setSecondsRemaining(
                    previous => {

                        if (previous <= 1) {

                            clearInterval(timer);

                            navigate("/");

                            return 0;

                        }

                        return previous - 1;

                    }
                );

            }, 1000);


        return () => {

            clearInterval(timer);

        };

    }, [navigate]);


    /* ========================================================
       END SESSION
       ======================================================== */

    const endSession = () => {

        navigate("/");

    };


    /* ========================================================
       STUDENT STATUS
       ======================================================== */

    const updateStudentStatus = (
        studentId,
        newStatus
    ) => {

        setStudents(
            previous =>
                previous.map(
                    student =>
                        student.student === studentId
                            ? {
                                ...student,
                                status:
                                    newStatus,
                            }
                            : student
                )
        );

    };


    /* ========================================================
       SAVE STUDENT ATTENDANCE
       ======================================================== */

    const saveStudentAttendance =
        async () => {

            try {

                setSaving(true);

                setMessage("");


                await Promise.all(

                    students.map(
                        student =>
                            API.post(
                                "/attendance/students/save/",
                                {
                                    student:
                                        student.student,

                                    date:
                                        selectedDate,

                                    status:
                                        student.status,
                                }
                            )
                    )

                );


                setMessage(
                    "Student attendance saved successfully."
                );


            } catch (error) {

                console.error(
                    "Student attendance save error:",
                    error
                );

                setMessage(
                    error.response?.data?.error ||
                    "Unable to save student attendance."
                );

            } finally {

                setSaving(false);

            }

        };


    /* ========================================================
       VOLUNTEER STATUS
       ======================================================== */

    const updateVolunteerStatus =
        async (
            attendanceId,
            newStatus
        ) => {

            try {

                await API.post(
                    "/attendance/volunteers/save/",
                    {
                        id:
                            attendanceId,

                        status:
                            newStatus,
                    }
                );


                setVolunteers(
                    previous =>
                        previous.map(
                            volunteer =>
                                volunteer.id === attendanceId
                                    ? {
                                        ...volunteer,
                                        status:
                                            newStatus,
                                    }
                                    : volunteer
                        )
                );


                setMessage(
                    "Volunteer attendance updated."
                );


            } catch (error) {

                console.error(
                    "Volunteer attendance error:",
                    error
                );

                setMessage(
                    error.response?.data?.error ||
                    "Unable to update volunteer attendance."
                );

            }

        };


    /* ========================================================
       AVAILABLE VOLUNTEERS
       ======================================================== */

    const openVolunteerModal =
        async () => {

            try {

                const response =
                    await API.get(
                        "/attendance/volunteers/available/",
                        {
                            params: {
                                date:
                                    selectedDate,
                            },
                        }
                    );


                setAvailableVolunteers(
                    response.data || []
                );


                setShowVolunteerModal(true);


            } catch (error) {

                console.error(
                    "Available volunteer error:",
                    error
                );

                setMessage(
                    error.response?.data?.error ||
                    "Unable to load available volunteers."
                );

            }

        };


    /* ========================================================
       ADD VOLUNTEER
       ======================================================== */

    const addVolunteer =
        async (
            volunteer
        ) => {

            try {

                const response =
                    await API.post(
                        "/attendance/volunteers/add/",
                        {
                            volunteer:
                                volunteer.id,

                            date:
                                selectedDate,
                        }
                    );


                setVolunteers(
                    previous => [
                        ...previous,
                        {
                            id:
                                response.data.id,

                            volunteer:
                                response.data.volunteer,

                            name:
                                response.data.name,

                            status:
                                response.data.status,
                        },
                    ]
                );


                setAvailableVolunteers(
                    previous =>
                        previous.filter(
                            item =>
                                item.id !==
                                volunteer.id
                        )
                );


                setShowVolunteerModal(false);


                setMessage(
                    `${volunteer.name} added to today's volunteer attendance.`
                );


            } catch (error) {

                console.error(
                    "Add volunteer error:",
                    error
                );

                setMessage(
                    error.response?.data?.error ||
                    "Unable to add volunteer."
                );

            }

        };


    /* ========================================================
       DELETE VOLUNTEER
       ======================================================== */

    const deleteVolunteer =
        async (
            attendanceId
        ) => {

            try {

                await API.delete(
                    `/attendance/volunteers/${attendanceId}/delete/`
                );


                setVolunteers(
                    previous =>
                        previous.filter(
                            volunteer =>
                                volunteer.id !==
                                attendanceId
                        )
                );


                setMessage(
                    "Volunteer removed from today's attendance."
                );


            } catch (error) {

                console.error(
                    "Delete volunteer error:",
                    error
                );

                setMessage(
                    error.response?.data?.error ||
                    "Unable to remove volunteer."
                );

            }

        };


    /* ========================================================
       PHOTO UPLOAD
       ======================================================== */

    const handlePhotoUpload =
        async (
            event,
            photoType
        ) => {

            const file =
                event.target.files?.[0];


            if (!file) {

                return;

            }


            /* ------------------------------------------------
               CHECK IMAGE
               ------------------------------------------------ */

            if (
                !file.type.startsWith(
                    "image/"
                )
            ) {

                setMessage(
                    "Please select an image file."
                );

                event.target.value = "";

                return;

            }


            /* ------------------------------------------------
               CHECK SIZE
               ------------------------------------------------ */

            if (
                file.size >
                10 * 1024 * 1024
            ) {

                setMessage(
                    "Photo must be smaller than 10 MB."
                );

                event.target.value = "";

                return;

            }


            try {

                if (
                    photoType ===
                    "STUDENT"
                ) {

                    setUploadingStudentPhoto(
                        true
                    );

                } else {

                    setUploadingVolunteerPhoto(
                        true
                    );

                }


                const response =
                    await uploadAttendancePhoto(
                        file,
                        photoType,
                        selectedDate
                    );


                /*
                 * Make sure the returned photo
                 * has a usable URL.
                 */

                const uploadedPhoto = {
                    ...response.data,

                    url:
                        getMediaUrl(
                            response.data.url ||
                            response.data.photo
                        ),
                };


                if (
                    photoType ===
                    "STUDENT"
                ) {

                    setStudentPhotos(
                        previous => [
                            uploadedPhoto,
                            ...previous,
                        ]
                    );

                } else {

                    setVolunteerPhotos(
                        previous => [
                            uploadedPhoto,
                            ...previous,
                        ]
                    );

                }


                setMessage(
                    "Photo uploaded successfully."
                );


            } catch (error) {

                console.error(
                    "Photo upload error:",
                    error
                );

                console.error(
                    "Photo upload response:",
                    error.response?.data
                );


                setMessage(
                    error.response?.data?.error ||
                    "Unable to upload photo."
                );

            } finally {

                setUploadingStudentPhoto(
                    false
                );

                setUploadingVolunteerPhoto(
                    false
                );

                event.target.value = "";

            }

        };


    /* ========================================================
       DELETE PHOTO
       ======================================================== */

    const deletePhoto =
        async (
            photoId,
            photoType
        ) => {

            const shouldDelete =
                window.confirm(
                    "Delete this photo?"
                );


            if (!shouldDelete) {

                return;

            }


            try {

                await API.delete(
                    `/attendance/photos/${photoId}/delete/`
                );


                if (
                    photoType ===
                    "STUDENT"
                ) {

                    setStudentPhotos(
                        previous =>
                            previous.filter(
                                photo =>
                                    photo.id !==
                                    photoId
                            )
                    );

                } else {

                    setVolunteerPhotos(
                        previous =>
                            previous.filter(
                                photo =>
                                    photo.id !==
                                    photoId
                            )
                    );

                }


                setMessage(
                    "Photo deleted successfully."
                );


            } catch (error) {

                console.error(
                    "Photo delete error:",
                    error
                );

                setMessage(
                    error.response?.data?.error ||
                    "Unable to delete photo."
                );

            }

        };


    /* ========================================================
       RENDER
       ======================================================== */

    return (

        <div className="admin-attendance-page">


            {/* ==================================================
                HEADER
                ================================================== */}

            <header className="toolkit-header">


                {/* ==================================================
                    LOGO — LEFT
                    ================================================== */}

                <div className="toolkit-logo">

                    <img
                        src="/jaago-attendance-logo.jpeg"
                        alt="Jaago Portal"
                    />

                </div>


                {/* ==================================================
                    TITLE — CENTER
                    ================================================== */}

                <div className="toolkit-brand">

                    <div className="toolkit-title">

                        <p className="toolkit-eyebrow">
                            ADMIN 1
                        </p>

                        <h1>
                            Attendance Tool Kit
                        </h1>

                        <p>
                            Manage daily student and volunteer attendance.
                        </p>

                    </div>

                </div>


                {/* ==================================================
                    SESSION — RIGHT
                    ================================================== */}

                <div className="toolkit-session">

                    <div className="session-label">
                        SESSION TIME
                    </div>

                    <div className="session-timer">

                        {formatTime(
                            secondsRemaining
                        )}

                    </div>


                    <div className="session-date">

                        <input
                            type="date"
                            value={
                                selectedDate
                            }
                            onChange={
                                event =>
                                    setSelectedDate(
                                        event.target.value
                                    )
                            }
                        />

                    </div>

                </div>

            </header>


            {/* ==================================================
                MESSAGE
                ================================================== */}

            {message && (

                <div className="toolkit-message">

                    <span>
                        {message}
                    </span>

                    <button
                        type="button"
                        onClick={() =>
                            setMessage("")
                        }
                    >
                        ×
                    </button>

                </div>

            )}


            {/* ==================================================
                ATTENDANCE
                ================================================== */}

            {loading ? (

                <div className="toolkit-loading">

                    Loading attendance...

                </div>

            ) : (

                <main className="attendance-toolkit-grid">


                    {/* ==================================================
                        STUDENT ATTENDANCE
                        ================================================== */}

                    <section className="toolkit-panel">


                        <div className="panel-header">

                            <div>

                                <span className="panel-kicker">
                                    DAILY RECORD
                                </span>

                                <h2>
                                    Student Attendance
                                </h2>

                                <p>
                                    Mark attendance for registered students.
                                </p>

                            </div>


                            <div className="panel-count">

                                {students.length}

                                <span>
                                    Students
                                </span>

                            </div>

                        </div>


                        {/* ==================================================
                            STUDENT PHOTO
                            ================================================== */}

                        <div className="attendance-photo-section">

                            <div className="photo-section-heading">

                                <div>

                                    <h3>
                                        Attendance Photo
                                    </h3>

                                    <p>
                                        Upload today's student attendance photo.
                                    </p>

                                </div>


                                <button
                                    type="button"
                                    className="photo-upload-btn"
                                    onClick={() =>
                                        studentPhotoInput.current?.click()
                                    }
                                    disabled={
                                        uploadingStudentPhoto
                                    }
                                >

                                    {uploadingStudentPhoto
                                        ? "Uploading..."
                                        : "+ Upload Photo"}

                                </button>


                                <input
                                    ref={
                                        studentPhotoInput
                                    }
                                    type="file"
                                    accept="image/*"
                                    hidden
                                    onChange={
                                        event =>
                                            handlePhotoUpload(
                                                event,
                                                "STUDENT"
                                            )
                                    }
                                />

                            </div>


                            <div className="photo-gallery">

                                {studentPhotos.length === 0 ? (

                                    <button
                                        type="button"
                                        className="photo-empty"
                                        onClick={() =>
                                            studentPhotoInput.current?.click()
                                        }
                                    >

                                        <span className="photo-empty-icon">
                                            +
                                        </span>

                                        <span>
                                            Add attendance photo
                                        </span>

                                    </button>

                                ) : (

                                    studentPhotos.map(
                                        photo => (

                                            <button
                                                type="button"
                                                key={
                                                    photo.id
                                                }
                                                className="attendance-photo"
                                                onClick={() =>
                                                    deletePhoto(
                                                        photo.id,
                                                        "STUDENT"
                                                    )
                                                }
                                                title="Click photo to delete"
                                            >

                                                <img
                                                    src={
                                                        getMediaUrl(
                                                            photo.url ||
                                                            photo.photo
                                                        )
                                                    }
                                                    alt="Student attendance"
                                                    onError={
                                                        event => {
                                                            console.error(
                                                                "Student photo failed to load:",
                                                                getMediaUrl(
                                                                    photo.url ||
                                                                    photo.photo
                                                                )
                                                            );

                                                            event.currentTarget.style.display =
                                                                "none";
                                                        }
                                                    }
                                                />

                                                <span className="photo-delete-overlay">
                                                    Click to delete
                                                </span>

                                            </button>

                                        )
                                    )

                                )}

                            </div>

                        </div>


                        {/* ==================================================
                            STUDENT LIST
                            ================================================== */}

                        <div className="attendance-list">

                            <div className="list-heading">

                                <span>
                                    Student
                                </span>

                                <span>
                                    Attendance
                                </span>

                            </div>


                            {students.length === 0 ? (

                                <div className="list-empty">

                                    No registered students found.

                                </div>

                            ) : (

                                students.map(
                                    student => (

                                        <div
                                            className="attendance-row"
                                            key={
                                                student.student
                                            }
                                        >

                                            <div className="person-info">

                                                <div className="person-avatar">

                                                    {getInitials(
                                                        student.name
                                                    )}

                                                </div>

                                                <div>

                                                    <strong>
                                                        {
                                                            student.name
                                                        }
                                                    </strong>

                                                    <span>

                                                        {
                                                            student.roll_no
                                                        }

                                                        {" · "}

                                                        Class{" "}

                                                        {
                                                            student.student_class
                                                        }

                                                    </span>

                                                </div>

                                            </div>


                                            <div className="status-buttons">

                                                <button
                                                    type="button"
                                                    className={
                                                        student.status ===
                                                        "PRESENT"
                                                            ? "status-btn present active"
                                                            : "status-btn present"
                                                    }
                                                    onClick={() =>
                                                        updateStudentStatus(
                                                            student.student,
                                                            "PRESENT"
                                                        )
                                                    }
                                                >
                                                    Present
                                                </button>


                                                <button
                                                    type="button"
                                                    className={
                                                        student.status ===
                                                        "ABSENT"
                                                            ? "status-btn absent active"
                                                            : "status-btn absent"
                                                    }
                                                    onClick={() =>
                                                        updateStudentStatus(
                                                            student.student,
                                                            "ABSENT"
                                                        )
                                                    }
                                                >
                                                    Absent
                                                </button>

                                            </div>

                                        </div>

                                    )
                                )

                            )}

                        </div>


                        {/* ==================================================
                            SAVE STUDENT
                            ================================================== */}

                        <div className="panel-footer">

                            <button
                                type="button"
                                className="save-panel-btn"
                                onClick={
                                    saveStudentAttendance
                                }
                                disabled={
                                    saving ||
                                    students.length === 0
                                }
                            >

                                {saving
                                    ? "Saving..."
                                    : "Save Student Attendance"}

                            </button>

                        </div>

                    </section>


                    {/* ==================================================
                        VOLUNTEER ATTENDANCE
                        ================================================== */}

                    <section className="toolkit-panel">


                        <div className="panel-header">

                            <div>

                                <span className="panel-kicker">
                                    DAILY RECORD
                                </span>

                                <h2>
                                    Volunteer Attendance
                                </h2>

                                <p>
                                    Record volunteers assigned for today.
                                </p>

                            </div>


                            <button
                                type="button"
                                className="add-volunteer-btn"
                                onClick={
                                    openVolunteerModal
                                }
                                aria-label="Add volunteer"
                            >
                                +
                            </button>

                        </div>


                        {/* ==================================================
                            VOLUNTEER PHOTO
                            ================================================== */}

                        <div className="attendance-photo-section">

                            <div className="photo-section-heading">

                                <div>

                                    <h3>
                                        Attendance Photo
                                    </h3>

                                    <p>
                                        Upload today's volunteer attendance photo.
                                    </p>

                                </div>


                                <button
                                    type="button"
                                    className="photo-upload-btn"
                                    onClick={() =>
                                        volunteerPhotoInput.current?.click()
                                    }
                                    disabled={
                                        uploadingVolunteerPhoto
                                    }
                                >

                                    {uploadingVolunteerPhoto
                                        ? "Uploading..."
                                        : "+ Upload Photo"}

                                </button>


                                <input
                                    ref={
                                        volunteerPhotoInput
                                    }
                                    type="file"
                                    accept="image/*"
                                    hidden
                                    onChange={
                                        event =>
                                            handlePhotoUpload(
                                                event,
                                                "VOLUNTEER"
                                            )
                                    }
                                />

                            </div>


                            <div className="photo-gallery">

                                {volunteerPhotos.length === 0 ? (

                                    <button
                                        type="button"
                                        className="photo-empty"
                                        onClick={() =>
                                            volunteerPhotoInput.current?.click()
                                        }
                                    >

                                        <span className="photo-empty-icon">
                                            +
                                        </span>

                                        <span>
                                            Add attendance photo
                                        </span>

                                    </button>

                                ) : (

                                    volunteerPhotos.map(
                                        photo => (

                                            <button
                                                type="button"
                                                key={
                                                    photo.id
                                                }
                                                className="attendance-photo"
                                                onClick={() =>
                                                    deletePhoto(
                                                        photo.id,
                                                        "VOLUNTEER"
                                                    )
                                                }
                                                title="Click photo to delete"
                                            >

                                                <img
                                                    src={
                                                        getMediaUrl(
                                                            photo.url ||
                                                            photo.photo
                                                        )
                                                    }
                                                    alt="Volunteer attendance"
                                                    onError={
                                                        event => {
                                                            console.error(
                                                                "Volunteer photo failed to load:",
                                                                getMediaUrl(
                                                                    photo.url ||
                                                                    photo.photo
                                                                )
                                                            );

                                                            event.currentTarget.style.display =
                                                                "none";
                                                        }
                                                    }
                                                />

                                                <span className="photo-delete-overlay">
                                                    Click to delete
                                                </span>

                                            </button>

                                        )
                                    )

                                )}

                            </div>

                        </div>


                        {/* ==================================================
                            VOLUNTEER LIST
                            ================================================== */}

                        <div className="attendance-list">

                            <div className="list-heading">

                                <span>
                                    Volunteer
                                </span>

                                <span>
                                    Attendance
                                </span>

                            </div>


                            {volunteers.length === 0 ? (

                                <div className="list-empty volunteer-empty">

                                    <div className="empty-plus">
                                        +
                                    </div>

                                    <strong>
                                        No volunteers added
                                    </strong>

                                    <span>
                                        Volunteers assigned by Admin 2
                                        can be added here.
                                    </span>

                                    <button
                                        type="button"
                                        onClick={
                                            openVolunteerModal
                                        }
                                    >
                                        Add Volunteer
                                    </button>

                                </div>

                            ) : (

                                volunteers.map(
                                    volunteer => (

                                        <div
                                            className="attendance-row volunteer-row"
                                            key={
                                                volunteer.id
                                            }
                                        >

                                            <div className="person-info">

                                                <div className="person-avatar volunteer-avatar">

                                                    {getInitials(
                                                        volunteer.name
                                                    )}

                                                </div>

                                                <div>

                                                    <strong>
                                                        {
                                                            volunteer.name
                                                        }
                                                    </strong>

                                                    <span>
                                                        Registered Volunteer
                                                    </span>

                                                </div>

                                            </div>


                                            <div className="volunteer-actions">

                                                <div className="status-buttons">

                                                    <button
                                                        type="button"
                                                        className={
                                                            volunteer.status ===
                                                            "PRESENT"
                                                                ? "status-btn present active"
                                                                : "status-btn present"
                                                        }
                                                        onClick={() =>
                                                            updateVolunteerStatus(
                                                                volunteer.id,
                                                                "PRESENT"
                                                            )
                                                        }
                                                    >
                                                        Present
                                                    </button>


                                                    <button
                                                        type="button"
                                                        className={
                                                            volunteer.status ===
                                                            "ABSENT"
                                                                ? "status-btn absent active"
                                                                : "status-btn absent"
                                                        }
                                                        onClick={() =>
                                                            updateVolunteerStatus(
                                                                volunteer.id,
                                                                "ABSENT"
                                                            )
                                                        }
                                                    >
                                                        Absent
                                                    </button>

                                                </div>


                                                <button
                                                    type="button"
                                                    className="remove-volunteer-btn"
                                                    onClick={() =>
                                                        deleteVolunteer(
                                                            volunteer.id
                                                        )
                                                    }
                                                    title="Remove volunteer"
                                                >
                                                    ×
                                                </button>

                                            </div>

                                        </div>

                                    )
                                )

                            )}

                        </div>

                    </section>

                </main>

            )}


            {/* ==================================================
                END SESSION
                ================================================== */}

            <footer className="toolkit-footer">

                <div>

                    <span className="footer-timer-label">
                        Session expires in
                    </span>

                    <strong>
                        {formatTime(
                            secondsRemaining
                        )}
                    </strong>

                </div>


                <button
                    type="button"
                    className="end-session-btn"
                    onClick={
                        endSession
                    }
                >
                    End Session
                </button>

            </footer>


            {/* ==================================================
                VOLUNTEER MODAL
                ================================================== */}

            {showVolunteerModal && (

                <div
                    className="volunteer-modal-backdrop"
                    onClick={() =>
                        setShowVolunteerModal(false)
                    }
                >

                    <div
                        className="volunteer-modal"
                        onClick={
                            event =>
                                event.stopPropagation()
                        }
                    >

                        <div className="modal-header">

                            <div>

                                <span>
                                    REGISTERED VOLUNTEERS
                                </span>

                                <h2>
                                    Add Volunteer
                                </h2>

                                <p>
                                    Select a registered volunteer
                                    who is available today.
                                </p>

                            </div>


                            <button
                                type="button"
                                className="modal-close"
                                onClick={() =>
                                    setShowVolunteerModal(false)
                                }
                            >
                                ×
                            </button>

                        </div>


                        <div className="available-volunteer-list">

                            {availableVolunteers.length === 0 ? (

                                <div className="modal-empty">

                                    <div>
                                        ✓
                                    </div>

                                    <strong>
                                        No volunteers available
                                    </strong>

                                    <span>
                                        Admin 2 has not made another
                                        volunteer available yet.
                                    </span>

                                </div>

                            ) : (

                                availableVolunteers.map(
                                    volunteer => (

                                        <button
                                            type="button"
                                            className="available-volunteer"
                                            key={
                                                volunteer.id
                                            }
                                            onClick={() =>
                                                addVolunteer(
                                                    volunteer
                                                )
                                            }
                                        >

                                            <div className="person-avatar volunteer-avatar">

                                                {getInitials(
                                                    volunteer.name
                                                )}

                                            </div>


                                            <div>

                                                <strong>
                                                    {
                                                        volunteer.name
                                                    }
                                                </strong>

                                                <span>

                                                    {
                                                        volunteer.email ||
                                                        volunteer.phone ||
                                                        "Registered Volunteer"
                                                    }

                                                </span>

                                            </div>


                                            <span className="add-item-icon">
                                                +
                                            </span>

                                        </button>

                                    )
                                )

                            )}

                        </div>

                    </div>

                </div>

            )}

        </div>

    );

}


export default Admin1Attendance;