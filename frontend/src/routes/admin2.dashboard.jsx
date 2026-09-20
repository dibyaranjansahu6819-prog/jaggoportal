import { createFileRoute } from "@tanstack/react-router";
import Admin2Dashboard from "@/admin2/Admin2Dashboard";

export const Route = createFileRoute("/admin2/dashboard")({
  head: () => ({
    meta: [
      { title: "Dashboard — Jaago Admin 2" },
      { name: "description", content: "School overview: students, attendance, volunteers, assignments, cautions and requests." },
      { property: "og:title", content: "Dashboard — Jaago Admin 2" },
      { property: "og:description", content: "School overview: students, attendance, volunteers, assignments, cautions and requests." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: Admin2Dashboard,
});
