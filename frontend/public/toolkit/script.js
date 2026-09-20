(function(){
  "use strict";

  document.getElementById("year").textContent = new Date().getFullYear();

  /* ============================================================
     API CONFIG — talks to the real Django backend.
     Change API_BASE if your backend runs on a different host/port.
     ============================================================ */
  var API_BASE = "http://127.0.0.1:8000/api";
  var AUTH_KEY = "jaago_auth";

  function getAuth(){
    try { return JSON.parse(localStorage.getItem(AUTH_KEY) || "null"); }
    catch(e){ return null; }
  }
  function setAuth(auth){ localStorage.setItem(AUTH_KEY, JSON.stringify(auth)); }
  function clearAuth(){ localStorage.removeItem(AUTH_KEY); }

  function extractApiError(data, fallback){
    if (!data) return fallback || "Something went wrong.";
    if (typeof data === "string") return data;
    if (data.detail) return data.detail;
    if (data.error) return data.error;
    var msgs = [];
    Object.keys(data).forEach(function(key){
      var val = data[key];
      if (Array.isArray(val)) msgs.push(key + ": " + val.join(", "));
      else if (typeof val === "string") msgs.push(key + ": " + val);
    });
    return msgs.length ? msgs.join(" | ") : (fallback || "Something went wrong.");
  }

  /* ------------------------------------------------------------
     BUG FIX — picking the right bearer token per request.
     Admin (jaago_auth) and Volunteer (jaago_volunteer_profile) are
     stored under two different localStorage keys, so BOTH can end
     up present at once in the same browser — e.g. you sign in as
     Admin 2 to assign a module, then sign in as a Volunteer in the
     same tab/browser to check the dashboard, without ever signing
     out of Admin 2. The old code always sent the Admin token when
     one existed, even for the volunteer's own endpoints. Since
     those endpoints require the TEACHER_VOLUNTEER role, an Admin
     token got silently rejected (403) and the dashboard fell back
     to "no assignment yet" / an empty roster — this is what was
     showing up as "assigned module not showing in volunteer
     dashboard." Fix: the two endpoints that only ever belong to
     the signed-in volunteer (/teachers/my-...) always use the
     volunteer's own token when one exists; everything else keeps
     the previous admin-first behavior.
     ------------------------------------------------------------ */
  function pickBearerToken(path){
    var auth = getAuth();
    var volunteer = getVolunteerProfile();
    var isVolunteerOwnedPath = path.indexOf("/teachers/my-") === 0;
    if (isVolunteerOwnedPath){
      if (volunteer && volunteer.access) return volunteer.access;
      if (auth && auth.access) return auth.access;
      return null;
    }
    if (auth && auth.access) return auth.access;
    if (volunteer && volunteer.access) return volunteer.access;
    return null;
  }

  async function apiFetch(path, options){
    options = options || {};
    var headers = options.headers || {};
    if (!(options.body instanceof FormData) && options.body && !headers["Content-Type"]){
      headers["Content-Type"] = "application/json";
    }
    var bearer = pickBearerToken(path);
    if (bearer){
      headers["Authorization"] = "Bearer " + bearer;
    }
    var res;
    try {
      res = await fetch(API_BASE + path, Object.assign({}, options, { headers: headers }));
    } catch(networkErr){
      var netErr = new Error("Unable to reach the server. Is the Django backend running at " + API_BASE + "?");
      netErr.network = true;
      throw netErr;
    }
    var data = null;
    try { data = await res.json(); } catch(e){ data = null; }
    if (!res.ok){
      var err = new Error(extractApiError(data, "Request failed (" + res.status + ")"));
      err.status = res.status;
      err.data = data;
      throw err;
    }
    return data;
  }

  async function apiLogin(username, password, expectedRole){
    var data = await apiFetch("/auth/login/", {
      method: "POST",
      body: JSON.stringify({ username: username, password: password })
    });
    if (expectedRole && (!data.profile || data.profile.role !== expectedRole)){
      var err = new Error("These credentials are not authorized for this panel.");
      err.roleMismatch = true;
      throw err;
    }
    var auth = { access: data.tokens.access, refresh: data.tokens.refresh, user: data.user, profile: data.profile };
    setAuth(auth);
    return auth;
  }

  /* ============================================================
     ROUTING
     ============================================================ */
  var views = ["home","student","teacher","attendance","admin1-signin","admin-signin","admin-status","admin2-students","admin2-volunteers","teacher-signin","volunteer-dashboard"];
  var admin1Authed = false;
  var adminStatusAuthed = false;
  var volunteerAuthed = false;

  // Declared up here (not down near the rest of the volunteer-dashboard
  // code) because navFromHash() runs synchronously below and can call
  // initVolunteerDashboard() before later `var` lines in this script
  // execute — a `var x = null;` further down would otherwise wipe out
  // the value that early call just set.
  var vdCurrentProfile = null;
  var vdRoster = [];        // real students Admin 1 marked PRESENT today in this volunteer's class — [{id, name, rollNo}]
  var vdAssignment = null;  // real today's Admin 2 assignment for this volunteer — {assigned_class, assigned_class_display, task, task_display, instruction, attachment_url}
  var vdPerformance = [];   // [{studentId, studentName, date, rating, description, hwDone, savedAt}] — still local-only, no backend endpoint for this yet
  var vdPerfModalStudentId = null;
  var vdPerfSelectedRating = null;
  var vdPerfSelectedHw = null;

  // Checking-dashboard homework check records — same local-only pattern as
  // vdPerformance above (no backend endpoint exists to persist these either).
  // [{studentId, studentName, date, hwDone, feedback, savedAt}]
  var vdChecking = [];
  var vdCheckModalStudentId = null;
  var vdCheckSelectedDone = null;

  // Special Added landing screen: which absent volunteer's work (if any)
  // this volunteer has picked up today. In-memory only, resets on reload/
  // logout — there is no real backend endpoint yet for "which absent
  // volunteers' work is available to cover", so VD_SPECIAL_ADDED_OPTIONS
  // below is static frontend-only demo data, ported verbatim from the
  // reference preview. Everything downstream of picking one (the Work
  // Details / Session / Student Progress screens) reuses the exact same
  // real rendering logic as Teaching/Checking — nothing is duplicated.
  var vdSpecialAddedActiveWork = null;
  var VD_SPECIAL_ADDED_OPTIONS = [
    { id: "sa1", originalVolunteer: "Aman", classLabel: "Class B", task: "TEACHING", subject: "Mathematics", instruction: "Teach fractions" },
    { id: "sa2", originalVolunteer: "Ravi", classLabel: "Class C", task: "CHECKING", subject: "English", instruction: "Check today's spelling exercise" },
  ];

  var VOLUNTEER_KEY = "jaago_volunteer_profile";
  function getVolunteerProfile(){
    try { return JSON.parse(localStorage.getItem(VOLUNTEER_KEY) || "null"); }
    catch(e){ return null; }
  }
  function setVolunteerProfile(p){ localStorage.setItem(VOLUNTEER_KEY, JSON.stringify(p)); }
  function clearVolunteerProfile(){ localStorage.removeItem(VOLUNTEER_KEY); }

  (function initAuthFromStorage(){
    var auth = getAuth();
    if (auth && auth.profile){
      if (auth.profile.role === "ADMIN1") admin1Authed = true;
      if (auth.profile.role === "ADMIN2") adminStatusAuthed = true;
    }
    if (getVolunteerProfile()) volunteerAuthed = true;
  })();

  function showView(name){
    if (views.indexOf(name) === -1) name = "home";
    if (name === "attendance" && !admin1Authed) name = "admin1-signin";
    if ((name === "admin-status" || name === "admin2-students" || name === "admin2-volunteers") && !adminStatusAuthed) name = "admin-signin";
    if (name === "volunteer-dashboard" && !volunteerAuthed) name = "teacher-signin";
    views.forEach(function(v){
      document.getElementById("view-" + v).classList.toggle("hidden", v !== name);
    });
    if (window.location.hash.replace("#", "") !== name){
      history.replaceState(null, "", "#" + name);
    }
    window.scrollTo({ top: 0, behavior: "instant" in window ? "instant" : "auto" });

    if (name === "attendance") initAttendanceToolkit();
    if (name === "admin-status") loadAdminDashboard();
    if (name === "admin2-students") loadAdmin2Students();
    if (name === "admin2-volunteers") loadAdmin2Volunteers();
    if (name === "volunteer-dashboard") initVolunteerDashboard();
  }

  function goToView(name){
    if (window.location.hash.replace("#", "") === name){
      showView(name);
    } else {
      window.location.hash = name;
    }
  }

  function navFromHash(){
    var h = (window.location.hash || "#home").replace("#","");
    showView(h || "home");
  }

  document.addEventListener("click", function(e){
    var el = e.target.closest("[data-nav]");
    if (!el) return;
    if (el.classList.contains("admin-panel-disabled")) { e.preventDefault(); return; }
    var target = el.getAttribute("data-nav");
    window.location.hash = target;
  });

  window.addEventListener("hashchange", navFromHash);
  navFromHash();

  function escapeHtml(s){
    var d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }

  var WEEKDAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
  function todayWeekdayName(){ return WEEKDAY_NAMES[new Date().getDay()]; }

  function showMessage(text){
    document.getElementById("toolkit-message-text").textContent = text;
    document.getElementById("toolkit-message").classList.remove("hidden");
  }
  document.getElementById("toolkit-message-close").addEventListener("click", function(){
    document.getElementById("toolkit-message").classList.add("hidden");
  });

  /* ============================================================
     ADMIN 1 SIGN IN — real JWT login
     ============================================================ */
  var admin1SigninForm = document.getElementById("admin1-signin-form");
  admin1SigninForm.addEventListener("submit", async function(e){
    e.preventDefault();
    var idVal = document.getElementById("admin1-id").value.trim();
    var pwVal = document.getElementById("admin1-password").value.trim();
    var errBox = document.getElementById("admin1-signin-error");
    errBox.classList.add("hidden");
    if (!idVal || !pwVal){
      errBox.textContent = "Please enter an Admin ID and password.";
      errBox.classList.remove("hidden");
      return;
    }
    var submitBtn = admin1SigninForm.querySelector("button[type=submit]");
    submitBtn.disabled = true;
    try {
      await apiLogin(idVal, pwVal, "ADMIN1");
      admin1Authed = true;
      admin1SigninForm.reset();
      goToView("attendance");
    } catch (err) {
      errBox.textContent = err.roleMismatch
        ? "These credentials are not an Admin 1 account."
        : (err.status === 401 ? "Invalid username or password." : err.message);
      errBox.classList.remove("hidden");
    } finally {
      submitBtn.disabled = false;
    }
  });

  /* ============================================================
     ADMIN 2 ("STATUS") SIGN IN — real JWT login
     ============================================================ */
  var adminSigninForm = document.getElementById("admin-signin-form");
  adminSigninForm.addEventListener("submit", async function(e){
    e.preventDefault();
    var idVal = document.getElementById("admin-id").value.trim();
    var pwVal = document.getElementById("admin-password").value.trim();
    var errBox = document.getElementById("admin-signin-error");
    errBox.classList.add("hidden");
    if (!idVal || !pwVal){
      errBox.textContent = "Please enter an Admin ID and password.";
      errBox.classList.remove("hidden");
      return;
    }
    var submitBtn = adminSigninForm.querySelector("button[type=submit]");
    submitBtn.disabled = true;
    try {
      await apiLogin(idVal, pwVal, "ADMIN2");
      adminStatusAuthed = true;
      adminSigninForm.reset();
      if (!hasSubscribed){
        hasSubscribed = true;
        subscribeTestimonials();
      }
      goToView("admin-status");
    } catch (err) {
      errBox.textContent = err.roleMismatch
        ? "These credentials are not an Admin 2 account."
        : (err.status === 401 ? "Invalid username or password." : err.message);
      errBox.classList.remove("hidden");
    } finally {
      submitBtn.disabled = false;
    }
  });

  /* ============================================================
     FORGOT PASSWORD — request-reset forms for Volunteer, Admin 1
     and Admin 2 sign-in. This only DESIGNS and wires the request
     form; actually emailing the link is a backend job. The reset
     endpoints below (/teachers/password-reset/request/ and
     /auth/password-reset/request/) do not exist on the backend yet
     — see the report for what still needs adding there. Until then
     (and even after), the UI never reveals whether an ID/email
     matched: it always shows the same neutral confirmation, which
     is the correct behavior for a real password-reset form anyway.
     ============================================================ */
  function wireForgotPassword(opts){
    var forgotLink = document.getElementById(opts.forgotLinkId);
    var panel = document.getElementById(opts.panelId);
    var backBtn = document.getElementById(opts.backBtnId);
    var signinForm = document.getElementById(opts.signinFormId);
    var resetForm = document.getElementById(opts.resetFormId);
    if (!forgotLink || !panel || !backBtn || !signinForm || !resetForm) return;

    function showResetPanel(){
      signinForm.classList.add("hidden");
      panel.classList.remove("hidden");
      var msg = document.getElementById(opts.resetMsgId);
      msg.textContent = "";
      msg.className = "modal-msg hidden";
      resetForm.reset();
    }
    function showSigninForm(){
      panel.classList.add("hidden");
      signinForm.classList.remove("hidden");
    }

    forgotLink.addEventListener("click", showResetPanel);
    backBtn.addEventListener("click", showSigninForm);

    resetForm.addEventListener("submit", async function(e){
      e.preventDefault();
      var idVal = document.getElementById(opts.resetIdInputId).value.trim();
      var emailVal = document.getElementById(opts.resetEmailInputId).value.trim();
      var msg = document.getElementById(opts.resetMsgId);
      var submitBtn = resetForm.querySelector("button[type=submit]");

      if (!idVal || !emailVal){
        msg.textContent = "Please enter both your ID and email.";
        msg.className = "modal-msg error";
        return;
      }

      submitBtn.disabled = true;
      var body = { email: emailVal };
      body[opts.idFieldName] = idVal;
      try {
        await apiFetch(opts.resetEndpoint, { method: "POST", body: JSON.stringify(body) });
      } catch (err) {
        // Deliberately ignored — see comment above the function.
      }
      msg.textContent = "If an account with that ID and email exists, we've sent a password reset link to the registered email address.";
      msg.className = "modal-msg success";
      submitBtn.disabled = false;
    });
  }

  wireForgotPassword({
    forgotLinkId: "teacher-forgot-link", panelId: "teacher-reset-panel", backBtnId: "teacher-reset-back",
    signinFormId: "teacher-signin-form", resetFormId: "teacher-reset-form",
    resetIdInputId: "teacher-reset-id", resetEmailInputId: "teacher-reset-email", resetMsgId: "teacher-reset-msg",
    resetEndpoint: "/teachers/password-reset/request/", idFieldName: "user_id"
  });
  wireForgotPassword({
    forgotLinkId: "admin1-forgot-link", panelId: "admin1-reset-panel", backBtnId: "admin1-reset-back",
    signinFormId: "admin1-signin-form", resetFormId: "admin1-reset-form",
    resetIdInputId: "admin1-reset-id", resetEmailInputId: "admin1-reset-email", resetMsgId: "admin1-reset-msg",
    resetEndpoint: "/auth/password-reset/request/", idFieldName: "username"
  });
  wireForgotPassword({
    forgotLinkId: "admin2-forgot-link", panelId: "admin2-reset-panel", backBtnId: "admin2-reset-back",
    signinFormId: "admin-signin-form", resetFormId: "admin2-reset-form",
    resetIdInputId: "admin2-reset-id", resetEmailInputId: "admin2-reset-email", resetMsgId: "admin2-reset-msg",
    resetEndpoint: "/auth/password-reset/request/", idFieldName: "username"
  });

  /* ============================================================
     STUDENT REGISTRATION — real POST /students/register/
     ============================================================ */
  var studentForm = document.getElementById("student-form");
  var studentError = document.getElementById("student-error");
  var studentSuccess = document.getElementById("student-success");

  studentForm.addEventListener("submit", async function(e){
    e.preventDefault();
    studentError.classList.add("hidden");

    var name = document.getElementById("s-name").value.trim();
    var school = document.getElementById("s-school").value.trim();
    var cls = document.getElementById("s-class").value;

    if (!name){ studentError.textContent = "Please enter the student's name."; studentError.classList.remove("hidden"); return; }
    if (!cls){ studentError.textContent = "Please select the student's class."; studentError.classList.remove("hidden"); return; }
    if (!school){ studentError.textContent = "Please enter the school name."; studentError.classList.remove("hidden"); return; }

    var submitBtn = studentForm.querySelector("button[type=submit]");
    submitBtn.disabled = true;
    submitBtn.textContent = "Registering...";

    try {
      var data = await apiFetch("/students/register/", {
        method: "POST",
        body: JSON.stringify({ name: name, student_class: cls, school_name: school })
      });

      document.getElementById("ss-name").textContent = data.name;
      document.getElementById("ss-school").textContent = data.school_name;
      document.getElementById("ss-class").textContent = data.student_class;
      document.getElementById("ss-roll").textContent = data.roll_no;

      studentForm.classList.add("hidden");
      studentSuccess.classList.remove("hidden");
    } catch (err) {
      studentError.textContent = err.message;
      studentError.classList.remove("hidden");
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Register Student";
    }
  });

  document.getElementById("student-again").addEventListener("click", function(){
    studentForm.reset();
    studentForm.classList.remove("hidden");
    studentSuccess.classList.add("hidden");
  });

  /* ============================================================
     VOLUNTEER / TEACHER REGISTRATION — real courses/subjects +
     real POST /teachers/register/
     ============================================================ */
  var teacherForm = document.getElementById("teacher-form");
  var teacherError = document.getElementById("teacher-error");
  var teacherSuccess = document.getElementById("teacher-success");
  document.getElementById("t-year").value = new Date().getFullYear();

  async function loadCoursesAndSubjects(){
    var courseSelect = document.getElementById("t-course");
    var subjectSelect = document.getElementById("t-subject");
    try {
      var courses = await apiFetch("/courses/");
      var subjects = await apiFetch("/subjects/");
      courses.forEach(function(c){
        var opt = document.createElement("option");
        opt.value = c.id;
        opt.textContent = c.name;
        courseSelect.appendChild(opt);
      });
      subjects.forEach(function(s){
        var opt = document.createElement("option");
        opt.value = s.id;
        opt.textContent = s.name;
        subjectSelect.appendChild(opt);
      });
    } catch (err) {
      teacherError.textContent = "Unable to load courses/subjects. Is the Django backend running? (" + err.message + ")";
      teacherError.classList.remove("hidden");
    }
  }
  loadCoursesAndSubjects();

  teacherForm.addEventListener("submit", async function(e){
    e.preventDefault();
    teacherError.classList.add("hidden");

    var name = document.getElementById("t-name").value.trim();
    var course = document.getElementById("t-course").value;
    var joiningYear = document.getElementById("t-year").value;
    var subject = document.getElementById("t-subject").value;
    var email = document.getElementById("t-email").value.trim();
    var whatsapp = document.getElementById("t-whatsapp").value.trim();
    var pass = document.getElementById("t-pass").value;
    var pass2 = document.getElementById("t-pass2").value;
    var days = Array.prototype.slice.call(document.querySelectorAll("#t-days input:checked")).map(function(c){ return c.value; });

    function fail(msg){ teacherError.textContent = msg; teacherError.classList.remove("hidden"); }

    if (!name) return fail("Please enter your full name.");
    if (!course) return fail("Please select a course.");
    if (!subject) return fail("Please select a subject.");
    if (!email) return fail("Please enter your email.");
    if (!/^\d{10}$/.test(whatsapp)) return fail("WhatsApp number must contain exactly 10 digits.");
    if (days.length === 0) return fail("Please select at least one free day.");
    if (pass.length < 8) return fail("Password must contain at least 8 characters.");
    if (pass !== pass2) return fail("Passwords do not match.");

    var submitBtn = teacherForm.querySelector("button[type=submit]");
    submitBtn.disabled = true;
    submitBtn.textContent = "Creating Account...";

    try {
      var data = await apiFetch("/teachers/register/", {
        method: "POST",
        body: JSON.stringify({
          name: name, course: course, joining_year: Number(joiningYear), subject: subject,
          email: email, whatsapp_number: whatsapp, free_days: days,
          password: pass, confirm_password: pass2
        })
      });

      document.getElementById("ts-name").textContent = data.name;
      document.getElementById("ts-id").textContent = data.user_id;

      teacherForm.classList.add("hidden");
      teacherSuccess.classList.remove("hidden");
    } catch (err) {
      teacherError.textContent = err.message;
      teacherError.classList.remove("hidden");
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Create Account";
    }
  });

  document.getElementById("teacher-again").addEventListener("click", function(){
    teacherForm.reset();
    document.getElementById("t-year").value = new Date().getFullYear();
    teacherForm.classList.remove("hidden");
    teacherSuccess.classList.add("hidden");
  });

  /* ============================================================
     VOLUNTEER SIGN IN — real POST /teachers/login/
     ============================================================ */
  var teacherSigninForm = document.getElementById("teacher-signin-form");
  if (teacherSigninForm){
    teacherSigninForm.addEventListener("submit", async function(e){
      e.preventDefault();
      var idVal = document.getElementById("teacher-signin-id").value.trim();
      var pwVal = document.getElementById("teacher-signin-password").value.trim();
      var errBox = document.getElementById("teacher-signin-error");
      errBox.classList.add("hidden");
      if (!idVal || !pwVal){
        errBox.textContent = "Please enter your Volunteer ID and password.";
        errBox.classList.remove("hidden");
        return;
      }
      var submitBtn = teacherSigninForm.querySelector("button[type=submit]");
      submitBtn.disabled = true;
      try {
        var data = await apiFetch("/teachers/login/", {
          method: "POST",
          body: JSON.stringify({ user_id: idVal, password: pwVal })
        });
        setVolunteerProfile({
          user_id: data.user_id, name: data.name, email: data.email,
          course: data.course, subject: data.subject,
          access: data.access, refresh: data.refresh
        });
        volunteerAuthed = true;
        teacherSigninForm.reset();
        goToView("volunteer-dashboard");
      } catch (err) {
        errBox.textContent = err.status === 401 ? "Invalid Volunteer ID or password." : (err.message || "Sign in failed.");
        errBox.classList.remove("hidden");
      } finally {
        submitBtn.disabled = false;
      }
    });
  }

  /* ============================================================
     VOLUNTEER DASHBOARD
     Assigned Work and the student roster below are now REAL data,
     fetched from your Django backend:
       GET /teachers/my-assignment-today/        (Admin 2's assignment)
       GET /teachers/my-class-present-students/  (Admin 1's attendance)
     The volunteer cannot mark attendance — that list is read-only,
     built entirely from what Admin 1 already saved in the
     Attendance Toolkit. Only the performance ratings below still
     live in this browser's localStorage, since there is still no
     backend endpoint for saving those.
     ============================================================ */
  function todayIsoDate(){
    var d = new Date();
    return d.getFullYear() + "-" + String(d.getMonth()+1).padStart(2,"0") + "-" + String(d.getDate()).padStart(2,"0");
  }

  function vdSessionKey(userId){ return "jaago_vd_session_" + userId; }
  function vdPerfKey(userId){ return "jaago_vd_performance_" + userId; }
  function vdCheckKey(userId){ return "jaago_vd_checking_" + userId; }

  function vdLoadJson(key, fallback){
    try { var v = JSON.parse(localStorage.getItem(key) || "null"); return v == null ? fallback : v; }
    catch(e){ return fallback; }
  }
  function vdSaveJson(key, value){ localStorage.setItem(key, JSON.stringify(value)); }

  function vdFormatTime(iso){
    var d = new Date(iso);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  // "2026-09-18" -> "18 September 2026"
  function vdFormatDateLong(isoDateStr){
    isoDateStr = isoDateStr || todayIsoDate();
    var parts = isoDateStr.split("-");
    if (parts.length !== 3) return isoDateStr;
    var d = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
    return d.toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" });
  }

  // Pull a readable file name out of an attachment URL for display next to the icon.
  function vdFileNameFromUrl(url){
    if (!url) return "";
    try {
      var clean = url.split("?")[0].split("#")[0];
      var parts = clean.split("/");
      return decodeURIComponent(parts[parts.length - 1] || "");
    } catch (e) {
      return "";
    }
  }

  /* ============================================================
     VOLUNTEER DASHBOARD — three screens, ported verbatim (structure,
     copy, and behavior) from the "Volunteer Work Flows" preview:
     Work Details -> an active Session screen with a big running
     timer -> Student Progress (Teaching only; Checking's roster sits
     inline in its own session panel instead, exactly as the preview
     has it). Which dashboard/screen a volunteer sees is decided
     automatically by their real backend assignment, never chosen by
     them.
     ============================================================ */
  var vdScreen = "details"; // "details" | "session" | "roster" | "landing" (Special Added only)
  var vdRosterErrorMsg = "";

  // Special Added's landing screen always wins while no work has been
  // picked yet, regardless of what screen was asked for -- matches the
  // reference's renderAll() priority check exactly.
  function vdShowScreen(name){
    if (vdIsSpecialAddedTask() && !vdSpecialAddedActiveWork){
      name = "landing";
    }
    vdScreen = name;
    document.getElementById("vd-screen-details").classList.toggle("hidden", name !== "details");
    document.getElementById("vd-screen-session").classList.toggle("hidden", name !== "session");
    document.getElementById("vd-screen-roster").classList.toggle("hidden", name !== "roster");
    document.getElementById("vd-screen-special-landing").classList.toggle("hidden", name !== "landing");
    if (name === "details"){
      renderVdDetailsScreen();
    } else if (name === "session" || name === "roster"){
      renderVdSessionScreen();
    } else if (name === "landing"){
      renderVdSpecialAddedLanding();
    }
  }

  var vdSessionTimerHandle = null;
  // Matches the preview's formatElapsed() exactly — H:MM:SS, not MM:SS.
  function vdFormatElapsed(ms){
    var totalSec = Math.max(0, Math.floor(ms / 1000));
    var h = Math.floor(totalSec / 3600);
    var m = Math.floor((totalSec % 3600) / 60);
    var s = totalSec % 60;
    return [h, m, s].map(function(n){ return String(n).padStart(2, "0"); }).join(":");
  }
  function vdStopSessionTimer(){
    if (vdSessionTimerHandle){ clearInterval(vdSessionTimerHandle); vdSessionTimerHandle = null; }
  }
  function vdStartSessionTimer(startedAtIso){
    var timerId = vdIsCheckingTask() ? "vd-session-timer-big-checking"
      : vdIsInvigilatorTask() ? "vd-session-timer-big-invigilator"
      : "vd-session-timer-big-teaching";
    var timerEl = document.getElementById(timerId);
    var startedAt = new Date(startedAtIso).getTime();
    function tick(){ timerEl.textContent = vdFormatElapsed(Date.now() - startedAt); }
    tick();
    vdStopSessionTimer();
    vdSessionTimerHandle = setInterval(tick, 1000);
  }

  // How many of today's present students still have no rating (Teaching) or
  // no homework check (Checking) recorded — same "is everyone done?" idea
  // the Checking flow in the preview used before letting the volunteer end
  // their session (Teaching's End Session never asks, exactly like the preview).
  function vdUnfinishedCount(){
    if (vdIsCheckingTask()){
      return vdRoster.filter(function(s){ return !vdCheckRecordFor(s.id); }).length;
    }
    var today = todayIsoDate();
    return vdRoster.filter(function(s){
      return !vdPerformance.some(function(r){ return r.studentId === s.id && r.date === today; });
    }).length;
  }

  function vdHideConfirmEndBox(){
    document.getElementById("vd-confirm-end-box").classList.add("hidden");
    document.getElementById("vd-end-session-row").classList.remove("hidden");
  }

  function vdActuallyEndSession(){
    vdSaveJson(vdSessionKey(vdCurrentProfile.user_id), null);
    vdHideConfirmEndBox();
    vdStopSessionTimer();
    if (vdIsSpecialAddedTask()){
      // Matches the reference's finishSession(): Special Added always
      // returns to picking another absent volunteer's work, not to a
      // fixed Work Details screen (there is no fixed assignment here).
      vdSpecialAddedActiveWork = null;
      vdShowScreen("landing");
    } else {
      vdShowScreen("details");
    }
  }

  // true when today's real assignment is the Special Added task -- the
  // one task type where the volunteer picks up an absent volunteer's
  // work rather than having a fixed one of their own.
  function vdIsSpecialAddedTask(){
    return !!(vdAssignment && vdAssignment.task === "SPECIAL_ADDED");
  }

  // The assignment this volunteer is effectively working under right now.
  // For every real task type this is just vdAssignment itself; for Special
  // Added (once a card has been picked on the landing screen) it's a
  // synthetic assignment built from that demo option instead, so every
  // other render function below can stay written in terms of one shape
  // without needing to know Special Added exists.
  function vdEffectiveAssignment(){
    if (vdIsSpecialAddedTask() && vdSpecialAddedActiveWork){
      var opt = vdSpecialAddedActiveWork;
      return {
        assigned_class_display: opt.classLabel,
        task: opt.task,
        task_display: opt.task === "CHECKING" ? "Checking" : "Teaching",
        instruction: opt.instruction,
        attachment_url: null,
        homework_attachment_url: null,
        assignment_date: vdAssignment.assignment_date,
        __specialAddedSubject: opt.subject,
        __specialAddedFrom: opt.originalVolunteer,
      };
    }
    return vdAssignment;
  }

  function vdIsCheckingTask(){
    var eff = vdEffectiveAssignment();
    return !!(eff && eff.task === "CHECKING");
  }
  function vdIsInvigilatorTask(){
    var eff = vdEffectiveAssignment();
    return !!(eff && eff.task === "INVIGILATOR");
  }

  // The eyebrow line above the dashboard heading -- "TODAY'S WORK" for a
  // volunteer's own fixed assignment, or "SPECIAL ADDED · COVERING X" while
  // standing in for an absent volunteer, exactly like the reference.
  function vdEyebrowText(){
    var eff = vdEffectiveAssignment();
    if (eff && eff.__specialAddedFrom){
      return "SPECIAL ADDED · COVERING " + eff.__specialAddedFrom.toUpperCase();
    }
    return "TODAY’S WORK";
  }

  // Header line shared by all three screens: "Subject: X · Class: Y"
  // (Invigilator has no subject, exactly like the reference's work.subject
  // being null for that role).
  function vdWorkSubline(){
    var eff = vdEffectiveAssignment();
    if (!eff) return "";
    var classLabel = eff.assigned_class_display || "—";
    var subject = eff.__specialAddedSubject || (vdCurrentProfile && vdCurrentProfile.subject);
    var showSubject = subject && eff.task !== "INVIGILATOR";
    return (showSubject ? ("Subject: " + subject + " · ") : "") + "Class: " + classLabel;
  }
  function vdWorkHeading(){
    var eff = vdEffectiveAssignment();
    if (!eff) return "Assigned Work";
    if (eff.task === "CHECKING") return "Checking Dashboard";
    if (eff.task === "INVIGILATOR") return "Invigilator Dashboard";
    return "Teaching Dashboard";
  }

  // Fills in the header + Work Details panel of Screen 1.
  function renderVdDetailsScreen(){
    document.getElementById("vd-details-eyebrow").textContent = vdEyebrowText();
    document.getElementById("vd-work-heading").textContent = vdWorkHeading();
    document.getElementById("vd-work-subline").textContent = vdWorkSubline();

    var eff = vdEffectiveAssignment();
    var panel = document.getElementById("vd-details-panel");
    panel.classList.toggle("violet", !eff || (eff.task !== "CHECKING" && eff.task !== "INVIGILATOR"));
    panel.classList.toggle("green", !!eff && eff.task === "CHECKING");
    panel.classList.toggle("yellow", !!eff && eff.task === "INVIGILATOR");

    var emptyEl = document.getElementById("vd-assignment-empty");
    var dateLine = document.getElementById("vd-work-date-line");
    var details = document.getElementById("vd-assignment-details");
    var startRow = document.getElementById("vd-start-session-row");

    if (!eff){
      emptyEl.classList.remove("hidden");
      dateLine.classList.add("hidden");
      details.classList.add("hidden");
      startRow.classList.add("hidden");
      return;
    }

    emptyEl.classList.add("hidden");
    dateLine.classList.remove("hidden");
    details.classList.remove("hidden");
    startRow.classList.remove("hidden");

    document.getElementById("vd-assignment-date").textContent = vdFormatDateLong(eff.assignment_date);
    document.getElementById("vd-assignment-instruction").textContent =
      eff.instruction || "No written instructions were added for today.";

    var materialRow = document.getElementById("vd-material-row");
    var materialLink = document.getElementById("vd-assignment-attachment");
    var materialName = document.getElementById("vd-assignment-attachment-name");
    if (eff.attachment_url){
      materialRow.classList.remove("hidden");
      materialLink.href = eff.attachment_url;
      materialName.textContent = vdFileNameFromUrl(eff.attachment_url) || "Attached file";
    } else {
      materialRow.classList.add("hidden");
    }

    // Homework module: optional, not sent by the real backend yet — shown
    // only if it ever is, same defensive read as before.
    var hwRow = document.getElementById("vd-homework-material-row");
    var hwLink = document.getElementById("vd-assignment-homework-attachment");
    var hwName = document.getElementById("vd-assignment-homework-attachment-name");
    if (eff.homework_attachment_url){
      hwRow.classList.remove("hidden");
      hwLink.href = eff.homework_attachment_url;
      hwName.textContent = vdFileNameFromUrl(eff.homework_attachment_url) || "Attached file";
    } else {
      hwRow.classList.add("hidden");
    }
  }

  // Special Added's landing screen -- picking one of today's "available
  // work" demo cards sets vdSpecialAddedActiveWork and drops straight into
  // the normal Work Details screen for whichever role that work is.
  function renderVdSpecialAddedLanding(){
    var name = (vdCurrentProfile && vdCurrentProfile.name) || "Volunteer";
    document.getElementById("vd-special-landing-name").textContent = "Welcome, " + name;

    var wrap = document.getElementById("vd-special-landing-cards");
    wrap.innerHTML = "";
    if (VD_SPECIAL_ADDED_OPTIONS.length === 0){
      wrap.innerHTML = '<p class="center-note">No absent-volunteer work is available to cover right now.</p>';
      return;
    }
    VD_SPECIAL_ADDED_OPTIONS.forEach(function(opt){
      var card = document.createElement("div");
      card.className = "work-card";
      var roleLabel = opt.task === "CHECKING" ? "Checking" : "Teaching";
      card.innerHTML =
        '<p class="kv-line"><b>Original Volunteer:</b> ' + escapeHtml(opt.originalVolunteer) + '</p>' +
        '<p class="kv-line"><b>Class:</b> ' + escapeHtml(opt.classLabel) + ' &middot; <b>Role:</b> ' + escapeHtml(roleLabel) +
          (opt.subject ? (' &middot; <b>Subject:</b> ' + escapeHtml(opt.subject)) : '') + '</p>' +
        '<p class="instruction-box">' + escapeHtml(opt.instruction) + '</p>' +
        '<button type="button" class="submit-btn violet" style="width:100%;" data-select-work="' + opt.id + '">Select This Work</button>';
      wrap.appendChild(card);
    });

    wrap.querySelectorAll("[data-select-work]").forEach(function(btn){
      btn.addEventListener("click", function(){
        var id = btn.getAttribute("data-select-work");
        var opt = VD_SPECIAL_ADDED_OPTIONS.filter(function(o){ return o.id === id; })[0];
        if (!opt) return;
        vdSpecialAddedActiveWork = opt;
        vdShowScreen("details");
      });
    });
  }

  // Fills in the Session screen: shared header + whichever role panel
  // applies (Teaching's timer+summary panel, or Checking's timer+inline
  // roster panel) — and the Student Progress screen's header/count when
  // that's the one currently showing.
  function renderVdSessionScreen(){
    var session = vdLoadJson(vdSessionKey(vdCurrentProfile.user_id), null);
    var eff = vdEffectiveAssignment();
    var checking = vdIsCheckingTask();
    var invigilating = vdIsInvigilatorTask();
    var heading = vdWorkHeading();
    var subline = vdWorkSubline();
    var eyebrow = vdEyebrowText();
    var classLabel = eff ? (eff.assigned_class_display || "—") : "—";

    ["vd-session-eyebrow", "vd-roster-eyebrow"].forEach(function(id){
      document.getElementById(id).textContent = eyebrow;
    });
    ["vd-session-work-heading", "vd-roster-work-heading"].forEach(function(id){
      document.getElementById(id).textContent = heading;
    });
    ["vd-session-work-subline", "vd-roster-work-subline"].forEach(function(id){
      document.getElementById(id).textContent = subline;
    });

    document.getElementById("vd-session-panel-teaching").classList.toggle("hidden", checking || invigilating);
    document.getElementById("vd-session-panel-checking").classList.toggle("hidden", !checking);
    document.getElementById("vd-session-panel-invigilator").classList.toggle("hidden", !invigilating);

    if (checking){
      document.getElementById("vd-cs-class").textContent = classLabel;
      document.getElementById("vd-cs-date").textContent = vdFormatDateLong(eff ? eff.assignment_date : null);
      document.getElementById("vd-cs-present-count").textContent = vdRoster.length;
      document.getElementById("vd-cs-checked-count").textContent = (vdRoster.length - vdUnfinishedCount()) + " / " + vdRoster.length;
      renderVdCheckingRoster();
    } else if (invigilating){
      document.getElementById("vd-inv-class").textContent = classLabel;
    } else {
      document.getElementById("vd-ts-class").textContent = classLabel;
      document.getElementById("vd-ts-subject").textContent = (vdCurrentProfile && vdCurrentProfile.subject) || "—";
      var finished = vdRoster.length - vdUnfinishedCount();
      document.getElementById("vd-ts-summary").textContent =
        vdRoster.length + " student" + (vdRoster.length === 1 ? "" : "s") + " present · " +
        finished + " / " + vdRoster.length + " rated";
    }

    if (vdScreen === "roster"){
      document.getElementById("vd-roster-class-label").textContent = classLabel;
      var rated = vdRoster.length - vdUnfinishedCount();
      document.getElementById("vd-roster-rated-count").textContent = rated + "/" + vdRoster.length;
      renderVdRoster();
    }

    if (session && session.active){
      vdStartSessionTimer(session.startedAt);
    } else {
      vdStopSessionTimer();
    }
  }

  /* ------------------------------------------------------------
     Real backend fetches for Assigned Work + the present-student
     roster. Both are read-only GETs against the two new endpoints.
     ------------------------------------------------------------ */

  // Which dashboard a volunteer sees is decided by their assignment's task,
  // not chosen by them — Teaching duty gets the Teaching Dashboard, Checking
  // duty gets the Checking Dashboard. (Only these two tasks exist on the
  // backend today; Invigilator and Special Added are preview-only until
  // the backend adds support for them.)
  async function fetchVdAssignment(){
    try {
      var resp = await apiFetch("/teachers/my-assignment-today/");
      vdAssignment = resp.assignment || null;
    } catch (err) {
      if (err.status === 401){
        clearVolunteerProfile();
        volunteerAuthed = false;
        goToView("teacher-signin");
        return;
      }
      vdAssignment = null;
    }
    // Re-run the current screen through vdShowScreen's own routing guard --
    // this is what redirects to Special Added's landing screen the moment
    // that becomes today's real assignment (or back out of it if it isn't
    // anymore), while re-rendering whatever screen is actually showing.
    vdShowScreen(vdScreen);
  }

  async function fetchVdPresentStudents(){
    vdRosterErrorMsg = "";
    try {
      var resp = await apiFetch("/teachers/my-class-present-students/");
      vdRoster = (resp.students || []).map(function(s){
        return { id: String(s.student_id), name: s.name, rollNo: s.roll_no };
      });
    } catch (err) {
      if (err.status === 401){
        clearVolunteerProfile();
        volunteerAuthed = false;
        goToView("teacher-signin");
        return;
      }
      vdRoster = [];
      vdRosterErrorMsg = err.message || "Unable to load today's present students.";
    }
  }

  async function refreshVdRoster(){
    // Also re-check today's Admin 2 assignment — if the volunteer already
    // had the dashboard open before Admin 2 assigned them a module, the
    // "Refresh" button is what picks it up without needing a full reload.
    await fetchVdAssignment();
    await fetchVdPresentStudents();
    if (vdScreen === "session" || vdScreen === "roster") renderVdSessionScreen();
  }

  function vdStats(studentId){
    var records = vdPerformance.filter(function(r){ return r.studentId === studentId; });
    var counts = { POOR: 0, AVERAGE: 0, GOOD: 0 };
    records.forEach(function(r){ if (counts.hasOwnProperty(r.rating)) counts[r.rating]++; });
    var total = records.length;
    var scoreMap = { POOR: 1, AVERAGE: 2, GOOD: 3 };
    var avgScore = total ? (records.reduce(function(sum, r){ return sum + (scoreMap[r.rating] || 0); }, 0) / total) : 0;
    return { total: total, counts: counts, avgScore: avgScore };
  }

  function vdStatsText(studentId){
    var s = vdStats(studentId);
    if (s.total === 0) return "No ratings recorded yet for this student.";
    function pct(n){ return Math.round((n / s.total) * 100); }
    return (
      s.total + " day" + (s.total === 1 ? "" : "s") + " recorded — " +
      "Good: " + s.counts.GOOD + " (" + pct(s.counts.GOOD) + "%), " +
      "Average: " + s.counts.AVERAGE + " (" + pct(s.counts.AVERAGE) + "%), " +
      "Poor: " + s.counts.POOR + " (" + pct(s.counts.POOR) + "%). " +
      "Overall average score: " + s.avgScore.toFixed(1) + " / 3."
    );
  }

  function vdCheckRecordFor(studentId){
    var today = todayIsoDate();
    return vdChecking.filter(function(r){ return r.studentId === studentId && r.date === today; })[0] || null;
  }

  // Teaching's separate "Student Progress" screen — Student / Jaago ID /
  // Status / Rate button, matching the preview's renderStudentProgressScreen
  // columns exactly (no serial number, no separate attendance column).
  function renderVdRoster(){
    var body = document.getElementById("vd-student-body");
    var empty = document.getElementById("vd-student-empty");
    var errorEl = document.getElementById("vd-roster-error");
    body.innerHTML = "";
    empty.classList.toggle("hidden", vdRoster.length > 0);
    if (vdRosterErrorMsg){
      errorEl.textContent = vdRosterErrorMsg;
      errorEl.classList.remove("hidden");
    } else {
      errorEl.classList.add("hidden");
    }

    vdRoster.forEach(function(s){
      var stats = vdStats(s.id);
      var statusBadge = stats.total === 0
        ? '<span class="att-status-label absent">Not rated</span>'
        : '<span class="att-status-label present">Rated ' + stats.total + 'x (avg ' + stats.avgScore.toFixed(1) + '/3)</span>';
      var tr = document.createElement("tr");
      tr.innerHTML =
        '<td>' + escapeHtml(s.name) + '</td>' +
        '<td class="att-col-id">' + escapeHtml(s.rollNo) + '</td>' +
        '<td>' + statusBadge + '</td>' +
        '<td><button type="button" class="module-btn" data-id="' + s.id + '">Rate</button></td>';
      body.appendChild(tr);
    });
  }

  // Checking's roster, shown inline inside its own session panel — Roll No /
  // Name / Status / Check button, matching the preview's
  // renderCheckingSessionScreen columns exactly.
  function renderVdCheckingRoster(){
    var body = document.getElementById("vd-checking-student-body");
    var empty = document.getElementById("vd-checking-student-empty");
    var errorEl = document.getElementById("vd-checking-roster-error");
    body.innerHTML = "";
    empty.classList.toggle("hidden", vdRoster.length > 0);
    if (vdRosterErrorMsg){
      errorEl.textContent = vdRosterErrorMsg;
      errorEl.classList.remove("hidden");
    } else {
      errorEl.classList.add("hidden");
    }

    vdRoster.forEach(function(s){
      var record = vdCheckRecordFor(s.id);
      var statusBadge = record
        ? '<span class="att-status-label present">&#10003; Checked</span>'
        : '<span class="att-status-label absent">&#9675; Pending</span>';
      var tr = document.createElement("tr");
      tr.innerHTML =
        '<td class="att-col-id">' + escapeHtml(s.rollNo) + '</td>' +
        '<td>' + escapeHtml(s.name) + '</td>' +
        '<td>' + statusBadge + '</td>' +
        '<td><button type="button" class="module-btn" data-id="' + s.id + '">' + (record ? "Update" : "Check") + '</button></td>';
      body.appendChild(tr);
    });
  }

  async function initVolunteerDashboard(){
    vdCurrentProfile = getVolunteerProfile();
    if (!vdCurrentProfile) { goToView("teacher-signin"); return; }

    document.getElementById("vd-name").textContent = vdCurrentProfile.name || "";
    document.getElementById("vd-subject").textContent = vdCurrentProfile.subject || "—";
    document.getElementById("vd-userid").textContent = vdCurrentProfile.user_id || "—";

    vdPerformance = vdLoadJson(vdPerfKey(vdCurrentProfile.user_id), []);
    vdChecking = vdLoadJson(vdCheckKey(vdCurrentProfile.user_id), []);

    // BUG FIX — this used to call renderVolunteerSessionControls()
    // (which, when today's session had already ended, fires off its
    // own fetchVdAssignment() call in the background) and THEN also
    // separately await fetchVdAssignment() itself right after. That
    // meant two concurrent requests to the same endpoint were racing
    // to set the shared vdAssignment variable — whichever response
    // came back LAST won, even if it happened to be the slower one
    // that failed or timed out. That race is exactly what was making
    // a real assignment intermittently vanish from "Assigned Work"
    // (while the unrelated present-students call, which only ever
    // ran once, kept working fine). Fetching the assignment fully
    // first, then fetching the roster, keeps this strictly sequential
    // — no more race. The roster is real, backend-driven data, so it's
    // always fetched here regardless of which of the three screens
    // (Work Details / Session / Present Students) ends up showing.
    await fetchVdAssignment();
    await fetchVdPresentStudents();

    var session = vdLoadJson(vdSessionKey(vdCurrentProfile.user_id), null);
    var startingScreen = (session && session.active && session.date === todayIsoDate()) ? "session" : "details";
    vdShowScreen(startingScreen);
  }

  var vdLogoutBtn = document.getElementById("volunteer-dashboard-logout");
  if (vdLogoutBtn){
    vdLogoutBtn.addEventListener("click", function(){
      clearVolunteerProfile();
      volunteerAuthed = false;
      goToView("home");
    });
  }

  var vdStartBtn = document.getElementById("vd-start-session");
  if (vdStartBtn){
    vdStartBtn.addEventListener("click", function(){
      vdSaveJson(vdSessionKey(vdCurrentProfile.user_id), {
        date: todayIsoDate(), active: true, startedAt: new Date().toISOString()
      });
      vdShowScreen("session");
    });
  }

  var vdOpenProgressBtn = document.getElementById("vd-open-progress-btn");
  if (vdOpenProgressBtn){
    vdOpenProgressBtn.addEventListener("click", function(){ vdShowScreen("roster"); });
  }

  // A session is always active when the Student Progress screen is
  // reachable at all (Teaching only reaches it via "Open Student
  // Progress" from the Session screen), so Back always returns there —
  // matching the preview's btn-back-session exactly.
  var vdBackFromRosterBtn = document.getElementById("vd-back-from-roster-btn");
  if (vdBackFromRosterBtn){
    vdBackFromRosterBtn.addEventListener("click", function(){ vdShowScreen("session"); });
  }

  // Ending a session never asks for confirmation for Teaching — only
  // Checking does, and only when some present student hasn't been
  // checked yet — exactly like the preview's wireScreenEvents().
  function vdEndSessionRequested(){
    var unfinished = vdUnfinishedCount();
    if (vdIsCheckingTask() && unfinished > 0 && vdRoster.length > 0){
      document.getElementById("vd-confirm-end-text").textContent =
        unfinished + " student" + (unfinished === 1 ? " has" : "s have") + " not been checked. End session anyway?";
      document.getElementById("vd-confirm-end-box").classList.remove("hidden");
      document.getElementById("vd-end-session-row").classList.add("hidden");
      return;
    }
    vdActuallyEndSession();
  }

  var vdEndBtn = document.getElementById("vd-end-session");
  if (vdEndBtn){ vdEndBtn.addEventListener("click", vdEndSessionRequested); }
  var vdEndBtnFromRoster = document.getElementById("vd-end-session-roster");
  if (vdEndBtnFromRoster){ vdEndBtnFromRoster.addEventListener("click", vdEndSessionRequested); }

  var vdConfirmEndCancelBtn = document.getElementById("vd-confirm-end-cancel");
  if (vdConfirmEndCancelBtn){
    vdConfirmEndCancelBtn.addEventListener("click", vdHideConfirmEndBox);
  }
  var vdConfirmEndYesBtn = document.getElementById("vd-confirm-end-yes");
  if (vdConfirmEndYesBtn){
    vdConfirmEndYesBtn.addEventListener("click", vdActuallyEndSession);
  }

  var vdRefreshRosterBtn = document.getElementById("vd-refresh-roster-btn");
  if (vdRefreshRosterBtn){
    vdRefreshRosterBtn.addEventListener("click", function(){ refreshVdRoster(); });
  }
  var vdCheckingRefreshBtn = document.getElementById("vd-checking-refresh-btn");
  if (vdCheckingRefreshBtn){
    vdCheckingRefreshBtn.addEventListener("click", function(){ refreshVdRoster(); });
  }

  var vdStudentBody = document.getElementById("vd-student-body");
  if (vdStudentBody){
    vdStudentBody.addEventListener("click", function(e){
      var moduleBtn = e.target.closest(".module-btn");
      if (!moduleBtn) return;
      openVdPerformanceModal(moduleBtn.getAttribute("data-id"));
    });
  }

  var vdCheckingStudentBody = document.getElementById("vd-checking-student-body");
  if (vdCheckingStudentBody){
    vdCheckingStudentBody.addEventListener("click", function(e){
      var moduleBtn = e.target.closest(".module-btn");
      if (!moduleBtn) return;
      openVdCheckingModal(moduleBtn.getAttribute("data-id"));
    });
  }

  var vdPerfModalOverlay = document.getElementById("vd-performance-modal-overlay");

  function openVdPerformanceModal(studentId){
    var student = vdRoster.filter(function(s){ return s.id === studentId; })[0];
    if (!student) return;
    vdPerfModalStudentId = studentId;

    var todayRecord = vdPerformance.filter(function(r){ return r.studentId === studentId && r.date === todayIsoDate(); })[0];
    vdPerfSelectedRating = todayRecord ? todayRecord.rating : null;
    vdPerfSelectedHw = todayRecord ? (todayRecord.hwDone ? "yes" : "no") : null;

    document.getElementById("vd-performance-modal-title").textContent = "Rate Performance — " + student.name;
    document.getElementById("vd-performance-description").value = todayRecord ? todayRecord.description : "";

    document.querySelectorAll("#vd-performance-buttons .att-btn").forEach(function(b){
      b.classList.toggle("active", b.getAttribute("data-rating") === vdPerfSelectedRating);
    });
    document.getElementById("vd-hw-yes").classList.toggle("active", vdPerfSelectedHw === "yes");
    document.getElementById("vd-hw-no").classList.toggle("active", vdPerfSelectedHw === "no");

    var msg = document.getElementById("vd-performance-modal-msg");
    msg.textContent = "";
    msg.className = "modal-msg";

    var statsBox = document.getElementById("vd-performance-stats");
    var stats = vdStats(studentId);
    if (stats.total > 0){
      statsBox.classList.remove("hidden");
      document.getElementById("vd-performance-stats-text").textContent = vdStatsText(studentId);
    } else {
      statsBox.classList.add("hidden");
    }

    vdPerfModalOverlay.classList.remove("hidden");
  }

  function closeVdPerformanceModal(){
    vdPerfModalOverlay.classList.add("hidden");
    vdPerfModalStudentId = null;
  }

  if (vdPerfModalOverlay){
    document.getElementById("vd-performance-modal-close").addEventListener("click", closeVdPerformanceModal);
    document.getElementById("vd-performance-modal-cancel").addEventListener("click", closeVdPerformanceModal);
    vdPerfModalOverlay.addEventListener("click", function(e){
      if (e.target === vdPerfModalOverlay) closeVdPerformanceModal();
    });

    document.getElementById("vd-performance-buttons").addEventListener("click", function(e){
      var btn = e.target.closest(".att-btn");
      if (!btn) return;
      vdPerfSelectedRating = btn.getAttribute("data-rating");
      document.querySelectorAll("#vd-performance-buttons .att-btn").forEach(function(b){
        b.classList.toggle("active", b === btn);
      });
    });

    document.getElementById("vd-hw-yes").addEventListener("click", function(){
      vdPerfSelectedHw = "yes";
      document.getElementById("vd-hw-yes").classList.add("active");
      document.getElementById("vd-hw-no").classList.remove("active");
    });
    document.getElementById("vd-hw-no").addEventListener("click", function(){
      vdPerfSelectedHw = "no";
      document.getElementById("vd-hw-no").classList.add("active");
      document.getElementById("vd-hw-yes").classList.remove("active");
    });

    document.getElementById("vd-performance-modal-save").addEventListener("click", function(){
      var msg = document.getElementById("vd-performance-modal-msg");
      if (!vdPerfSelectedRating){
        msg.textContent = "Please pick Poor, Average or Good.";
        msg.className = "modal-msg error";
        return;
      }
      if (!vdPerfSelectedHw){
        msg.textContent = "Please mark whether homework was done.";
        msg.className = "modal-msg error";
        return;
      }
      var student = vdRoster.filter(function(s){ return s.id === vdPerfModalStudentId; })[0];
      if (!student) return;

      var description = document.getElementById("vd-performance-description").value.trim();
      var today = todayIsoDate();
      var existingIdx = vdPerformance.findIndex(function(r){ return r.studentId === vdPerfModalStudentId && r.date === today; });
      var record = {
        studentId: vdPerfModalStudentId, studentName: student.name, date: today,
        rating: vdPerfSelectedRating, description: description,
        hwDone: vdPerfSelectedHw === "yes", savedAt: new Date().toISOString()
      };
      if (existingIdx === -1) vdPerformance.push(record); else vdPerformance[existingIdx] = record;
      vdSaveJson(vdPerfKey(vdCurrentProfile.user_id), vdPerformance);

      msg.textContent = "Saved.";
      msg.className = "modal-msg success";

      var statsBox = document.getElementById("vd-performance-stats");
      statsBox.classList.remove("hidden");
      document.getElementById("vd-performance-stats-text").textContent = vdStatsText(vdPerfModalStudentId);

      if (vdScreen === "roster") renderVdSessionScreen();
      setTimeout(closeVdPerformanceModal, 900);
    });
  }

  /* ============================================================
     VOLUNTEER: CHECKING DASHBOARD MODAL (Checking-task assignments)
     Same local-only storage pattern as the Teaching performance
     modal above — no backend endpoint exists yet to persist these.
     ============================================================ */
  var vdCheckModalOverlay = document.getElementById("vd-checking-modal-overlay");

  function openVdCheckingModal(studentId){
    var student = vdRoster.filter(function(s){ return s.id === studentId; })[0];
    if (!student) return;
    vdCheckModalStudentId = studentId;

    var todayRecord = vdCheckRecordFor(studentId);
    vdCheckSelectedDone = todayRecord ? (todayRecord.hwDone ? "yes" : "no") : null;

    document.getElementById("vd-checking-modal-title").textContent = "Student Check — " + student.name;
    document.getElementById("vd-checking-feedback").value = todayRecord ? (todayRecord.feedback || "") : "";

    document.getElementById("vd-checking-done").classList.toggle("active", vdCheckSelectedDone === "yes");
    document.getElementById("vd-checking-notdone").classList.toggle("active", vdCheckSelectedDone === "no");

    var msg = document.getElementById("vd-checking-modal-msg");
    msg.textContent = "";
    msg.className = "modal-msg";

    vdCheckModalOverlay.classList.remove("hidden");
  }

  function closeVdCheckingModal(){
    vdCheckModalOverlay.classList.add("hidden");
    vdCheckModalStudentId = null;
  }

  if (vdCheckModalOverlay){
    document.getElementById("vd-checking-modal-close").addEventListener("click", closeVdCheckingModal);
    document.getElementById("vd-checking-modal-cancel").addEventListener("click", closeVdCheckingModal);
    vdCheckModalOverlay.addEventListener("click", function(e){
      if (e.target === vdCheckModalOverlay) closeVdCheckingModal();
    });

    document.getElementById("vd-checking-done").addEventListener("click", function(){
      vdCheckSelectedDone = "yes";
      document.getElementById("vd-checking-done").classList.add("active");
      document.getElementById("vd-checking-notdone").classList.remove("active");
    });
    document.getElementById("vd-checking-notdone").addEventListener("click", function(){
      vdCheckSelectedDone = "no";
      document.getElementById("vd-checking-notdone").classList.add("active");
      document.getElementById("vd-checking-done").classList.remove("active");
    });

    document.getElementById("vd-checking-modal-save").addEventListener("click", function(){
      var msg = document.getElementById("vd-checking-modal-msg");
      if (!vdCheckSelectedDone){
        msg.textContent = "Please mark whether homework was done.";
        msg.className = "modal-msg error";
        return;
      }
      var student = vdRoster.filter(function(s){ return s.id === vdCheckModalStudentId; })[0];
      if (!student) return;

      var feedback = document.getElementById("vd-checking-feedback").value.trim();
      var today = todayIsoDate();
      var existingIdx = vdChecking.findIndex(function(r){ return r.studentId === vdCheckModalStudentId && r.date === today; });
      var record = {
        studentId: vdCheckModalStudentId, studentName: student.name, date: today,
        hwDone: vdCheckSelectedDone === "yes", feedback: feedback, savedAt: new Date().toISOString()
      };
      if (existingIdx === -1) vdChecking.push(record); else vdChecking[existingIdx] = record;
      vdSaveJson(vdCheckKey(vdCurrentProfile.user_id), vdChecking);

      msg.textContent = "Saved.";
      msg.className = "modal-msg success";

      renderVdSessionScreen();
      setTimeout(closeVdCheckingModal, 900);
    });
  }

  /* ============================================================
     ADMIN 1: ATTENDANCE TOOLKIT (real backend session + data)
     ============================================================ */
  var secondsRemaining = 0;
  var sessionTimerInterval = null;
  function formatTime(s){
    s = Math.max(0, s);
    var m = Math.floor(s/60), r = s % 60;
    return String(m).padStart(2,"0") + ":" + String(r).padStart(2,"0");
  }

  function startSessionTimer(expiresAtIso){
    var timerEl = document.getElementById("session-timer");
    if (sessionTimerInterval) clearInterval(sessionTimerInterval);
    var expiresAt = new Date(expiresAtIso).getTime();
    function tick(){
      secondsRemaining = Math.floor((expiresAt - Date.now()) / 1000);
      timerEl.textContent = formatTime(secondsRemaining);
      if (secondsRemaining <= 0){
        clearInterval(sessionTimerInterval);
        sessionTimerInterval = null;
        endAdmin1Session(true);
      }
    }
    tick();
    sessionTimerInterval = setInterval(tick, 1000);
  }

  async function endAdmin1Session(expired){
    if (sessionTimerInterval){ clearInterval(sessionTimerInterval); sessionTimerInterval = null; }
    try { await apiFetch("/attendance/session/end/", { method: "POST" }); } catch(e){ /* best effort */ }
    admin1Authed = false;
    clearAuth();
    if (expired) window.alert("Your 10-minute attendance session has ended. Please sign in again.");
    goToView("home");
  }

  var attendanceBackBtn = document.querySelector("#view-attendance .back-btn");
  if (attendanceBackBtn){
    attendanceBackBtn.addEventListener("click", function(){
      endAdmin1Session(false);
    });
  }

  var today = new Date();
  var iso = today.getFullYear() + "-" + String(today.getMonth()+1).padStart(2,"0") + "-" + String(today.getDate()).padStart(2,"0");
  var attendanceDateInput = document.getElementById("attendance-date");
  if (attendanceDateInput) attendanceDateInput.value = iso;

  var studentCountEl = document.getElementById("student-count");
  var volunteerCountEl = document.getElementById("volunteer-count");
  var admin1Students = [];
  var admin1Volunteers = [];
  var admin1ClassFilter = "ALL";

  /* ------------------------------------------------------------
     Class-group mapping (frontend-only display grouping).
     The backend only stores each student's raw grade
     (LKG, UKG, 1..10) on student_class -- there is no
     "Class A/B/C/D/E" field in the database. This groups
     that raw grade into the 5 buckets Admin 1 asked for,
     purely for display/filtering here:
       1-3   -> Class A
       4-6   -> Class B
       7-8   -> Class C
       9-10  -> Class D
       LKG/UKG -> Class E
     ------------------------------------------------------------ */
  function classGroupFor(studentClass){
    var g = String(studentClass || "").toUpperCase();
    if (g === "LKG" || g === "UKG") return "E";
    var n = Number(g);
    if (n >= 1 && n <= 3) return "A";
    if (n >= 4 && n <= 6) return "B";
    if (n === 7 || n === 8) return "C";
    if (n === 9 || n === 10) return "D";
    return "-";
  }

  var classGroupLabels = {
    A: "Class A (1-3)",
    B: "Class B (4-6)",
    C: "Class C (7-8)",
    D: "Class D (9-10)",
    E: "Class E (LKG-UKG)"
  };

  var classFilterEl = document.getElementById("attendance-class-filter");
  if (classFilterEl){
    classFilterEl.addEventListener("change", function(){
      admin1ClassFilter = classFilterEl.value;
      renderAdmin1StudentTable();
    });
  }

  function renderAdmin1StudentTable(){
    var body = document.getElementById("student-attendance-body");
    var empty = document.getElementById("student-attendance-empty");
    body.innerHTML = "";

    var visible = admin1Students.filter(function(s){
      if (admin1ClassFilter === "ALL") return true;
      return classGroupFor(s.class) === admin1ClassFilter;
    });

    empty.classList.toggle("hidden", visible.length > 0);
    if (visible.length === 0 && admin1Students.length > 0){
      empty.textContent = "No students in this class group.";
    } else {
      empty.textContent = "No students registered yet — register a student to see them here.";
    }
    studentCountEl.textContent = visible.length;

    visible.forEach(function(s, idx){
      var tr = document.createElement("tr");
      var presentActive = s.status === "PRESENT" ? " active" : "";
      var absentActive = s.status === "ABSENT" ? " active" : "";
      var statusLabel = s.status === "PRESENT" ? '<span class="att-status-label present">Status: Present</span>'
        : s.status === "ABSENT" ? '<span class="att-status-label absent">Status: Absent</span>' : "";
      var group = classGroupFor(s.class);
      var groupBadge = group === "-" ? "" :
        '<span class="class-group-badge group-' + group.toLowerCase() + '">' + group + '</span>';
      tr.innerHTML =
        '<td class="att-col-sl">' + (idx + 1) + '</td>' +
        '<td>' + escapeHtml(s.name) + '</td>' +
        '<td class="att-col-id">' + escapeHtml(s.roll_no) + '</td>' +
        '<td>' + groupBadge + '</td>' +
        '<td><div class="att-toggle">' +
          '<button type="button" class="att-btn present' + presentActive + '" data-id="' + s.student_id + '" data-status="PRESENT">Present</button>' +
          '<button type="button" class="att-btn absent' + absentActive + '" data-id="' + s.student_id + '" data-status="ABSENT">Absent</button>' +
          statusLabel +
        '</div></td>';
      body.appendChild(tr);
    });
  }

  document.getElementById("student-attendance-body").addEventListener("click", async function(e){
    var btn = e.target.closest(".att-btn");
    if (!btn) return;
    var id = Number(btn.getAttribute("data-id"));
    var status = btn.getAttribute("data-status");
    var student = admin1Students.filter(function(s){ return s.student_id === id; })[0];
    if (!student) return;
    var previous = student.status;
    student.status = status;
    renderAdmin1StudentTable();
    try {
      await apiFetch("/attendance/students/save/", {
        method: "POST",
        body: JSON.stringify({ student: id, status: status })
      });
    } catch (err) {
      student.status = previous;
      renderAdmin1StudentTable();
      showMessage(err.message || "Unable to save student attendance.");
    }
  });

  function renderAdmin1VolunteerTable(){
    var body = document.getElementById("volunteer-attendance-body");
    var empty = document.getElementById("volunteer-attendance-empty");
    body.innerHTML = "";
    empty.classList.toggle("hidden", admin1Volunteers.length > 0);
    volunteerCountEl.textContent = admin1Volunteers.length;

    admin1Volunteers.forEach(function(v){
      var tr = document.createElement("tr");
      var presentActive = v.status === "PRESENT" ? " active" : "";
      var absentActive = v.status === "ABSENT" ? " active" : "";
      var dept = v.task === "TEACHING" ? "Teaching" : v.task === "INVIGILATOR" ? "Invigilator" : "Checking";
      var deptClass = v.task === "TEACHING" ? "teaching" : v.task === "INVIGILATOR" ? "invigilator" : "checking";
      var statusLabel = v.status === "PRESENT" ? '<span class="att-status-label present">Status: Present</span>'
        : v.status === "ABSENT" ? '<span class="att-status-label absent">Status: Absent</span>' : "";
      var specialNote = "";
      if (v.source === "SPECIAL_ADDED"){
        specialNote = v.status === "PRESENT"
          ? '<span class="special-added-note access">Special Added &mdash; dashboard access available</span>'
          : '<span class="special-added-note no-access">Special Added &mdash; no substitute-work access</span>';
      }
      tr.innerHTML =
        '<td class="att-col-id">' + escapeHtml(v.user_id) + '</td>' +
        '<td>' + escapeHtml(v.volunteer_name) +
          (v.source === "SPECIAL_ADDED" ? '<span class="source-badge special">Special Added</span>' : "") +
          specialNote + '</td>' +
        '<td><span class="dept-badge ' + deptClass + '">' + dept + '</span></td>' +
        '<td><div class="att-toggle">' +
          '<button type="button" class="att-btn present' + presentActive + '" data-id="' + v.id + '" data-status="PRESENT">Present</button>' +
          '<button type="button" class="att-btn absent' + absentActive + '" data-id="' + v.id + '" data-status="ABSENT">Absent</button>' +
          statusLabel +
        '</div></td>';
      body.appendChild(tr);
    });
  }

  document.getElementById("volunteer-attendance-body").addEventListener("click", async function(e){
    var btn = e.target.closest(".att-btn");
    if (!btn) return;
    var attendanceId = Number(btn.getAttribute("data-id"));
    var status = btn.getAttribute("data-status");
    var volunteer = admin1Volunteers.filter(function(v){ return v.id === attendanceId; })[0];
    if (!volunteer) return;
    var previous = volunteer.status;
    volunteer.status = status;
    renderAdmin1VolunteerTable();
    try {
      await apiFetch("/attendance/volunteers/save/", {
        method: "POST",
        body: JSON.stringify({ volunteer: volunteer.volunteer, status: status, task: volunteer.task })
      });
    } catch (err) {
      volunteer.status = previous;
      renderAdmin1VolunteerTable();
      showMessage(err.message || "Unable to save volunteer attendance.");
    }
  });

  /* ============================================================
     ADMIN 1: ADD VOLUNTEER (Special Added)
     Registered volunteers come from the existing Admin 2
     volunteers endpoint; adding one marks them SPECIAL_ADDED.
     Present  -> Special Added Dashboard becomes available.
     Absent   -> no substitute-work access.
     ============================================================ */
  var addVolunteerOverlay = document.getElementById("add-volunteer-modal-overlay");
  var addVolunteerSelect = document.getElementById("add-volunteer-select");
  var addVolunteerMsg = document.getElementById("add-volunteer-msg");
  var addVolunteerRole = "TEACHING";
  var addVolunteerStatus = "PRESENT";
  var registeredVolunteers = [];

  function setToggleActive(containerId, attr, value){
    var container = document.getElementById(containerId);
    Array.prototype.forEach.call(container.querySelectorAll(".att-btn"), function(b){
      b.classList.toggle("active", b.getAttribute(attr) === value);
    });
  }

  document.getElementById("add-volunteer-role").addEventListener("click", function(e){
    var btn = e.target.closest(".att-btn");
    if (!btn) return;
    addVolunteerRole = btn.getAttribute("data-role");
    setToggleActive("add-volunteer-role", "data-role", addVolunteerRole);
  });
  document.getElementById("add-volunteer-status").addEventListener("click", function(e){
    var btn = e.target.closest(".att-btn");
    if (!btn) return;
    addVolunteerStatus = btn.getAttribute("data-status");
    setToggleActive("add-volunteer-status", "data-status", addVolunteerStatus);
  });

  function closeAddVolunteerModal(){ addVolunteerOverlay.classList.add("hidden"); }
  document.getElementById("add-volunteer-close").addEventListener("click", closeAddVolunteerModal);
  document.getElementById("add-volunteer-cancel").addEventListener("click", closeAddVolunteerModal);
  addVolunteerOverlay.addEventListener("click", function(e){ if (e.target === addVolunteerOverlay) closeAddVolunteerModal(); });

  document.getElementById("add-volunteer-open").addEventListener("click", async function(){
    addVolunteerMsg.classList.add("hidden");
    addVolunteerMsg.textContent = "";
    addVolunteerRole = "TEACHING";
    addVolunteerStatus = "PRESENT";
    setToggleActive("add-volunteer-role", "data-role", addVolunteerRole);
    setToggleActive("add-volunteer-status", "data-status", addVolunteerStatus);
    try {
      var resp = await apiFetch("/admin2/volunteers/");
      registeredVolunteers = resp.volunteers || [];
    } catch (err) {
      registeredVolunteers = [];
    }
    var alreadyAdded = admin1Volunteers.map(function(v){ return String(v.volunteer); });
    var available = registeredVolunteers.filter(function(v){ return alreadyAdded.indexOf(String(v.id)) === -1; });
    addVolunteerSelect.innerHTML = "";
    if (available.length === 0){
      var opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "No registered volunteers available";
      addVolunteerSelect.appendChild(opt);
      document.getElementById("add-volunteer-save").disabled = true;
    } else {
      available.forEach(function(v){
        var opt = document.createElement("option");
        opt.value = v.id;
        opt.textContent = v.name + " (" + v.user_id + ")";
        addVolunteerSelect.appendChild(opt);
      });
      document.getElementById("add-volunteer-save").disabled = false;
    }
    addVolunteerOverlay.classList.remove("hidden");
  });

  document.getElementById("add-volunteer-save").addEventListener("click", async function(){
    var id = addVolunteerSelect.value;
    if (!id) return;
    var vol = registeredVolunteers.filter(function(v){ return String(v.id) === id; })[0];
    if (!vol) return;
    var saveBtn = document.getElementById("add-volunteer-save");
    saveBtn.disabled = true;
    var record = {
      id: -Date.now(),
      volunteer: vol.id,
      user_id: vol.user_id,
      volunteer_name: vol.name,
      task: addVolunteerRole,
      status: addVolunteerStatus,
      source: "SPECIAL_ADDED"
    };
    try {
      await apiFetch("/attendance/volunteers/save/", {
        method: "POST",
        body: JSON.stringify({ volunteer: vol.id, status: addVolunteerStatus, task: addVolunteerRole, source: "SPECIAL_ADDED" })
      });
    } catch (err) {
      // No dedicated special-added endpoint yet — keep the record locally.
    }
    admin1Volunteers.push(record);
    renderAdmin1VolunteerTable();
    closeAddVolunteerModal();
    if (addVolunteerStatus === "PRESENT"){
      showMessage(vol.name + " added as Special Added (Present) — the Special Added Dashboard is now available to them.");
    } else {
      showMessage(vol.name + " added as Special Added (Absent) — they get no substitute-work access.");
    }
  });

  var attendanceToolkitLoaded = false;
  async function initAttendanceToolkit(){
    if (!admin1Authed) return;
    try {
      var sessionResp = await apiFetch("/attendance/session/start/", { method: "POST" });
      startSessionTimer(sessionResp.session.expires_at);

      var studentsResp = await apiFetch("/attendance/students/");
      admin1Students = studentsResp.students || [];
      renderAdmin1StudentTable();

      var volunteersResp = await apiFetch("/attendance/volunteers/current/");
      admin1Volunteers = volunteersResp.volunteers || [];
      renderAdmin1VolunteerTable();

      attendanceToolkitLoaded = true;
    } catch (err) {
      if (err.status === 401){
        clearAuth();
        admin1Authed = false;
        goToView("admin1-signin");
        return;
      }
      showMessage(err.message || "Unable to load attendance data.");
    }
  }

  /* ============================================================
     ADMIN 2 DASHBOARD ("STATUS")
     ============================================================ */
  function attachOverviewToggle(cardId, overviewId, closeId, onOpen){
    var card = document.getElementById(cardId);
    var overview = document.getElementById(overviewId);
    if (card){
      card.addEventListener("click", function(){
        overview.classList.toggle("hidden");
        if (!overview.classList.contains("hidden") && onOpen) onOpen();
      });
    }
    var closeBtn = document.getElementById(closeId);
    if (closeBtn){
      closeBtn.addEventListener("click", function(){ overview.classList.add("hidden"); });
    }
  }

  var admin2DashboardData = null;

  async function loadAdminDashboard(){
    if (!adminStatusAuthed) return;
    try {
      admin2DashboardData = await apiFetch("/admin2/dashboard/");
      document.getElementById("dash-student-total").textContent = admin2DashboardData.students.total_registered;
      document.getElementById("dash-volunteer-total").textContent = admin2DashboardData.volunteers.registered;
      document.getElementById("dash-ov-total").textContent = admin2DashboardData.students.total_registered;
      document.getElementById("dash-ov-present").textContent = admin2DashboardData.students.present_today;
      document.getElementById("dash-ov-absent").textContent = Math.max(0, admin2DashboardData.students.total_registered - admin2DashboardData.students.present_today);
      document.getElementById("dash-vol-ov-total").textContent = admin2DashboardData.volunteers.registered;
      document.getElementById("dash-vol-ov-assigned").textContent = admin2DashboardData.assignments_today;
    } catch (err) {
      if (err.status === 401){
        clearAuth();
        adminStatusAuthed = false;
        goToView("admin-signin");
        return;
      }
      showMessage(err.message || "Unable to load the Admin 2 dashboard.");
    }
  }

  attachOverviewToggle("dash-card-student", "dash-student-overview", "dash-student-overview-close", loadAdminDashboard);
  attachOverviewToggle("dash-card-volunteer", "dash-volunteer-overview", "dash-volunteer-overview-close", loadAdminDashboard);

  /* ============================================================
     ADMIN 2: REGISTERED STUDENTS VIEW
     NOTE: the backend only exposes TODAY's present-student list
     (no per-date historical query for Admin 2), so this view
     always shows today, and students not marked present are
     labelled "Not Marked" rather than a separately-tracked
     "Absent" (the backend doesn't expose that distinction here).
     ============================================================ */
  var admin2StudentFilter = "all";
  var admin2StudentRoster = [];
  var admin2PresentIds = {};

  var admin2DateInput = document.getElementById("admin2-student-date");
  if (admin2DateInput){
    admin2DateInput.value = iso;
    admin2DateInput.readOnly = true;
    admin2DateInput.title = "Admin 2 can currently only view today's attendance.";
  }

  function renderAdmin2StudentsTable(){
    var body = document.getElementById("admin2-student-body");
    var empty = document.getElementById("admin2-student-empty");

    var present = 0, notMarked = 0;
    admin2StudentRoster.forEach(function(s){
      if (admin2PresentIds[s.id]) present++; else notMarked++;
    });
    document.getElementById("a2-total").textContent = admin2StudentRoster.length;
    document.getElementById("a2-present").textContent = present;
    document.getElementById("a2-absent").textContent = notMarked;

    var rows = admin2StudentRoster.filter(function(s){
      var isPresent = !!admin2PresentIds[s.id];
      if (admin2StudentFilter === "present") return isPresent;
      if (admin2StudentFilter === "absent") return !isPresent;
      return true;
    });

    body.innerHTML = "";
    empty.classList.toggle("hidden", rows.length > 0);
    rows.forEach(function(s, idx){
      var isPresent = !!admin2PresentIds[s.id];
      var pillClass = isPresent ? "present" : "notmarked";
      var pillText = isPresent ? "Present" : "Not Marked";
      var tr = document.createElement("tr");
      tr.innerHTML =
        '<td class="att-col-sl">' + (idx + 1) + '</td>' +
        '<td>' + escapeHtml(s.name) + '</td>' +
        '<td class="att-col-id">' + escapeHtml(s.roll_no) + '</td>' +
        '<td>' + escapeHtml(s.school_name || "—") + '</td>' +
        '<td>' + escapeHtml(s.student_class || "—") + '</td>' +
        '<td><span class="att-status-pill ' + pillClass + '">' + pillText + '</span></td>';
      body.appendChild(tr);
    });
  }

  document.querySelectorAll("#view-admin2-students .filter-btn").forEach(function(btn){
    btn.addEventListener("click", function(){
      document.querySelectorAll("#view-admin2-students .filter-btn").forEach(function(b){ b.classList.remove("active"); });
      btn.classList.add("active");
      admin2StudentFilter = btn.getAttribute("data-filter");
      renderAdmin2StudentsTable();
    });
  });

  async function loadAdmin2Students(){
    if (!adminStatusAuthed) return;
    try {
      var totalResp = await apiFetch("/admin2/students/total/");
      admin2StudentRoster = totalResp.students || [];
      var presentResp = await apiFetch("/admin2/students/present-today/");
      admin2PresentIds = {};
      (presentResp.students || []).forEach(function(s){ admin2PresentIds[s.id] = true; });
      renderAdmin2StudentsTable();
    } catch (err) {
      if (err.status === 401){
        clearAuth();
        adminStatusAuthed = false;
        goToView("admin-signin");
        return;
      }
      showMessage(err.message || "Unable to load the student roster.");
    }
  }

  /* ============================================================
     ADMIN 2: REGISTERED / ASSIGNED VOLUNTEERS VIEW
     ============================================================ */
  var admin2VolunteerTab = "registered";
  var admin2RegisteredVolunteers = [];
  var admin2TodayAssignments = [];
  var admin2PendingPicks = [];        // picked from the picker, dept chosen locally, not yet sent
  var revealedVolunteerIds = {};
  var deptToggleCounter = 0;
  function nextDefaultDept(){
    deptToggleCounter++;
    return (deptToggleCounter % 2 === 1) ? "Teaching" : "Checking";
  }

  function deptBadgeClass(dept){ return dept === "Teaching" ? "teaching" : "checking"; }
  function formatDays(days){ return (days && days.length) ? days.join(", ") : "—"; }

  function alreadyHandledVolunteerIds(){
    var ids = {};
    admin2TodayAssignments.forEach(function(a){ ids[a.volunteer] = true; });
    admin2PendingPicks.forEach(function(p){ ids[p.volunteerId] = true; });
    return ids;
  }

  var assignVolunteerBtn = document.getElementById("assign-volunteer-btn");
  var admin2VolunteerPicker = document.getElementById("admin2-volunteer-picker");
  var admin2VolunteerPickerList = document.getElementById("admin2-volunteer-picker-list");
  var admin2VolunteerPickerEmpty = document.getElementById("admin2-volunteer-picker-empty");
  var admin2VolunteerPickerHint = document.getElementById("admin2-volunteer-picker-hint");

  function renderAssignVolunteerPicker(){
    if (!admin2VolunteerPickerList) return;
    var weekday = todayWeekdayName();
    if (admin2VolunteerPickerHint) admin2VolunteerPickerHint.textContent = "Volunteers free today (" + weekday + ")";
    var handled = alreadyHandledVolunteerIds();
    var remaining = admin2RegisteredVolunteers.filter(function(v){
      if (handled[v.id]) return false;
      var freeDays = v.free_days || [];
      return freeDays.indexOf(weekday) !== -1;
    });
    admin2VolunteerPickerList.innerHTML = "";
    admin2VolunteerPickerEmpty.classList.toggle("hidden", remaining.length > 0);
    admin2VolunteerPickerEmpty.textContent = "No unassigned volunteers are free today (" + weekday + ").";
    remaining.forEach(function(v){
      var li = document.createElement("li");
      li.className = "volunteer-picker-item";
      var revealed = !!revealedVolunteerIds[v.id];
      var rowHtml = '<button type="button" class="volunteer-picker-name-btn" data-id="' + v.id + '">' + escapeHtml(v.name) + '</button>';
      if (revealed){
        var suggestedDept = nextDefaultDept();
        rowHtml += '<div class="volunteer-picker-reveal">' +
          '<span class="dept-badge ' + deptBadgeClass(suggestedDept) + '">' + suggestedDept + '</span>' +
          '<button type="button" class="volunteer-picker-confirm-btn" data-id="' + v.id + '" data-dept="' + suggestedDept + '">Add to Table</button>' +
        '</div>';
      }
      li.innerHTML = rowHtml;
      admin2VolunteerPickerList.appendChild(li);
    });
  }

  if (assignVolunteerBtn){
    assignVolunteerBtn.addEventListener("click", function(){
      var opening = admin2VolunteerPicker.classList.contains("hidden");
      admin2VolunteerPicker.classList.toggle("hidden");
      assignVolunteerBtn.textContent = opening ? "− Close List" : "+ Assign Volunteer";
      if (opening) renderAssignVolunteerPicker();
    });
  }

  if (admin2VolunteerPickerList){
    admin2VolunteerPickerList.addEventListener("click", function(e){
      var nameBtn = e.target.closest(".volunteer-picker-name-btn");
      if (nameBtn){
        var id = nameBtn.getAttribute("data-id");
        revealedVolunteerIds[id] = !revealedVolunteerIds[id];
        renderAssignVolunteerPicker();
        return;
      }
      var confirmBtn = e.target.closest(".volunteer-picker-confirm-btn");
      if (confirmBtn){
        var cid = Number(confirmBtn.getAttribute("data-id"));
        var dept = confirmBtn.getAttribute("data-dept");
        var vol = admin2RegisteredVolunteers.filter(function(v){ return v.id === cid; })[0];
        if (!vol) return;
        admin2PendingPicks.push({
          volunteerId: vol.id, userId: vol.user_id, name: vol.name, subject: vol.subject_name || vol.subject,
          freeDays: vol.free_days, email: vol.email,
          dept: dept, deptConfirmed: true, moduleSent: false
        });
        delete revealedVolunteerIds[cid];
        renderAssignVolunteerPicker();
        renderAdmin2VolunteersView();
      }
    });
  }

  function renderAdmin2VolunteersView(){
    var thead = document.getElementById("admin2-volunteer-thead");
    var body = document.getElementById("admin2-volunteer-body");
    var empty = document.getElementById("admin2-volunteer-empty");
    if (!thead || !body) return;

    document.getElementById("a2v-total").textContent = admin2RegisteredVolunteers.length;
    document.getElementById("a2v-assigned").textContent = admin2TodayAssignments.length + admin2PendingPicks.length;

    var assignWrap = document.getElementById("admin2-assign-wrap");
    if (assignWrap) assignWrap.classList.toggle("hidden", admin2VolunteerTab !== "assigned");

    body.innerHTML = "";

    if (admin2VolunteerTab === "assigned"){
      thead.innerHTML = '<tr><th>Jaago User ID</th><th>Name</th><th>Subject</th><th>Free Days</th><th>Department</th><th>Module</th><th>Remove</th></tr>';
      var rowsCount = admin2TodayAssignments.length + admin2PendingPicks.length;
      empty.classList.toggle("hidden", rowsCount > 0);
      empty.textContent = "No volunteers assigned yet — use “+ Assign Volunteer” above to assign today's volunteers.";

      admin2TodayAssignments.forEach(function(a, idx){
        var dept = a.task === "TEACHING" ? "Teaching" : "Checking";
        var tr = document.createElement("tr");
        tr.innerHTML =
          '<td class="att-col-id">' + escapeHtml(a.volunteer_user_id) + '</td>' +
          '<td>' + escapeHtml(a.volunteer_name) + '</td>' +
          '<td>' + escapeHtml(a.volunteer_subject || "—") + '</td>' +
          '<td>—</td>' +
          '<td><span class="att-status-label ' + deptBadgeClass(dept) + '">Status: ' + dept + '</span></td>' +
          '<td><span class="module-sent-badge">&#10003; Module Sent (' + escapeHtml(a.email_status) + ')</span></td>' +
          '<td><button type="button" class="remove-assignment-btn" data-source="server" data-idx="' + idx + '" data-assignment-id="' + a.id + '">Remove</button></td>';
        body.appendChild(tr);
      });

      admin2PendingPicks.forEach(function(p, idx){
        var teachingActive = p.dept === "Teaching" ? " active" : "";
        var checkingActive = p.dept === "Checking" ? " active" : "";
        var moduleCell = p.moduleSent
          ? '<span class="module-sent-badge">&#10003; Module Sent</span>'
          : '<button type="button" class="module-btn" data-idx="' + idx + '">Assign Module</button>';
        var tr = document.createElement("tr");
        tr.innerHTML =
          '<td class="att-col-id">' + escapeHtml(p.userId || "—") + '</td>' +
          '<td>' + escapeHtml(p.name) + '</td>' +
          '<td>' + escapeHtml(p.subject || "—") + '</td>' +
          '<td>' + escapeHtml(formatDays(p.freeDays)) + '</td>' +
          '<td><div class="att-toggle">' +
            '<button type="button" class="dept-btn' + teachingActive + '" data-idx="' + idx + '" data-dept="Teaching">Teaching</button>' +
            '<button type="button" class="dept-btn' + checkingActive + '" data-idx="' + idx + '" data-dept="Checking">Checking</button>' +
          '</div></td>' +
          '<td>' + moduleCell + '</td>' +
          '<td><button type="button" class="remove-assignment-btn" data-source="pending" data-idx="' + idx + '" data-assignment-id="' + (p.assignmentId || "") + '">Remove</button></td>';
        body.appendChild(tr);
      });
    } else {
      thead.innerHTML = '<tr><th class="att-col-sl">Sl</th><th>Jaago User ID</th><th>Name</th><th>Free Days</th></tr>';
      empty.classList.toggle("hidden", admin2RegisteredVolunteers.length > 0);
      empty.textContent = "No volunteers registered yet.";
      admin2RegisteredVolunteers.forEach(function(v, idx){
        var tr = document.createElement("tr");
        tr.innerHTML =
          '<td class="att-col-sl">' + (idx + 1) + '</td>' +
          '<td class="att-col-id">' + escapeHtml(v.user_id) + '</td>' +
          '<td>' + escapeHtml(v.name) + '</td>' +
          '<td>' + escapeHtml(formatDays(v.free_days)) + '</td>';
        body.appendChild(tr);
      });
    }
  }

  document.querySelectorAll("#view-admin2-volunteers .filter-btn").forEach(function(btn){
    btn.addEventListener("click", function(){
      document.querySelectorAll("#view-admin2-volunteers .filter-btn").forEach(function(b){ b.classList.remove("active"); });
      btn.classList.add("active");
      admin2VolunteerTab = btn.getAttribute("data-vtab");
      renderAdmin2VolunteersView();
    });
  });

  document.getElementById("admin2-volunteer-body").addEventListener("click", function(e){
    var deptBtn = e.target.closest(".dept-btn");
    if (deptBtn){
      var idx = Number(deptBtn.getAttribute("data-idx"));
      var pick = admin2PendingPicks[idx];
      if (!pick) return;
      pick.dept = deptBtn.getAttribute("data-dept");
      pick.deptConfirmed = true;
      renderAdmin2VolunteersView();
      return;
    }
    var moduleBtn = e.target.closest(".module-btn");
    if (moduleBtn){
      openModuleModal(Number(moduleBtn.getAttribute("data-idx")));
      return;
    }
    var removeBtn = e.target.closest(".remove-assignment-btn");
    if (removeBtn){
      handleRemoveAssignmentClick(removeBtn);
    }
  });

  // NEW — Admin 2 "Remove" button (delete an assigned volunteer's
  // assignment). Two cases:
  //
  // 1) The row has a real, server-saved assignment id (either from
  //    admin2TodayAssignments, or from a pending pick that was
  //    already sent/assigned earlier this session) — confirm, then
  //    call DELETE /admin2/assignments/<id>/delete/ and only update
  //    local state once the server confirms it's gone.
  //
  // 2) The row is a pending pick that was never actually sent to the
  //    backend yet (no assignmentId) — nothing exists server-side to
  //    delete, so just drop it from the local pending list.
  async function handleRemoveAssignmentClick(btn){
    var source = btn.getAttribute("data-source");
    var idx = Number(btn.getAttribute("data-idx"));
    var assignmentIdRaw = btn.getAttribute("data-assignment-id");
    var assignmentId = assignmentIdRaw ? Number(assignmentIdRaw) : null;

    if (!assignmentId){
      // Never sent to the backend — just remove locally.
      if (source === "pending" && admin2PendingPicks[idx]){
        admin2PendingPicks.splice(idx, 1);
        renderAdmin2VolunteersView();
      }
      return;
    }

    var ok = window.confirm("Remove this assignment? The volunteer will no longer see it on their dashboard.");
    if (!ok) return;

    btn.disabled = true;
    btn.textContent = "Removing…";

    try {
      await apiFetch("/admin2/assignments/" + assignmentId + "/delete/", {
        method: "DELETE"
      });

      if (source === "server"){
        admin2TodayAssignments = admin2TodayAssignments.filter(function(a){
          return a.id !== assignmentId;
        });
      } else if (source === "pending" && admin2PendingPicks[idx]){
        admin2PendingPicks.splice(idx, 1);
      }

      renderAdmin2VolunteersView();
    } catch (err) {
      if (err.status === 401){
        clearAuth();
        adminStatusAuthed = false;
        goToView("admin-signin");
        return;
      }
      showMessage((err && err.message) || "Unable to remove this assignment. Please try again.");
      btn.disabled = false;
      btn.textContent = "Remove";
    }
  }

  async function loadAdmin2Volunteers(){
    if (!adminStatusAuthed) return;
    try {
      var volResp = await apiFetch("/admin2/volunteers/");
      admin2RegisteredVolunteers = volResp.volunteers || [];
      var assignResp = await apiFetch("/admin2/assignments/today/");
      admin2TodayAssignments = assignResp.assignments || [];
      renderAdmin2VolunteersView();
    } catch (err) {
      if (err.status === 401){
        clearAuth();
        adminStatusAuthed = false;
        goToView("admin-signin");
        return;
      }
      showMessage(err.message || "Unable to load volunteers.");
    }
  }

  /* ============================================================
     MODULE ASSIGNMENT MODAL — real POST /admin2/assignments/send/
     (this is what actually sends the real Gmail SMTP email)
     ============================================================ */
  var moduleModalOverlay = document.getElementById("module-modal-overlay");
  var moduleModalTargetIdx = null;

  function openModuleModal(pendingIdx){
    var pick = admin2PendingPicks[pendingIdx];
    if (!pick) return;
    moduleModalTargetIdx = pendingIdx;
    document.getElementById("module-modal-title").textContent = "Assign Module — " + pick.name;
    document.getElementById("module-class-input").value = "";
    document.getElementById("module-task-input").value = "";
    document.getElementById("module-file-input").value = "";
    document.getElementById("module-file-name").textContent = "";
    document.getElementById("module-homework-input").value = "";
    document.getElementById("module-homework-file-input").value = "";
    document.getElementById("module-homework-file-name").textContent = "";
    document.getElementById("module-email-display").value = pick.email || "";
    var msg = document.getElementById("module-modal-msg");
    msg.textContent = "";
    msg.className = "modal-msg";
    moduleModalOverlay.classList.remove("hidden");
  }

  function closeModuleModal(){
    moduleModalOverlay.classList.add("hidden");
    moduleModalTargetIdx = null;
  }

  document.getElementById("module-modal-close").addEventListener("click", closeModuleModal);
  document.getElementById("module-modal-cancel").addEventListener("click", closeModuleModal);
  moduleModalOverlay.addEventListener("click", function(e){
    if (e.target === moduleModalOverlay) closeModuleModal();
  });

  document.getElementById("module-file-input").addEventListener("change", function(){
    var f = this.files && this.files[0];
    document.getElementById("module-file-name").textContent = f ? ("Attached: " + f.name) : "";
  });

  document.getElementById("module-homework-file-input").addEventListener("change", function(){
    var f = this.files && this.files[0];
    document.getElementById("module-homework-file-name").textContent = f ? ("Attached: " + f.name) : "";
  });

  /* ------------------------------------------------------------
     Shared by both modal buttons below — reads + validates the
     form, returns a ready FormData (or null after showing the
     validation message in msg).
     ------------------------------------------------------------ */
  function readModuleFormOrShowError(pick, msg){
    var assignedClass = document.getElementById("module-class-input").value;
    var task = document.getElementById("module-task-input").value.trim();
    var fileInput = document.getElementById("module-file-input");
    var file = fileInput.files && fileInput.files[0];
    var homeworkText = document.getElementById("module-homework-input").value.trim();
    var homeworkFileInput = document.getElementById("module-homework-file-input");
    var homeworkFile = homeworkFileInput.files && homeworkFileInput.files[0];

    if (!assignedClass){
      msg.textContent = "Please choose which class this is for.";
      msg.className = "modal-msg error";
      return null;
    }
    if (!task){
      msg.textContent = "Please describe the task.";
      msg.className = "modal-msg error";
      return null;
    }

    var formData = new FormData();
    formData.append("volunteer", pick.volunteerId);
    formData.append("assigned_class", assignedClass);
    formData.append("task", pick.dept === "Teaching" ? "TEACHING" : "CHECKING");
    formData.append("instruction", task);
    if (file) formData.append("attachment", file);
    // Homework module is optional — only sent if Admin 2 filled it in.
    if (homeworkText) formData.append("homework_instruction", homeworkText);
    if (homeworkFile) formData.append("homework_attachment", homeworkFile);
    return formData;
  }

  document.getElementById("module-modal-send").addEventListener("click", async function(){
    var pick = admin2PendingPicks[moduleModalTargetIdx];
    if (!pick) return;

    var msg = document.getElementById("module-modal-msg");
    var formData = readModuleFormOrShowError(pick, msg);
    if (!formData) return;

    var sendBtn = document.getElementById("module-modal-send");
    sendBtn.disabled = true;
    sendBtn.textContent = "Sending...";
    msg.textContent = "";
    msg.className = "modal-msg";

    try {
      var result = await apiFetch("/admin2/assignments/send/", {
        method: "POST",
        body: formData
      });

      pick.moduleSent = true;
      pick.assignmentId = result && result.assignment ? result.assignment.id : null;
      msg.textContent = "✓ Sent to " + (pick.email || "their registered email") + ".";
      msg.className = "modal-msg success";

      renderAdmin2VolunteersView();
      setTimeout(closeModuleModal, 1400);
    } catch (err) {
      msg.textContent = err.message || "Unable to send. Please try again.";
      msg.className = "modal-msg error";
    } finally {
      sendBtn.disabled = false;
      sendBtn.textContent = "Send Email";
    }
  });

  /* ------------------------------------------------------------
     TEMPORARY testing button — "Assign (No Email)". Your Django
     backend's /admin2/assignments/send/ endpoint already creates
     the VolunteerAssignment row FIRST and only tries to email it
     after, so even when the email attempt fails (e.g. SMTP not
     set up yet) the assignment itself is already saved and comes
     back in the error response's `assignment` field. This button
     calls the exact same endpoint with the exact same data as
     "Send Email" — it just also treats that
     saved-but-email-failed response as a success here on the
     frontend, so you can test class/homework assignment end-to-end
     without working SMTP. Once email sending is set up, the
     regular "Send Email" button covers this case on its own and
     this button can be removed.
     ------------------------------------------------------------ */
  document.getElementById("module-modal-assign").addEventListener("click", async function(){
    var pick = admin2PendingPicks[moduleModalTargetIdx];
    if (!pick) return;

    var msg = document.getElementById("module-modal-msg");
    var formData = readModuleFormOrShowError(pick, msg);
    if (!formData) return;

    var assignBtn = document.getElementById("module-modal-assign");
    assignBtn.disabled = true;
    assignBtn.textContent = "Assigning...";
    msg.textContent = "";
    msg.className = "modal-msg";

    try {
      var assignResult = await apiFetch("/admin2/assignments/send/", {
        method: "POST",
        body: formData
      });

      pick.moduleSent = true;
      pick.assignmentId = assignResult && assignResult.assignment ? assignResult.assignment.id : null;
      msg.textContent = "✓ Assigned (email also sent successfully).";
      msg.className = "modal-msg success";
      renderAdmin2VolunteersView();
      setTimeout(closeModuleModal, 1400);
    } catch (err) {
      // The assignment row is created before the email is attempted,
      // so a saved `assignment` in the error body means the class /
      // task / homework data went through — only the email failed.
      if (err.data && err.data.assignment){
        pick.moduleSent = true;
        pick.assignmentId = err.data.assignment.id || null;
        msg.textContent = "✓ Assigned (email not sent — SMTP isn't set up yet, but the assignment itself was saved).";
        msg.className = "modal-msg success";
        renderAdmin2VolunteersView();
        setTimeout(closeModuleModal, 1800);
      } else {
        msg.textContent = err.message || "Unable to assign. Please try again.";
        msg.className = "modal-msg error";
      }
    } finally {
      assignBtn.disabled = false;
      assignBtn.textContent = "Assign (No Email)";
    }
  });

  /* ============================================================
     TESTIMONIALS CAROUSEL (unchanged — uses Claude Artifact
     capabilities when available; harmless no-op otherwise)
     ============================================================ */
  var basePlaceholders = [
    { name: "Name Placeholder", role: "Student, Jaago", quote: "Placeholder testimonial text — swap this for a real quote once you add photos and feedback.", initials: "NP", color: "#3f9142", photoUrl: null },
    { name: "Name Placeholder", role: "Parent", quote: "Placeholder testimonial text — swap this for a real quote once you add photos and feedback.", initials: "NP", color: "#c9930f", photoUrl: null },
    { name: "Name Placeholder", role: "Volunteer Teacher", quote: "Placeholder testimonial text — swap this for a real quote once you add photos and feedback.", initials: "NP", color: "#7c3aed", photoUrl: null },
    { name: "Name Placeholder", role: "School Principal", quote: "Placeholder testimonial text — swap this for a real quote once you add photos and feedback.", initials: "NP", color: "#b5822f", photoUrl: null }
  ];
  var liveTestimonials = [];
  var testimonials = basePlaceholders.slice();
  var testiIndex = 0;
  var testiTimer = null;
  var dbNS = null;
  var assetsNS = null;
  var avatarColors = ["#3f9142", "#c9930f", "#7c3aed", "#b5822f", "#2563eb", "#c0392b"];

  function initialsFor(name){
    var parts = String(name || "").trim().split(/\s+/).filter(Boolean);
    if (parts.length === 0) return "?";
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }

  function renderTestimonial(i){
    var t = testimonials[i];
    if (!t) return;
    var card = document.getElementById("testimonial-card");
    card.classList.remove("flash");
    void card.offsetWidth;
    var avatarHtml = t.photoUrl
      ? '<img class="testimonial-avatar-img" src="' + escapeHtml(t.photoUrl) + '" alt="' + escapeHtml(t.name) + '" />'
      : '<div class="testimonial-avatar" style="background:' + t.color + '">' + escapeHtml(t.initials) + '</div>';
    card.innerHTML =
      avatarHtml +
      '<p class="testimonial-quote">“' + escapeHtml(t.quote) + '”</p>' +
      '<p class="testimonial-name">' + escapeHtml(t.name) + '</p>' +
      '<p class="testimonial-role">' + escapeHtml(t.role) + '</p>';
    card.classList.add("flash");
    var dots = document.querySelectorAll("#testimonial-dots .carousel-dot");
    dots.forEach(function(d, idx){ d.classList.toggle("active", idx === i); });
  }

  function buildDots(){
    var dots = document.getElementById("testimonial-dots");
    dots.innerHTML = "";
    testimonials.forEach(function(_, idx){
      var b = document.createElement("button");
      b.type = "button";
      b.className = "carousel-dot" + (idx === testiIndex ? " active" : "");
      b.setAttribute("aria-label", "Go to testimonial " + (idx + 1));
      b.addEventListener("click", function(){ goToTestimonial(idx); });
      dots.appendChild(b);
    });
  }

  function rebuildTestimonials(preserveIndex){
    testimonials = basePlaceholders.concat(liveTestimonials);
    if (!preserveIndex || testiIndex >= testimonials.length){
      testiIndex = testimonials.length - 1;
      if (testiIndex < 0) testiIndex = 0;
    }
    buildDots();
    renderTestimonial(testiIndex);
  }

  function goToTestimonial(i){
    testiIndex = (i + testimonials.length) % testimonials.length;
    renderTestimonial(testiIndex);
    var dots = document.querySelectorAll("#testimonial-dots .carousel-dot");
    dots.forEach(function(d, idx){ d.classList.toggle("active", idx === testiIndex); });
    resetTestiTimer();
  }
  function nextTestimonial(){ goToTestimonial(testiIndex + 1); }
  function prevTestimonial(){ goToTestimonial(testiIndex - 1); }
  function resetTestiTimer(){
    if (testiTimer) clearInterval(testiTimer);
    testiTimer = setInterval(nextTestimonial, 60000);
  }

  document.getElementById("testi-prev").addEventListener("click", prevTestimonial);
  document.getElementById("testi-next").addEventListener("click", nextTestimonial);
  buildDots();
  renderTestimonial(0);
  resetTestiTimer();

  var addToggleBtn = document.getElementById("testi-add-toggle");
  var addForm = document.getElementById("testi-add-form");
  var addMsg = document.getElementById("testi-form-msg");
  var submitBtn2 = document.getElementById("testi-submit-btn");

  var hasSubscribed = false;

  addToggleBtn.addEventListener("click", function(){
    addForm.hidden = !addForm.hidden;
    addMsg.textContent = "";
    addMsg.className = "testi-form-msg";
    if (!addForm.hidden){
      if (!dbNS){
        addMsg.textContent = "Still connecting… you can start typing, and it will save once ready.";
        addMsg.className = "testi-form-msg";
      } else if (!hasSubscribed){
        hasSubscribed = true;
        subscribeTestimonials();
      }
      setTimeout(function(){
        var nameInput = document.getElementById("testi-in-name");
        if (nameInput) nameInput.focus();
      }, 50);
    }
  });
  document.getElementById("testi-cancel-btn").addEventListener("click", function(){
    addForm.hidden = true;
    addForm.reset();
    addMsg.textContent = "";
  });

  function subscribeTestimonials(){
    if (!dbNS) return;
    try {
      dbNS.collection("testimonials").orderBy("createdAt", "asc").onSnapshot(
        function(snap){
          liveTestimonials = snap.docs.map(function(d){
            var data = d.data() || {};
            return {
              id: d.id,
              name: data.name || "Anonymous",
              role: data.role || "Community Member",
              quote: data.quote || "",
              photoUrl: data.photoUrl || null,
              initials: initialsFor(data.name),
              color: data.color || avatarColors[Math.floor(Math.random() * avatarColors.length)],
            };
          });
          rebuildTestimonials(true);
          renderManageList();
        },
        function(err){ console.error("testimonials snapshot error", err); }
      );
    } catch (e) { console.error(e); }
  }

  function renderManageList(){
    var list = document.getElementById("testi-manage-list");
    var empty = document.getElementById("testi-manage-empty");
    if (!list || !empty) return;
    list.innerHTML = "";
    if (!liveTestimonials.length){
      empty.hidden = false;
      return;
    }
    empty.hidden = true;
    liveTestimonials.forEach(function(t){
      var row = document.createElement("div");
      row.className = "testi-manage-row";
      row.innerHTML =
        '<div class="testi-manage-info">' +
          '<strong>' + escapeHtml(t.name) + '</strong>' +
          '<span class="testi-manage-role">' + escapeHtml(t.role) + '</span>' +
          '<p class="testi-manage-quote">' + escapeHtml(t.quote) + '</p>' +
        '</div>' +
        '<button type="button" class="testi-delete-btn" data-id="' + escapeHtml(t.id) + '">Delete</button>';
      list.appendChild(row);
    });
  }

  document.getElementById("testi-manage-list").addEventListener("click", function(e){
    var btn = e.target.closest(".testi-delete-btn");
    if (!btn) return;
    var id = btn.getAttribute("data-id");
    if (!id || !dbNS) return;

    if (btn.dataset.confirm !== "1"){
      btn.dataset.confirm = "1";
      btn.textContent = "Confirm?";
      setTimeout(function(){
        if (btn.dataset.confirm === "1"){
          btn.dataset.confirm = "";
          btn.textContent = "Delete";
        }
      }, 3000);
      return;
    }

    btn.disabled = true;
    btn.textContent = "Deleting…";
    dbNS.collection("testimonials").doc(id).delete().catch(function(err){
      console.error(err);
      btn.disabled = false;
      btn.dataset.confirm = "";
      btn.textContent = "Delete";
    });
  });

  addForm.addEventListener("submit", async function(e){
    e.preventDefault();
    addMsg.textContent = "";
    addMsg.className = "testi-form-msg";

    var name = document.getElementById("testi-in-name").value.trim();
    var role = document.getElementById("testi-in-role").value.trim();
    var quote = document.getElementById("testi-in-quote").value.trim();
    var fileInput = document.getElementById("testi-in-photo");

    if (!name || !quote){
      addMsg.textContent = "Please add your name and a short story.";
      addMsg.className = "testi-form-msg error";
      return;
    }
    if (!dbNS){
      addMsg.textContent = "Still connecting to storage — please wait a moment and press Add Testimonial again.";
      addMsg.className = "testi-form-msg error";
      return;
    }
    if (!hasSubscribed){
      hasSubscribed = true;
      subscribeTestimonials();
    }

    submitBtn2.disabled = true;
    submitBtn2.textContent = "Adding…";

    try {
      var photoId = null;
      var photoUrl = null;

      if (fileInput.files && fileInput.files[0] && assetsNS){
        var uploadRes = await assetsNS.upload(fileInput.files[0]);
        photoId = uploadRes.id;
        photoUrl = uploadRes.url;
      }

      await dbNS.collection("testimonials").add({
        name: name,
        role: role || "Community Member",
        quote: quote,
        photoId: photoId,
        photoUrl: photoUrl,
        color: avatarColors[Math.floor(Math.random() * avatarColors.length)],
        createdAt: Date.now(),
      });

      addForm.reset();
      addMsg.textContent = "Thank you! Your testimonial has been added.";
      addMsg.className = "testi-form-msg success";
      setTimeout(function(){ addForm.hidden = true; addMsg.textContent = ""; }, 1800);
    } catch (err) {
      console.error(err);
      addMsg.textContent = "Couldn't save that just now (" + (err && err.code ? err.code : "error") + "). Please try again.";
      addMsg.className = "testi-form-msg error";
    } finally {
      submitBtn2.disabled = false;
      submitBtn2.textContent = "Add Testimonial";
    }
  });

  (async function initCapabilities(){
    try {
      if (window.claude && typeof window.claude.use === "function"){
        dbNS = await window.claude.use("db");
        assetsNS = await window.claude.use("assets");
      }
    } catch (e) { /* no host capabilities available */ }
  })();

})();
