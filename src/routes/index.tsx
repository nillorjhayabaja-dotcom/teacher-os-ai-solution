import { createFileRoute, Link } from "@tanstack/react-router";
import {
  BookOpen, Calculator, FileText, Users, AlertTriangle, Sparkles,
  ArrowRight, Clock, CheckCircle2, TrendingUp, MessageSquare,
} from "lucide-react";
import {
  mockClasses, pendingWorkflows, atRiskStudents, performanceTrend,
} from "@/lib/mock-data";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Dashboard · TeacherOS" },
      { name: "description", content: "Your daily execution system: today's classes, pending workflows, AI briefing, and at-risk students." },
    ],
  }),
  component: DashboardPage,
});

const quickActions = [
  { to: "/lesson-planning", label: "Start Lesson Planning", icon: BookOpen, tone: "primary" },
  { to: "/grading", label: "Start Grading Cycle", icon: Calculator, tone: "info" },
  { to: "/forms", label: "Generate SF Forms", icon: FileText, tone: "warning" },
  { to: "/students", label: "Run Risk Scan", icon: AlertTriangle, tone: "destructive" },
];

function DashboardPage() {
  const today = new Date().toLocaleDateString("en-PH", {
    weekday: "long", month: "long", day: "numeric", year: "numeric",
  });

  return (
    <div className="px-4 lg:px-8 py-6 lg:py-8 max-w-[1600px] mx-auto space-y-6">
      <PageHeader
        eyebrow={today}
        title="Magandang umaga, Teacher Mariel 👋"
        description="You have 5 classes today, 3 pending workflows, and 2 students need attention. AI has prepared a briefing for you."
        actions={
          <Link to="/agents">
            <Button className="gap-2">
              <Sparkles className="size-4" />
              AI Daily Briefing
            </Button>
          </Link>
        }
      />

      {/* Quick actions */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {quickActions.map((a) => (
          <Link key={a.to} to={a.to as string}
            className="group rounded-xl border border-border bg-card p-4 hover:border-primary hover:shadow-elegant transition-all">
            <div className={cn(
              "size-9 rounded-lg grid place-items-center mb-3",
              a.tone === "primary" && "bg-primary/10 text-primary",
              a.tone === "info" && "bg-info/10 text-info",
              a.tone === "warning" && "bg-warning/15 text-warning-foreground",
              a.tone === "destructive" && "bg-destructive/10 text-destructive",
            )}>
              <a.icon className="size-4" />
            </div>
            <div className="text-sm font-semibold text-foreground">{a.label}</div>
            <div className="mt-1 flex items-center gap-1 text-xs text-muted-foreground group-hover:text-primary transition-colors">
              Open workflow <ArrowRight className="size-3" />
            </div>
          </Link>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Today's classes */}
        <div className="lg:col-span-2 rounded-xl border border-border bg-card">
          <div className="flex items-center justify-between p-5 border-b border-border">
            <div>
              <h2 className="text-base font-semibold">Today's Classes</h2>
              <p className="text-xs text-muted-foreground mt-0.5">Tap a class to start the lesson workflow.</p>
            </div>
            <Link to="/teaching" className="text-xs text-primary font-medium hover:underline">View week →</Link>
          </div>
          <ul className="divide-y divide-border">
            {mockClasses.map((c, i) => (
              <li key={c.id} className="flex items-center gap-4 p-4 hover:bg-muted/40 transition-colors">
                <div className="w-24 shrink-0">
                  <div className="text-xs font-mono text-muted-foreground">{c.time}</div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm">{c.subject}</div>
                  <div className="text-xs text-muted-foreground">{c.section} · {c.room}</div>
                </div>
                {i === 0 ? (
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-success/10 text-success">NEXT</span>
                ) : (
                  <Clock className="size-4 text-muted-foreground" />
                )}
              </li>
            ))}
          </ul>
        </div>

        {/* AI briefing */}
        <div className="rounded-xl border border-primary/30 bg-gradient-to-br from-primary-soft to-card p-5">
          <div className="flex items-center gap-2">
            <div className="size-8 rounded-lg bg-gradient-primary grid place-items-center">
              <Sparkles className="size-4 text-primary-foreground" />
            </div>
            <div>
              <div className="text-sm font-semibold">AI Daily Briefing</div>
              <div className="text-[11px] text-muted-foreground">Generated 6:12 AM</div>
            </div>
          </div>
          <ul className="mt-4 space-y-3 text-sm">
            <li className="flex gap-2">
              <CheckCircle2 className="size-4 text-success mt-0.5 shrink-0" />
              <span>3 DLLs ready to review for Math 6 (Week 4).</span>
            </li>
            <li className="flex gap-2">
              <AlertTriangle className="size-4 text-warning-foreground mt-0.5 shrink-0" />
              <span><strong>2 students</strong> in Sampaguita dropped &gt;5% in Quarter 1. Suggested interventions ready.</span>
            </li>
            <li className="flex gap-2">
              <FileText className="size-4 text-primary mt-0.5 shrink-0" />
              <span>SF2 for September is <strong>92% auto-filled</strong>. 3 attendance entries need confirmation.</span>
            </li>
            <li className="flex gap-2">
              <MessageSquare className="size-4 text-info mt-0.5 shrink-0" />
              <span>Draft parent letters prepared for 3 absentees (Tagalog + English).</span>
            </li>
          </ul>
          <Link to="/agents" className="mt-5 inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline">
            Open AI Agent Workspace <ArrowRight className="size-3" />
          </Link>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Pending workflows */}
        <div className="lg:col-span-2 rounded-xl border border-border bg-card">
          <div className="flex items-center justify-between p-5 border-b border-border">
            <h2 className="text-base font-semibold">Pending Workflows</h2>
            <span className="text-xs text-muted-foreground">{pendingWorkflows.length} items</span>
          </div>
          <ul className="divide-y divide-border">
            {pendingWorkflows.map((w) => (
              <li key={w.id} className="flex items-center gap-4 p-4 hover:bg-muted/40">
                <span className={cn(
                  "size-2 rounded-full shrink-0",
                  w.severity === "high" && "bg-destructive",
                  w.severity === "medium" && "bg-warning",
                  w.severity === "low" && "bg-muted-foreground/50",
                )}/>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium">{w.title}</div>
                  <div className="text-xs text-muted-foreground">{w.module} · due {w.due}</div>
                </div>
                <Button size="sm" variant="outline">Resume</Button>
              </li>
            ))}
          </ul>
        </div>

        {/* Performance trend */}
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold">Class Average</h2>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-3xl font-display font-semibold">87<span className="text-base text-muted-foreground">.2</span></span>
                <span className="text-xs text-success flex items-center gap-0.5"><TrendingUp className="size-3"/>+3.1</span>
              </div>
            </div>
          </div>
          <div className="mt-3 h-32">
            <ResponsiveContainer>
              <AreaChart data={performanceTrend}>
                <defs>
                  <linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="oklch(0.55 0.20 258)" stopOpacity={0.35}/>
                    <stop offset="100%" stopColor="oklch(0.55 0.20 258)" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false}/>
                <XAxis dataKey="week" tick={{ fontSize: 10, fill: "var(--muted-foreground)" }} axisLine={false} tickLine={false}/>
                <YAxis hide domain={[75, 95]}/>
                <Tooltip contentStyle={{ background: "var(--popover)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }}/>
                <Area type="monotone" dataKey="avg" stroke="oklch(0.55 0.20 258)" strokeWidth={2} fill="url(#g1)"/>
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* At risk */}
      <div className="rounded-xl border border-border bg-card">
        <div className="flex items-center justify-between p-5 border-b border-border">
          <div>
            <h2 className="text-base font-semibold flex items-center gap-2">
              <AlertTriangle className="size-4 text-destructive"/> At-risk students
            </h2>
            <p className="text-xs text-muted-foreground mt-0.5">Predicted by Student Risk Analyst agent.</p>
          </div>
          <Link to="/students" className="text-xs text-primary font-medium hover:underline">Open hub →</Link>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 p-4">
          {atRiskStudents.map((s) => (
            <div key={s.id} className="flex items-center gap-3 p-3 rounded-lg border border-border hover:border-destructive/50 transition-colors">
              <div className="size-9 rounded-full bg-destructive/10 text-destructive grid place-items-center text-xs font-semibold">
                {s.name.split(",")[0].slice(0,2).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">{s.name}</div>
                <div className="text-xs text-muted-foreground">Avg {s.averageGrade} · Att {s.attendance}%</div>
              </div>
              <Users className="size-4 text-muted-foreground"/>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
