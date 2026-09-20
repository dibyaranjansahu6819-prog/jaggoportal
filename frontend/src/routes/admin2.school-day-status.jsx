import { createFileRoute } from "@tanstack/react-router";
import Admin2SchoolDayStatus from "@/admin2/Admin2SchoolDayStatus";

export const Route = createFileRoute("/admin2/school-day-status")({
  head: () => ({
    meta: [
      { title: "School Day Status — Jaago Admin 2" },
      { name: "description", content: "Set the school day mode: Regular Class, Playing Day or Holiday." },
      { property: "og:title", content: "School Day Status — Jaago Admin 2" },
      { property: "og:description", content: "Set the school day mode: Regular Class, Playing Day or Holiday." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: Admin2SchoolDayStatus,
});
