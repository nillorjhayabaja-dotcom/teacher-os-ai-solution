import { createFileRoute } from "@tanstack/react-router";
import { ModulePreview } from "@/components/module-preview";
import { School } from "lucide-react";

export const Route = createFileRoute("/programs")({
  head: () => ({ meta: [{ title: "School Programs · TeacherOS" }] }),
  component: () => (
    <ModulePreview
      icon={School}
      eyebrow="School Programs Workflow"
      title="Plan, run, and report school programs"
      description="Feeding Program, DRRM, Brigada Eskwela, school events — from kickoff to post-activity reporting in one workflow."
      steps={[
        { title: "Program Setup", desc: "Pick program, owners, dates." },
        { title: "Planning Phase", desc: "Objectives, target beneficiaries, risks." },
        { title: "Budget Generator", desc: "Auto-itemize line items vs MOOE." },
        { title: "Activity Timeline", desc: "Gantt-style schedule + reminders." },
        { title: "Execution Log", desc: "Photos, headcount, on-the-day notes." },
        { title: "Post-Report", desc: "AI-drafted accomplishment report." },
      ]}
    />
  ),
});
