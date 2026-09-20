import { createFileRoute } from "@tanstack/react-router";
import StudentSignup from "../signup/StudentSignup";

export const Route = createFileRoute("/student/signup")({
  head: () => ({
    meta: [
      { title: "Student Signup — Jaago Attendance" },
      { name: "description", content: "Register a student for Jaago attendance." },
      { property: "og:title", content: "Student Signup — Jaago Attendance" },
      { property: "og:description", content: "Register a student for Jaago attendance." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: StudentSignup,
});
