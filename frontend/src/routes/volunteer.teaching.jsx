import { createFileRoute } from "@tanstack/react-router";
import VolunteerTeaching from "../volunteer/VolunteerTeaching";

export const Route = createFileRoute("/volunteer/teaching")({
  head: () => ({
    meta: [
      { title: "Track Progress — Jaago Teaching Portal" },
      { name: "description", content: "Record student performance for today's Teaching assignment." },
    ],
  }),
  component: VolunteerTeaching,
});
