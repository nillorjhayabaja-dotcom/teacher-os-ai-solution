import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { PageHeader } from "@/components/page-header";
import { WorkflowStepper } from "@/components/workflow-stepper";
import { Button } from "@/components/ui/button";
import { mockStudents } from "@/lib/mock-data";
import {
  Upload, Database, Pencil, ShieldCheck, Wand2, AlertCircle,
  Check, Download, Send, Search, ChevronRight, FileText,
} from "lucide-react";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/forms")({
  head: () => ({
    meta: [
      { title: "School Forms Pipeline · TeacherOS" },
      { name: "description", content: "SF1–SF10 with AI auto-fill, validation, and submission tracking. DepEd-compliant layouts." },
    ],
  }),
  component: FormsPage,
});

const steps = [
  { id: 1, title: "Data Source", desc: "Excel, LIS, or manual" },
  { id: 2, title: "Validation", desc: "Detect missing/mismatched" },
  { id: 3, title: "AI Auto-Fill", desc: "Forms Agent fills fields" },
  { id: 4, title: "Form Preview", desc: "DepEd-exact layout" },
  { id: 5, title: "Error Correction", desc: "AI-suggested fixes" },
  { id: 6, title: "Export & Track", desc: "PDF + submission log" },
];

const formTypes = [
  { code: "SF1", name: "School Register", status: "ready" },
  { code: "SF2", name: "Daily Attendance", status: "in-progress", progress: 92 },
  { code: "SF5", name: "Promotion Report", status: "draft" },
  { code: "SF9", name: "Learner Progress Report", status: "ready" },
  { code: "SF10", name: "Learner Permanent Record", status: "draft" },
];

function FormsPage() {
  const [step, setStep] = useState(1);
  const [activeForm, setActiveForm] = useState("SF2");
  const [autoFilled, setAutoFilled] = useState(false);
  const [filling, setFilling] = useState(false);

  function runAutoFill() {
    setFilling(true);
    setTimeout(() => { setFilling(false); setAutoFilled(true); setStep(4); }, 1500);
  }

  return (
    <div className="px-4 lg:px-8 py-6 lg:py-8 max-w-[1600px] mx-auto space-y-6">
      <PageHeader
        eyebrow="Highest Priority Module"
        title="School Forms Pipeline"
        description="SF1, SF2, SF5, SF9, and SF10 with AI auto-fill, validation, and submission tracking — DepEd-compliant end-to-end."
        actions={
          <>
            <Button variant="outline" className="gap-2"><Upload className="size-4"/>Import LIS</Button>
            <Button className="gap-2"><Wand2 className="size-4"/>New batch</Button>
          </>
        }
      />

      {/* Form selector */}
      <div className="flex gap-2 overflow-x-auto pb-1">
        {formTypes.map(f => (
          <button key={f.code} onClick={()=>setActiveForm(f.code)}
            className={cn(
              "shrink-0 rounded-lg border px-4 py-3 text-left min-w-[180px] transition-all",
              activeForm === f.code ? "border-primary bg-primary-soft shadow-elegant" : "border-border bg-card hover:border-input"
            )}>
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs font-semibold text-primary">{f.code}</span>
              <span className={cn(
                "text-[10px] px-1.5 py-0.5 rounded font-medium",
                f.status === "ready" && "bg-success/10 text-success",
                f.status === "in-progress" && "bg-warning/15 text-warning-foreground",
                f.status === "draft" && "bg-muted text-muted-foreground",
              )}>{f.status}</span>
            </div>
            <div className="mt-1 text-sm font-medium">{f.name}</div>
            {f.progress && <div className="mt-2 h-1 rounded-full bg-muted overflow-hidden">
              <div className="h-full bg-primary" style={{ width: `${f.progress}%` }}/>
            </div>}
          </button>
        ))}
      </div>

      <WorkflowStepper steps={steps} current={step} onSelect={setStep} />

      {step === 1 && (
        <div className="rounded-xl border border-border bg-card p-6">
          <h2 className="font-semibold mb-1">Step 1 · Select Data Source for {activeForm}</h2>
          <p className="text-sm text-muted-foreground mb-5">Choose how to pull learner data into the form.</p>
          <div className="grid sm:grid-cols-3 gap-3">
            <SourceCard icon={Upload} title="Excel Upload" desc="LIS-formatted .xlsx" onClick={()=>setStep(2)} active />
            <SourceCard icon={Database} title="LIS Import" desc="Direct from Learner Info System" onClick={()=>setStep(2)} />
            <SourceCard icon={Pencil} title="Manual Entry" desc="Type student data" onClick={()=>setStep(2)} />
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="rounded-xl border border-border bg-card p-6">
          <h2 className="font-semibold">Step 2 · Validation Engine</h2>
          <p className="text-sm text-muted-foreground mt-1">AI scans the uploaded data and flags inconsistencies.</p>

          <div className="mt-5 grid sm:grid-cols-3 gap-3">
            <Stat label="Records found" value="40" tone="primary"/>
            <Stat label="Warnings" value="3" tone="warning" />
            <Stat label="Errors" value="1" tone="destructive" />
          </div>

          <ul className="mt-5 divide-y divide-border border border-border rounded-lg">
            <ValidationRow tone="error" title="LRN mismatch: J. Santos" desc="LRN length is 11 digits (should be 12)."/>
            <ValidationRow tone="warn" title="Missing father's name: A. Reyes" desc="SF1 requires both parent names." />
            <ValidationRow tone="warn" title="Attendance mismatch: M. Cruz" desc="Manual register shows 18, LIS shows 17 days present." />
            <ValidationRow tone="warn" title="Grade gap: K. Bautista" desc="Q1 grade missing in MAPEH." />
          </ul>

          <div className="mt-5 flex justify-end">
            <Button onClick={()=>setStep(3)} className="gap-2">Proceed with warnings <ChevronRight className="size-4"/></Button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="rounded-xl border border-border bg-card p-6">
          <h2 className="font-semibold">Step 3 · AI Auto-Fill Engine</h2>
          <p className="text-sm text-muted-foreground mt-1">The Forms Agent fills every required field automatically.</p>
          <div className="mt-5 rounded-lg bg-muted/40 p-4 text-sm">
            <div className="font-medium">Form: {activeForm} · Daily Attendance Report</div>
            <div className="text-muted-foreground mt-1">Section: Sampaguita · 40 learners · Month: September 2026</div>
          </div>
          <Button onClick={runAutoFill} disabled={filling} className="mt-5 gap-2">
            {filling ? <><Wand2 className="size-4 animate-pulse"/>Filling 1,240 fields…</> : <><Wand2 className="size-4"/>Run AI Auto-Fill</>}
          </Button>
          {filling && (
            <div className="mt-4 h-2 rounded-full bg-muted overflow-hidden">
              <div className="h-full bg-gradient-primary animate-pulse" style={{ width: "65%" }}/>
            </div>
          )}
        </div>
      )}

      {step === 4 && (
        <div className="space-y-4">
          <div className="rounded-xl border border-border bg-card overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-border bg-muted/40">
              <div className="flex items-center gap-2 text-sm">
                <FileText className="size-4 text-primary"/>
                <span className="font-semibold">{activeForm} — Preview</span>
                <span className="text-muted-foreground">· DepEd Form Layout</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="absolute left-2 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground"/>
                  <input placeholder="Find learner…" className="pl-7 h-8 text-xs rounded border border-input bg-background w-44"/>
                </div>
              </div>
            </div>
            <div className="p-6 overflow-x-auto">
              <SFPreview />
            </div>
          </div>
          <div className="flex justify-between">
            <Button variant="outline" onClick={()=>setStep(3)}>Back</Button>
            <Button onClick={()=>setStep(5)} className="gap-2">Review errors <ChevronRight className="size-4"/></Button>
          </div>
        </div>
      )}

      {step === 5 && (
        <div className="rounded-xl border border-border bg-card p-6">
          <h2 className="font-semibold">Step 5 · Error Correction Mode</h2>
          <p className="text-sm text-muted-foreground mt-1">Errors highlighted in red. Accept AI suggestions or fix manually.</p>
          <div className="mt-5 divide-y divide-border border border-border rounded-lg">
            <FixRow problem="LRN: 137020025488 (11 digits)" suggestion="137020025488? Suggest verifying with LIS or appending check digit." />
            <FixRow problem="Father's name (blank) — A. Reyes" suggestion="Auto-fill from registration record: 'Roberto Reyes'." />
            <FixRow problem="Sept attendance: 17 vs 18" suggestion="Use register count: 18 (manual takes precedence per DO 8 s.2015)." />
          </div>
          <div className="mt-5 flex justify-between">
            <Button variant="outline" onClick={()=>setStep(4)}>Back to preview</Button>
            <Button onClick={()=>setStep(6)} className="gap-2"><ShieldCheck className="size-4"/>Mark as validated</Button>
          </div>
        </div>
      )}

      {step === 6 && (
        <div className="grid lg:grid-cols-2 gap-6">
          <div className="rounded-xl border border-border bg-card p-6">
            <h2 className="font-semibold">Export</h2>
            <div className="mt-4 space-y-2">
              <Button className="w-full justify-start gap-2"><Download className="size-4"/>Download as PDF</Button>
              <Button variant="outline" className="w-full justify-start gap-2"><Download className="size-4"/>Download as Excel</Button>
              <Button variant="outline" className="w-full justify-start gap-2"><Send className="size-4"/>Submit to Principal</Button>
            </div>
          </div>
          <div className="rounded-xl border border-border bg-card p-6">
            <h2 className="font-semibold">Submission Tracker</h2>
            <ol className="mt-4 space-y-3 text-sm">
              <Track ok title="Validated" time="Just now" />
              <Track ok title="Sent to Principal" time="Pending" pending />
              <Track title="Approved by Principal" pending />
              <Track title="Submitted to Division Office" pending />
            </ol>
          </div>
        </div>
      )}

      {autoFilled && (
        <div className="fixed bottom-6 right-6 rounded-lg border border-success/30 bg-card p-3 shadow-elegant flex items-center gap-2 text-sm">
          <Check className="size-4 text-success"/>Form autosaved
        </div>
      )}
    </div>
  );
}

function SourceCard({ icon: Icon, title, desc, onClick, active }: { icon: typeof Upload; title: string; desc: string; onClick: ()=>void; active?: boolean }) {
  return (
    <button onClick={onClick}
      className={cn("rounded-lg border p-5 text-left transition-all hover:border-primary hover:shadow-elegant",
        active ? "border-primary bg-primary-soft" : "border-border bg-card")}>
      <Icon className="size-5 text-primary"/>
      <div className="mt-3 font-semibold text-sm">{title}</div>
      <div className="text-xs text-muted-foreground mt-0.5">{desc}</div>
    </button>
  );
}

function Stat({ label, value, tone }: { label: string; value: string; tone: "primary"|"warning"|"destructive" }) {
  return (
    <div className="rounded-lg border border-border p-4">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className={cn("mt-1 text-2xl font-display font-semibold",
        tone === "primary" && "text-primary",
        tone === "warning" && "text-warning-foreground",
        tone === "destructive" && "text-destructive")}>{value}</div>
    </div>
  );
}

function ValidationRow({ tone, title, desc }: { tone: "error"|"warn"; title: string; desc: string }) {
  return (
    <li className="flex items-start gap-3 p-3">
      <AlertCircle className={cn("size-4 mt-0.5", tone === "error" ? "text-destructive" : "text-warning-foreground")}/>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium">{title}</div>
        <div className="text-xs text-muted-foreground">{desc}</div>
      </div>
      <Button size="sm" variant="outline">Fix</Button>
    </li>
  );
}

function FixRow({ problem, suggestion }: { problem: string; suggestion: string }) {
  return (
    <div className="p-4">
      <div className="text-sm font-medium text-destructive">{problem}</div>
      <div className="mt-2 flex items-start gap-2 text-xs text-muted-foreground">
        <Wand2 className="size-3.5 text-primary mt-0.5 shrink-0"/>
        <span><span className="font-semibold text-foreground">AI suggests:</span> {suggestion}</span>
      </div>
      <div className="mt-3 flex gap-2">
        <Button size="sm" className="gap-1.5"><Check className="size-3.5"/>Accept</Button>
        <Button size="sm" variant="outline">Edit manually</Button>
      </div>
    </div>
  );
}

function Track({ title, time, ok, pending }: { title: string; time?: string; ok?: boolean; pending?: boolean }) {
  return (
    <li className="flex items-center gap-3">
      <div className={cn("size-6 rounded-full grid place-items-center text-[11px] font-semibold",
        ok && "bg-success text-success-foreground",
        pending && "bg-muted text-muted-foreground",
      )}>
        {ok ? <Check className="size-3.5"/> : "•"}
      </div>
      <div className="flex-1">
        <div className="font-medium">{title}</div>
        {time && <div className="text-xs text-muted-foreground">{time}</div>}
      </div>
    </li>
  );
}

function SFPreview() {
  const sample = mockStudents.slice(0, 12);
  return (
    <div className="min-w-[900px]">
      <div className="border border-foreground/80 p-4 font-serif">
        <div className="text-center text-xs">
          <div>Republic of the Philippines</div>
          <div className="font-bold">DEPARTMENT OF EDUCATION</div>
          <div>Region III · Division of Bulacan · Sampaloc Elementary School</div>
          <div className="mt-1 font-bold text-sm">SF2 — DAILY ATTENDANCE REPORT OF LEARNERS</div>
          <div>School Year 2026–2027 · Month of September · Grade 6 — Sampaguita</div>
        </div>
        <table className="w-full mt-3 text-[11px] border-collapse">
          <thead>
            <tr className="bg-muted/60">
              <th className="border border-foreground/60 p-1 w-8">#</th>
              <th className="border border-foreground/60 p-1 text-left">LEARNER'S NAME (Last, First, M.I.)</th>
              <th className="border border-foreground/60 p-1 w-16">LRN</th>
              <th className="border border-foreground/60 p-1 w-10">Sex</th>
              {[1,2,3,4,5,8,9,10,11,12].map(d => <th key={d} className="border border-foreground/60 p-1 w-6">{d}</th>)}
              <th className="border border-foreground/60 p-1 w-12 bg-primary/10">TOTAL</th>
            </tr>
          </thead>
          <tbody>
            {sample.map((s, i) => (
              <tr key={s.id}>
                <td className="border border-foreground/60 p-1 text-center">{i + 1}</td>
                <td className="border border-foreground/60 p-1">{s.name}</td>
                <td className="border border-foreground/60 p-1 font-mono">{s.lrn}</td>
                <td className="border border-foreground/60 p-1 text-center">{s.sex}</td>
                {[1,2,3,4,5,8,9,10,11,12].map(d => (
                  <td key={d} className={cn("border border-foreground/60 p-1 text-center",
                    (i % 7 === 3 && d === 5) && "bg-destructive/20 text-destructive")}>
                    {(i % 7 === 3 && d === 5) ? "X" : ""}
                  </td>
                ))}
                <td className="border border-foreground/60 p-1 text-center font-semibold bg-primary/5">{s.attendance > 95 ? 20 : 19}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
