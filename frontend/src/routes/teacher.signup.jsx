import { createFileRoute } from "@tanstack/react-router";
import TeacherSignup from "../signup/TeacherSignup";

export const Route = createFileRoute("/teacher/signup")({
  head: () => ({
    meta: [
      { title: "Teacher Signup — Jaago Attendance" },
      { name: "description", content: "Register a teacher for Jaago attendance." },
      { property: "og:title", content: "Teacher Signup — Jaago Attendance" },
      { property: "og:description", content: "Register a teacher for Jaago attendance." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: TeacherSignup,
});
