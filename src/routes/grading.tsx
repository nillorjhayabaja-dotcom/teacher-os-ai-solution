import { createFileRoute } from "@tanstack/react-router";
import { ModulePreview } from "@/components/module-preview";
import { Calculator } from "lucide-react";

export const Route = createFileRoute("/grading")({
  head: () => ({ meta: [{ title: "Grading Cycle · TeacherOS" }] }),
  component: () => (
    <ModulePreview
      icon={Calculator}
      eyebrow="Grading Cycle Engine"
      title="DepEd-weighted quarter grading, end to end"
      description="Not a gradebook — a full workflow from raw scores to finalized SF9, with AI error detection and at-risk analytics."
      steps={[
        { title: "Data Input", desc: "Written Works · Performance Tasks · Quarterly Exams." },
        { title: "Weight Configuration", desc: "DepEd matrices per learning area, pre-loaded." },
        { title: "AI Computation", desc: "Auto-calc with anomaly detection." },
        { title: "Analytics", desc: "Class performance, ranking, risk flags." },
        { title: "Approval Workflow", desc: "Draft → Review → Finalize with sign-off log." },
        { title: "Export", desc: "Report cards, grade sheets, SF9 integration." },
      ]}
    />
  ),
});
