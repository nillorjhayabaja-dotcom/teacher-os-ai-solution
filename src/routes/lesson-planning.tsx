import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { PageHeader } from "@/components/page-header";
import { WorkflowStepper } from "@/components/workflow-stepper";
import { Button } from "@/components/ui/button";
import { mockMELCs } from "@/lib/mock-data";
import {
  Sparkles,
  Download,
  FileText,
  Wand2,
  ChevronRight,
  ChevronDown,
  Check,
  History,
  FileDown,
  Save,
} from "lucide-react";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/lesson-planning")({
  head: () => ({
    meta: [
      { title: "Lesson Planning Pipeline · TeacherOS" },
      {
        name: "description",
        content:
          "Generate DepEd DLLs aligned with MELC. Input → AI Generation → Review → Export → Archive.",
      },
    ],
  }),
  component: LessonPlanningPage,
});

const steps = [
  { id: 1, title: "Input", desc: "Grade, subject, MELC" },
  { id: 2, title: "AI Generation", desc: "Objectives & activities" },
  { id: 3, title: "Review Editor", desc: "Refine & align" },
  { id: 4, title: "Export", desc: "Word, PDF, weekly DLL" },
  { id: 5, title: "Archive", desc: "Version history" },
];

function LessonPlanningPage() {
  const [step, setStep] = useState(1);
  const [subject, setSubject] = useState<keyof typeof mockMELCs>("Mathematics");
  const [grade, setGrade] = useState("6");
  const [quarter, setQuarter] = useState("Quarter 1");
  const [selectedMELC, setSelectedMELC] = useState<string[]>([]);
  const [generating, setGenerating] = useState(false);
  const [generated, setGenerated] = useState(false);

  const melcGroups = mockMELCs[subject] ?? {};
  const melcList: { code: string; text: string }[] =
    (melcGroups as Record<string, { code: string; text: string }[]>)[quarter] ?? [];

  function toggleMelc(code: string) {
    setSelectedMELC((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code],
    );
  }

  function runGeneration() {
    setGenerating(true);
    setTimeout(() => {
      setGenerating(false);
      setGenerated(true);
      setStep(3);
    }, 1600);
  }

  return (
    <div className="px-4 lg:px-8 py-6 lg:py-8 max-w-[1600px] mx-auto space-y-6">
      <PageHeader
        eyebrow="Lesson Planning Pipeline"
        title="Daily Lesson Log (DLL) Builder"
        description="MELC-aligned, DepEd-compliant lesson plans generated in minutes. Five guided steps, autosaved at every stage."
        actions={
          <>
            <Button variant="outline" className="gap-2">
              <History className="size-4" />
              Version history
            </Button>
            <Button className="gap-2">
              <Save className="size-4" />
              Save draft
            </Button>
          </>
        }
      />

      <WorkflowStepper steps={steps} current={step} onSelect={setStep} />

      {step === 1 && (
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 rounded-xl border border-border bg-card p-6 space-y-5">
            <h2 className="font-semibold">Step 1 · Input</h2>
            <div className="grid sm:grid-cols-3 gap-4">
              <Field label="Grade Level">
                <select
                  value={grade}
                  onChange={(e) => setGrade(e.target.value)}
                  className={inputCls}
                >
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
                    <option key={n}>{n}</option>
                  ))}
                </select>
              </Field>
              <Field label="Subject">
                <select
                  value={subject}
                  onChange={(e) => setSubject(e.target.value as keyof typeof mockMELCs)}
                  className={inputCls}
                >
                  {Object.keys(mockMELCs).map((s) => (
                    <option key={s}>{s}</option>
                  ))}
                </select>
              </Field>
              <Field label="Quarter">
                <select
                  value={quarter}
                  onChange={(e) => setQuarter(e.target.value)}
                  className={inputCls}
                >
                  <option>Quarter 1</option>
                  <option>Quarter 2</option>
                  <option>Quarter 3</option>
                  <option>Quarter 4</option>
                </select>
              </Field>
            </div>

            <div>
              <div className="text-xs font-semibold text-muted-foreground mb-2">
                MELC Competencies
              </div>
              <div className="rounded-lg border border-border divide-y divide-border">
                {melcList.length === 0 && (
                  <p className="p-4 text-sm text-muted-foreground">
                    No MELCs seeded for this combination. Try Mathematics · Quarter 1.
                  </p>
                )}
                {melcList.map((m) => {
                  const on = selectedMELC.includes(m.code);
                  return (
                    <button
                      key={m.code}
                      onClick={() => toggleMelc(m.code)}
                      className={cn(
                        "w-full flex items-start gap-3 p-3 text-left hover:bg-muted/40",
                        on && "bg-primary-soft",
                      )}
                    >
                      <div
                        className={cn(
                          "mt-0.5 size-4 rounded border grid place-items-center shrink-0",
                          on ? "bg-primary border-primary text-primary-foreground" : "border-input",
                        )}
                      >
                        {on && <Check className="size-3" />}
                      </div>
                      <div>
                        <div className="text-xs font-mono text-primary">{m.code}</div>
                        <div className="text-sm">{m.text}</div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
            <div className="flex justify-end">
              <Button
                onClick={() => setStep(2)}
                disabled={selectedMELC.length === 0}
                className="gap-2"
              >
                Continue <ChevronRight className="size-4" />
              </Button>
            </div>
          </div>

          <AsideTips />
        </div>
      )}

      {step === 2 && (
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 rounded-xl border border-border bg-card p-6 space-y-4">
            <h2 className="font-semibold">Step 2 · AI Generation</h2>
            <p className="text-sm text-muted-foreground">
              The Lesson Planning Agent will draft Objectives, Procedure, Assessment,
              Differentiation, and Reflection sections aligned to your selected MELCs.
            </p>

            <div className="rounded-lg bg-muted/40 p-4 text-sm">
              <div className="font-medium">Context</div>
              <div className="mt-1 text-muted-foreground">
                Grade {grade} · {subject} · {quarter} · {selectedMELC.length} MELC(s)
              </div>
            </div>

            <Button
              onClick={runGeneration}
              disabled={generating}
              className="gap-2 w-full sm:w-auto"
            >
              {generating ? (
                <>
                  <Sparkles className="size-4 animate-pulse" />
                  Generating…
                </>
              ) : (
                <>
                  <Wand2 className="size-4" />
                  Run AI Generation
                </>
              )}
            </Button>

            {generating && (
              <ul className="text-xs text-muted-foreground space-y-1.5 pt-2">
                <li className="flex items-center gap-2">
                  <Check className="size-3 text-success" /> Parsing MELC codes…
                </li>
                <li className="flex items-center gap-2">
                  <Check className="size-3 text-success" /> Matching curriculum guide…
                </li>
                <li className="flex items-center gap-2">
                  <Sparkles className="size-3 text-primary animate-pulse" /> Drafting procedure…
                </li>
              </ul>
            )}
          </div>
          <AsideTips />
        </div>
      )}

      {step === 3 && (
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <div className="rounded-xl border border-border bg-card">
              <div className="flex items-center justify-between p-4 border-b border-border">
                <h2 className="font-semibold">Step 3 · Review Editor</h2>
                <div className="flex items-center gap-2">
                  <Button size="sm" variant="outline" className="gap-1.5">
                    <Wand2 className="size-3.5" />
                    Improve
                  </Button>
                  <span className="text-[11px] font-medium px-2 py-1 rounded bg-success/10 text-success flex items-center gap-1">
                    <Check className="size-3" />
                    MELC-aligned
                  </span>
                </div>
              </div>
              <div className="p-6 space-y-5 text-sm">
                <DLLSection
                  title="I. Objectives"
                  body="At the end of the lesson, learners will be able to: (a) add and subtract simple fractions with and without regrouping; (b) solve routine word problems involving fractions; (c) appreciate the use of fractions in daily Filipino life."
                />
                <DLLSection
                  title="II. Content"
                  body={`Subject Matter: ${subject} – ${quarter}\nMELCs: ${selectedMELC.join(", ")}`}
                />
                <DLLSection
                  title="III. Learning Resources"
                  body="K-12 Curriculum Guide, DepEd LR Portal, Realia (sliced bibingka), printed worksheets."
                />
                <DLLSection
                  title="IV. Procedure"
                  body="A. Reviewing previous lesson (5 min)\nB. Establishing purpose (5 min) — Story of pansit serving\nC. Presenting examples (10 min)\nD. Guided practice (15 min)\nE. Independent practice (10 min)\nF. Generalization (5 min)"
                />
                <DLLSection
                  title="V. Assessment"
                  body="10-item formative quiz; rubric-based group output (4 pts)."
                />
                <DLLSection
                  title="VI. Reflection"
                  body="No. of learners who earned 80% — ___\nNo. of learners who require additional activities — ___"
                />
              </div>
            </div>
            <div className="flex justify-between">
              <Button variant="outline" onClick={() => setStep(2)}>
                Back
              </Button>
              <Button onClick={() => setStep(4)} className="gap-2">
                Continue to Export <ChevronRight className="size-4" />
              </Button>
            </div>
          </div>
          <AsideTips />
        </div>
      )}

      {step === 4 && (
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 rounded-xl border border-border bg-card p-6 space-y-4">
            <h2 className="font-semibold">Step 4 · Export</h2>
            <div className="grid sm:grid-cols-3 gap-3">
              <ExportCard icon={FileText} label="Word (.docx)" />
              <ExportCard icon={FileDown} label="PDF (printable)" />
              <ExportCard icon={Download} label="Weekly DLL bundle" />
            </div>
            <div className="flex justify-between pt-2">
              <Button variant="outline" onClick={() => setStep(3)}>
                Back
              </Button>
              <Button onClick={() => setStep(5)} className="gap-2">
                Archive lesson <ChevronRight className="size-4" />
              </Button>
            </div>
          </div>
          <AsideTips />
        </div>
      )}

      {step === 5 && (
        <div className="rounded-xl border border-border bg-card p-6">
          <h2 className="font-semibold">Step 5 · Archive</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Saved to your DLL library. Reuse or clone for next year.
          </p>
          <div className="mt-4 divide-y divide-border border border-border rounded-lg">
            {[
              { v: "v3 · Current", date: "Today, 10:14 AM", note: "AI-improved Procedure section" },
              { v: "v2", date: "Today, 9:52 AM", note: "Manual edits to Assessment" },
              { v: "v1", date: "Today, 9:40 AM", note: "Initial AI draft" },
            ].map((v) => (
              <div key={v.v} className="flex items-center gap-4 p-3">
                <History className="size-4 text-muted-foreground" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium">{v.v}</div>
                  <div className="text-xs text-muted-foreground">
                    {v.date} · {v.note}
                  </div>
                </div>
                <Button size="sm" variant="outline">
                  Restore
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}

      {generated && step !== 5 && (
        <div className="fixed bottom-6 right-6 rounded-lg border border-success/30 bg-card p-3 shadow-elegant flex items-center gap-2 text-sm">
          <Check className="size-4 text-success" />
          Lesson autosaved
        </div>
      )}
    </div>
  );
}

const inputCls =
  "w-full h-9 px-3 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring/30";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <div className="text-xs font-medium text-muted-foreground mb-1.5">{label}</div>
      {children}
    </label>
  );
}

function DLLSection({ title, body }: { title: string; body: string }) {
  const [open, setOpen] = useState(true);
  return (
    <div>
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between text-left"
      >
        <h3 className="font-semibold text-foreground">{title}</h3>
        <ChevronDown className={cn("size-4 transition-transform", !open && "-rotate-90")} />
      </button>
      {open && (
        <pre className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground font-sans leading-relaxed">
          {body}
        </pre>
      )}
    </div>
  );
}

function ExportCard({ icon: Icon, label }: { icon: typeof FileText; label: string }) {
  return (
    <button className="rounded-lg border border-border p-4 text-left hover:border-primary hover:shadow-elegant transition-all">
      <Icon className="size-5 text-primary" />
      <div className="mt-3 text-sm font-medium">{label}</div>
      <div className="text-xs text-muted-foreground">Download instantly</div>
    </button>
  );
}

function AsideTips() {
  return (
    <div className="rounded-xl border border-primary/20 bg-primary-soft/40 p-5">
      <div className="flex items-center gap-2">
        <Sparkles className="size-4 text-primary" />
        <span className="text-sm font-semibold">AI Tips</span>
      </div>
      <ul className="mt-3 space-y-2 text-xs text-muted-foreground">
        <li>• Selecting 2–3 MELCs gives the richest weekly DLL.</li>
        <li>• You can edit any section after generation — autosave is on.</li>
        <li>• Use “Improve” to ask for differentiation strategies for SPED learners.</li>
      </ul>
    </div>
  );
}
