import axios from "axios";


const API_BASE_URL =
    "http://127.0.0.1:8000/api";


const BACKEND_URL =
    "http://127.0.0.1:8000";


const API = axios.create({
    baseURL: API_BASE_URL,

    headers: {
        "Content-Type": "application/json",
    },
});


/* ============================================================
   UPLOAD ATTENDANCE PHOTO
   ============================================================ */

export const uploadAttendancePhoto = (
    file,
    photoType,
    date
) => {

    const formData =
        new FormData();

    formData.append(
        "photo",
        file
    );

    formData.append(
        "photo_type",
        photoType
    );

    formData.append(
        "date",
        date
    );


    return API.post(
        "/attendance/photos/upload/",
        formData,
        {
            headers: {
                "Content-Type":
                    "multipart/form-data",
            },
        }
    );

};


/* ============================================================
   CONVERT DJANGO MEDIA URL TO FULL URL
   ============================================================ */

export const getMediaUrl = (
    url
) => {

    if (!url) {
        return "";
    }


    if (
        url.startsWith("http://") ||
        url.startsWith("https://")
    ) {

        return url;

    }


    if (url.startsWith("/")) {

        return (
            BACKEND_URL +
            url
        );

    }


    return (
        BACKEND_URL +
        "/" +
        url
    );

};


export default API;