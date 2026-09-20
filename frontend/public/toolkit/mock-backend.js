// ============================================================
// TEST HARNESS ONLY -- not part of the real app. This stubs the
// Django backend so you can click through the real index.html /
// script.js / style.css logic right here, without a running
// server. Use the panel in the corner to switch which task type
// the mock backend assigns and reload. INVIGILATOR and
// SPECIAL_ADDED are included here for demo purposes even though
// your real backend can't send those values yet -- the frontend
// code is ready for them regardless.
// ============================================================
(function(){
  var TASKS = ['TEACHING', 'CHECKING', 'INVIGILATOR', 'SPECIAL_ADDED'];
  window.__TEST_TASK__ = localStorage.getItem('__test_task__') || 'TEACHING';

  var STUDENTS = [
    { student_id: 1, roll_no: 'JAA0235', name: 'Rahul Sen', class: '5', marked_at: '2026-09-19T09:00:00Z' },
    { student_id: 2, roll_no: 'JAA0236', name: 'Aman Roy', class: '5', marked_at: '2026-09-19T09:01:00Z' },
    { student_id: 3, roll_no: 'JAA0237', name: 'Meera Das', class: '5', marked_at: '2026-09-19T09:05:00Z' },
  ];

  window.fetch = async function(url, opts){
    opts = opts || {};
    var method = (opts.method || 'GET').toUpperCase();
    var p = String(url).replace(/^https?:\/\/[^/]+\/api/, '');
    var key = method + ' ' + p;

    await new Promise(function(r){ setTimeout(r, 120); }); // feels like a real request

    if (key === 'POST /teachers/login/'){
      return new Response(JSON.stringify({
        message: 'Login successful.', user_id: 'TESTVOL', name: 'Test Volunteer',
        email: 'test@example.com', course: 'Mathematics Program', subject: 'Mathematics',
        role: 'TEACHER_VOLUNTEER', access: 'TESTACCESS', refresh: 'TESTREFRESH',
      }), { status: 200 });
    }
    if (key === 'GET /teachers/my-assignment-today/'){
      var task = window.__TEST_TASK__;
      var byTask = {
        TEACHING: { instruction: 'Cover fractions chapter 3, pages 10-14.', class: 'Class B' },
        CHECKING: { instruction: "Check today's homework for chapter 3.", class: 'Class B' },
        INVIGILATOR: { instruction: "Supervise today's assigned activity.", class: 'Class C' },
        SPECIAL_ADDED: { instruction: '', class: '' },
      };
      var info = byTask[task];
      return new Response(JSON.stringify({ assignment: {
        assigned_class: info.class, assigned_class_display: info.class,
        task: task, task_display: task,
        instruction: info.instruction,
        attachment_url: task === 'SPECIAL_ADDED' ? null : 'https://example.com/fractions.pdf',
        assignment_date: '2026-09-19',
      }}), { status: 200 });
    }
    if (key === 'GET /teachers/my-class-present-students/'){
      return new Response(JSON.stringify({ assigned_class_display: 'Class B', students: STUDENTS }), { status: 200 });
    }

    // ---- Everything below: any credentials work everywhere, no real
    // backend needed. Admin 1 / Admin 2 sign-in share one endpoint, so
    // the role is inferred from which panel you're signing in from.
    if (key === 'POST /auth/login/'){
      var onAdmin1 = window.location.hash.indexOf('admin1') !== -1;
      var role = onAdmin1 ? 'ADMIN1' : 'ADMIN2';
      return new Response(JSON.stringify({
        tokens: { access: 'TESTACCESS', refresh: 'TESTREFRESH' },
        user: { username: 'demo' },
        profile: { role: role },
      }), { status: 200 });
    }
    if (key === 'GET /courses/'){
      return new Response(JSON.stringify([
        { id: 1, name: 'Mathematics Program' }, { id: 2, name: 'English Program' },
      ]), { status: 200 });
    }
    if (key === 'GET /subjects/'){
      return new Response(JSON.stringify([
        { id: 1, name: 'Mathematics' }, { id: 2, name: 'English' }, { id: 3, name: 'Science' },
      ]), { status: 200 });
    }
    if (key === 'POST /teachers/register/'){
      var tBody = opts.body ? JSON.parse(opts.body) : {};
      return new Response(JSON.stringify({ name: tBody.name || 'Test Volunteer', user_id: 'JAAV' + Math.floor(Math.random()*900+100) }), { status: 200 });
    }
    if (key === 'POST /students/register/'){
      var sBody = opts.body ? JSON.parse(opts.body) : {};
      return new Response(JSON.stringify({
        name: sBody.name || 'Test Student', school_name: sBody.school_name || 'Test School',
        student_class: sBody.student_class || '5', roll_no: 'PRIM' + Math.floor(Math.random()*900+100),
      }), { status: 200 });
    }

    // ---- Admin 1: Attendance Toolkit ----
    if (key === 'POST /attendance/session/start/'){
      return new Response(JSON.stringify({ session: { expires_at: new Date(Date.now() + 30*60000).toISOString() } }), { status: 200 });
    }
    if (key === 'POST /attendance/session/end/'){
      return new Response(JSON.stringify({}), { status: 200 });
    }
    if (key === 'GET /attendance/students/'){
      return new Response(JSON.stringify({ students: [
        { student_id: 1, name: 'Rahul Sharma', roll_no: 'JAA0235', class: '2', status: null },
        { student_id: 2, name: 'Aman Kumar', roll_no: 'JAA0236', class: '4', status: 'PRESENT' },
        { student_id: 3, name: 'Meera Das', roll_no: 'JAA0237', class: '2', status: null },
        { student_id: 4, name: 'Zoya Ali', roll_no: 'JAA0238', class: '5', status: 'ABSENT' },
      ] }), { status: 200 });
    }
    if (key === 'POST /attendance/students/save/'){
      return new Response(JSON.stringify({}), { status: 200 });
    }
    if (key === 'GET /attendance/volunteers/current/'){
      return new Response(JSON.stringify({ volunteers: [
        { id: 1, volunteer: 101, user_id: 'JAAV01', volunteer_name: 'Priyam Ghosh', task: 'TEACHING', status: 'PRESENT' },
        { id: 2, volunteer: 102, user_id: 'JAAV02', volunteer_name: 'Dibha Roy', task: 'CHECKING', status: null },
      ] }), { status: 200 });
    }
    if (key === 'POST /attendance/volunteers/save/'){
      return new Response(JSON.stringify({}), { status: 200 });
    }

    // ---- Admin 2: Dashboard / Students / Volunteers / Assignments ----
    if (key === 'GET /admin2/dashboard/'){
      return new Response(JSON.stringify({
        students: { total_registered: 250, present_today: 217 },
        volunteers: { registered: 42 },
        assignments_today: 18,
      }), { status: 200 });
    }
    if (key === 'GET /admin2/students/total/'){
      return new Response(JSON.stringify({ students: [
        { id: 1, name: 'Rahul Sharma', roll_no: 'JAA0235', school_name: 'Jaago School', student_class: '2' },
        { id: 2, name: 'Aman Kumar', roll_no: 'JAA0236', school_name: 'Jaago School', student_class: '4' },
        { id: 3, name: 'Meera Das', roll_no: 'JAA0237', school_name: 'Jaago School', student_class: '2' },
      ] }), { status: 200 });
    }
    if (key === 'GET /admin2/students/present-today/'){
      return new Response(JSON.stringify({ students: [ { id: 1 }, { id: 2 } ] }), { status: 200 });
    }
    if (key === 'GET /admin2/volunteers/'){
      return new Response(JSON.stringify({ volunteers: [
        { id: 1, user_id: 'JAAV01', name: 'Priyam Ghosh', subject_name: 'Mathematics', free_days: [todayWeekdayNameMock(), 'Friday'], email: 'priyam@example.com' },
        { id: 2, user_id: 'JAAV02', name: 'Dibha Roy', subject_name: 'English', free_days: ['Monday'], email: 'dibha@example.com' },
      ] }), { status: 200 });
    }
    if (key === 'GET /admin2/assignments/today/'){
      return new Response(JSON.stringify({ assignments: [] }), { status: 200 });
    }
    if (key === 'POST /admin2/assignments/send/'){
      return new Response(JSON.stringify({ assignment: { id: Math.floor(Math.random()*10000) } }), { status: 200 });
    }
    if (/^DELETE \/admin2\/assignments\/\d+\/delete\/$/.test(key)){
      return new Response(JSON.stringify({}), { status: 200 });
    }

    return new Response(JSON.stringify({ detail: 'unhandled mock route in test harness: ' + key }), { status: 404 });
  };

  function todayWeekdayNameMock(){
    return ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'][new Date().getDay()];
  }

  window.addEventListener('DOMContentLoaded', function(){
    var bar = document.createElement('div');
    bar.style.cssText = 'position:fixed;bottom:0;left:0;right:0;z-index:99999;background:#3a3226;color:#fff;font:12px/1.4 -apple-system,sans-serif;padding:8px 12px;display:flex;gap:8px;align-items:center;justify-content:center;flex-wrap:wrap;';
    var btnsHtml = TASKS.map(function(t){
      var active = t === window.__TEST_TASK__;
      return '<button data-task="' + t + '" style="cursor:pointer;padding:4px 10px;border-radius:6px;border:0;background:' + (active ? '#7c3aed' : '#5a5040') + ';color:#fff;font-weight:' + (active ? '700' : '400') + ';">' + t + '</button>';
    }).join('');
    bar.innerHTML =
      '<b>TEST HARNESS</b>' +
      btnsHtml +
      '<button id="__resetTest" style="cursor:pointer;padding:4px 10px;border-radius:6px;border:0;background:#e8b514;color:#3a3226;">Reset / Sign out</button>' +
      '<span style="opacity:.7;">login with any Volunteer ID + password</span>';
    document.body.appendChild(bar);
    bar.querySelectorAll('[data-task]').forEach(function(b){
      b.addEventListener('click', function(){
        localStorage.setItem('__test_task__', b.getAttribute('data-task'));
        location.reload();
      });
    });
    document.getElementById('__resetTest').addEventListener('click', function(){
      var keep = ['__test_task__'];
      Object.keys(localStorage).forEach(function(k){ if (keep.indexOf(k) === -1) localStorage.removeItem(k); });
      location.hash = '#home';
      location.reload();
    });
  });
})();
