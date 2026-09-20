import { createFileRoute } from "@tanstack/react-router";
import VolunteerChecking from "../volunteer/VolunteerChecking";

export const Route = createFileRoute("/volunteer/checking")({
  head: () => ({
    meta: [
      { title: "Homework Checking — Jaago Teaching Portal" },
      { name: "description", content: "Mark today's homework as done or not done for each present student." },
    ],
  }),
  component: VolunteerChecking,
});
