import { createFileRoute } from "@tanstack/react-router";
import VolunteerSpecialAdded from "../volunteer/VolunteerSpecialAdded";

export const Route = createFileRoute("/volunteer/special-added")({
  head: () => ({
    meta: [
      { title: "Special Added Work — Jaago Teaching Portal" },
      { name: "description", content: "Pick an absent volunteer's assignment to cover today." },
    ],
  }),
  component: VolunteerSpecialAdded,
});
