import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/page-header";
import { mockStudents } from "@/lib/mock-data";
import { AlertTriangle, TrendingUp, TrendingDown, Sparkles, Search } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/students")({
  head: () => ({ meta: [{ title: "Student Intelligence Hub · TeacherOS" }] }),
  component: StudentsPage,
});

function StudentsPage() {
  const [q, setQ] = useState("");
  const [selected, setSelected] = useState(mockStudents[0]);
  const filtered = mockStudents.filter(s => s.name.toLowerCase().includes(q.toLowerCase()));

  return (
    <div className="px-4 lg:px-8 py-6 lg:py-8 max-w-[1600px] mx-auto space-y-6">
      <PageHeader
        eyebrow="Student Intelligence Hub"
        title="40 learners · Grade 6 · 3 sections"
        description="Risk prediction, intervention suggestions, and case management — powered by the Student Risk Analyst agent."
        actions={<Button className="gap-2"><Sparkles className="size-4"/>Run risk scan</Button>}
      />

      <div className="grid lg:grid-cols-12 gap-6">
        <div className="lg:col-span-5 rounded-xl border border-border bg-card">
          <div className="p-4 border-b border-border">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground"/>
              <input value={q} onChange={(e)=>setQ(e.target.value)} placeholder="Search learner…"
                className="w-full h-9 pl-9 pr-3 rounded-md bg-muted/60 text-sm focus:outline-none focus:ring-2 focus:ring-ring/30"/>
            </div>
          </div>
          <ul className="max-h-[60vh] overflow-y-auto divide-y divide-border">
            {filtered.map(s => (
              <li key={s.id}>
                <button onClick={()=>setSelected(s)}
                  className={cn("w-full flex items-center gap-3 p-3 text-left hover:bg-muted/40",
                    selected.id === s.id && "bg-primary-soft")}>
                  <div className={cn("size-9 rounded-full grid place-items-center text-xs font-semibold",
                    s.risk === "high" ? "bg-destructive/10 text-destructive" :
                    s.risk === "medium" ? "bg-warning/15 text-warning-foreground" : "bg-success/10 text-success")}>
                    {s.name.split(",")[0].slice(0,2).toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">{s.name}</div>
                    <div className="text-[11px] text-muted-foreground">{s.section} · LRN {s.lrn}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold">{s.averageGrade}</div>
                    <div className="text-[11px] text-muted-foreground">{s.attendance}%</div>
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div className="lg:col-span-7 space-y-4">
          <div className="rounded-xl border border-border bg-card p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs font-mono text-muted-foreground">LRN {selected.lrn}</div>
                <h2 className="text-xl font-display font-semibold">{selected.name}</h2>
                <div className="text-xs text-muted-foreground">{selected.section} · Guardian: {selected.guardian} · {selected.contact}</div>
              </div>
              <div className={cn("text-xs font-semibold px-3 py-1.5 rounded-full",
                selected.risk === "high" ? "bg-destructive/10 text-destructive" :
                selected.risk === "medium" ? "bg-warning/15 text-warning-foreground" : "bg-success/10 text-success")}>
                {selected.risk.toUpperCase()} RISK
              </div>
            </div>

            <div className="mt-5 grid sm:grid-cols-3 gap-3">
              <Metric label="Average grade" value={selected.averageGrade.toString()} trend="up" />
              <Metric label="Attendance" value={`${selected.attendance}%`} trend={selected.attendance > 90 ? "up" : "down"}/>
              <Metric label="Behavior notes" value="2" trend="flat" />
            </div>
          </div>

          {selected.risk !== "low" && (
            <div className="rounded-xl border border-primary/30 bg-primary-soft/40 p-5">
              <div className="flex items-center gap-2 text-sm font-semibold text-primary">
                <Sparkles className="size-4"/> AI Intervention Suggestions
              </div>
              <ul className="mt-3 text-sm space-y-2 text-foreground/90">
                <li>• Schedule 1-on-1 remediation in Math (fractions) — 15 min, Friday after class.</li>
                <li>• Send Tagalog letter to guardian about 3 unexcused absences.</li>
                <li>• Pair with a high-achieving learner for next group activity.</li>
              </ul>
              <div className="mt-4 flex gap-2">
                <Button size="sm">Open case</Button>
                <Button size="sm" variant="outline">Draft letter</Button>
              </div>
            </div>
          )}

          <div className="rounded-xl border border-border bg-card p-5">
            <div className="text-sm font-semibold mb-3">Case Management</div>
            <ol className="space-y-2 text-sm">
              <CaseRow label="Issue" value="Drop in Q1 Math grade (89 → 78)" />
              <CaseRow label="Action" value="Remediation + parent notice" />
              <CaseRow label="Status" value="In progress" tone="warn" />
              <CaseRow label="Next review" value="Friday, Sept 27" />
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}

function Metric({ label, value, trend }: { label: string; value: string; trend: "up"|"down"|"flat" }) {
  return (
    <div className="rounded-lg border border-border p-4">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 flex items-end gap-2">
        <span className="text-2xl font-display font-semibold">{value}</span>
        {trend === "up" && <TrendingUp className="size-4 text-success mb-1"/>}
        {trend === "down" && <TrendingDown className="size-4 text-destructive mb-1"/>}
        {trend === "flat" && <AlertTriangle className="size-4 text-muted-foreground mb-1"/>}
      </div>
    </div>
  );
}

function CaseRow({ label, value, tone }: { label: string; value: string; tone?: "warn" }) {
  return (
    <li className="flex items-center justify-between border-b border-border last:border-0 pb-2 last:pb-0">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className={cn("font-medium", tone === "warn" && "text-warning-foreground")}>{value}</span>
    </li>
  );
}
