import { createFileRoute } from "@tanstack/react-router";

// @ts-expect-error - JSX page ported from the original frontend
import Admin1Attendance from "../admin1/Admin1Attendance";

export const Route = createFileRoute("/admin1/attendance-dashboard")({
  head: () => ({
    meta: [
      { title: "Admin 1 Attendance Toolkit — Jaago" },
      {
        name: "description",
        content:
          "Mark student attendance, upload the attendance photo and record volunteer attendance for today's session.",
      },
      { property: "og:title", content: "Admin 1 Attendance Toolkit — Jaago" },
      {
        property: "og:description",
        content:
          "Mark student attendance, upload the attendance photo and record volunteer attendance for today's session.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: Admin1Attendance,
});
