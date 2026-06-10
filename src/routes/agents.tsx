import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { aiAgents } from "@/lib/mock-data";
import {
  BookOpen,
  ClipboardCheck,
  Calculator,
  FileText,
  FileSignature,
  AlertTriangle,
  Play,
  Clock,
  Sparkles,
  ArrowRight,
} from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

const iconMap = { BookOpen, ClipboardCheck, Calculator, FileText, FileSignature, AlertTriangle };

export const Route = createFileRoute("/agents")({
  head: () => ({
    meta: [
      { title: "AI Agent Workspace · TeacherOS" },
      {
        name: "description",
        content:
          "Multi-agent system for lesson planning, grading, forms, reports, and student risk analysis.",
      },
    ],
  }),
  component: AgentsPage,
});

function AgentsPage() {
  const [selected, setSelected] = useState<string>("lesson");
  const [running, setRunning] = useState(false);
  const [log, setLog] = useState<string[]>([]);

  const agent = aiAgents.find((a) => a.id === selected)!;

  function run() {
    setRunning(true);
    setLog([]);
    const lines = [
      "→ Loading context: Grade 6, Sampaguita, Quarter 1",
      "→ Retrieving MELC alignment matrix…",
      "→ Drafting 5 lesson objectives (Bloom: Apply, Analyze)",
      "→ Generating differentiation strategies for SPED + advanced learners",
      "→ Reflecting on prior week assessment scores",
      "✓ Output ready — 1 DLL · 3 worksheets · 1 quiz",
    ];
    lines.forEach((l, i) => setTimeout(() => setLog((prev) => [...prev, l]), i * 500));
    setTimeout(() => setRunning(false), lines.length * 500);
  }

  return (
    <div className="px-4 lg:px-8 py-6 lg:py-8 max-w-[1600px] mx-auto space-y-6">
      <PageHeader
        eyebrow="The Brain"
        title="AI Agent Workspace"
        description="Six context-aware agents orchestrate your teacher workflows. Each agent has its own memory, task input, and execution history."
      />

      <div className="grid lg:grid-cols-12 gap-6">
        {/* Agent list */}
        <div className="lg:col-span-4 space-y-2">
          {aiAgents.map((a) => {
            const Icon = iconMap[a.icon as keyof typeof iconMap];
            const active = a.id === selected;
            return (
              <button
                key={a.id}
                onClick={() => setSelected(a.id)}
                className={cn(
                  "w-full text-left rounded-xl border p-4 transition-all flex items-start gap-3",
                  active
                    ? "border-primary bg-primary-soft shadow-elegant"
                    : "border-border bg-card hover:border-input",
                )}
              >
                <div className={cn("size-10 rounded-lg grid place-items-center shrink-0", a.color)}>
                  <Icon className="size-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-sm">{a.name}</div>
                  <div className="text-xs text-muted-foreground mt-0.5">{a.desc}</div>
                  <div className="mt-2 flex items-center gap-2 text-[11px] text-muted-foreground">
                    <span className="size-1.5 rounded-full bg-success animate-pulse" />
                    online
                    <span>·</span>
                    <span>{Math.floor(Math.random() * 40) + 5} runs today</span>
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* Agent workspace */}
        <div className="lg:col-span-8 space-y-4">
          <div className="rounded-xl border border-border bg-card p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs text-primary font-semibold uppercase tracking-wider">
                  Active agent
                </div>
                <h2 className="text-xl font-display font-semibold mt-1">{agent.name}</h2>
                <p className="text-sm text-muted-foreground">{agent.desc}</p>
              </div>
              <Button onClick={run} disabled={running} className="gap-2">
                {running ? (
                  <>
                    <Sparkles className="size-4 animate-pulse" />
                    Running…
                  </>
                ) : (
                  <>
                    <Play className="size-4" />
                    Run workflow
                  </>
                )}
              </Button>
            </div>

            <div className="mt-5 grid sm:grid-cols-2 gap-4">
              <div>
                <div className="text-xs font-semibold text-muted-foreground mb-1.5">Task Input</div>
                <textarea
                  defaultValue="Generate a weekly DLL bundle for Math 6, Quarter 1, week 4 with differentiation."
                  className="w-full h-28 p-3 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring/30 resize-none"
                />
              </div>
              <div>
                <div className="text-xs font-semibold text-muted-foreground mb-1.5">
                  Memory Context
                </div>
                <div className="rounded-md border border-border bg-muted/40 p-3 text-xs space-y-1.5">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Grade level</span>
                    <span className="font-medium">6</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Section</span>
                    <span className="font-medium">Sampaguita</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Subject</span>
                    <span className="font-medium">Mathematics</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Past DLLs available</span>
                    <span className="font-medium">12</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Linked module</span>
                    <span className="font-medium text-primary">Lesson Planning</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            <div className="rounded-xl border border-border bg-card p-5">
              <div className="text-xs font-semibold text-muted-foreground mb-3">Execution Log</div>
              <div className="font-mono text-xs space-y-1.5 min-h-[160px]">
                {log.length === 0 && (
                  <p className="text-muted-foreground">
                    Click "Run workflow" to see live execution.
                  </p>
                )}
                {log.map((l, i) => (
                  <div
                    key={i}
                    className={cn(l.startsWith("✓") ? "text-success" : "text-foreground/80")}
                  >
                    {l}
                  </div>
                ))}
              </div>
            </div>
            <div className="rounded-xl border border-border bg-card p-5">
              <div className="flex items-center justify-between mb-3">
                <div className="text-xs font-semibold text-muted-foreground">Recent runs</div>
                <Clock className="size-3.5 text-muted-foreground" />
              </div>
              <ul className="space-y-2 text-xs">
                {[
                  "6:12 AM · Daily briefing",
                  "Yesterday 4:30 PM · Math 6 DLL",
                  "Yesterday 2:15 PM · Worksheet pack",
                  "Mon · Quarterly assessment",
                ].map((r) => (
                  <li
                    key={r}
                    className="flex items-center justify-between p-2 rounded hover:bg-muted/40"
                  >
                    <span>{r}</span>
                    <ArrowRight className="size-3 text-muted-foreground" />
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
