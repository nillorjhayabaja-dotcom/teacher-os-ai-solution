import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { PageHeader } from "@/components/page-header";
import { WorkflowStepper } from "@/components/workflow-stepper";
import { Button } from "@/components/ui/button";
import { mockStudents, mockGradeEntries, type GradeEntry } from "@/lib/mock-data";
import {
  Calculator, Upload, Sparkles, Check, ChevronRight, AlertCircle,
  TrendingUp, TrendingDown, ShieldCheck, Download, FileText, Wand2, Save,
} from "lucide-react";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/grading")({
  head: () => ({
    meta: [
      { title: "Grading Cycle · TeacherOS" },
      { name: "description", content: "DepEd-weighted quarter grading with AI anomaly detection and analytics." },
    ],
  }),
  component: GradingPage,
});

const steps = [
  { id: 1, title: "Data Input", desc: "Raw scores grid" },
  { id: 2, title: "Weights", desc: "DepEd configuration" },
  { id: 3, title: "AI Compute", desc: "Auto-calc & detect" },
  { id: 4, title: "Analytics", desc: "Charts & rankings" },
  { id: 5, title: "Approval", desc: "Draft → Review → Final" },
  { id: 6, title: "Export", desc: "SF9 & grade sheets" },
];

function GradingPage() {
  const [step, setStep] = useState(1);
  const [entries, setEntries] = useState<GradeEntry[]>(mockGradeEntries);
  const [weights, setWeights] = useState({ ww: 30, pt: 50, exam: 20 });
  const [computed, setComputed] = useState(false);
  const [approvalStatus, setApprovalStatus] = useState<"draft" | "review" | "final">("draft");
  const [computing, setComputing] = useState(false);
  const [anomalies, setAnomalies] = useState<{ studentId: string; field: string; issue: string; fix: string }[]>([]);

  const studentMap = Object.fromEntries(mockStudents.map(s => [s.id, s]));

  function runComputation() {
    setComputing(true);
    setAnomalies([]);
    setTimeout(() => {
      const detected: typeof anomalies = [];
      const updated = entries.map(e => {
        if (e.pt1 > 30) detected.push({ studentId: e.studentId, field: "PT1", issue: "PT score exceeds max 30", fix: "Cap at 30" });
        if (e.ww1 === 0) detected.push({ studentId: e.studentId, field: "WW1", issue: "Missing Written Work 1 score", fix: "Flag for review" });
        const ww = (e.ww1 / 20) * 100;
        const pt = (Math.min(e.pt1, 30) / 30) * 100;
        const ex = (e.exam / 50) * 100;
        const final = ww * (weights.ww / 100) + pt * (weights.pt / 100) + ex * (weights.exam / 100);
        return { ...e, final: Math.round(final * 10) / 10 };
      });
      setEntries(updated);
      setComputed(true);
      setAnomalies(detected);
      setComputing(false);
      setStep(4);
    }, 1200);
  }

  const updateEntry = (studentId: string, field: keyof GradeEntry, value: number) => {
    setEntries(prev => prev.map(e => e.studentId === studentId ? { ...e, [field]: value } : e));
  };

  return (
    <div className="px-4 lg:px-8 py-6 lg:py-8 max-w-[1600px] mx-auto space-y-6">
      <PageHeader
        eyebrow="Grading Cycle Engine"
        title="DepEd-Weighted Quarter Grading"
        description="Grade 6 · Mathematics · Sampaguita · Quarter 1 — From raw scores to finalized SF9, with AI error detection and at-risk analytics."
        actions={
          <>
            <Button variant="outline" className="gap-2"><Upload className="size-4"/>Import Excel</Button>
            <Button className="gap-2"><Save className="size-4"/>Save draft</Button>
          </>
        }
      />

      <WorkflowStepper steps={steps} current={step} onSelect={setStep} />

      {/* Step 1: Data Input - Spreadsheet */}
      {step === 1 && (
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          <div className="flex items-center justify-between p-4 border-b border-border bg-muted/20">
            <h2 className="font-semibold">Step 1 · Raw Scores Input</h2>
            <div className="text-xs text-muted-foreground">40 students · 6 columns</div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-muted/40 border-b border-border">
                  <th className="sticky left-0 bg-muted/40 text-left p-3 text-xs font-semibold text-muted-foreground uppercase min-w-[200px]">Student</th>
                  <th className="p-3 text-xs font-semibold text-muted-foreground uppercase text-center min-w-[80px]">WW1<br/><span className="font-normal text-[10px]">/20</span></th>
                  <th className="p-3 text-xs font-semibold text-muted-foreground uppercase text-center min-w-[80px]">WW2<br/><span className="font-normal text-[10px]">/20</span></th>
                  <th className="p-3 text-xs font-semibold text-muted-foreground uppercase text-center min-w-[80px]">PT1<br/><span className="font-normal text-[10px]">/30</span></th>
                  <th className="p-3 text-xs font-semibold text-muted-foreground uppercase text-center min-w-[80px]">PT2<br/><span className="font-normal text-[10px]">/30</span></th>
                  <th className="p-3 text-xs font-semibold text-muted-foreground uppercase text-center min-w-[80px]">Exam<br/><span className="font-normal text-[10px]">/50</span></th>
                  <th className="p-3 text-xs font-semibold text-muted-foreground uppercase text-center min-w-[90px] bg-primary/5">Final</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((e, i) => {
                  const s = studentMap[e.studentId];
                  if (!s) return null;
                  return (
                    <tr key={e.studentId} className={cn("border-b border-border hover:bg-muted/20", i % 2 === 0 && "bg-muted/10")}>
                      <td className="sticky left-0 bg-inherit p-3 font-medium text-sm">{s.name}</td>
                      <td className={cn("p-2 text-center", e.ww1 === 0 && "bg-destructive/10")}>
                        <EditableCell value={e.ww1} onChange={(v) => updateEntry(e.studentId, "ww1", v)} />
                      </td>
                      <td className="p-2 text-center">
                        <EditableCell value={e.ww2} onChange={(v) => updateEntry(e.studentId, "ww2", v)} />
                      </td>
                      <td className={cn("p-2 text-center", e.pt1 > 30 && "bg-destructive/10")}>
                        <EditableCell value={e.pt1} onChange={(v) => updateEntry(e.studentId, "pt1", v)} />
                        {e.pt1 > 30 && <AlertCircle className="size-3 text-destructive mx-auto mt-0.5"/>}
                      </td>
                      <td className="p-2 text-center">
                        <EditableCell value={e.pt2} onChange={(v) => updateEntry(e.studentId, "pt2", v)} />
                      </td>
                      <td className="p-2 text-center">
                        <EditableCell value={e.exam} onChange={(v) => updateEntry(e.studentId, "exam", v)} />
                      </td>
                      <td className="p-3 text-center font-semibold text-base">
                        {e.final ? (
                          <span className={cn(e.final < 75 && "text-destructive")}>
                            {e.final}
                            {e.final < 75 && <TrendingDown className="size-3 inline ml-1 text-destructive"/>}
                          </span>
                        ) : "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="flex justify-between items-center p-4 border-t border-border bg-muted/20">
            <div className="text-xs text-muted-foreground">🟡 Cells in red indicate potential data issues</div>
            <Button onClick={() => setStep(2)} className="gap-2">Configure Weights <ChevronRight className="size-4"/></Button>
          </div>
        </div>
      )}

      {/* Step 2: Weight Configuration */}
      {step === 2 && (
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 rounded-xl border border-border bg-card p-6 space-y-6">
            <h2 className="font-semibold">Step 2 · DepEd Weight Configuration</h2>
            <p className="text-sm text-muted-foreground">Configure the weight percentages per component as prescribed by DepEd Order 8, s.2015.</p>

            <div className="space-y-4 max-w-md">
              <WeightSlider label="Written Works (WW)" value={weights.ww} onChange={(v) => setWeights(w => ({ ...w, ww: v }))} max={100} />
              <WeightSlider label="Performance Tasks (PT)" value={weights.pt} onChange={(v) => setWeights(w => ({ ...w, pt: v }))} max={100} />
              <WeightSlider label="Quarterly Exam (QE)" value={weights.exam} onChange={(v) => setWeights(w => ({ ...w, exam: v }))} max={100} />
              <div className="pt-4 border-t border-border flex items-center justify-between">
                <span className="text-sm font-semibold">Total</span>
                <span className={cn("text-lg font-bold", weights.ww + weights.pt + weights.exam === 100 ? "text-success" : "text-destructive")}>
                  {weights.ww + weights.pt + weights.exam}%
                </span>
              </div>
              {weights.ww + weights.pt + weights.exam !== 100 && (
                <p className="text-xs text-destructive">Weights must sum to 100%</p>
              )}
            </div>

            <div className="flex justify-between pt-2">
              <Button variant="outline" onClick={() => setStep(1)}>← Back to Input</Button>
              <Button onClick={() => setStep(3)} className="gap-2" disabled={weights.ww + weights.pt + weights.exam !== 100}>
                Run AI Computation <ChevronRight className="size-4"/>
              </Button>
            </div>
          </div>
          <div className="rounded-xl border border-primary/20 bg-primary-soft/40 p-5">
            <Sparkles className="size-4 text-primary"/>
            <h3 className="text-sm font-semibold mt-2">DepEd Presets</h3>
            <ul className="mt-3 space-y-2 text-xs text-muted-foreground">
              <li>
                <button onClick={() => setWeights({ ww: 30, pt: 50, exam: 20 })} className="text-primary hover:underline">Math, Science, English</button>
                <br/>WW 30% · PT 50% · Exam 20%
              </li>
              <li>
                <button onClick={() => setWeights({ ww: 40, pt: 40, exam: 20 })} className="text-primary hover:underline">AP, ESP, TLE</button>
                <br/>WW 40% · PT 40% · Exam 20%
              </li>
              <li>
                <button onClick={() => setWeights({ ww: 20, pt: 60, exam: 20 })} className="text-primary hover:underline">MAPEH</button>
                <br/>WW 20% · PT 60% · Exam 20%
              </li>
            </ul>
          </div>
        </div>
      )}

      {/* Step 3: AI Computation */}
      {step === 3 && (
        <div className="rounded-xl border border-border bg-card p-6 space-y-5">
          <h2 className="font-semibold">Step 3 · AI Grade Computation</h2>
          <p className="text-sm text-muted-foreground">The Grade Computation Agent will apply the configured weights, detect anomalies, and compute final grades.</p>

          <div className="rounded-lg bg-muted/40 p-4 text-sm space-y-1">
            <div className="font-medium">Computation Context</div>
            <div className="text-muted-foreground">Grade 6 · Math · Sampaguita · Q1 · {entries.length} students</div>
            <div className="text-muted-foreground">Weights: WW {weights.ww}% · PT {weights.pt}% · Exam {weights.exam}%</div>
          </div>

          <Button onClick={runComputation} disabled={computing} className="gap-2" size="lg">
            {computing ? <><Sparkles className="size-4 animate-pulse"/>Computing {entries.length} grades…</> : <><Wand2 className="size-4"/>Run AI Computation</>}
          </Button>

          {computing && (
            <div>
              <div className="h-2 rounded-full bg-muted overflow-hidden">
                <div className="h-full bg-gradient-primary animate-pulse" style={{ width: "60%" }}/>
              </div>
              <ul className="mt-3 text-xs text-muted-foreground space-y-1">
                <li className="flex items-center gap-2"><Check className="size-3 text-success"/> Validating score ranges…</li>
                <li className="flex items-center gap-2"><Sparkles className="size-3 text-primary animate-pulse"/> Applying weights…</li>
                <li className="flex items-center gap-2 text-muted-foreground/50"> Detecting anomalies…</li>
              </ul>
            </div>
          )}

          {anomalies.length > 0 && (
            <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4">
              <h3 className="text-sm font-semibold text-destructive flex items-center gap-2">
                <AlertCircle className="size-4"/> {anomalies.length} Anomalies Detected
              </h3>
              {anomalies.map((a, i) => (
                <div key={i} className="mt-2 flex items-start gap-2 text-sm">
                  <span className="text-destructive">⚠</span>
                  <div className="flex-1">
                    <span className="font-medium">{studentMap[a.studentId]?.name}</span> — {a.issue}
                    <div className="mt-1 flex gap-2">
                      <Button size="sm" className="gap-1"><Check className="size-3"/>{a.fix}</Button>
                      <Button size="sm" variant="outline">Ignore</Button>
                      <Button size="sm" variant="outline">Edit</Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="flex justify-between pt-2">
            <Button variant="outline" onClick={() => setStep(2)}>← Back</Button>
            <Button onClick={() => setStep(4)} disabled={!computed} className="gap-2">View Analytics <ChevronRight className="size-4"/></Button>
          </div>
        </div>
      )}

      {/* Step 4: Analytics */}
      {step === 4 && (
        <div className="space-y-6">
          <div className="grid lg:grid-cols-3 gap-6">
            <div className="rounded-xl border border-border bg-card p-5">
              <div className="text-xs text-muted-foreground font-semibold">Class Average</div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-3xl font-display font-semibold">
                  {Math.round(entries.reduce((s, e) => s + (e.final || 0), 0) / entries.length)}
                </span>
                <span className="text-xs text-success flex items-center gap-0.5"><TrendingUp className="size-3"/>+2.1</span>
              </div>
            </div>
            <div className="rounded-xl border border-border bg-card p-5">
              <div className="text-xs text-muted-foreground font-semibold">Passing Rate</div>
              <div className="mt-2 text-3xl font-display font-semibold text-success">
                {Math.round(entries.filter(e => (e.final || 0) >= 75).length / entries.length * 100)}%
              </div>
            </div>
            <div className="rounded-xl border border-border bg-card p-5">
              <div className="text-xs text-muted-foreground font-semibold">At-Risk Students</div>
              <div className="mt-2 text-3xl font-display font-semibold text-destructive">
                {entries.filter(e => (e.final || 0) < 75).length}
              </div>
            </div>
          </div>

          <div className="grid lg:grid-cols-2 gap-6">
            <div className="rounded-xl border border-border bg-card p-5">
              <h3 className="text-sm font-semibold mb-3">At-Risk Students (Grade {'<'} 75)</h3>
              <div className="divide-y divide-border">
                {entries.filter(e => (e.final || 0) < 75).map(e => {
                  const s = studentMap[e.studentId];
                  return s ? (
                    <div key={e.studentId} className="flex items-center gap-3 py-2.5">
                      <div className="size-8 rounded-full bg-destructive/10 text-destructive grid place-items-center text-xs font-semibold">
                        {s.name.charAt(0)}
                      </div>
                      <div className="flex-1">
                        <div className="text-sm font-medium">{s.name}</div>
                        <div className="text-xs text-muted-foreground">Att {s.attendance}%</div>
                      </div>
                      <div className="text-lg font-bold text-destructive">{e.final}</div>
                    </div>
                  ) : null;
                })}
              </div>
            </div>

            <div className="rounded-xl border border-border bg-card p-5">
              <h3 className="text-sm font-semibold mb-3">Top Performers</h3>
              <div className="divide-y divide-border">
                {[...entries].sort((a, b) => (b.final || 0) - (a.final || 0)).slice(0, 5).map((e, i) => {
                  const s = studentMap[e.studentId];
                  return s ? (
                    <div key={e.studentId} className="flex items-center gap-3 py-2.5">
                      <span className="text-xs font-bold text-muted-foreground w-5">#{i + 1}</span>
                      <div className="flex-1">
                        <div className="text-sm font-medium">{s.name}</div>
                        <div className="text-xs text-muted-foreground">{s.section}</div>
                      </div>
                      <div className="text-lg font-bold text-success">{e.final}</div>
                    </div>
                  ) : null;
                })}
              </div>
            </div>
          </div>

          <div className="flex justify-between">
            <Button variant="outline" onClick={() => setStep(3)}>← Back</Button>
            <Button onClick={() => setStep(5)} className="gap-2">Continue to Approval <ChevronRight className="size-4"/></Button>
          </div>
        </div>
      )}

      {/* Step 5: Approval Workflow */}
      {step === 5 && (
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 rounded-xl border border-border bg-card p-6 space-y-6">
            <h2 className="font-semibold">Step 5 · Approval Workflow</h2>

            <div className="flex gap-2">
              {(["draft", "review", "final"] as const).map(status => (
                <button key={status} onClick={() => setApprovalStatus(status)}
                  className={cn("flex-1 rounded-lg border py-3 text-center text-sm font-medium transition-all",
                    approvalStatus === status ? "border-primary bg-primary-soft text-primary" : "border-border bg-card text-muted-foreground hover:border-input")}>
                  {status === "draft" && "📝 Draft"}
                  {status === "review" && "🔍 Review"}
                  {status === "final" && "✅ Final"}
                </button>
              ))}
            </div>

            <div className="rounded-lg bg-muted/40 p-4 space-y-3 text-sm">
              <div className="flex justify-between"><span className="text-muted-foreground">Students computed</span><span className="font-medium">{entries.length}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Manual overrides</span><span className="font-medium">{anomalies.length}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">At-risk flagged</span><span className="font-medium text-destructive">{entries.filter(e => (e.final || 0) < 75).length}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Status</span><span className="font-medium capitalize">{approvalStatus}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Last edited</span><span className="font-medium">Today, 10:45 AM</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Reviewer</span><span className="font-medium">Head Teacher (assigned)</span></div>
            </div>

            <div className="flex gap-3">
              <Button variant="outline" className="flex-1">✏️ Continue Editing</Button>
              <Button className="flex-1" disabled={approvalStatus === "final"}>
                {approvalStatus === "draft" ? "📤 Submit for Review" : approvalStatus === "review" ? "✅ Finalize" : "✓ Already Finalized"}
              </Button>
            </div>
          </div>
          <div className="rounded-xl border border-primary/20 bg-primary-soft/40 p-5">
            <div className="flex items-center gap-2">
              <ShieldCheck className="size-4 text-primary"/>
              <span className="text-sm font-semibold">Compliance Check</span>
            </div>
            <ul className="mt-3 space-y-2 text-xs text-muted-foreground">
              <li className="flex items-center gap-2"><Check className="size-3 text-success"/> DO 8 s.2015 weights applied</li>
              <li className="flex items-center gap-2"><Check className="size-3 text-success"/> All 40 students computed</li>
              <li className="flex items-center gap-2 text-warning-foreground"><AlertCircle className="size-3"/> {anomalies.length} anomalies overridden</li>
            </ul>
          </div>
        </div>
      )}

      {/* Step 6: Export */}
      {step === 6 && (
        <div className="grid lg:grid-cols-2 gap-6">
          <div className="rounded-xl border border-border bg-card p-6">
            <h2 className="font-semibold">Step 6 · Export</h2>
            <div className="mt-4 space-y-3">
              <Button className="w-full justify-start gap-3" size="lg"><Download className="size-4"/>Download Grade Sheet (Excel)</Button>
              <Button variant="outline" className="w-full justify-start gap-3" size="lg"><FileText className="size-4"/>Generate SF9 Report Cards</Button>
              <Button variant="outline" className="w-full justify-start gap-3" size="lg"><Download className="size-4"/>Download Summary Report (PDF)</Button>
              <Button variant="outline" className="w-full justify-start gap-3" size="lg"><ShieldCheck className="size-4"/>Submit to Principal for Approval</Button>
            </div>
          </div>
          <div className="rounded-xl border border-border bg-card p-6">
            <h2 className="font-semibold">Submission Tracker</h2>
            <ol className="mt-4 space-y-4 text-sm">
              {[
                { label: "Draft Created", time: "Today, 10:15 AM", done: true },
                { label: "AI Computation Complete", time: "Today, 10:16 AM", done: computed },
                { label: "Submitted for Review", time: "Pending", done: approvalStatus !== "draft" },
                { label: "Approved by Head Teacher", time: "Pending", done: false },
                { label: "Finalized & Exported", time: "Pending", done: false },
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

function EditableCell({ value, onChange }: { value: number; onChange: (v: number) => void }) {
  return (
    <input
      type="number"
      value={value}
      onChange={(e) => onChange(Math.max(0, parseInt(e.target.value) || 0))}
      className="w-16 text-center bg-transparent border-b border-transparent hover:border-input focus:border-primary focus:outline-none text-sm [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
    />
  );
}

function WeightSlider({ label, value, onChange, max }: { label: string; value: number; onChange: (v: number) => void; max: number }) {
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span>{label}</span>
        <span className="font-semibold text-primary">{value}%</span>
      </div>
      <input type="range" min={0} max={max} value={value} onChange={(e) => onChange(parseInt(e.target.value))}
        className="w-full h-2 rounded-full appearance-none bg-muted [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:size-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary [&::-webkit-slider-thumb]:cursor-pointer" />
      <div className="flex justify-between text-[10px] text-muted-foreground mt-0.5">
        <span>0%</span>
        <span>{max}%</span>
      </div>
    </div>
  );
}