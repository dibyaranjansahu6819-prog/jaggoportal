import { useState } from "react";
import API from "../services/api";


function StudentSignup() {

    const [formData, setFormData] = useState({
        name: "",
        student_class: "",
        school_name: "",
    });

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(null);


    const classes = [
        {
            value: "LKG",
            label: "LKG",
        },
        {
            value: "UKG",
            label: "UKG",
        },
        {
            value: "1",
            label: "Class 1",
        },
        {
            value: "2",
            label: "Class 2",
        },
        {
            value: "3",
            label: "Class 3",
        },
        {
            value: "4",
            label: "Class 4",
        },
        {
            value: "5",
            label: "Class 5",
        },
        {
            value: "6",
            label: "Class 6",
        },
        {
            value: "7",
            label: "Class 7",
        },
        {
            value: "8",
            label: "Class 8",
        },
        {
            value: "9",
            label: "Class 9",
        },
        {
            value: "10",
            label: "Class 10",
        },
    ];


    const handleChange = (event) => {

        const { name, value } = event.target;

        setFormData((previous) => ({
            ...previous,
            [name]: value,
        }));

    };


    const handleSubmit = async (event) => {

        event.preventDefault();

        setError("");
        setSuccess(null);


        if (!formData.name.trim()) {

            setError(
                "Please enter the student's name."
            );

            return;
        }


        if (!formData.student_class) {

            setError(
                "Please select the student's class."
            );

            return;
        }


        if (!formData.school_name.trim()) {

            setError(
                "Please enter the school name."
            );

            return;
        }


        setLoading(true);


        try {

            const response = await API.post(
                "/students/register/",
                {
                    name: formData.name.trim(),
                    student_class:
                        formData.student_class,
                    school_name:
                        formData.school_name.trim(),
                }
            );


            setSuccess(response.data);


            setFormData({
                name: "",
                student_class: "",
                school_name: "",
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

        <div className="student-signup-page">

            <div className="student-signup-card">

                <div className="student-signup-header">

                    <h1>
                        Student Registration
                    </h1>

                    <p>
                        Register a new student
                    </p>

                </div>


                {error && (

                    <div className="error-message">
                        {error}
                    </div>

                )}


                {success ? (

                    <div className="student-success">

                        <h2>
                            Registration Successful!
                        </h2>

                        <p>
                            Student:
                            {" "}
                            <strong>
                                {success.name}
                            </strong>
                        </p>

                        <p>
                            School:
                            {" "}
                            <strong>
                                {success.school_name}
                            </strong>
                        </p>

                        <p>
                            Class:
                            {" "}
                            <strong>
                                {success.student_class}
                            </strong>
                        </p>


                        <div className="roll-number-box">

                            <span>
                                Student Roll Number
                            </span>

                            <strong>
                                {success.roll_no}
                            </strong>

                        </div>


                        <p className="roll-info">

                            This Roll Number has been
                            automatically generated.

                        </p>


                        <button
                            type="button"
                            onClick={() =>
                                setSuccess(null)
                            }
                        >
                            Register Another Student
                        </button>

                    </div>

                ) : (

                    <form
                        onSubmit={handleSubmit}
                        className="student-signup-form"
                    >

                        {/* Student Name */}

                        <div className="form-group">

                            <label>
                                Student Name
                            </label>

                            <input
                                type="text"
                                name="name"
                                value={formData.name}
                                onChange={handleChange}
                                placeholder="Enter student name"
                                required
                            />

                        </div>


                        {/* School Name */}

                        <div className="form-group">

                            <label>
                                School Name
                            </label>

                            <input
                                type="text"
                                name="school_name"
                                value={
                                    formData.school_name
                                }
                                onChange={handleChange}
                                placeholder="Enter school name"
                                required
                            />

                        </div>


                        {/* Class */}

                        <div className="form-group">

                            <label>
                                Class
                            </label>

                            <select
                                name="student_class"
                                value={
                                    formData.student_class
                                }
                                onChange={handleChange}
                                required
                            >

                                <option value="">
                                    Select Class
                                </option>

                                {classes.map((item) => (

                                    <option
                                        key={item.value}
                                        value={item.value}
                                    >
                                        {item.label}
                                    </option>

                                ))}

                            </select>

                        </div>


                        {/* Roll Number Information */}

                        <div className="auto-roll-info">

                            <span>
                                Roll Number
                            </span>

                            <strong>
                                Automatically generated
                            </strong>

                            <small>
                                Example: JAA0935
                            </small>

                        </div>


                        {/* Submit */}

                        <button
                            type="submit"
                            className="student-register-button"
                            disabled={loading}
                        >

                            {loading
                                ? "Registering..."
                                : "Register Student"}

                        </button>

                    </form>

                )}

            </div>

        </div>

    );

}


export default StudentSignup;