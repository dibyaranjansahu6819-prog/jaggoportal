import { createFileRoute } from "@tanstack/react-router";
import { Admin2DailyPNG } from "@/admin2/Admin2Operations";

export const Route = createFileRoute("/admin2/daily-png")({
  head: () => ({
    meta: [
      { title: "Daily PNG — Jaago Admin 2" },
      { name: "description", content: "Simple daily school record: date, status, class, volunteer, subject and role." },
      { property: "og:title", content: "Daily PNG — Jaago Admin 2" },
      { property: "og:description", content: "Simple daily school record: date, status, class, volunteer, subject and role." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: Admin2DailyPNG,
});
