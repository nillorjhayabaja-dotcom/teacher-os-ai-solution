import { createFileRoute } from "@tanstack/react-router";
import { ModulePreview } from "@/components/module-preview";
import { CalendarDays } from "lucide-react";

export const Route = createFileRoute("/teaching")({
  head: () => ({ meta: [{ title: "Teaching Workflow · TeacherOS" }] }),
  component: () => (
    <ModulePreview
      icon={CalendarDays}
      eyebrow="Teaching Workflow"
      title="Your weekly teaching execution system"
      description="Plan, teach, assess, reflect — a single rhythm for your entire week, with autopilot suggestions from the AI Daily Briefing."
      steps={[
        { title: "Weekly Plan", desc: "Auto-built from your DLLs and bell schedule." },
        { title: "Daily Execution", desc: "Today's classes with one-tap workflow start." },
        { title: "Attendance Capture", desc: "Quick check-in, feeds SF2 instantly." },
        { title: "Formative Pulse", desc: "AI gauges mastery after each lesson." },
        { title: "Reflection Log", desc: "Auto-prompts: what worked, what didn't." },
        { title: "Hand-off to RPMS", desc: "Evidence collected automatically." },
      ]}
    />
  ),
});
