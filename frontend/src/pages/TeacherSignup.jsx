import { useEffect, useState } from "react";
import API from "../services/api";


function TeacherSignup() {
    const [courses, setCourses] = useState([]);
    const [subjects, setSubjects] = useState([]);

    const [formData, setFormData] = useState({
        name: "",
        course: "",
        joining_year: new Date().getFullYear(),
        subject: "",
        email: "",
        whatsapp_number: "",
        free_days: [],
        password: "",
        confirm_password: "",
    });

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(null);

    const days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ];


    // Load courses and subjects from Django
    useEffect(() => {
        const loadData = async () => {
            try {
                const [courseResponse, subjectResponse] =
                    await Promise.all([
                        API.get("/courses/"),
                        API.get("/subjects/"),
                    ]);

                setCourses(courseResponse.data);
                setSubjects(subjectResponse.data);
            } catch (err) {
                console.error(err);

                setError(
                    "Unable to load courses and subjects. Make sure Django server is running."
                );
            }
        };

        loadData();
    }, []);


    // Handle normal inputs
    const handleChange = (event) => {
        const { name, value } = event.target;

        setFormData((previous) => ({
            ...previous,
            [name]: value,
        }));
    };


    // Handle free-day selection
    const handleFreeDayChange = (day) => {
        setFormData((previous) => {
            const alreadySelected =
                previous.free_days.includes(day);

            if (alreadySelected) {
                return {
                    ...previous,
                    free_days: previous.free_days.filter(
                        (item) => item !== day
                    ),
                };
            }

            return {
                ...previous,
                free_days: [
                    ...previous.free_days,
                    day,
                ],
            };
        });
    };


    // Submit registration
    const handleSubmit = async (event) => {
        event.preventDefault();

        setError("");
        setSuccess(null);

        // Name validation
        if (!formData.name.trim()) {
            setError("Please enter your full name.");
            return;
        }

        // Course validation
        if (!formData.course) {
            setError("Please select a course.");
            return;
        }

        // Subject validation
        if (!formData.subject) {
            setError("Please select a subject.");
            return;
        }

        // Joining year validation
        const joiningYear = Number(
            formData.joining_year
        );

        if (
            joiningYear < 1900 ||
            joiningYear > 2100
        ) {
            setError("Please enter a valid joining year.");
            return;
        }

        // Email validation
        if (!formData.email.trim()) {
            setError("Please enter your email.");
            return;
        }

        // WhatsApp validation
        if (!/^\d{10}$/.test(formData.whatsapp_number)) {
            setError(
                "WhatsApp number must contain exactly 10 digits."
            );
            return;
        }

        // Free days validation
        if (formData.free_days.length === 0) {
            setError(
                "Please select at least one free day."
            );
            return;
        }

        // Password validation
        if (formData.password.length < 8) {
            setError(
                "Password must contain at least 8 characters."
            );
            return;
        }

        if (
            formData.password !==
            formData.confirm_password
        ) {
            setError("Passwords do not match.");
            return;
        }


        setLoading(true);

        try {
            const response = await API.post(
                "/teachers/register/",
                {
                    ...formData,
                    joining_year: joiningYear,
                }
            );

            setSuccess(response.data);

            // Clear form
            setFormData({
                name: "",
                course: "",
                joining_year: new Date().getFullYear(),
                subject: "",
                email: "",
                whatsapp_number: "",
                free_days: [],
                password: "",
                confirm_password: "",
            });

        } catch (err) {
            console.error(err);

            const responseData =
                err.response?.data;

            if (responseData) {
                const messages = [];

                Object.entries(responseData).forEach(
                    ([field, value]) => {
                        if (Array.isArray(value)) {
                            messages.push(
                                `${field}: ${value.join(", ")}`
                            );
                        } else if (
                            typeof value === "string"
                        ) {
                            messages.push(
                                `${field}: ${value}`
                            );
                        }
                    }
                );

                setError(
                    messages.length > 0
                        ? messages.join(" | ")
                        : "Registration failed."
                );
            } else {
                setError(
                    "Unable to connect to the server."
                );
            }

        } finally {
            setLoading(false);
        }
    };


    return (
        <div className="signup-page">

            <div className="signup-card">

                <div className="signup-header">
                    <h1>Volunter Registration</h1>

                    <p>
                        Create your volunter account
                    </p>
                </div>


                {error && (
                    <div className="error-message">
                        {error}
                    </div>
                )}


                {success && (
                    <div className="success-message">

                        <h2>
                            Registration Successful!
                        </h2>

                        <p>
                            Welcome, {success.name}
                        </p>

                        <div className="user-id-box">

                            <span>
                                Your Teacher User ID
                            </span>

                            <strong>
                                {success.user_id}
                            </strong>

                        </div>

                        <p>
                            Please save this User ID.
                            You will use it to sign in.
                        </p>

                        <button
                            type="button"
                            onClick={() => setSuccess(null)}
                        >
                            Register Another Teacher
                        </button>

                    </div>
                )}


                {!success && (
                    <form
                        onSubmit={handleSubmit}
                        className="signup-form"
                    >

                        {/* Full Name */}
                        <div className="form-group">

                            <label>
                                Full Name
                            </label>

                            <input
                                type="text"
                                name="name"
                                value={formData.name}
                                onChange={handleChange}
                                placeholder="Enter full name"
                                required
                            />

                        </div>


                        {/* Course */}
                        <div className="form-group">

                            <label>
                                Course
                            </label>

                            <select
                                name="course"
                                value={formData.course}
                                onChange={handleChange}
                                required
                            >

                                <option value="">
                                    Select Course
                                </option>

                                {courses.map((course) => (
                                    <option
                                        key={course.id}
                                        value={course.id}
                                    >
                                        {course.name}
                                    </option>
                                ))}

                            </select>

                        </div>


                        {/* Joining Year */}
                        <div className="form-group">

                            <label>
                                Joining Year
                            </label>

                            <input
                                type="number"
                                name="joining_year"
                                value={formData.joining_year}
                                onChange={handleChange}
                                min="1900"
                                max="2100"
                                required
                            />

                            <small>
                                Enter the year you joined
                                the institution.
                            </small>

                        </div>


                        {/* Subject */}
                        <div className="form-group">

                            <label>
                                Subject
                            </label>

                            <select
                                name="subject"
                                value={formData.subject}
                                onChange={handleChange}
                                required
                            >

                                <option value="">
                                    Select Subject
                                </option>

                                {subjects.map((subject) => (
                                    <option
                                        key={subject.id}
                                        value={subject.id}
                                    >
                                        {subject.name}
                                    </option>
                                ))}

                            </select>

                        </div>


                        {/* Email */}
                        <div className="form-group">

                            <label>
                                Email
                            </label>

                            <input
                                type="email"
                                name="email"
                                value={formData.email}
                                onChange={handleChange}
                                placeholder="teacher@example.com"
                                required
                            />

                        </div>


                        {/* WhatsApp */}
                        <div className="form-group">

                            <label>
                                WhatsApp Number
                            </label>

                            <input
                                type="tel"
                                name="whatsapp_number"
                                value={
                                    formData.whatsapp_number
                                }
                                onChange={handleChange}
                                placeholder="10 digit number"
                                maxLength="10"
                                required
                            />

                        </div>


                        {/* Free Days */}
                        <div className="form-group">

                            <label>
                                Free Days
                            </label>

                            <p className="field-help">
                                Select at least one day.
                            </p>

                            <div className="days-container">

                                {days.map((day) => (
                                    <label
                                        key={day}
                                        className="day-option"
                                    >

                                        <input
                                            type="checkbox"
                                            checked={formData.free_days.includes(
                                                day
                                            )}
                                            onChange={() =>
                                                handleFreeDayChange(
                                                    day
                                                )
                                            }
                                        />

                                        <span>
                                            {day}
                                        </span>

                                    </label>
                                ))}

                            </div>

                        </div>


                        {/* Password */}
                        <div className="form-group">

                            <label>
                                Password
                            </label>

                            <input
                                type="password"
                                name="password"
                                value={formData.password}
                                onChange={handleChange}
                                placeholder="Minimum 8 characters"
                                minLength="8"
                                required
                            />

                        </div>


                        {/* Confirm Password */}
                        <div className="form-group">

                            <label>
                                Confirm Password
                            </label>

                            <input
                                type="password"
                                name="confirm_password"
                                value={
                                    formData.confirm_password
                                }
                                onChange={handleChange}
                                placeholder="Re-enter password"
                                required
                            />

                        </div>


                        {/* Submit */}
                        <button
                            type="submit"
                            className="signup-button"
                            disabled={loading}
                        >

                            {loading
                                ? "Creating Account..."
                                : "Create Account"}

                        </button>

                    </form>
                )}

            </div>

        </div>
    );
}


export default TeacherSignup;