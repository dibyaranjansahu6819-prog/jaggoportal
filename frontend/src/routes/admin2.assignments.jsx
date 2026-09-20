import { createFileRoute } from "@tanstack/react-router";
import { Admin2Assignments } from "@/admin2/Admin2Operations";

export const Route = createFileRoute("/admin2/assignments")({
  head: () => ({
    meta: [
      { title: "Assignment History — Jaago Admin 2" },
      { name: "description", content: "Volunteer assignments, instruction emails and work session status." },
      { property: "og:title", content: "Assignment History — Jaago Admin 2" },
      { property: "og:description", content: "Volunteer assignments, instruction emails and work session status." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: Admin2Assignments,
});
