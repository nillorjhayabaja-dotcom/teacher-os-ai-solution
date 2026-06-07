import { createFileRoute } from "@tanstack/react-router";
import { ModulePreview } from "@/components/module-preview";
import { BarChart3 } from "lucide-react";

export const Route = createFileRoute("/reports")({
  head: () => ({ meta: [{ title: "Reports & Compliance · TeacherOS" }] }),
  component: () => (
    <ModulePreview
      icon={BarChart3}
      eyebrow="Reports & Compliance Engine"
      title="Replace manual documentation"
      description="RPMS, monthly accomplishment, narrative reports, and school documentation — drafted by AI, validated by you, evidence auto-attached."
      steps={[
        { title: "Input", desc: "Select report type and period." },
        { title: "AI Draft", desc: "Narrative generated from your activity logs." },
        { title: "Review", desc: "Rich editor with section anchors." },
        { title: "Attach Evidence", desc: "Photos, DLLs, sample outputs auto-linked." },
        { title: "Export", desc: "Word, PDF, online portal." },
        { title: "Submit", desc: "Track approval through Head Teacher → Principal." },
      ]}
    />
  ),
});
