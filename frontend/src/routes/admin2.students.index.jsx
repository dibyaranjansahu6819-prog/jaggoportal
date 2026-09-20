import { createFileRoute } from "@tanstack/react-router";
import Admin2Students from "@/admin2/Admin2Students";

export const Route = createFileRoute("/admin2/students/")({
  head: () => ({
    meta: [
      { title: "Students — Jaago Admin 2" },
      { name: "description", content: "Search and review student records, attendance and XP." },
      { property: "og:title", content: "Students — Jaago Admin 2" },
      { property: "og:description", content: "Search and review student records, attendance and XP." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: Admin2Students,
});
