import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { mockTeachingWeek, mockClasses } from "@/lib/mock-data";
import {
  CalendarDays, Check, ChevronRight, Sparkles,
  Clock, BookOpen, Users, ClipboardList, RefreshCw,
} from "lucide-react";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/teaching")({
  head: () => ({
    meta: [
      { title: "Teaching Workflow · TeacherOS" },
      { name: "description", content: "Weekly teaching execution system with attendance capture, lesson tracking, and reflection logging." },
    ],
  }),
  component: TeachingPage,
});

function TeachingPage() {
  const [selectedDay, setSelectedDay] = useState(2); // Wednesday (in-progress)
  const week = mockTeachingWeek;
  const day = week[selectedDay];

  const completedClasses = week.reduce((sum, d) => sum + d.classes.filter(c => c.status === "completed").length, 0);
  const totalClasses = week.reduce((sum, d) => sum + d.classes.length, 0);
  const dllLinked = week.reduce((sum, d) => sum + d.classes.filter(c => c.dllLinked).length, 0);
  const attendanceDone = week.reduce((sum, d) => sum + d.classes.filter(c => c.attendanceCaptured).length, 0);
  const reflectionsDone = week.reduce((sum, d) => sum + d.classes.filter(c => c.reflectionDone).length, 0);

  return (
    <div className="px-4 lg:px-8 py-6 lg:py-8 max-w-[1600px] mx-auto space-y-6">
      <PageHeader
        eyebrow="Teaching Workflow"
        title="Your Weekly Execution System"
        description="Plan, teach, assess, reflect — a single rhythm for your entire week."
        actions={
          <Link to="/lesson-planning">
            <Button className="gap-2"><BookOpen className="size-4"/>Open Lesson Planner</Button>
          </Link>
        }
      />

      {/* Weekly stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard label="Total Classes" value={totalClasses.toString()} icon={CalendarDays} color="primary" />
        <StatCard label="Completed" value={completedClasses.toString()} icon={Check} color="success" />
        <StatCard label="DLL Linked" value={`${dllLinked}/${totalClasses}`} icon={BookOpen} color="info" />
        <StatCard label="Attendance" value={`${attendanceDone}/${totalClasses}`} icon={Users} color="warning" />
      </div>

      {/* Day selector */}
      <div className="flex gap-2 overflow-x-auto pb-1">
        {week.map((d, i) => (
          <button key={d.date} onClick={() => setSelectedDay(i)}
            className={cn("shrink-0 rounded-lg border px-4 py-3 text-left min-w-[140px] transition-all",
              selectedDay === i ? "border-primary bg-primary-soft shadow-elegant" : "border-border bg-card hover:border-input")}>
            <div className="text-xs font-semibold text-muted-foreground">{d.dayName}</div>
            <div className="text-[11px] text-muted-foreground">{new Date(d.date).toLocaleDateString('en-PH', { month: 'short', day: 'numeric' })}</div>
            <div className="mt-1.5 flex gap-1">
              {d.classes.map(c => (
                <div key={c.id} className={cn("size-2 rounded-full",
                  c.status === "completed" ? "bg-success" :
                  c.status === "in-progress" ? "bg-primary" : "bg-muted-foreground/30")} />
              ))}
            </div>
          </button>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Class list for selected day */}
        <div className="lg:col-span-2 space-y-4">
          <div className="rounded-xl border border-border bg-card">
            <div className="p-4 border-b border-border flex items-center justify-between">
              <h2 className="font-semibold">{day.dayName}'s Classes</h2>
              <span className="text-xs text-muted-foreground">{day.classes.filter(c => c.status === "completed").length}/{day.classes.length} done</span>
            </div>
            <div className="divide-y divide-border">
              {day.classes.map(c => (
                <div key={c.id} className="p-4 flex items-center gap-4 hover:bg-muted/20 transition-colors">
                  <div className={cn("size-10 rounded-lg grid place-items-center",
                    c.status === "completed" ? "bg-success/10 text-success" :
                    c.status === "in-progress" ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground")}>
                    {c.status === "completed" ? <Check className="size-4"/> :
                     c.status === "in-progress" ? <Clock className="size-4"/> :
                     <span className="text-xs font-bold">{c.time.split("–")[0].trim()}</span>}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium">{c.subject}</div>
                    <div className="text-xs text-muted-foreground">{c.time} · {c.section}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    {c.status === "completed" ? (
                      <div className="flex gap-1">
                        {c.dllLinked && <span className="text-[10px] px-1.5 py-0.5 rounded bg-success/10 text-success">DLL</span>}
                        {c.attendanceCaptured && <span className="text-[10px] px-1.5 py-0.5 rounded bg-info/10 text-info">Att</span>}
                        {c.reflectionDone && <span className="text-[10px] px-1.5 py-0.5 rounded bg-primary/10 text-primary">Ref</span>}
                      </div>
                    ) : c.status === "in-progress" ? (
                      <div className="flex gap-2">
                        <Button size="sm" variant="outline" className="gap-1"><Users className="size-3"/>Att</Button>
                        <Button size="sm" className="gap-1"><ClipboardList className="size-3"/>Start</Button>
                      </div>
                    ) : (
                      <span className="text-xs text-muted-foreground">
                        {c.time}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Quick actions for today */}
          {day.classes.some(c => c.status === "in-progress" || c.status === "upcoming") && (
            <div className="rounded-xl border border-primary/30 bg-gradient-to-br from-primary-soft to-card p-5">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <Sparkles className="size-4 text-primary"/> AI Suggestions for Today
              </div>
              <ul className="mt-3 space-y-2 text-sm">
                <li className="flex gap-2">
                  <Check className="size-4 text-success mt-0.5 shrink-0"/>
                  <span>DLL for Math 6 is ready — <button className="text-primary hover:underline">Review now</button></span>
                </li>
                <li className="flex gap-2">
                  <RefreshCw className="size-4 text-primary mt-0.5 shrink-0"/>
                  <span>Attendance for Science 6 (Rosal) needs capture from yesterday</span>
                </li>
                <li className="flex gap-2">
                  <ClipboardList className="size-4 text-warning-foreground mt-0.5 shrink-0"/>
                  <span>2 reflections pending from Monday classes</span>
                </li>
              </ul>
            </div>
          )}
        </div>

        {/* Sidebar: Weekly progress */}
        <div className="space-y-4">
          <div className="rounded-xl border border-border bg-card p-5">
            <h3 className="text-sm font-semibold mb-3">Weekly Progress</h3>
            <div className="space-y-3">
              <ProgressItem label="Classes Completed" current={completedClasses} total={totalClasses} color="bg-success" />
              <ProgressItem label="DLL Linked" current={dllLinked} total={totalClasses} color="bg-primary" />
              <ProgressItem label="Attendance Captured" current={attendanceDone} total={totalClasses} color="bg-info" />
              <ProgressItem label="Reflections Done" current={reflectionsDone} total={totalClasses} color="bg-warning" />
            </div>
          </div>

          <div className="rounded-xl border border-border bg-card p-5">
            <h3 className="text-sm font-semibold mb-3">This Week's Schedule</h3>
            <div className="space-y-2 text-sm">
              {mockClasses.map(c => (
                <div key={c.id} className="flex items-center gap-2 text-xs">
                  <span className="w-20 shrink-0 text-muted-foreground font-mono">{c.time.split("–")[0].trim()}</span>
                  <span className="font-medium">{c.subject}</span>
                  <span className="text-muted-foreground">· {c.section}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-xl border border-primary/20 bg-primary-soft/40 p-5">
            <Sparkles className="size-4 text-primary"/>
            <h3 className="text-sm font-semibold mt-2">Formative Pulse</h3>
            <p className="text-xs text-muted-foreground mt-1">AI gauges class mastery after each lesson. Currently tracking 3 subjects.</p>
            <div className="mt-3 space-y-2 text-xs">
              <div className="flex justify-between"><span>Math 6</span><span className="text-success font-medium">82% mastery</span></div>
              <div className="flex justify-between"><span>Science 6</span><span className="text-warning-foreground font-medium">74% mastery</span></div>
              <div className="flex justify-between"><span>English 6</span><span className="text-primary font-medium">88% mastery</span></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, icon: Icon, color }: { label: string; value: string; icon: typeof CalendarDays; color: string }) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="flex items-center gap-2">
        <div className={cn("size-8 rounded-lg grid place-items-center",
          color === "primary" && "bg-primary/10 text-primary",
          color === "success" && "bg-success/10 text-success",
          color === "info" && "bg-info/10 text-info",
          color === "warning" && "bg-warning/15 text-warning-foreground")}>
          <Icon className="size-4"/>
        </div>
        <div className="text-xs text-muted-foreground">{label}</div>
      </div>
      <div className="mt-2 text-2xl font-display font-semibold">{value}</div>
    </div>
  );
}

function ProgressItem({ label, current, total, color }: { label: string; current: number; total: number; color: string }) {
  const pct = Math.round(current / total * 100);
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span>{label}</span>
        <span className="font-medium">{current}/{total}</span>
      </div>
      <div className="h-1.5 rounded-full bg-muted overflow-hidden">
        <div className={cn("h-full rounded-full transition-all", color)} style={{ width: `${pct}%` }}/>
      </div>
    </div>
  );
}