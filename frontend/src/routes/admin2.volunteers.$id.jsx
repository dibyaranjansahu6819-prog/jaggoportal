import { createFileRoute } from "@tanstack/react-router";
import Admin2VolunteerDetail from "@/admin2/Admin2VolunteerDetail";

export const Route = createFileRoute("/admin2/volunteers/$id")({
  head: () => ({
    meta: [
      { title: "Volunteer Details — Jaago Admin 2" },
      { name: "description", content: "Volunteer profile, XP history, attendance, assignments, absences and caution status." },
      { property: "og:title", content: "Volunteer Details — Jaago Admin 2" },
      { property: "og:description", content: "Volunteer profile, XP history, attendance, assignments, absences and caution status." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: Admin2VolunteerDetail,
});
