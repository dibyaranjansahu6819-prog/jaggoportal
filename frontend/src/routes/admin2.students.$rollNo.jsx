import { createFileRoute } from "@tanstack/react-router";
import Admin2StudentDetail from "@/admin2/Admin2StudentDetail";

export const Route = createFileRoute("/admin2/students/$rollNo")({
  head: () => ({
    meta: [
      { title: "Student Details — Jaago Admin 2" },
      { name: "description", content: "Student profile, attendance, XP, homework and 14-day performance." },
      { property: "og:title", content: "Student Details — Jaago Admin 2" },
      { property: "og:description", content: "Student profile, attendance, XP, homework and 14-day performance." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: Admin2StudentDetail,
});
