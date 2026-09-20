import { createFileRoute } from "@tanstack/react-router";
import Admin1History from "../admin1/Admin1History";

export const Route = createFileRoute("/admin1/history")({
  head: () => ({
    meta: [
      { title: "Attendance History — Jaago Admin 1" },
      { name: "description", content: "Today's attendance summary and past attendance sessions." },
    ],
  }),
  component: Admin1History,
});
