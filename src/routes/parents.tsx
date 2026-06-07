import { createFileRoute } from "@tanstack/react-router";
import { ModulePreview } from "@/components/module-preview";
import { MessageSquare } from "lucide-react";

export const Route = createFileRoute("/parents")({
  head: () => ({ meta: [{ title: "Parent Communication · TeacherOS" }] }),
  component: () => (
    <ModulePreview
      icon={MessageSquare}
      eyebrow="Parent Communication Flow"
      title="Structured, AI-drafted parent comms"
      description="Templates, auto-translated to Tagalog/Bisaya/English, with SMS and Messenger preview and a full communication history per learner."
      steps={[
        { title: "Select Student", desc: "Pull learner profile + recent issues." },
        { title: "Select Issue", desc: "Absence, grade drop, behavior, achievement." },
        { title: "AI Drafts Message", desc: "Tone-matched, bilingual." },
        { title: "Review", desc: "Edit + preview in messaging surface." },
        { title: "Send / Export", desc: "SMS, Messenger, printable letter." },
        { title: "History", desc: "All comms logged per student." },
      ]}
    />
  ),
});
