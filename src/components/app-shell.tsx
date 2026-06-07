import type { ReactNode } from "react";
import { SidebarNav } from "./sidebar-nav";
import { Bell, Search, Sparkles } from "lucide-react";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen w-full bg-background">
      <SidebarNav />
      <div className="flex-1 flex flex-col min-w-0">
        <header className="sticky top-0 z-30 flex items-center gap-3 h-14 px-4 lg:px-8 border-b border-border bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="lg:hidden flex items-center gap-2">
            <div className="size-7 rounded-md bg-gradient-primary grid place-items-center">
              <Sparkles className="size-4 text-primary-foreground" />
            </div>
            <span className="font-display font-semibold">TeacherOS</span>
          </div>

          <div className="flex-1 max-w-xl ml-auto lg:ml-0">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
              <input
                placeholder="Search students, lessons, forms, MELC codes…"
                className="w-full h-9 pl-9 pr-3 rounded-md bg-muted/60 border border-transparent focus:bg-background focus:border-input focus:outline-none focus:ring-2 focus:ring-ring/30 text-sm"
              />
            </div>
          </div>

          <button className="relative size-9 grid place-items-center rounded-md hover:bg-muted">
            <Bell className="size-4 text-muted-foreground" />
            <span className="absolute top-2 right-2 size-1.5 rounded-full bg-destructive" />
          </button>
          <div className="hidden sm:flex items-center gap-2.5 pl-2 border-l border-border ml-1">
            <div className="size-8 rounded-full bg-primary text-primary-foreground grid place-items-center text-xs font-semibold">MR</div>
            <div className="leading-tight text-xs">
              <div className="font-medium">T. Mariel Reyes</div>
              <div className="text-muted-foreground">Grade 6 · Sampaguita</div>
            </div>
          </div>
        </header>

        <main className="flex-1 min-w-0">{children}</main>
      </div>
    </div>
  );
}
