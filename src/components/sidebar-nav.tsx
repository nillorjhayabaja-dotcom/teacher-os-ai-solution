import { Link, useRouterState } from "@tanstack/react-router";
import {
  Home, CalendarDays, BookOpen, Calculator, FileText, Users,
  MessageSquare, BarChart3, School, Bot, Settings, Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

type NavItem = {
  to: string;
  label: string;
  icon: typeof Home;
  badge?: string;
  accent?: boolean;
};

const nav: NavItem[] = [
  { to: "/", label: "Dashboard", icon: Home },
  { to: "/teaching", label: "Teaching Workflow", icon: CalendarDays },
  { to: "/lesson-planning", label: "Lesson Planning", icon: BookOpen },
  { to: "/grading", label: "Grading Cycle", icon: Calculator },
  { to: "/forms", label: "School Forms", icon: FileText, badge: "SF1–SF10" },
  { to: "/students", label: "Student Intelligence", icon: Users },
  { to: "/parents", label: "Parent Comms", icon: MessageSquare },
  { to: "/reports", label: "Reports & Compliance", icon: BarChart3 },
  { to: "/programs", label: "School Programs", icon: School },
  { to: "/agents", label: "AI Agent Workspace", icon: Bot, accent: true },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function SidebarNav() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <aside className="hidden lg:flex flex-col w-64 shrink-0 h-screen sticky top-0 border-r border-sidebar-border bg-sidebar text-sidebar-foreground">
      <div className="px-5 py-5 border-b border-sidebar-border">
        <Link to="/" className="flex items-center gap-2.5">
          <div className="size-9 rounded-lg bg-gradient-primary grid place-items-center shadow-glow">
            <Sparkles className="size-5 text-primary-foreground" />
          </div>
          <div className="leading-tight">
            <div className="font-display font-semibold text-base">TeacherOS</div>
            <div className="text-[11px] text-muted-foreground">DepEd · Aligned</div>
          </div>
        </Link>
      </div>

      <nav className="flex-1 overflow-y-auto p-3 space-y-0.5">
        {nav.map(({ to, label, icon: Icon, badge, accent }) => {
          const active = to === "/" ? pathname === "/" : pathname.startsWith(to);
          return (
            <Link
              key={to}
              to={to}
              className={cn(
                "group flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                  : "text-sidebar-foreground/80 hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground",
                accent && !active && "text-primary",
              )}
            >
              <Icon className={cn("size-4 shrink-0", active ? "text-primary" : "")} />
              <span className="flex-1 truncate">{label}</span>
              {badge && (
                <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-primary/10 text-primary">
                  {badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      <div className="m-3 rounded-lg border border-sidebar-border bg-card p-3">
        <div className="flex items-center gap-2 text-xs font-medium text-foreground">
          <div className="size-1.5 rounded-full bg-success animate-pulse" />
          AI Assistant active
        </div>
        <p className="mt-1.5 text-[11px] text-muted-foreground leading-relaxed">
          6 agents online. Context-aware suggestions on every screen.
        </p>
      </div>
    </aside>
  );
}
