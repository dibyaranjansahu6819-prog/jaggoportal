# Jaago Portal Change Plan

This file records the planned Jaago Portal changes, their verified current implementation, affected files, dependencies, and verification/rollback approach. It is a plan only; none of the code changes described below have been applied.

## How to use this file

Each change has a stable ID and a status of Planned, In progress, Done, or Blocked; update the summary and detailed entry together as work progresses. Add new entries using the same template, assign the next unused `CHG-NNN` ID, and record completed work in the Change log. Any uncertain product decision is explicitly marked **Needs confirmation** rather than assumed.

## Summary

| ID | Title | Type | Status | Risk | Area |
|---|---|---|---|---|---|
| CHG-001 | Landing page header section | modify | Planned | Low | Frontend |
| CHG-002 | Landing page About Us and Meet our Developers | feature | Planned | Medium | Frontend |
| CHG-003 | Student registration class groups | modify | Planned | High | Both |
| CHG-004 | Admin 2 day status: Holiday and Playing Day | feature | Planned | High | Both |
| CHG-005 | Student homework verification and +10 XP | modify | Planned | Medium | Both |
| CHG-006 | Block removed students from re-registering | feature | Planned | High | Both |
| CHG-007 | Assignment emails with attached modules | feature | Planned | Medium | Both |
| CHG-008 | Volunteer XP system | modify | Planned | High | Both |

## Recommended implementation order

1. **CHG-001 and CHG-002** can be implemented independently of backend work; settle developer-content questions before publishing the profile cards.
2. **CHG-003** should precede changes to group-specific assignment, attendance, and checking behavior because those workflows compare the same persisted group codes.
3. **CHG-004** should establish the authoritative date/status rules before CHG-008 calculates volunteer XP; specifically, Playing Day must be excluded from the new volunteer XP rules.
4. **CHG-007** should be completed before substitute coverage in CHG-008 if substitute lesson modules must be selected and emailed.
5. **CHG-005** can proceed after the checking-to-homework state transition is agreed; it is separate from volunteer XP.
6. **CHG-006** can proceed independently, but requires approval of the identity-matching, privacy, and override rules before persisting repeat-registration identifiers.

## CHG-001: Landing page header section
- **Status:** Planned
- **Type:** modify
- **Description:** Move the “Jaago Teaching Portal” heading/tagline and the four access cards for Admin 1, Admin 2, Volunteer, and Student to the top of the landing-page content, immediately after the site header. This makes the primary sign-up/sign-in actions the first content visitors encounter.
- **Current behavior/structure:** `frontend/src/routes/index.tsx` currently renders the About Us section and developer cards before the `.portal-intro` heading and `.portal-choice-grid`. The four cards already link to the current role routes.
- **Target behavior/structure:**
  ```text
  portal header/navigation
  └── main content
      ├── portal intro/title and tagline
      ├── four portal access cards
      ├── About Us
      └── Meet our Developers
  ```
- **Files affected:**

  | File path | What changes |
  |---|---|
  | `frontend/src/routes/index.tsx` | Reorder `portal-intro` and `portal-choice-grid` before About Us and developer sections; preserve the current route destinations and card labels. |
  | `frontend/src/styles.css` | Adjust `.portal-intro`, `.portal-choice-grid`, and section spacing as needed after the order change; retain existing responsive layout and design tokens. |

- **Database changes:** None. No models, migrations, or `seed_demo_data` changes.
- **Step-by-step instructions:**
  1. In `HomePage`, move the existing `.portal-intro` and `.portal-choice-grid` sections directly below the header.
  2. Keep the existing `portalChoices` labels and links unchanged unless separately approved.
  3. Check desktop and mobile spacing using the existing `.portal-*` styles.
  4. Run `npm run lint` and `npm run build` from `frontend/`.
- **Dependencies and side effects:** The page navigation contains a `#about` link, and the About section's `id="about"` must remain. Add or update a developer-section navigation link only if desired; that navigation behavior is not specified.
- **Open questions:** **Needs confirmation:** Should “very top” mean the first content below the current site header, or should the title and access cards replace/merge into the header itself?
- **Verification:** Open `/` at desktop and mobile widths; confirm title and all four role cards appear before About Us and that each card still opens its existing route.
- **Rollback:** Restore the original JSX section order and corresponding CSS spacing changes.

## CHG-002: Landing page About Us and Meet our Developers
- **Status:** Planned
- **Type:** feature
- **Description:** Place About Us and Meet our Developers below the access cards, retaining Jaago’s current visual system. The page already has both sections and three developer cards, so the primary work is positioning and validating the content rather than introducing a second copy. Use explicit placeholders for unapproved developer information until the listed content is confirmed.
- **Current behavior/structure:** `frontend/src/routes/index.tsx` contains an About Us paragraph and a “Meet the Developers” section with three hard-coded names, roles, biographies, initials, and LinkedIn links. The cards use initials rather than photos; no image/photo fields are present in the data. `frontend/src/styles.css` contains `.portal-about`, `.portal-developers`, `.developer-card` and responsive styling. `frontend/src/routes/toolkit.tsx` renders a standalone iframe at `/toolkit/index.html`; it is not shown as a shared homepage component.
- **Target behavior/structure:** Both sections appear below the four access cards. Until approval, developer cards display clearly labeled placeholders for name, photo/avatar, role, biography, and link rather than presenting unverified data as final. Reuse existing Jaago tokens/card styling; do not assume the iframe toolkit supplies reusable React components.
- **Files affected:**

  | File path | What changes |
  |---|---|
  | `frontend/src/routes/index.tsx` | Position the sections after the cards; represent any unconfirmed developer profiles as placeholders; add section anchors/navigation if required. |
  | `frontend/src/styles.css` | Refine the existing About/developer sections to match the reordered page and placeholder states; preserve responsive rules. |
  | `frontend/public/` | Affected only if approved developer photos are supplied and added; exact filenames and rights/consent are **Needs confirmation**. |
  | `frontend/src/routes/toolkit.tsx` | No change expected unless “toolkit components” means components from the iframe toolkit; the relationship needs confirmation. |

- **Database changes:** None. No migrations or seed changes.
- **Step-by-step instructions:**
  1. Reorder the existing About and developer sections after the access cards as part of CHG-001.
  2. Confirm whether the currently hard-coded names, roles, biographies, and links are approved; show placeholders for any unapproved fields.
  3. Add approved photos only after receiving image files and usage permission; otherwise keep a neutral initials/placeholder avatar.
  4. Reuse the current `.portal-*` styles and check keyboard navigation, image alt text, and mobile layout.
  5. Run `npm run lint` and `npm run build` from `frontend/`.
- **Dependencies and side effects:** Depends on CHG-001 for final section order. The current header has Home/About anchors but not a developers anchor. `toolkit.tsx` is an iframe route, so direct reuse of its contents is not evidenced by the repository.
- **Open questions:**
  - **Needs confirmation:** Are the three developer names, roles, biographies, and LinkedIn URLs already in `frontend/src/routes/index.tsx` approved, or should each be replaced by a placeholder?
  - **Needs confirmation:** Provide the approved developer names, photos, roles, biographies, and profile links; confirm image-use permission.
  - **Needs confirmation:** Does “follow the toolkit components” mean the visual styles in `frontend/src/styles.css`, shared components under `frontend/src/components/`, or the separate iframe at `/toolkit/index.html`?
  - **Needs confirmation:** Should the header navigation include a “Meet our Developers” anchor?
- **Verification:** Visit `/`; verify the two sections follow the cards, placeholders are explicit where data is missing, any supplied photos have useful alt text, and layout remains usable at narrow widths.
- **Rollback:** Restore the previous section content/order and remove any newly added photo assets only if they were introduced by this change.

## CHG-003: Student registration class groups
- **Status:** Planned
- **Type:** modify
- **Description:** Align student class-to-group assignment with A=LKG/UKG, B=Classes 1–3, C=Classes 4–6, D=Classes 7–8, and E=Classes 9–10. The `student_class` field currently stores the individual class while `group` stores the derived cohort, and current code maps those cohorts differently; update all group-dependent assignment, attendance, roster, and checking behavior consistently. Keep individual class values and existing roll numbers intact unless a product decision requires a roll-number format change.
- **Current behavior/structure:** `Student.student_class` is a `CharField(max_length=3)` with choices LKG, UKG, and 1–10. `Student.group` is a non-editable `CharField` with `ClassA`–`ClassE` values. `Student.get_group_for_class()` currently maps LKG/UKG→ClassE, 1–3→ClassA, 4–6→ClassB, 7–8→ClassC, 9–10→ClassD. `VolunteerAssignment.assigned_class` uses the same ClassA–ClassE values. Student roll numbers are generated independently from a global `StudentRegistrationSequence`; no student data is seeded by `seed_demo_data`.
- **Target behavior/structure:** Map LKG/UKG→ClassA, 1–3→ClassB, 4–6→ClassC, 7–8→ClassD, and 9–10→ClassE. Use the same group semantics in student lists, attendance, teaching/checking eligibility, and Admin 2 assignment selection. Recommended compatibility approach: preserve persisted/API codes `ClassA`–`ClassE` and change their meanings, while displaying labels “Group A”–“Group E”; confirm before changing those external codes.
- **Files affected:**

  | File path | What changes |
  |---|---|
  | `frontend/src/signup/StudentSignup.jsx` | Group the existing class options under the required group labels without changing submitted individual `student_class` values. |
  | `backend/students/models.py` | Change `Student.get_group_for_class()` mapping; keep `student_class` choices and group field choices consistent with the decided representation. |
  | `backend/students/serializers.py` | Keep `student_class`/`group` response fields aligned with the selected public group labels/codes. |
  | `backend/students/utils.py` | Review roll-number generation; it uses class code plus a global sequence, not group, so change only if roll-number policy is explicitly revised. |
  | `backend/admin2/models.py` | Align `VolunteerAssignment.CLASS_CHOICES` group meaning/labels with the student cohort mapping. |
  | `backend/admin2/serializers.py` | Ensure assignment input validation and student/assignment display serializers expose consistent group values. |
  | `backend/admin2/views.py` | Review student summary/present queries and ordering; ensure any class/group filters are based on the new group semantics. |
  | `backend/attendance/views.py` | Review student attendance list ordering/output and any group selection used by the Admin 1 toolkit/dashboard. |
  | `backend/teachers/volunteer_progress_views.py` | Ensure teaching student selection filters using the updated `Student.group` and `assigned_class`. |
  | `backend/teachers/volunteer_checking_views.py` | Ensure checking student selection and `student.group != assignment.assigned_class` validation use the new mapping. |
  | `backend/teachers/volunteer_progress_serializers.py` | Keep progress payload group/class values consistent. |
  | `backend/teachers/volunteer_checking_serializers.py` | Keep checking payload group/class values consistent. |
  | `frontend/src/admin2/Admin2Roster.jsx` | Update the assignment class options’ labels and values only according to the agreed internal/public group-code decision. |
  | `frontend/src/admin2/Admin2Students.jsx` | Change class-only filtering/display as needed to expose groups and individual classes accurately. |
  | `frontend/src/admin2/Admin2StudentDetail.jsx` | Display the derived group label consistently. |
  | `backend/students/migrations/` | Add a new data migration for existing `Student.group` values; do not edit already-applied migrations such as `0005_student_group_and_homework.py` or `0010_alter_student_group.py`. |
  | `backend/admin2/migrations/` | Add a data migration for `VolunteerAssignment.assigned_class` values if stored codes retain the same names but their meanings are being remapped. |
  | `backend/students/tests.py`, `backend/teachers/test_volunteer_progress_homework_xp.py`, `backend/teachers/test_volunteer_checking.py`, `backend/attendance/tests.py`, `backend/admin2/tests.py` | Update expectations and cover all five group mappings and cross-group assignment rejection. |

- **Database changes:** `student_class` and `group` are existing fields; no new model is inherently required. Add a forward data migration mapping old group semantics to the newly requested semantics: old ClassE→ClassA, old ClassA→ClassB, old ClassB→ClassC, old ClassC→ClassD, old ClassD→ClassE. Apply the corresponding semantic mapping to stored `VolunteerAssignment.assigned_class` values so each assignment continues to refer to the same actual student cohort. Do not alter student names, individual `student_class`, roll numbers, or the global `StudentRegistrationSequence`. `seed_demo_data` creates no students or assignments, so no student seed updates are expected.
- **Step-by-step instructions:**
  1. Confirm whether internal/API values remain `ClassA`–`ClassE` or change to bare `A`–`E`.
  2. Implement and unit-test the new class-to-group mapping in `Student.get_group_for_class()`.
  3. Update student registration labels and Admin 2 assignment options.
  4. Add a reversible data migration for existing student groups and assignment groups, with an explicit reverse mapping.
  5. Review the API serializers/views and all listed group comparisons/filters.
  6. Run `python manage.py makemigrations --check`, `python manage.py migrate`, then relevant students, teachers, attendance, and admin2 tests.
  7. Manually register each boundary class and verify it appears only in the expected group’s assignment and attendance lists.
- **Dependencies and side effects:** Existing students and historical assignments use group codes with old meanings. If only the `get_group_for_class()` function changes, existing records will remain in the old groups until saved; the data migration is necessary. A change to public group codes also affects API clients and report labels. Roll-number generation in `backend/students/utils.py` currently uses a class code and global sequence; it does not encode the group.
- **Open questions:**
  - **Needs confirmation:** Should stored/API group codes remain `ClassA`–`ClassE` for compatibility, or become bare `A`–`E`?
  - **Needs confirmation:** Should Admin 2 filter by individual class, group, or both?
  - **Needs confirmation:** Is the existing roll-number format to remain unchanged? The current implementation is `JAA` + class code + global sequence and does not encode group.
- **Verification:** Test all 12 allowed class values against expected group values; verify Admin 2 roster assignment options, student lists, Admin 1 attendance ordering, volunteer teaching/checking lists, API serializer output, and historical rows after migration. Run all affected Django tests against a database containing old group values.
- **Rollback:** Apply the migration’s reverse mapping, revert model/frontend mapping and labels, and deploy the prior code. Take a database backup before migration; reverse data migration must restore old group semantics.

## CHG-004: Admin 2 day status: Holiday and Playing Day
- **Status:** Planned
- **Type:** feature
- **Description:** Complete a consistent Admin 2 calendar and day-status workflow for Holiday and Playing Day. Significant backend support already exists: holidays are date-specific records, and `DailySchoolStatus` supports HOLIDAY, PLAYING_DAY, and REGULAR_CLASS for today/tomorrow; however the frontend only has a single-date form/table and a today/tomorrow radio page, and the two holiday/status sources are not consistently enforced by all flows.
- **Current behavior/structure:** `attendance.Holiday` has a unique date, name, active flag, creator, and timestamps; Admin 2 can create/list and activate/deactivate it at `/api/admin2/holidays/`. `admin2.DailySchoolStatus` stores one status per date, but `DailySchoolStatusView` reads/writes only today or tomorrow. `Admin2Holidays.jsx` uses a date input and table, not a calendar. `Admin2SchoolDayStatus.jsx` sets tomorrow’s status. Assignment validation requires tomorrow to be REGULAR_CLASS. Attendance endpoints check `Holiday.is_holiday()`; playing-day volunteer attendance is populated automatically from active volunteers, while student attendance can still be taken. Volunteer checking is blocked unless the day is regular class. `VolunteerDashboardView` returns school status and assignment, but no dedicated student dashboard or student day view was found.
- **Target behavior/structure:** Give Admin 2 a calendar view to add/review holidays and set or see day status. Holiday blocks student attendance, volunteer assignment/work, and homework; Playing Day creates no volunteer assignments, permits student attendance for students who attend, and does not imply ordinary teaching/checking work. Show volunteers the day status and no-assignment message; student-facing status display is not present and needs product direction. Make one authoritative status decision per date and ensure the holiday model and daily status cannot disagree silently.
- **Files affected:**

  | File path | What changes |
  |---|---|
  | `frontend/src/admin2/Admin2Holidays.jsx` | Replace/augment the single-date input/table with a calendar that displays active/inactive holiday dates and supports Admin 2 create/update actions. |
  | `frontend/src/admin2/Admin2SchoolDayStatus.jsx` | Extend the today/tomorrow-only control if Admin 2 must set future dates from the calendar; show the same selected date/status source. |
  | `frontend/src/routes/admin2.holidays.jsx` | Keep the existing route and mount the calendar UI if component composition needs changes. |
  | `frontend/src/routes/admin2.school-day-status.jsx` | Keep the existing route and mount any date-specific status editor if needed. |
  | `backend/attendance/models.py` | Review `Holiday` as the holiday calendar record; add fields only if calendar requirements need more than date/name/active. |
  | `backend/admin2/models.py` | Review `DailySchoolStatus`; it already supports the three statuses per date. Any range/category or source fields require a product decision. |
  | `backend/admin2/holiday_views.py` and `backend/admin2/holiday_serializers.py` | Add date-range filtering/bulk operations only if required by calendar UX; current APIs list/create and patch one holiday. |
  | `backend/admin2/views.py` and `backend/admin2/serializers.py` | Extend day-status API for arbitrary selected dates and reconcile holiday records with `DailySchoolStatus`. |
  | `backend/admin2/urls.py` | Add routes only if a separate calendar/date-range API is selected; current endpoints are `daily-status/` and `holidays/`. |
  | `backend/attendance/views.py` | Centralize/refine holiday and Playing Day checks in Admin 1 attendance endpoints; student attendance must remain available on Playing Day but not Holiday. |
  | `backend/teachers/volunteer_views.py` | Ensure volunteer dashboard and work session/assignment responses consistently expose no-work status for Holiday/Playing Day. |
  | `backend/teachers/volunteer_checking_views.py` | Retain/align the existing regular-day guard and ensure Holiday/Playing Day are consistently blocked from checking. |
  | `backend/admin2/serializers.py` | Keep assignment validation aligned with the effective date’s status. |
  | `backend/admin2/tests.py`, `backend/admin2/tests_holiday.py`, `backend/attendance/tests.py`, `backend/teachers/test_volunteer_checking.py` | Add tests for source reconciliation and expected assignment, attendance, and work behavior. |

- **Database changes:** Existing `Holiday` and `DailySchoolStatus` tables cover much of the data need. Prefer no schema change if the existing unique-date records suffice. If the two records are unified or expanded, add migrations and define conflict resolution for dates that already have a `Holiday` row and a separate `DailySchoolStatus(status="HOLIDAY")`. No `seed_demo_data` changes are currently indicated.
- **Step-by-step instructions:**
  1. Decide which record is authoritative for a holiday and how `Holiday` and `DailySchoolStatus` are synchronized.
  2. Define supported calendar scope (single date, arbitrary future dates, or ranges) and status transition rules.
  3. Add/extend backend serializer and endpoints without breaking existing `?scope=today|tomorrow` callers.
  4. Update holiday and day-status UI to share the selected date and show current status.
  5. Align attendance/work/assignment guards and add tests for Holiday, Playing Day, and Regular Class.
  6. Run migrations if schema changed; run relevant Admin 2, attendance, teacher workflow tests.
  7. Manually verify Admin 2 calendar, student attendance during Playing Day, no assignment creation during Playing Day, volunteer display, and Holiday restrictions.
- **Dependencies and side effects:** CHG-008 depends on Playing Day semantics because the new volunteer XP rules explicitly exclude playing days. Existing behavior differs between records: `attendance/views.py` checks the `Holiday` table, while assignments and volunteer workflows also inspect `DailySchoolStatus`. Saving HOLIDAY to `DailySchoolStatus` alone may not create an `attendance.Holiday` record, so current Holiday restrictions may diverge. Playing Day currently awards attendance XP through `sync_attendance_xp`; CHG-008 must change this if the new no-reward rule is confirmed.
- **Open questions:**
  - **Needs confirmation:** Should `Holiday` be the canonical holiday calendar, or should a HOLIDAY `DailySchoolStatus` be created/updated in tandem?
  - **Needs confirmation:** Must Admin 2 set statuses for arbitrary future dates, date ranges, or only today/tomorrow?
  - **Needs confirmation:** On Playing Day, should all registered students be listed for Admin 1 attendance, or only students otherwise considered to have joined that session? No separate student opt-in/join-session model was found.
  - **Needs confirmation:** What should a student see on Holiday or Playing Day? There is currently student registration, but no student login/dashboard route or day-status display.
  - **Needs confirmation:** Should a manually chosen HOLIDAY status create a holiday name/reason, or is a reason optional?
- **Verification:** Test creating/deactivating a holiday, saving each day status, assignment rejection on non-regular days, Admin 1 student attendance permitted on Playing Day and blocked on Holiday, volunteer attendance on Playing Day, and no volunteer work/checking on non-regular days.
- **Rollback:** Revert UI/API changes and restore prior status guard logic. If introducing data synchronization, reverse the migration and preserve pre-existing rows; back up status/holiday tables first.

## CHG-005: Student homework verification and +10 XP
- **Status:** Planned
- **Type:** modify
- **Description:** Award student +10 XP when a checking volunteer verifies that homework is DONE, and award no XP when it is NOT_DONE. The database already has `StudentChecking`, `StudentHomework`, and `StudentXPTransaction`, and `sync_homework_xp()` already awards +10 XP when a `StudentHomework` record is completed; the missing connection is that the checking save endpoint currently only writes `StudentChecking` and does not update homework status or trigger XP synchronization.
- **Current behavior/structure:** `VolunteerChecking.jsx` posts DONE/NOT_DONE to `/api/teachers/checking/students/<student_id>/save/`. `VolunteerCheckingSaveView` requires an existing `StudentHomework`, then creates/updates `StudentChecking` after validating a present student, active checking assignment, and active work session; it does not update `StudentHomework`. The teaching progress save flow creates a PENDING homework record when homework is given and removes unfinished PENDING homework when homework is not given, while preserving COMPLETED homework. Separately, `/api/students/homework/<homework_id>/complete/` lets an authorized volunteer complete homework and calls `students.services.sync_homework_xp()`. `StudentHomework` is unique per student and assignment; `StudentXPTransaction.homework` is a nullable one-to-one link, and the service awards 10 points for COMPLETED and removes an automatic transaction if no longer completed.
- **Target behavior/structure:** Treat the checking-team DONE decision as the verification event that marks the matching homework record COMPLETED and syncs one +10 transaction; NOT_DONE leaves/returns the homework as PENDING and yields no active completion XP. Preserve role/assignment/present-student/work-session authorization, and prevent duplicate XP on retries or checking updates. The current one-to-one homework XP link is sufficient for the basic award; an immutable reversal/audit policy may require a ledger adjustment.
- **Files affected:**

  | File path | What changes |
  |---|---|
  | `frontend/src/volunteer/VolunteerChecking.jsx` | Keep the DONE/NOT_DONE checking form; display the resulting homework/XP outcome if the API returns it. |
  | `backend/teachers/volunteer_checking_views.py` | In `VolunteerCheckingSaveView`, synchronize the matching homework state and XP after validating/saving the checking decision. |
  | `backend/teachers/volunteer_checking_serializers.py` | Include completion/XP result fields only if needed by the client; current serializer covers checking record fields. |
  | `backend/students/models.py` | Existing `StudentHomework` and `StudentXPTransaction` models likely suffice; add fields only if an audit/reversal policy is selected. |
  | `backend/students/services.py` | Reuse/refine `sync_homework_xp()` so repeat DONE saves do not duplicate awards and NOT_DONE behavior follows the approved reversal policy. |
  | `backend/students/views.py` | Keep the separate complete endpoint compatible or route both flows through shared synchronization logic. |
  | `backend/students/serializers.py` | Return consistent homework and XP response data where needed. |
  | `backend/teachers/tests.py` or focused checking tests and `backend/students/tests.py` | Cover first DONE, repeated DONE, NOT_DONE, transition from DONE to NOT_DONE, and authorization. |

- **Database changes:** No schema change is necessary to award a single XP transaction per homework because `StudentXPTransaction.homework` is already one-to-one and `StudentHomework` uniquely pairs student/assignment. If an immutable ledger is required, add a reversal/adjustment transaction design rather than silently deleting the original award; migration and historical backfill policy are **Needs confirmation**. `seed_demo_data` does not seed students or homework.
- **Step-by-step instructions:**
  1. Decide whether checker DONE should set `StudentHomework.status=COMPLETED` directly or use a shared service endpoint.
  2. In the checking save transaction, update the existing homework record for the same student and assignment to COMPLETED or PENDING according to the approved DONE/NOT_DONE rule; preserve the current requirement that homework exists before checking.
  3. Call the shared XP synchronizer only after the homework state is saved, with transaction handling that prevents duplicate awards.
  4. Return `xp_awarded` and the updated homework/checking record where appropriate.
  5. Add focused tests for repeated saves and state transitions.
  6. Run relevant teachers and students Django tests; manually check one DONE and one NOT_DONE student in Volunteer Checking and Admin 2 student XP history.
- **Dependencies and side effects:** The existing direct homework completion endpoint and checking workflow must share the same idempotency rules. Student XP is displayed via student XP APIs and Admin 2 student detail/history; no student-facing authenticated dashboard was found. CHG-008 is a separate volunteer XP rules change and should not be mixed into this student XP logic.
- **Open questions:**
  - **Needs confirmation:** If checking changes from DONE to NOT_DONE after XP was awarded, should the award be removed (current synchronizer behavior), or should an explicit negative/reversal transaction preserve audit history?
  - **Needs confirmation:** Should an Admin 2 user be able to override a checking decision or student homework XP?
  - **Needs confirmation:** Should the XP response show the checker’s identity and the time of verification? `StudentXPTransaction.created_by` exists but current `sync_homework_xp()` sets it to `None`.
- **Verification:** Use a valid checking assignment and present students. Verify DONE updates homework to COMPLETED and adds exactly +10 once; repeated saves do not add more; NOT_DONE yields zero active completion XP; unauthorized/non-present/non-checking submissions remain rejected; student XP/history APIs report the resulting total.
- **Rollback:** Revert the checking-to-homework synchronization while keeping existing homework/XP tables and prior direct completion endpoint. If data has been changed, restore status/XP according to the approved audit policy; take a backup before backfill.

## CHG-006: Block removed students from re-registering
- **Status:** Planned
- **Type:** feature
- **Description:** Add a controlled process to flag a removed student’s later registration attempt, warn Admin 2, and allow Admin 2 to review or explicitly override the block. The current removal/status/access-request system applies to volunteers only; `Student` has no email, phone, guardian, birth-date, or removal status field, and student registration is public.
- **Current behavior/structure:** `Student` stores roll number, name, individual class, group, school, and creation time. `StudentRegistrationView` is `AllowAny` and creates a student using `StudentRegistrationSerializer`; no student removal endpoint or registration-attempt review queue exists. Admin 2’s `VolunteerAccountStatus`, removal endpoint, caution UI, and volunteer access-request endpoint are volunteer-specific and should not be reused as student identity matching without explicit design.
- **Target behavior/structure:** Before creating a student, normalize and compare an approved identifying key against records marked removed. A likely match should create a reviewable registration attempt and prevent automatic registration until Admin 2 approves or denies it. Admin 2 must be able to view match evidence, override a false positive, and record who made the decision; the new student-registration payload must collect only the minimum identity data approved.
- **Files affected:**

  | File path | What changes |
  |---|---|
  | `frontend/src/signup/StudentSignup.jsx` | Add only the approved identifier fields; show a clear pending/rejected/approved response rather than reporting a blocked attempt as a successful registration. |
  | `frontend/src/admin2/Admin2Students.jsx` | Surface pending registration-review warnings/counts or a link to the review queue. |
  | `frontend/src/admin2/Admin2StudentDetail.jsx` | Add removal/block history and Admin 2 controls only if student removal management belongs on this detail page. |
  | `frontend/src/admin2/Admin2Operations.jsx` | Add review/approve/deny interface if a separate operations panel is chosen. |
  | `frontend/src/routes/admin2.access-requests.jsx` and `frontend/src/admin2/Admin2Operations.jsx` | Extend or separate the existing volunteer access-request screen only if the product explicitly wants student registration alerts in that queue. |
  | `backend/students/models.py` | Add a proposed student removal/identity record and registration-attempt model, or fields on Student, based on the identifier and retention decision. Exact model names are **Needs confirmation**. |
  | `backend/students/serializers.py` | Validate/normalize registration identifier and expose safe registration outcome data. |
  | `backend/students/views.py` | Check identity blocks before creating a student; create an auditable pending attempt and return a non-success registration state for potential matches. |
  | `backend/students/urls.py` | Add the registration-review API route(s), with their final paths **Needs confirmation**. |
  | `backend/admin2/serializers.py` | Serialize registration attempts and removal/block details for Admin 2. |
  | `backend/admin2/views.py` | Add Admin 2-only list/detail/decision endpoints and an override audit record. |
  | `backend/admin2/urls.py` | Register the new review/override endpoints. |
  | `backend/admin2/permissions.py` | Not found in the repository; permissions are in `backend/accounts/permissions.py`. Modify the existing permissions module only if a new role check is needed. |
  | `backend/students/tests.py`, `backend/admin2/tests.py` | Cover exact match, possible match, false positive override, denied attempt, and repeat attempt behavior. |

- **Database changes:** A new identity/removal record is likely needed because the current Student model has no robust identifier beyond name/school/class; a registration-attempt table is likely needed for audit and admin review. Exact model/field design depends on the chosen identifier. Store a normalized protected value or keyed hash only if security/privacy review approves; never assume that name alone is sufficient. Add migrations and define retention/deletion rules. No student seed data exists in `seed_demo_data`; decide whether any removed test/demo students should be seeded (not recommended without approved data).
- **Step-by-step instructions:**
  1. Choose the matching identifier and define what constitutes a definite versus possible match.
  2. Define student removal authority, required reason, review status, data retention, and audit access.
  3. Add model(s) and migrations; add indexes/uniqueness constraints only after collision analysis.
  4. Update registration validation and Admin 2 review/override API with role permissions.
  5. Add the registration UI fields and clear warning states.
  6. Add tests for duplicates and false positives, then migrate and exercise the full registration/review flow.
- **Dependencies and side effects:** This changes a currently public registration API and may affect any external client. A hard block based on weak matching can deny legitimate students; a new identifier also increases sensitive personal data collection. Existing volunteer removal should remain separate unless the product chooses a shared policy.
- **Open questions:**
  - **Needs confirmation:** Which identifier(s) are allowed: phone number, guardian name/contact, date of birth, government identifier, or a combination such as name + school + date of birth? Each has different false-positive, privacy, and collection impacts.
  - **Needs confirmation:** Is a match an automatic block or a pending Admin 2 review? What confidence/match rules should be used?
  - **Needs confirmation:** Which Admin 2 role/account(s) can remove, approve, deny, or override, and must a reason be recorded?
  - **Needs confirmation:** How long should removed-student identifiers and denied registration attempts be retained, and should identifiers be encrypted or stored as keyed hashes?
  - **Needs confirmation:** Should a blocked attempt appear in the existing volunteer “Access Requests” page or a distinct student-registration review queue?
  - **Needs confirmation:** Which contact fields should be added to student registration, and what notice/consent is required?
- **Verification:** Register a student with a new identifier; remove/mark that student; submit a matching registration with a different email (email is not currently a Student field); confirm no duplicate Student is created and Admin 2 sees the attempt; approve a legitimate false positive and verify registration can proceed; ensure non-admins cannot review/override.
- **Rollback:** Disable the match/block decision endpoint and restore public registration behavior; retain review records until their approved deletion policy is applied. Restore database backup if migration or bulk identifier normalization caused corruption.

## CHG-007: Assignment emails with attached modules
- **Status:** Planned
- **Type:** feature
- **Description:** Provide Admin 2 with module/lesson-plan management and attach an appropriate module to each teaching assignment email; checking assignments should continue to email the checker at their registered email. The current assignment form already accepts a module attachment and a separate homework attachment, and the backend sends each assignment’s available files through Resend; what is missing is a reusable module library/management flow and task-specific attachment policy.
- **Current behavior/structure:** `Admin2Roster.jsx` accepts an “Attach Module” file and optional homework file and posts multipart data to `/api/admin2/assignments/send/`. `VolunteerAssignment.attachment` and `homework_attachment` are stored under `MEDIA_ROOT` in date-based folders. `SendAssignmentSerializer` permits PDF, PNG, JPG/JPEG, DOC/DOCX, TXT, XLS/XLSX and caps each attachment at 10 MB. `SendAssignmentView` creates an assignment for tomorrow and sends a text email to the volunteer’s registered email using Resend; any provided module and homework files are attached regardless of task. Failures are recorded as FAILED while the assignment remains saved; retry is available. `settings.py` defines Gmail SMTP for password reset/cautions, while the assignment view uses `RESEND_API_KEY` and `RESEND_FROM_EMAIL` (fallback sender `onboarding@resend.dev`).
- **Target behavior/structure:** Admin 2 can upload, list, update, and select reusable lesson modules; a selected module is linked to a teaching assignment and attached to the faculty/teaching volunteer’s assignment email. Checking volunteers still receive an assignment email at the registered email but do not receive a teaching module unless explicitly selected. Preserve delivery status and retry behavior. File storage remains Django media storage unless a storage migration is separately approved.
- **Files affected:**

  | File path | What changes |
  |---|---|
  | `frontend/src/admin2/Admin2Roster.jsx` | Replace or supplement direct file upload with module selection; preserve assignment/task and recipient details. |
  | `frontend/src/admin2/Admin2Operations.jsx` | Show selected module/title and attachment status in assignment history and provide management access if the UI is placed there. |
  | `frontend/src/routes/admin2.roster.jsx` and `frontend/src/routes/admin2.assignments.jsx` | Add a module-management route only if selected; route path is **Needs confirmation**. |
  | `backend/admin2/models.py` | Add a reusable module model if library management is required; retain the existing `VolunteerAssignment.attachment` for legacy/direct uploads or migrate/link as decided. |
  | `backend/admin2/serializers.py` | Add module upload/list/select validation; enforce file extension and size policy. |
  | `backend/admin2/views.py` | Add module CRUD and adjust `SendAssignmentView` / `RetryAssignmentEmailView` to attach the selected module only for applicable task types. |
  | `backend/admin2/urls.py` | Register module-management endpoints; paths are **Needs confirmation**. |
  | `backend/admin2/services.py` | Only if extracting shared email composition/delivery logic; current assignment sending and retry code is in `views.py`. |
  | `backend/config/settings.py` | Keep existing Resend/Gmail configuration or add storage/email options only if the deployment decision requires them. |
  | `backend/admin2/migrations/` | Add a migration for the module table and assignment link if a reusable library is approved. |
  | `backend/admin2/tests.py`, `backend/admin2/test_excel_export.py` | Add upload, file validation, task-specific attachment, delivery failure, retry, and legacy attachment tests. |

- **Database changes:** A reusable module library would likely add a `TeachingModule` model (proposed name) with title, file, optional subject/class applicability, active flag, uploader, and timestamps, plus a nullable FK on `VolunteerAssignment`. Exact fields and relationship are **Needs confirmation**. Existing `attachment` file paths remain valid; do not move/delete historical files without a storage migration and backup. `seed_demo_data` should not create dummy lesson files unless a non-sensitive test module is requested.
- **Step-by-step instructions:**
  1. Decide whether module management is a reusable catalog or merely the existing upload-per-assignment field with a better UI.
  2. Confirm who can upload/manage modules, allowed file types/sizes, and whether modules are scoped by subject/class.
  3. If a library is selected, add the model and migration, module serializer/views/URLs, and Admin 2 upload/list/select UI.
  4. Update assignment creation and retry email composition so teaching vs checking recipients receive the correct attachments.
  5. Retain the current Resend status/error persistence and retry semantics; confirm sender/domain configuration.
  6. Test supported and rejected files, teaching/checking deliveries, stored media links, retries, and legacy assignment rows.
- **Dependencies and side effects:** CHG-008’s substitute teaching flow depends on module selection if the substitute must receive the absent faculty member’s lesson plan. Current email delivery is implemented in both send and retry paths, so both must stay consistent. The repository does not configure an explicit total HTTP request limit or external object storage; current file-level limit is 10 MB per attachment.
- **Open questions:**
  - **Needs confirmation:** Should modules be reusable library records, or is the current per-assignment upload sufficient with improved management?
  - **Needs confirmation:** Should a module be attached only for `TEACHING`, or can checking/invigilator assignments also select one?
  - **Needs confirmation:** Are the current 10 MB and PDF/PNG/JPG/JPEG/DOC/DOCX/TXT/XLS/XLSX limits appropriate for modules? Should lesson files be PDF-only?
  - **Needs confirmation:** Should modules be scoped by course, subject, class group, or globally available?
  - **Needs confirmation:** Is Resend the required assignment provider, and what verified sender/domain should be used in each environment?
  - **Needs confirmation:** Where should Admin 2 manage the module library: a new route or within Registered Volunteers/Assignments?
- **Verification:** Upload an approved module, select it on a TEACHING assignment, verify the assignment and file persist and the volunteer receives an email with attachment; create a CHECKING assignment and verify the checker receives email at `Teacher.email`; test unsupported and oversized files; force delivery failure and use retry; confirm existing assignment attachments still open via `/media/`.
- **Rollback:** Revert UI/API and restore assignment-specific attachment handling. Do not delete the new module table or stored files until assignments referencing them have been migrated or unlinked and a backup exists.

## CHG-008: Volunteer XP system
- **Status:** Planned
- **Type:** modify
- **Description:** Change automatic volunteer XP to the requested rules: assigned faculty absent −5, present but unassigned +5, and a substitute who teaches an absent faculty member’s class +10. The current ledger already tracks automatic attendance XP and Admin 2 manual adjustments, but its values differ (assigned present +10, assigned absent −10, special present +5, Playing Day present +10), and the volunteer dashboard does not display XP or a list of substitute opportunities.
- **Current behavior/structure:** `VolunteerXPTransaction` records points/source/reason and optionally one-to-one attendance; `sync_attendance_xp()` is called by the `VolunteerAttendance` post-save signal in `admin2/signals.py`. It deletes/recreates the automatic XP row for the attendance record when the attendance changes. Existing constants are `NORMAL_PRESENT_XP=10`, `NORMAL_ABSENT_XP=-10`, and `SPECIAL_PRESENT_XP=5`; Playing Day present currently receives +10 and absent 0. `Admin2VolunteerDetail.jsx` and `/api/admin2/xp/<volunteer_id>/` show the Admin 2 ledger and allow manual adjustment. `VolunteerDashboardView` does not return XP. `SpecialAddedWorkAccess` can authorize one special volunteer for one assignment and current special-added UI does not show a directory of absent faculty/class students to every present unassigned volunteer.
- **Target behavior/structure:** Apply the three requested rules with clear sources/reasons and duplicate protection. Calculate attendance-based values only once the attendance/session is finalized, if finalization is adopted; changing or reopening attendance must update/reverse automatic points safely without duplicating awards. Playing Day should grant neither attendance penalty nor reward under the requested dependency. A present, unassigned faculty member should see eligible absent-faculty coverage options with teaching instructions, class, students, and any selected module, and a successful substitute coverage should record +10 XP. Display current XP/history to both Admin 2 and the volunteer.
- **Files affected:**

  | File path | What changes |
  |---|---|
  | `backend/admin2/models.py` | Extend XP source choices or add a coverage relation/ledger linkage to distinguish unassigned presence and substitute teaching from ordinary attendance. |
  | `backend/admin2/services.py` | Replace XP constants/rules; implement idempotent finalization/recalculation and no-XP Playing Day behavior; preserve manual adjustment behavior. |
  | `backend/admin2/signals.py` | Reconsider immediate `post_save` XP calculation; trigger calculation at approved attendance finalization or ensure synchronization is safe before and after finalization. |
  | `backend/attendance/models.py` | Add an explicit finalization field/state to `AttendanceSession` only if an explicit finalization lifecycle is chosen; currently it has active/end/expiry times but no finalization status. |
  | `backend/attendance/views.py` | Add/adjust session finalization or attendance actions, and expose eligible absent/unassigned coverage data if it belongs in attendance APIs. |
  | `backend/admin2/serializers.py` | Expose new XP source labels and any substitute/coverage summary fields. |
  | `backend/admin2/views.py` and `backend/admin2/urls.py` | Add Admin 2 reporting/coverage administration only if needed; existing volunteer XP history and manual adjustment endpoints are present. |
  | `backend/teachers/models.py` | Extend `SpecialAddedWorkAccess` or add a dedicated substitute coverage model if its current one-special-volunteer-per-day rule cannot represent the requested flow. |
  | `backend/teachers/volunteer_views.py` | Include volunteer XP and available substitute coverage links in dashboard responses. |
  | `backend/teachers/special_added_views.py` | Review/extend existing selection flow to authorize the new substitute work without violating current Special Added rules. |
  | `backend/teachers/urls.py` | Add a coverage list/select endpoint if not represented by existing special-added routes. |
  | `frontend/src/routes/volunteer.dashboard.jsx` | Display the volunteer’s XP and coverage opportunities including absent volunteer, class, teaching instruction, and student names. |
  | `frontend/src/volunteer/VolunteerSpecialAdded.jsx` | Reuse or replace the current Special Added selection UI according to the approved substitute model. |
  | `frontend/src/admin2/Admin2VolunteerDetail.jsx` | Continue displaying XP history and ensure new source/reason records are human-readable. |
  | `frontend/src/admin2/Admin2Volunteers.jsx` | Keep roster XP totals consistent with new automatic transactions. |
  | `backend/admin2/tests.py`, `backend/attendance/tests.py`, `backend/teachers/test_special_added_work_access.py`, `backend/teachers/test_special_added_work_flow.py` | Cover each rule, playing day, finalization, duplicate protection, multiple substitutes, attendance edits, and authorization. |

- **Database changes:** `VolunteerXPTransaction` already provides a ledger, points, source, reason, optional one-to-one attendance, and actor; the current attendance relation can protect one attendance-based award per record. A distinct `VolunteerCoverage`/`SubstituteCoverage` relation is likely needed if one attendance record can cover multiple absent assignments or one absent assignment can be split among several substitutes. An explicit `AttendanceSession` finalization field may be needed. Exact schema depends on when attendance is finalized and how multiple substitutes/partial coverage are credited. Add migrations with existing XP values preserved; do not rewrite historical ledger points unless a backfill is approved. `seed_demo_data` currently creates no XP/attendance demo records.
- **Step-by-step instructions:**
  1. Confirm the XP value for assigned-present volunteers; the prompt defines absent, unassigned-present, and substitute values but current assigned-present is +10.
  2. Agree on session finalization timing and whether attendance edits after finalization create compensating ledger entries or recalculate/delete automatic transactions.
  3. Define how coverage opportunities are generated and reserved, and whether one absent assignment can be covered by one or several substitutes.
  4. Design coverage records and new ledger source/relationship; add migrations without rewriting existing XP history.
  5. Update attendance XP calculation to use the new values and suppress Playing Day awards under CHG-004 rules.
  6. Add API data/actions and volunteer dashboard UI for coverage and current XP; preserve Admin 2 totals/history.
  7. Update assignment email/module integration from CHG-007 for substitute lesson materials.
  8. Run the existing XP/attendance/special-added test suites, then manually test assigned absence, unassigned present, substitute cover, Playing Day, repeated attendance saves, and Admin 2 manual adjustment.
- **Dependencies and side effects:** Depends on CHG-004 for day status and Playing Day suppression; depends on CHG-007 if substitute coverage sends modules. Existing `SpecialAddedWorkAccess` allows one assigned replacement per volunteer/day and `VolunteerAssignment` is unique per volunteer/date, while the proposed substitute scenario may need a different many-to-many coverage relation. Existing attendance save signals calculate XP immediately; changing timing may affect XP totals and caution evaluation. Caution creation is also triggered from assigned absence saves and should remain independent of XP.
- **Open questions:**
  - **Needs confirmation:** What XP should a faculty member receive when present and assigned? The existing rule is +10, but the new list does not state whether to keep or change it.
  - **Needs confirmation:** Does “present but has not been assigned” include any volunteer present on a regular class day, or only volunteers explicitly marked `SPECIAL_ADDED`?
  - **Needs confirmation:** What exactly counts as substitute teaching: accepted/selected coverage, completed work session, recorded student progress, or Admin 1 confirmation?
  - **Needs confirmation:** When is attendance finalized (Admin 1 closes the session, a deadline, or another approval), and can finalized attendance be edited?
  - **Needs confirmation:** If an absent faculty member has multiple classes/tasks, may multiple substitutes each receive +10, or should the +10 be divided/limited? How should partial coverage be recorded?
  - **Needs confirmation:** Should assigned-present and substitute XP be suppressed on all Playing Days, including attendance rows marked PRESENT?
  - **Needs confirmation:** Should historical XP be recalculated to the new rule values, or should new values apply only from a release date onward?
  - **Needs confirmation:** Should XP totals/history be shown to volunteers via the dashboard, or through a separate volunteer XP page?
- **Verification:** Verify all three requested outcomes and selected policy for assigned-present; ensure repeated attendance updates do not duplicate XP; ensure Playing Day does not award or penalize XP; verify substitute candidates see only eligible absent assignments and correct class/student lists; test two substitutes and one substitute covering multiple assignments; verify totals in Admin 2 roster/detail and the volunteer UI.
- **Rollback:** Revert calculation and UI/API changes. Keep the ledger/migration data; if XP transactions have been written under new rules, do not delete or overwrite them without an approved adjustment plan. Restore a database backup before any historical recalculation.

## Consolidated Needs confirmation

1. **CHG-001:** Whether the title/cards belong below the current site header or should merge into/replace it.
2. **CHG-002:** Whether existing developer names, roles, biographies, and LinkedIn links are approved; provide approved profile content/photos/permissions; clarify what “toolkit components” means; decide whether navigation needs a developers anchor.
3. **CHG-003:** Preserve `ClassA`–`ClassE` codes or expose bare A–E; Admin 2 filters by class/group/both; preserve the existing roll-number format.
4. **CHG-004:** Canonical holiday source and synchronization; supported future/range calendar; Playing Day student attendance eligibility; student-facing status behavior; holiday reason/name requirements.
5. **CHG-005:** XP revocation versus audit-preserving reversal after DONE→NOT_DONE; Admin 2 override ability; recording/displaying checker identity and verification time.
6. **CHG-006:** Student match identifiers and confidence rules; automatic block versus review; removal/override authorities and reason; data retention and protection; existing or separate review queue; registration contact fields and consent.
7. **CHG-007:** Reusable module library versus current per-assignment upload; task applicability; file limits/types; class/subject scoping; email provider/sender; management UI location.
8. **CHG-008:** Assigned-present XP; definition of unassigned-present; what qualifies as completed substitute work; attendance finalization and post-finalization edits; multiple substitute credit policy; Playing Day XP suppression; historical backfill policy; volunteer XP display location.

## Change log

| Date | Change ID | What was done | Done by |
|---|---|---|---|
|  |  |  |  |
