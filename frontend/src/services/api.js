import axios from "axios";

/* ============================================================
   BASE URLS

   Configurable through Vite env vars so the same build can
   point at a local Django server or a deployed one:

       VITE_API_BASE_URL=https://your-backend.example.com/api
       VITE_BACKEND_URL=https://your-backend.example.com
   ============================================================ */

const BACKEND_URL =
    import.meta.env.VITE_BACKEND_URL ||
    "http://127.0.0.1:8000";

const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL ||
    `${BACKEND_URL}/api`;

/* ============================================================
   TOKEN STORAGE

   The backend (accounts.LoginView / teachers.TeacherLoginView)
   returns a SimpleJWT access + refresh pair. We keep them in
   localStorage so a page refresh does not sign the user out.
   ============================================================ */

const ACCESS_TOKEN_KEY = "jaago_access_token";
const REFRESH_TOKEN_KEY = "jaago_refresh_token";
const ROLE_KEY = "jaago_role";
const USER_KEY = "jaago_user";

export const tokenStorage = {
    getAccess: () => localStorage.getItem(ACCESS_TOKEN_KEY),
    getRefresh: () => localStorage.getItem(REFRESH_TOKEN_KEY),
    getRole: () => localStorage.getItem(ROLE_KEY),
    getUser: () => {
        const raw = localStorage.getItem(USER_KEY);
        try {
            return raw ? JSON.parse(raw) : null;
        } catch {
            return null;
        }
    },
    setSession: ({ access, refresh, role, user }) => {
        if (access) localStorage.setItem(ACCESS_TOKEN_KEY, access);
        if (refresh) localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
        if (role) localStorage.setItem(ROLE_KEY, role);
        if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
    },
    setAccess: (access) => {
        if (access) localStorage.setItem(ACCESS_TOKEN_KEY, access);
    },
    clear: () => {
        localStorage.removeItem(ACCESS_TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
        localStorage.removeItem(ROLE_KEY);
        localStorage.removeItem(USER_KEY);
    },
};

/* ============================================================
   AXIOS INSTANCE
   ============================================================ */

const API = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

// Login requests must never carry a (possibly stale/expired) access
// token: JWTAuthentication validates any Authorization header it sees
// before the view runs, even on AllowAny endpoints, so a dead token
// left over from a previous session would fail login with
// "Given token not valid for any token type" before credentials are
// ever checked.
const isLoginEndpoint = (url) =>
    Boolean(url) &&
    (url.includes("/auth/login") || url.includes("/teachers/login"));

// Attach the JWT access token to every outgoing request except login.
API.interceptors.request.use((config) => {
    const token = tokenStorage.getAccess();

    if (token && !isLoginEndpoint(config.url)) {
        config.headers = config.headers || {};
        config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
});

/* ------------------------------------------------------------
   401 HANDLING

   IMPORTANT: this backend does NOT expose a JWT refresh
   endpoint (accounts/urls.py has no /auth/token/refresh/, and
   SimpleJWT's TokenRefreshView is not wired into config/urls.py).
   A refresh token is issued at login but there is currently no
   server route to redeem it. Without changing the backend the
   only correct behaviour on a 401 is to clear the stale session
   so the app cleanly asks the user to sign in again, rather than
   silently retrying against a nonexistent endpoint.

   The access token itself lives for 30 minutes (SIMPLE_JWT
   ACCESS_TOKEN_LIFETIME in settings.py), so this only triggers
   once that window has passed.
   ------------------------------------------------------------ */

API.interceptors.response.use(
    (response) => response,
    (error) => {
        const originalRequest = error.config;

        if (
            error.response &&
            error.response.status === 401 &&
            !isLoginEndpoint(originalRequest?.url)
        ) {
            tokenStorage.clear();
        }

        return Promise.reject(error);
    }
);

/* ============================================================
   AUTH HELPERS

   These wrap the three real login flows this backend exposes:

     - Volunteers / Teachers: POST /teachers/login/
           body: { user_id, password }
     - Admin 1 / Admin 2 / anyone with a Django auth account:
       POST /auth/login/
           body: { username, password }
           -> { profile: { role: "ADMIN1" | "ADMIN2" | ... }, tokens }

   There is no separate backend login route per role — Admin 1
   and Admin 2 both authenticate through the common endpoint and
   are told apart by `profile.role` in the response.
   ============================================================ */

export const loginVolunteer = async (userId, password) => {
    const response = await API.post("/teachers/login/", {
        user_id: userId,
        password,
    });

    const data = response.data;

    tokenStorage.setSession({
        access: data.access,
        refresh: data.refresh,
        role: data.role || "TEACHER_VOLUNTEER",
        user: {
            user_id: data.user_id,
            name: data.name,
            email: data.email,
            course: data.course,
            subject: data.subject,
        },
    });

    return data;
};

export const loginWithUsername = async (username, password) => {
    const response = await API.post("/auth/login/", {
        username,
        password,
    });

    const data = response.data;

    tokenStorage.setSession({
        access: data.tokens?.access,
        refresh: data.tokens?.refresh,
        role: data.profile?.role,
        user: data.user,
    });

    return data;
};

export const logout = () => {
    tokenStorage.clear();
};

export const getCurrentRole = () => tokenStorage.getRole();
export const getCurrentUser = () => tokenStorage.getUser();
export const isAuthenticated = () => Boolean(tokenStorage.getAccess());

/* ============================================================
   CONVERT A DJANGO MEDIA PATH TO A FULL URL

   Assignment attachments (VolunteerAssignment.attachment /
   homework_attachment) come back from the API as relative
   /media/... paths — this makes them clickable.
   ============================================================ */

export const getMediaUrl = (url) => {
    if (!url) {
        return "";
    }

    if (url.startsWith("http://") || url.startsWith("https://")) {
        return url;
    }

    if (url.startsWith("/")) {
        return BACKEND_URL + url;
    }

    return `${BACKEND_URL}/${url}`;
};

export { BACKEND_URL, API_BASE_URL };
export default API;
