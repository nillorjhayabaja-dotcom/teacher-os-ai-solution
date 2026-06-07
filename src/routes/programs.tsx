import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { mockPrograms, type Program } from "@/lib/mock-data";
import {
  School, Sparkles, Check, ChevronRight, Download,
  CalendarDays, PiggyBank, FileText, ClipboardList,
} from "lucide-react";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/programs")({
  head: () => ({
    meta: [
      { title: "School Programs · TeacherOS" },
      { name: "description", content: "Plan, execute, and report on Feeding Program, DRRM, Brigada Eskwela and other school programs." },
    ],
  }),
  component: ProgramsPage,
});

const weekLabels = ["Sep W1", "Sep W2", "Sep W3", "Sep W4", "Oct W1", "Oct W2", "Oct W3", "Oct W4"];

function ProgramsPage() {
  const [selected, setSelected] = useState<Program>(mockPrograms[0]);

  const program = mockPrograms.find(p => p.id === selected.id) || mockPrograms[0];

  return (
    <div className="px-4 lg:px-8 py-6 lg:py-8 max-w-[1600px] mx-auto space-y-6">
      <PageHeader
        eyebrow="School Programs Workflow"
        title="Plan, Run, and Report"
        description="Feeding Program, DRRM, Brigada Eskwela — from kickoff to post-activity reporting in one workflow."
        actions={
          <Button className="gap-2"><Sparkles className="size-4"/>AI Program Setup</Button>
        }
      />

      {/* Program Selector */}
      <div className="flex gap-3 overflow-x-auto pb-2">
        {mockPrograms.map(p => (
          <button key={p.id} onClick={() => setSelected(p)}
            className={cn("shrink-0 rounded-xl border p-4 text-left min-w-[220px] transition-all",
              selected.id === p.id ? "border-primary bg-primary-soft shadow-elegant" : "border-border bg-card hover:border-input")}>
            <div className="flex items-center justify-between">
              <span className="font-semibold text-sm">{p.name}</span>
              <span className={cn("text-[10px] px-1.5 py-0.5 rounded font-medium",
                p.status === "planning" && "bg-info/10 text-info",
                p.status === "execution" && "bg-warning/15 text-warning-foreground",
                p.status === "reporting" && "bg-primary/10 text-primary",
                p.status === "completed" && "bg-success/10 text-success")}>
                {p.status}
              </span>
            </div>
            <div className="mt-2 text-xs text-muted-foreground">
              Budget: ₱{p.budget.toLocaleString()} · Spent: ₱{p.spent.toLocaleString()}
            </div>
            <div className="mt-2 h-1.5 rounded-full bg-muted overflow-hidden">
              <div className={cn("h-full rounded-full", p.status === "completed" ? "bg-success" : "bg-primary")}
                style={{ width: `${Math.round(p.spent / p.budget * 100)}%` }}/>
            </div>
          </button>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Status Bar */}
          <div className="rounded-xl border border-border bg-card p-4 flex items-center gap-4">
            {(["planning", "execution", "reporting", "completed"] as const).map((s, i) => (
              <div key={s} className="flex items-center gap-2 flex-1">
                <div className={cn("size-7 rounded-full grid place-items-center text-[11px] font-semibold",
                  program.status === s ? "bg-primary text-primary-foreground" :
                  ["planning", "execution", "reporting", "completed"].indexOf(program.status) > i ? "bg-success text-success-foreground" : "bg-muted text-muted-foreground")}>
                  {["planning", "execution", "reporting", "completed"].indexOf(program.status) > i ? <Check className="size-3.5"/> : i + 1}
                </div>
                <div className="text-xs">
                  <div className="font-medium capitalize">{s}</div>
                  {i < 3 && <ChevronRight className="size-3 text-muted-foreground mt-0.5"/>}
                </div>
              </div>
            ))}
          </div>

          {/* Timeline (Gantt) */}
          <div className="rounded-xl border border-border bg-card p-5">
            <h2 className="font-semibold mb-4 flex items-center gap-2">
              <CalendarDays className="size-4 text-primary"/> Timeline
            </h2>
            <div className="overflow-x-auto">
              <div className="min-w-[700px]">
                <div className="flex mb-2">
                  <div className="w-48 shrink-0" />
                  {weekLabels.map(w => (
                    <div key={w} className="flex-1 text-center text-[10px] text-muted-foreground font-medium">{w}</div>
                  ))}
                </div>
                <div className="space-y-2">
                  {program.tasks.map((task, i) => (
                    <div key={i} className="flex items-center">
                      <div className="w-48 shrink-0 text-xs font-medium truncate pr-3">{task.name}</div>
                      <div className="flex-1 flex gap-0.5">
                        {weekLabels.map((_, wi) => {
                          const isActive = wi + 1 >= task.startWeek && wi + 1 < task.startWeek + task.duration;
                          return (
                            <div key={wi} className={cn("flex-1 h-6 rounded-sm",
                              isActive && task.status === "done" && "bg-primary",
                              isActive && task.status === "in-progress" && "bg-warning",
                              isActive && task.status === "pending" && "bg-muted border border-dashed border-muted-foreground/30",
                              !isActive && "bg-transparent")} />
                          );
                        })}
                      </div>
                      <div className="w-16 text-right text-[10px] text-muted-foreground">
                        {task.status === "done" ? "✓" : task.status === "in-progress" ? "🔄" : "○"}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Budget */}
          <div className="rounded-xl border border-border bg-card p-5">
            <h2 className="font-semibold mb-4 flex items-center gap-2">
              <PiggyBank className="size-4 text-primary"/> Budget Breakdown
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left p-2 text-xs font-semibold text-muted-foreground">Item</th>
                    <th className="text-right p-2 text-xs font-semibold text-muted-foreground">Qty</th>
                    <th className="text-right p-2 text-xs font-semibold text-muted-foreground">Unit Cost</th>
                    <th className="text-right p-2 text-xs font-semibold text-muted-foreground">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { item: "Rice (50kg sack)", qty: 2, cost: 2500 },
                    { item: "Chicken (whole, kg)", qty: 15, cost: 180 },
                    { item: "Vegetables (assorted)", qty: 1, cost: 1500 },
                    { item: "Cooking supplies", qty: 1, cost: 800 },
                  ].map((row, i) => (
                    <tr key={i} className="border-b border-border last:border-0">
                      <td className="p-2 text-sm">{row.item}</td>
                      <td className="p-2 text-right">{row.qty}</td>
                      <td className="p-2 text-right">₱{row.cost.toLocaleString()}</td>
                      <td className="p-2 text-right font-medium">₱{(row.qty * row.cost).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="bg-muted/40">
                    <td className="p-2 font-semibold" colSpan={3}>TOTAL BUDGET</td>
                    <td className="p-2 text-right font-bold">₱10,000</td>
                  </tr>
                  <tr>
                    <td className="p-2 text-muted-foreground" colSpan={3}>MOOE Allocation</td>
                    <td className="p-2 text-right font-medium">₱15,000</td>
                  </tr>
                  <tr>
                    <td className="p-2 text-muted-foreground" colSpan={3}>Remaining</td>
                    <td className="p-2 text-right font-medium text-success">₱5,000</td>
                  </tr>
                </tfoot>
              </table>
            </div>
            <div className="mt-4 flex gap-2">
              <Button size="sm" variant="outline" className="gap-1.5"><PiggyBank className="size-3"/>Add Line Item</Button>
              <Button size="sm" variant="outline" className="gap-1.5">📋 Import from Template</Button>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          <div className="rounded-xl border border-border bg-card p-5">
            <h3 className="text-sm font-semibold mb-3">Program Details</h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between"><span className="text-muted-foreground">Name</span><span className="font-medium">{program.name}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Status</span><span className="font-medium capitalize">{program.status}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Budget</span><span className="font-medium">₱{program.budget.toLocaleString()}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Spent</span><span className="font-medium">₱{program.spent.toLocaleString()}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Start</span><span className="font-medium">{new Date(program.startDate).toLocaleDateString()}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">End</span><span className="font-medium">{new Date(program.endDate).toLocaleDateString()}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Tasks</span><span className="font-medium">{program.tasks.length}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Progress</span><span className="font-medium">{Math.round(program.tasks.filter(t => t.status === "done").length / program.tasks.length * 100)}%</span></div>
            </div>
          </div>

          <div className="rounded-xl border border-primary/20 bg-primary-soft/40 p-5">
            <Sparkles className="size-4 text-primary"/>
            <h3 className="text-sm font-semibold mt-2">AI-Powered Report</h3>
            <p className="text-xs text-muted-foreground mt-1">Generate a post-activity accomplishment report with AI from your execution logs.</p>
            <Button size="sm" className="mt-3 w-full gap-1.5"><FileText className="size-3"/>Generate Report</Button>
          </div>

          <div className="rounded-xl border border-border bg-card p-5">
            <h3 className="text-sm font-semibold mb-3">Quick Actions</h3>
            <div className="space-y-2">
              <Button size="sm" variant="outline" className="w-full justify-start gap-2"><ClipboardList className="size-3"/>Log Activity</Button>
              <Button size="sm" variant="outline" className="w-full justify-start gap-2"><CalendarDays className="size-3"/>Add Milestone</Button>
              <Button size="sm" variant="outline" className="w-full justify-start gap-2"><Download className="size-3"/>Export Report</Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}