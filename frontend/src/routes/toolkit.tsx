import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/toolkit")({
  head: () => ({
    meta: [
      { title: "Admin 1 Attendance Toolkit — Jaago" },
      {
        name: "description",
        content:
          "Jaago Admin 1 attendance toolkit: student attendance, volunteer attendance, and Add Volunteer (Special Added).",
      },
      { property: "og:title", content: "Admin 1 Attendance Toolkit — Jaago" },
      {
        property: "og:description",
        content:
          "Jaago Admin 1 attendance toolkit: student attendance, volunteer attendance, and Add Volunteer (Special Added).",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: ToolkitPage,
});

function ToolkitPage() {
  return (
    <iframe
      src="/toolkit/index.html"
      title="Admin 1 Attendance Toolkit"
      style={{
        position: "fixed",
        inset: 0,
        width: "100%",
        height: "100%",
        border: "none",
      }}
    />
  );
}
