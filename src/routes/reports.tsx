import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { PageHeader } from "@/components/page-header";
import { WorkflowStepper } from "@/components/workflow-stepper";
import { Button } from "@/components/ui/button";
import { mockReportTemplates } from "@/lib/mock-data";
import {
  BarChart3, Sparkles, Check, ChevronRight, FileText,
  Download, Upload, Wand2, Edit, ShieldCheck, Paperclip,
} from "lucide-react";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/reports")({
  head: () => ({
    meta: [
      { title: "Reports & Compliance · TeacherOS" },
      { name: "description", content: "RPMS, monthly accomplishment, narrative reports with AI drafting and evidence attachment." },
    ],
  }),
  component: ReportsPage,
});

const steps = [
  { id: 1, title: "Template", desc: "Select report type" },
  { id: 2, title: "Input", desc: "Key info for AI" },
  { id: 3, title: "AI Draft", desc: "Generated preview" },
  { id: 4, title: "Review", desc: "Edit sections" },
  { id: 5, title: "Evidence", desc: "Attach files" },
  { id: 6, title: "Export", desc: "PDF & submit" },
];

const types = [
  { id: "RPMS", label: "RPMS", desc: "Performance Review", icon: "📋" },
  { id: "Monthly", label: "Monthly Accomplishment", desc: "Monthly report", icon: "📊" },
  { id: "Narrative", label: "Narrative Report", desc: "Activity write-up", icon: "📝" },
];

const sampleDraft = `I. INTRODUCTION
This report covers the accomplishments, challenges, and interventions implemented during the period under review.

II. KEY ACCOMPLISHMENTS
- Successfully delivered 45 lessons across 3 sections
- Conducted 2 formative assessments per week per section
- Identified and provided remediation for 5 at-risk learners
- Maintained 92% average attendance rate across all sections

III. CHALLENGES
- 3 students identified with significant learning gaps in Mathematics
- Limited instructional materials for Science experiments
- 2 cases of chronic absenteeism requiring parent intervention

IV. INTERVENTIONS
- Implemented weekly remediation sessions every Friday
- Created supplementary worksheets for low-performing learners
- Scheduled parent-teacher conferences for absentees

V. RECOMMENDATIONS
- Continue remediation program for at-risk learners
- Request additional Science laboratory supplies
- Strengthen parent communication for attendance monitoring`;

function ReportsPage() {
  const [step, setStep] = useState(1);
  const [selectedTemplate, setSelectedTemplate] = useState(mockReportTemplates[0]);
  const [accomplishments, setAccomplishments] = useState("");
  const [challenges, setChallenges] = useState("");
  const [interventions, setInterventions] = useState("");
  const [draft, setDraft] = useState("");
  const [generating, setGenerating] = useState(false);
  const [generated, setGenerated] = useState(false);
  const [evidence, setEvidence] = useState<string[]>(["DLL_Week4_Math.pdf", "Science_Fair_Photos.zip", "Quiz_Results_Q1.xlsx"]);
  const [dragging, setDragging] = useState(false);

  function generateReport() {
    setGenerating(true);
    setTimeout(() => {
      setDraft(sampleDraft);
      setGenerating(false);
      setGenerated(true);
      setStep(4);
    }, 1500);
  }

  return (
    <div className="px-4 lg:px-8 py-6 lg:py-8 max-w-[1600px] mx-auto space-y-6">
      <PageHeader
        eyebrow="Reports & Compliance Engine"
        title="Replace Manual Documentation with AI Drafting"
        description="RPMS, monthly accomplishment, narrative reports — drafted by AI, validated by you, evidence auto-attached."
        actions={
          <Button className="gap-2"><Wand2 className="size-4"/>New Report</Button>
        }
      />

      <WorkflowStepper steps={steps} current={step} onSelect={setStep} />

      {/* Step 1: Select Template */}
      {step === 1 && (
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 rounded-xl border border-border bg-card p-6">
            <h2 className="font-semibold mb-4">Step 1 · Select Report Template</h2>
            <div className="grid sm:grid-cols-3 gap-3">
              {types.map(type => (
                <button key={type.id} onClick={() => {
                  setSelectedTemplate(mockReportTemplates.find(t => t.type === type.id) || mockReportTemplates[0]);
                }}
                  className={cn("rounded-xl border p-5 text-left transition-all hover:border-primary",
                    selectedTemplate.type === type.id ? "border-primary bg-primary-soft" : "border-border bg-card")}>
                  <span className="text-2xl">{type.icon}</span>
                  <div className="mt-3 font-semibold text-sm">{type.label}</div>
                  <div className="text-xs text-muted-foreground mt-0.5">{type.desc}</div>
                </button>
              ))}
            </div>

            <div className="mt-8">
              <h3 className="text-sm font-semibold mb-3">Recent Reports</h3>
              <div className="divide-y divide-border border border-border rounded-lg">
                {mockReportTemplates.map(r => (
                  <div key={r.id} className="flex items-center justify-between p-3 hover:bg-muted/40">
                    <div>
                      <div className="text-sm font-medium">{r.name}</div>
                      <div className="text-xs text-muted-foreground">{r.type} · Last edited: {r.lastEdited}</div>
                    </div>
                    <span className={cn("text-[10px] px-2 py-0.5 rounded font-medium",
                      r.status === "completed" ? "bg-success/10 text-success" :
                      r.status === "in-progress" ? "bg-warning/15 text-warning-foreground" : "bg-muted text-muted-foreground")}>
                      {r.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end mt-6">
              <Button onClick={() => setStep(2)} className="gap-2">
                Continue <ChevronRight className="size-4"/>
              </Button>
            </div>
          </div>
          <div className="rounded-xl border border-primary/20 bg-primary-soft/40 p-5">
            <Sparkles className="size-4 text-primary"/>
            <h3 className="text-sm font-semibold mt-2">AI Tips</h3>
            <ul className="mt-3 space-y-2 text-xs text-muted-foreground">
              <li>• RPMS reports auto-populate from your DLLs and grades</li>
              <li>• Monthly reports pull data from your execution logs</li>
              <li>• Narrative reports use AI to write complete stories</li>
              <li>• All reports support evidence attachment (PDF, images)</li>
            </ul>
          </div>
        </div>
      )}

      {/* Step 2: Input */}
      {step === 2 && (
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 rounded-xl border border-border bg-card p-6 space-y-5">
            <h2 className="font-semibold">Step 2 · Input Information for AI Draft</h2>
            <p className="text-sm text-muted-foreground">Provide key details for the AI to generate your {selectedTemplate.name}.</p>

            <div>
              <label className="text-xs font-semibold text-muted-foreground mb-1.5 block">Key Accomplishments</label>
              <textarea value={accomplishments} onChange={(e) => setAccomplishments(e.target.value)}
                placeholder="e.g., Delivered 45 lessons, conducted assessments, held parent meetings..."
                className="w-full h-24 p-3 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring/30 resize-none" />
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground mb-1.5 block">Challenges Faced</label>
              <textarea value={challenges} onChange={(e) => setChallenges(e.target.value)}
                placeholder="e.g., Learning gaps, attendance issues, resource limitations..."
                className="w-full h-20 p-3 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring/30 resize-none" />
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground mb-1.5 block">Interventions Applied</label>
              <textarea value={interventions} onChange={(e) => setInterventions(e.target.value)}
                placeholder="e.g., Remediation sessions, supplementary materials, parent conferences..."
                className="w-full h-20 p-3 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring/30 resize-none" />
            </div>

            <div className="flex justify-between pt-2">
              <Button variant="outline" onClick={() => setStep(1)}>← Back</Button>
              <Button onClick={generateReport} className="gap-2">
                <Wand2 className="size-4"/> Generate Report with AI
              </Button>
            </div>
          </div>
          <div className="rounded-xl border border-border bg-card p-5">
            <h3 className="text-sm font-semibold mb-3">Report Context</h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between"><span className="text-muted-foreground">Template</span><span className="font-medium">{selectedTemplate.name}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Period</span><span className="font-medium">Quarter 1, Sy 2026-2027</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Teacher</span><span className="font-medium">Mariel Reyes</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">School</span><span className="font-medium">Sampaloc ES</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Division</span><span className="font-medium">Bulacan</span></div>
            </div>
          </div>
        </div>
      )}

      {/* Step 3: Generating */}
      {step === 3 && generating && (
        <div className="rounded-xl border border-border bg-card p-8 text-center">
          <Sparkles className="size-10 text-primary mx-auto animate-pulse"/>
          <h2 className="font-semibold mt-4 text-lg">AI is writing your report…</h2>
          <p className="text-sm text-muted-foreground mt-1">Drafting narrative, formatting sections, and checking DepEd compliance.</p>
          <div className="mt-6 max-w-md mx-auto">
            <div className="h-2 rounded-full bg-muted overflow-hidden">
              <div className="h-full bg-gradient-primary animate-pulse" style={{ width: "60%" }}/>
            </div>
            <ul className="mt-4 text-xs text-muted-foreground space-y-1.5 text-left">
              <li className="flex items-center gap-2"><Check className="size-3 text-success"/> Analyzing input data…</li>
              <li className="flex items-center gap-2"><Sparkles className="size-3 text-primary animate-pulse"/> Drafting Introduction…</li>
              <li className="flex items-center gap-2 text-muted-foreground/50"> Writing Accomplishments…</li>
              <li className="flex items-center gap-2 text-muted-foreground/50"> Formatting sections…</li>
            </ul>
          </div>
        </div>
      )}

      {/* Step 4: Review & Edit */}
      {step === 4 && (
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <div className="rounded-xl border border-border bg-card">
              <div className="flex items-center justify-between p-4 border-b border-border">
                <h2 className="font-semibold">Step 4 · Review & Edit Draft</h2>
                <div className="flex items-center gap-2">
                  <Button size="sm" variant="outline" className="gap-1.5"><Wand2 className="size-3"/>Improve</Button>
                  <span className="text-[11px] font-medium px-2 py-1 rounded bg-success/10 text-success flex items-center gap-1">
                    <Check className="size-3"/>AI-generated
                  </span>
                </div>
              </div>
              <div className="p-6">
                <div className="text-sm whitespace-pre-wrap font-sans leading-relaxed text-foreground/90">{draft}</div>
              </div>
            </div>
            <div className="flex justify-between">
              <Button variant="outline" onClick={() => setStep(2)}>← Back</Button>
              <Button onClick={() => setStep(5)} className="gap-2">
                Attach Evidence <ChevronRight className="size-4"/>
              </Button>
            </div>
          </div>
          <div className="space-y-4">
            <div className="rounded-xl border border-border bg-card p-5">
              <h3 className="text-sm font-semibold flex items-center gap-2">
                <Edit className="size-4 text-primary"/> Editing Tools
              </h3>
              <div className="mt-3 space-y-2">
                <Button size="sm" variant="outline" className="w-full justify-start gap-2"><Wand2 className="size-3"/>Improve Section</Button>
                <Button size="sm" variant="outline" className="w-full justify-start gap-2">📝 Add Paragraph</Button>
                <Button size="sm" variant="outline" className="w-full justify-start gap-2">🔍 Check Grammar</Button>
                <Button size="sm" variant="outline" className="w-full justify-start gap-2">📏 Adjust Length</Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Step 5: Evidence Upload */}
      {step === 5 && (
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <div className="rounded-xl border border-border bg-card p-6">
              <h2 className="font-semibold mb-1">Step 5 · Attach Evidence</h2>
              <p className="text-sm text-muted-foreground mb-4">Drag & drop files or click to browse. Supported: PDF, DOCX, JPG, PNG, XLSX.</p>

              <div
                onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                onDrop={(e) => { e.preventDefault(); setDragging(false); setEvidence(prev => [...prev, "New_File.pdf"]); }}
                className={cn("border-2 border-dashed rounded-xl p-8 text-center transition-all",
                  dragging ? "border-primary bg-primary-soft" : "border-border hover:border-primary/50")}>
                <Paperclip className="size-8 text-muted-foreground mx-auto"/>
                <p className="mt-2 text-sm text-muted-foreground">Drop files here or <span className="text-primary hover:underline cursor-pointer">browse</span></p>
                <p className="text-xs text-muted-foreground mt-1">Max 20MB per file</p>
              </div>

              <div className="mt-4 space-y-2">
                {evidence.map((file, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 rounded-lg border border-border">
                    {file.endsWith(".pdf") ? <FileText className="size-5 text-destructive"/> :
                     file.endsWith(".zip") ? <FileText className="size-5 text-warning-foreground"/> :
                     <FileText className="size-5 text-success"/>}
                    <div className="flex-1">
                      <div className="text-sm font-medium">{file}</div>
                      <div className="text-xs text-muted-foreground">Uploaded just now · Linked to: {selectedTemplate.name}</div>
                    </div>
                    <Button size="sm" variant="ghost" className="text-muted-foreground">✕</Button>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-between">
              <Button variant="outline" onClick={() => setStep(4)}>← Back to Draft</Button>
              <Button onClick={() => setStep(6)} className="gap-2">
                Continue to Export <ChevronRight className="size-4"/>
              </Button>
            </div>
          </div>
          <div className="rounded-xl border border-border bg-card p-5">
            <h3 className="text-sm font-semibold mb-3">Auto-Tagged Evidence</h3>
            <div className="space-y-2 text-xs">
              <div className="flex items-center gap-2 p-2 rounded bg-muted/40">
                <Check className="size-3 text-success"/> DLL_Week4_Math.pdf → Math 6 Wk4
              </div>
              <div className="flex items-center gap-2 p-2 rounded bg-muted/40">
                <Check className="size-3 text-success"/> Science_Fair_Photos.zip → Science Fair
              </div>
              <div className="flex items-center gap-2 p-2 rounded bg-muted/40">
                <Check className="size-3 text-success"/> Quiz_Results_Q1.xlsx → Q1 Assessment
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Step 6: Export */}
      {step === 6 && (
        <div className="grid lg:grid-cols-2 gap-6">
          <div className="rounded-xl border border-border bg-card p-6">
            <h2 className="font-semibold">Step 6 · Export & Submit</h2>
            <div className="mt-4 space-y-3">
              <Button className="w-full justify-start gap-3" size="lg"><Download className="size-4"/>Download as PDF</Button>
              <Button variant="outline" className="w-full justify-start gap-3" size="lg"><FileText className="size-4"/>Download as Word</Button>
              <Button variant="outline" className="w-full justify-start gap-3" size="lg"><ShieldCheck className="size-4"/>Submit to Head Teacher</Button>
              <Button variant="outline" className="w-full justify-start gap-3" size="lg"><Upload className="size-4"/>Upload to RPMS Portal</Button>
            </div>
          </div>
          <div className="rounded-xl border border-border bg-card p-6">
            <h2 className="font-semibold">Submission Tracker</h2>
            <ol className="mt-4 space-y-4 text-sm">
              {[
                { label: "Draft Created", time: "Just now", done: true },
                { label: "AI Generated", time: "Just now", done: generated },
                { label: "Evidence Attached", time: `${evidence.length} files`, done: true },
                { label: "Submitted to Head Teacher", time: "Pending", done: false },
                { label: "Approved", time: "Pending", done: false },
              ].map((item) => (
                <li key={item.label} className="flex items-center gap-3">
                  <div className={cn("size-7 rounded-full grid place-items-center shrink-0",
                    item.done ? "bg-success text-success-foreground" : "bg-muted text-muted-foreground")}>
                    {item.done ? <Check className="size-3.5"/> : <span className="text-[10px]">•</span>}
                  </div>
                  <div className="flex-1">
                    <div className="font-medium">{item.label}</div>
                    <div className="text-xs text-muted-foreground">{item.time}</div>
                  </div>
                </li>
              ))}
            </ol>
          </div>
          <div className="lg:col-span-2 flex justify-between pt-2">
            <Button variant="outline" onClick={() => setStep(5)}>← Back</Button>
            <Link to="/">
              <Button>Return to Dashboard</Button>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}