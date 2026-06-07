import type { ReactNode } from "react";
import { useEffect, useRef, useState } from "react";
import { SidebarNav } from "./sidebar-nav";
import {
  Bell,
  Search,
  Sparkles,
  X,
  Wand2,
  FileText,
  MessageSquare,
  Bot,
  ChevronDown,
  LogOut,
  User as UserIcon,
  Settings as SettingsIcon,
  LifeBuoy,
  GraduationCap,
  Mail,
  School,
  Calendar,
  BookOpen,
  CircleDot,
  Minimize2,
  History,
  Lightbulb,
  Trash2,
  ArrowUp,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

type ChatMessage = {
  id: string;
  role: "assistant" | "user";
  content: string;
  time: string;
};

const QUICK_PROMPTS = [
  { icon: Wand2, label: "Fix errors on this page" },
  { icon: FileText, label: "Generate a report" },
  { icon: MessageSquare, label: "Summarize this page" },
  { icon: Lightbulb, label: "Suggest lesson activities" },
];

const MEMORY_ITEMS = [
  { label: "DLL Math 6 Wk 4", done: true },
  { label: "SF2 Validation", done: true },
  { label: "Grade computing", done: false },
  { label: "Parent letter draft", done: false },
];

function pickReply(input: string): string {
  const q = input.toLowerCase();
  if (q.includes("error") || q.includes("fix"))
    return "Scanned this page — I found 2 inconsistencies in SF2 dates and 1 missing LRN. Want me to auto-correct them?";
  if (q.includes("report"))
    return "I can generate a Weekly Class Performance Report, an At-Risk Student Report, or an SF5 Promotion Report. Which one would you like?";
  if (q.includes("summar"))
    return "This page covers your Grade 6 · Sampaguita class — 42 students, 78% average, with 3 students flagged for follow-up. Top performer: Lian M.";
  if (q.includes("lesson") || q.includes("activity"))
    return "For MELC M6NS-Ia-86, I suggest: (1) a grouping activity on prime/composite numbers, (2) a real-world word problem set, and (3) a 10-item formative check. Shall I draft the DLL section?";
  return "Got it! I'm working on it. In the meantime, you can pin a screen context, attach a DepEd form, or pick a quick action above to keep moving.";
}

function SendIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const [aiOpen, setAiOpen] = useState(false);
  const [aiMinimized, setAiMinimized] = useState(false);
  const [hasInteracted, setHasInteracted] = useState(false);
  const [aiMessage, setAiMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Hi T. Mariel! 👋 I'm your AI teaching assistant. I can help draft lessons, validate DepEd forms, generate reports, and more. What are we working on today?",
      time: "now",
    },
  ]);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  // Close on Escape
  useEffect(() => {
    if (!aiOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setAiOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [aiOpen]);

  // Auto-focus input when panel opens
  useEffect(() => {
    if (aiOpen && !aiMinimized) {
      const t = setTimeout(() => inputRef.current?.focus(), 220);
      return () => clearTimeout(t);
    }
  }, [aiOpen, aiMinimized]);

  // Auto-scroll messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, aiOpen, aiMinimized]);

  const handleOpen = () => {
    setAiOpen(true);
    setAiMinimized(false);
    setHasInteracted(true);
  };

  const handleMinimize = () => {
    setAiMinimized(true);
  };

  const handleRestore = () => {
    setAiMinimized(false);
  };

  const handleSend = () => {
    const text = aiMessage.trim();
    if (!text) return;
    const userMsg: ChatMessage = {
      id: `u-${Date.now()}`,
      role: "user",
      content: text,
      time: "now",
    };
    setMessages((prev) => [...prev, userMsg]);
    setAiMessage("");

    setTimeout(() => {
      const reply: ChatMessage = {
        id: `a-${Date.now()}`,
        role: "assistant",
        content: pickReply(text),
        time: "now",
      };
      setMessages((prev) => [...prev, reply]);
    }, 700);
  };

  const onQuickPrompt = (label: string) => {
    setAiMessage(label);
    setHasInteracted(true);
    requestAnimationFrame(() => inputRef.current?.focus());
  };

  const clearChat = () => {
    setMessages([
      {
        id: "welcome-2",
        role: "assistant",
        content: "New conversation started. How can I help you?",
        time: "now",
      },
    ]);
  };

  return (
    <div className="flex min-h-screen w-full bg-background">
      <SidebarNav />
      <div className="flex-1 flex flex-col min-w-0">
        <header className="sticky top-0 z-30 flex items-center gap-3 h-14 px-4 lg:px-6 border-b border-border bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
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

          {/* Mobile-only compact profile (inline in topbar) */}
          <div className="md:hidden flex items-center gap-1">
            <button
              className="relative size-10 grid place-items-center rounded-full hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring transition-colors"
              aria-label="Notifications"
            >
              <Bell className="size-5 text-muted-foreground" />
              <span className="absolute top-1.5 right-1.5 min-w-[18px] h-[18px] px-1 grid place-items-center rounded-full bg-destructive text-destructive-foreground text-[10px] font-bold ring-2 ring-background">
                3
              </span>
            </button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  aria-label="Open user menu"
                  className="group flex items-center gap-1.5 rounded-full pl-0.5 pr-1.5 py-0.5 hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring transition-colors"
                >
                  <span className="relative">
                    <Avatar className="size-8 ring-1 ring-border shadow-sm">
                      <AvatarImage src="" alt="T. Mariel Reyes" />
                      <AvatarFallback className="bg-gradient-to-br from-primary via-primary/90 to-purple-600 text-primary-foreground text-[11px] font-bold">
                        MR
                      </AvatarFallback>
                    </Avatar>
                    <span
                      className="absolute -bottom-0.5 -right-0.5 size-2.5 rounded-full bg-success ring-2 ring-background"
                      aria-hidden="true"
                    />
                  </span>
                  <ChevronDown
                    className="size-3.5 text-muted-foreground transition-transform duration-200 group-data-[state=open]:rotate-180"
                    aria-hidden="true"
                  />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                align="end"
                sideOffset={8}
                className="w-72 p-0 overflow-hidden rounded-2xl border-border/60 shadow-2xl"
              >
                <div className="relative px-4 pt-4 pb-3 bg-gradient-to-br from-primary/12 via-primary/5 to-purple-500/8">
                  <div className="relative flex items-center gap-3">
                    <div className="relative shrink-0">
                      <Avatar className="size-12 ring-[3px] ring-background shadow-lg">
                        <AvatarImage src="" alt="T. Mariel Reyes" />
                        <AvatarFallback className="bg-gradient-to-br from-primary via-primary/90 to-purple-600 text-primary-foreground text-sm font-bold">
                          MR
                        </AvatarFallback>
                      </Avatar>
                      <span
                        className="absolute -bottom-0.5 -right-0.5 size-3.5 rounded-full bg-success ring-[3px] ring-background"
                        aria-hidden="true"
                      />
                    </div>
                    <div className="min-w-0 flex-1">
                      <h3 className="text-sm font-semibold truncate">T. Mariel Reyes</h3>
                      <p className="text-xs text-muted-foreground truncate">
                        mariel.reyes@deped.gov.ph
                      </p>
                      <span className="mt-1.5 inline-flex items-center gap-1 rounded-full bg-primary/10 text-primary text-[10px] font-medium px-2 py-0.5 ring-1 ring-primary/20">
                        <GraduationCap className="size-3" />
                        Grade 6 · Sampaguita
                      </span>
                    </div>
                  </div>
                </div>
                <div className="p-1.5">
                  <DropdownMenuItem className="cursor-pointer gap-2.5 py-2.5 px-2.5 rounded-lg focus:bg-primary/8">
                    <span className="size-7 rounded-md bg-primary/10 text-primary grid place-items-center">
                      <UserIcon className="size-3.5" />
                    </span>
                    <span className="flex-1 font-medium text-sm">My profile</span>
                  </DropdownMenuItem>
                  <DropdownMenuItem className="cursor-pointer gap-2.5 py-2.5 px-2.5 rounded-lg focus:bg-primary/8">
                    <span className="size-7 rounded-md bg-blue-500/10 text-blue-600 dark:text-blue-400 grid place-items-center">
                      <SettingsIcon className="size-3.5" />
                    </span>
                    <span className="flex-1 font-medium text-sm">Account settings</span>
                  </DropdownMenuItem>
                  <DropdownMenuItem className="cursor-pointer gap-2.5 py-2.5 px-2.5 rounded-lg focus:bg-primary/8">
                    <span className="size-7 rounded-md bg-amber-500/10 text-amber-600 dark:text-amber-400 grid place-items-center">
                      <LifeBuoy className="size-3.5" />
                    </span>
                    <span className="flex-1 font-medium text-sm">Help & support</span>
                  </DropdownMenuItem>
                </div>
                <DropdownMenuSeparator className="my-0" />
                <div className="p-1.5">
                  <DropdownMenuItem className="cursor-pointer gap-2.5 py-2.5 px-2.5 rounded-lg text-destructive focus:text-destructive focus:bg-destructive/10">
                    <span className="size-7 rounded-md bg-destructive/10 grid place-items-center">
                      <LogOut className="size-3.5" />
                    </span>
                    <span className="flex-1 font-medium text-sm">Sign out</span>
                  </DropdownMenuItem>
                </div>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* Top-right cluster: Bell + Profile on md+ screens */}
        <div className="hidden md:flex fixed top-3 right-4 z-50 items-center gap-1.5">
          <button
            className="relative size-11 grid place-items-center rounded-full bg-secondary/60 hover:bg-secondary ring-1 ring-border/40 hover:ring-primary/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring transition-all duration-200"
            aria-label="Notifications"
          >
            <Bell className="size-5 text-foreground" />
            <span className="absolute -top-0.5 -right-0.5 min-w-[20px] h-[20px] px-1.5 grid place-items-center rounded-full bg-destructive text-destructive-foreground text-[11px] font-bold ring-2 ring-background">
              3
            </span>
          </button>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                aria-label="Open user menu"
                className={cn(
                  "group flex items-center gap-1.5 rounded-full pl-0.5 pr-1.5 py-0.5",
                  "bg-secondary/60 hover:bg-secondary",
                  "ring-1 ring-border/40",
                  "hover:ring-primary/30 hover:shadow-[0_8px_24px_rgb(0,0,0,0.08)]",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                  "transition-all duration-200 ease-out",
                )}
              >
                <span className="relative">
                  <span
                    className="absolute inset-0 rounded-full bg-gradient-to-br from-primary via-primary/80 to-purple-500 blur-sm opacity-60 group-hover:opacity-80 transition-opacity"
                    aria-hidden="true"
                  />
                  <Avatar className="relative size-9 ring-2 ring-background shadow-sm">
                    <AvatarImage src="" alt="T. Mariel Reyes" />
                    <AvatarFallback className="bg-gradient-to-br from-primary via-primary/90 to-purple-600 text-primary-foreground text-xs font-bold">
                      MR
                    </AvatarFallback>
                  </Avatar>
                  <span className="absolute -bottom-0.5 -right-0.5 flex">
                    <span
                      className="absolute inline-flex size-2.5 rounded-full bg-success opacity-75 animate-ping"
                      aria-hidden="true"
                    />
                    <span
                      className="relative inline-flex size-2.5 rounded-full bg-success ring-2 ring-background"
                      aria-hidden="true"
                    />
                  </span>
                </span>
                <ChevronDown
                  className="size-3.5 text-muted-foreground transition-transform duration-300 group-data-[state=open]:rotate-180"
                  aria-hidden="true"
                />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              align="end"
              sideOffset={14}
              className="w-80 p-0 overflow-hidden rounded-2xl border-border/60 shadow-2xl"
            >
              <div className="relative px-5 pt-5 pb-4 bg-gradient-to-br from-primary/12 via-primary/5 to-purple-500/8">
                <div
                  className="absolute -top-8 -right-8 size-32 rounded-full bg-primary/15 blur-2xl pointer-events-none"
                  aria-hidden="true"
                />
                <div
                  className="absolute -bottom-6 -left-6 size-24 rounded-full bg-purple-500/10 blur-xl pointer-events-none"
                  aria-hidden="true"
                />

                <div className="relative flex items-start gap-3.5">
                  <div className="relative shrink-0">
                    <span
                      className="absolute inset-0 rounded-full bg-gradient-to-br from-primary to-purple-500 blur-md opacity-50"
                      aria-hidden="true"
                    />
                    <Avatar className="relative size-14 ring-[3px] ring-background shadow-lg">
                      <AvatarImage src="" alt="T. Mariel Reyes" />
                      <AvatarFallback className="bg-gradient-to-br from-primary via-primary/90 to-purple-600 text-primary-foreground text-base font-bold">
                        MR
                      </AvatarFallback>
                    </Avatar>
                    <span
                      className="absolute -bottom-0.5 -right-0.5 size-4 rounded-full bg-success ring-[3px] ring-background"
                      aria-hidden="true"
                    />
                  </div>

                  <div className="min-w-0 flex-1 pt-0.5">
                    <div className="flex items-center gap-2">
                      <h3 className="text-[15px] font-semibold text-foreground truncate">
                        T. Mariel Reyes
                      </h3>
                    </div>
                    <div className="mt-0.5 flex items-center gap-1 text-xs text-muted-foreground">
                      <Mail className="size-3 shrink-0" />
                      <span className="truncate">mariel.reyes@deped.gov.ph</span>
                    </div>
                    <div className="mt-2 flex items-center gap-1.5 flex-wrap">
                      <span className="inline-flex items-center gap-1 rounded-full bg-success/12 text-success text-[10.5px] font-medium px-2 py-0.5 ring-1 ring-success/20">
                        <CircleDot className="size-2.5" />
                        Online
                      </span>
                      <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 text-primary text-[10.5px] font-medium px-2 py-0.5 ring-1 ring-primary/20">
                        <GraduationCap className="size-3" />
                        Grade 6 · Sampaguita
                      </span>
                    </div>
                  </div>
                </div>

                {/* Quick stats row */}
                <div className="relative mt-4 grid grid-cols-3 gap-2 px-1">
                  <div className="flex flex-col items-center justify-center rounded-lg bg-background/60 backdrop-blur-sm ring-1 ring-border/40 py-2">
                    <BookOpen className="size-3.5 text-muted-foreground mb-0.5" />
                    <span className="text-sm font-semibold leading-none">42</span>
                    <span className="text-[10px] text-muted-foreground mt-0.5">Students</span>
                  </div>
                  <div className="flex flex-col items-center justify-center rounded-lg bg-background/60 backdrop-blur-sm ring-1 ring-border/40 py-2">
                    <Calendar className="size-3.5 text-muted-foreground mb-0.5" />
                    <span className="text-sm font-semibold leading-none">Wk 4</span>
                    <span className="text-[10px] text-muted-foreground mt-0.5">This week</span>
                  </div>
                  <div className="flex flex-col items-center justify-center rounded-lg bg-background/60 backdrop-blur-sm ring-1 ring-border/40 py-2">
                    <School className="size-3.5 text-muted-foreground mb-0.5" />
                    <span className="text-sm font-semibold leading-none">S.Y.</span>
                    <span className="text-[10px] text-muted-foreground mt-0.5">2025–2026</span>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="p-1.5">
                <DropdownMenuItem className="cursor-pointer gap-2.5 py-2.5 px-2.5 rounded-lg focus:bg-primary/8">
                  <span className="size-7 rounded-md bg-primary/10 text-primary grid place-items-center">
                    <UserIcon className="size-3.5" />
                  </span>
                  <span className="flex-1 font-medium text-sm">My profile</span>
                  <DropdownMenuShortcut>⇧⌘P</DropdownMenuShortcut>
                </DropdownMenuItem>
                <DropdownMenuItem className="cursor-pointer gap-2.5 py-2.5 px-2.5 rounded-lg focus:bg-primary/8">
                  <span className="size-7 rounded-md bg-blue-500/10 text-blue-600 dark:text-blue-400 grid place-items-center">
                    <SettingsIcon className="size-3.5" />
                  </span>
                  <span className="flex-1 font-medium text-sm">Account settings</span>
                  <DropdownMenuShortcut>⌘S</DropdownMenuShortcut>
                </DropdownMenuItem>
                <DropdownMenuItem className="cursor-pointer gap-2.5 py-2.5 px-2.5 rounded-lg focus:bg-primary/8">
                  <span className="size-7 rounded-md bg-amber-500/10 text-amber-600 dark:text-amber-400 grid place-items-center">
                    <LifeBuoy className="size-3.5" />
                  </span>
                  <span className="flex-1 font-medium text-sm">Help & support</span>
                </DropdownMenuItem>
              </div>

              <DropdownMenuSeparator className="my-0" />

              <div className="p-1.5">
                <DropdownMenuItem className="cursor-pointer gap-2.5 py-2.5 px-2.5 rounded-lg text-destructive focus:text-destructive focus:bg-destructive/10">
                  <span className="size-7 rounded-md bg-destructive/10 grid place-items-center">
                    <LogOut className="size-3.5" />
                  </span>
                  <span className="flex-1 font-medium text-sm">Sign out</span>
                  <DropdownMenuShortcut className="text-destructive/60">⇧⌘Q</DropdownMenuShortcut>
                </DropdownMenuItem>
              </div>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Main content area */}
        <main className="flex-1 min-w-0">{children}</main>
      </div>

      {/* ============================================================== */}
      {/*  AI ASSISTANT — Floating bottom-right (industry-standard)        */}
      {/* ============================================================== */}

      {/* Backdrop (visible only on mobile, when open) */}
      {aiOpen && !aiMinimized && (
        <button
          aria-label="Close AI Assistant"
          onClick={() => setAiOpen(false)}
          className="md:hidden fixed inset-0 z-40 bg-foreground/40 backdrop-blur-sm animate-in fade-in duration-200"
        />
      )}

      {/* Floating Chat Panel (positioned above the FAB) */}
      <div
        role="dialog"
        aria-label="AI Assistant"
        aria-hidden={!aiOpen}
        className={cn(
          "fixed z-50 flex flex-col overflow-hidden bg-card border border-border shadow-2xl",
          // Facebook-Messenger style: anchored to bottom-right, compact
          "bottom-24 right-4 sm:right-6",
          "w-[calc(100vw-2rem)] sm:w-[340px]",
          "h-[min(520px,calc(100vh-7rem))]",
          "rounded-2xl",
          "transition-all duration-200 ease-out origin-bottom-right",
          aiOpen && !aiMinimized
            ? "opacity-100 translate-y-0 scale-100 pointer-events-auto"
            : "opacity-0 translate-y-3 scale-95 pointer-events-none",
        )}
      >
        {/* Header */}
        <div className="relative px-4 pt-4 pb-3 bg-gradient-to-br from-primary via-primary/95 to-purple-600 text-primary-foreground">
          <div
            className="absolute -top-6 -right-6 size-24 rounded-full bg-white/10 blur-2xl pointer-events-none"
            aria-hidden="true"
          />
          <div
            className="absolute -bottom-4 -left-4 size-20 rounded-full bg-white/10 blur-xl pointer-events-none"
            aria-hidden="true"
          />

          <div className="relative flex items-start gap-3">
            <div className="relative shrink-0">
              <div className="size-10 rounded-xl bg-white/15 backdrop-blur-sm grid place-items-center ring-1 ring-white/20 shadow-lg">
                <Sparkles className="size-5" />
              </div>
              <span
                className="absolute -bottom-0.5 -right-0.5 size-3 rounded-full bg-success ring-2 ring-primary"
                aria-hidden="true"
              />
            </div>
            <div className="min-w-0 flex-1">
              <h2 className="text-sm font-semibold leading-tight">TeacherOS AI</h2>
              <p className="text-[11px] text-primary-foreground/80 mt-0.5 flex items-center gap-1.5">
                <span className="size-1.5 rounded-full bg-success animate-pulse" />
                Online · Context: Lesson Planning
              </p>
            </div>
            <div className="flex items-center gap-0.5">
              <button
                onClick={handleMinimize}
                aria-label="Minimize"
                className="size-8 grid place-items-center rounded-lg hover:bg-white/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/40 transition-colors"
              >
                <Minimize2 className="size-4" />
              </button>
              <button
                onClick={() => setAiOpen(false)}
                aria-label="Close"
                className="size-8 grid place-items-center rounded-lg hover:bg-white/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/40 transition-colors"
              >
                <X className="size-4" />
              </button>
            </div>
          </div>

          {/* Context chip */}
          <div className="relative mt-3 flex items-center gap-1.5">
            <button className="inline-flex items-center gap-1.5 rounded-full bg-white/15 hover:bg-white/25 backdrop-blur-sm text-[11px] font-medium pl-2 pr-2.5 py-1 ring-1 ring-white/20 transition-colors">
              <Bot className="size-3" />
              Use this screen's data
            </button>
            <button
              onClick={clearChat}
              aria-label="Clear conversation"
              className="size-7 grid place-items-center rounded-full hover:bg-white/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/40 transition-colors"
            >
              <Trash2 className="size-3.5" />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto px-4 py-4 space-y-3 bg-gradient-to-b from-muted/30 to-background"
        >
          {messages.map((m) => (
            <div
              key={m.id}
              className={cn(
                "flex gap-2 animate-in fade-in slide-in-from-bottom-1 duration-200",
                m.role === "user" ? "flex-row-reverse" : "flex-row",
              )}
            >
              {m.role === "assistant" ? (
                <div className="size-7 shrink-0 rounded-lg bg-gradient-primary grid place-items-center shadow-sm">
                  <Sparkles className="size-3.5 text-primary-foreground" />
                </div>
              ) : (
                <div className="size-7 shrink-0 rounded-lg bg-secondary text-secondary-foreground grid place-items-center text-[10px] font-bold">
                  MR
                </div>
              )}
              <div
                className={cn(
                  "max-w-[78%] rounded-2xl px-3 py-2 text-[13px] leading-relaxed shadow-sm",
                  m.role === "assistant"
                    ? "bg-card border border-border rounded-tl-sm"
                    : "bg-primary text-primary-foreground rounded-tr-sm",
                )}
              >
                {m.content}
              </div>
            </div>
          ))}
        </div>

        {/* Quick actions (only show when not yet deeply chatting) */}
        {messages.length <= 1 && (
          <div className="px-4 pb-3 pt-1 border-t border-border bg-background">
            <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              Try a quick action
            </p>
            <div className="grid grid-cols-2 gap-1.5">
              {QUICK_PROMPTS.map((p) => {
                const Icon = p.icon;
                return (
                  <button
                    key={p.label}
                    onClick={() => onQuickPrompt(p.label)}
                    className="group flex items-center gap-2 rounded-lg border border-border bg-card hover:bg-primary/5 hover:border-primary/30 px-2.5 py-2 text-left text-[12px] font-medium text-foreground transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/30"
                  >
                    <span className="size-6 rounded-md bg-primary/10 text-primary grid place-items-center group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                      <Icon className="size-3" />
                    </span>
                    <span className="truncate">{p.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Memory hint (collapsed, when chatting) */}
        {messages.length > 1 && (
          <div className="px-4 py-2 border-t border-border bg-muted/30 flex items-center gap-2">
            <History className="size-3.5 text-muted-foreground shrink-0" />
            <span className="text-[11px] text-muted-foreground truncate">
              {MEMORY_ITEMS.filter((m) => m.done).length} of {MEMORY_ITEMS.length} recent tasks
              complete
            </span>
          </div>
        )}

        {/* Composer */}
        <div className="p-3 border-t border-border bg-background">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-end gap-2"
          >
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                value={aiMessage}
                onChange={(e) => setAiMessage(e.target.value)}
                placeholder="Ask AI anything…"
                className="w-full h-10 pl-3 pr-3 rounded-xl bg-muted/60 border border-transparent focus:bg-background focus:border-input focus:outline-none focus:ring-2 focus:ring-ring/30 text-sm placeholder:text-muted-foreground"
              />
            </div>
            <Button
              type="submit"
              size="icon"
              disabled={!aiMessage.trim()}
              className="size-10 rounded-xl shadow-sm shrink-0"
              aria-label="Send message"
            >
              <ArrowUp className="size-4" />
            </Button>
          </form>
          <p className="text-[10px] text-muted-foreground mt-1.5 text-center">
            AI responses are context-aware · Autosaved
          </p>
        </div>
      </div>

      {/* ============================================================== */}
      {/*  FAB — Floating Action Button (always visible)                  */}
      {/*  Industry-standard placement: bottom-right, above content       */}
      {/* ============================================================== */}

      {/* Minimized peek — shown when chat is open but minimized */}
      {aiOpen && aiMinimized && (
        <button
          onClick={handleRestore}
          className="fixed bottom-6 right-4 sm:right-6 z-50 group flex items-center gap-2 pl-3 pr-4 py-3 rounded-full bg-gradient-to-br from-primary via-primary to-purple-600 text-primary-foreground shadow-glow hover:shadow-2xl hover:scale-[1.02] active:scale-95 transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          aria-label="Restore AI Assistant"
        >
          <span className="relative size-7 rounded-lg bg-white/20 grid place-items-center">
            <Sparkles className="size-4" />
            <span
              className="absolute -top-0.5 -right-0.5 size-2 rounded-full bg-success ring-2 ring-primary"
              aria-hidden="true"
            />
          </span>
          <span className="text-sm font-semibold">AI Assistant</span>
          <span className="text-[10px] text-primary-foreground/80 hidden sm:inline">
            Tap to expand
          </span>
        </button>
      )}

      {/* Default FAB — circular floating button */}
      {!aiOpen && (
        <div className="fixed bottom-6 right-4 sm:right-6 z-50 flex flex-col items-end gap-2">
          {/* Tooltip / label, visible on hover (desktop only) */}
          <div className="hidden sm:flex items-center gap-1.5 rounded-full bg-foreground text-background px-3 py-1.5 text-xs font-medium shadow-elegant opacity-0 -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-200 pointer-events-none">
            <Bot className="size-3" />
            <span>Ask TeacherOS AI</span>
          </div>

          {/* The button itself */}
          <button
            onClick={handleOpen}
            aria-label="Open AI Assistant"
            className="group relative size-14 rounded-full bg-gradient-to-br from-primary via-primary to-purple-600 text-primary-foreground shadow-glow hover:shadow-2xl hover:scale-105 active:scale-95 transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            {/* Attention pulse — only when not yet interacted with */}
            {!hasInteracted && (
              <>
                <span
                  className="absolute inset-0 rounded-full bg-primary opacity-60 animate-ping"
                  aria-hidden="true"
                />
                <span
                  className="absolute -inset-1 rounded-full bg-primary/30 blur-md animate-pulse"
                  aria-hidden="true"
                />
              </>
            )}

            {/* Gradient highlight on hover */}
            <span
              className="absolute inset-0 rounded-full bg-gradient-to-tr from-white/0 via-white/20 to-white/0 opacity-0 group-hover:opacity-100 transition-opacity"
              aria-hidden="true"
            />

            {/* Icon */}
            <Sparkles className="relative size-6 mx-auto" />

            {/* Online indicator dot */}
            <span
              className="absolute top-1.5 right-1.5 size-2.5 rounded-full bg-success ring-2 ring-primary"
              aria-hidden="true"
            />
          </button>
        </div>
      )}
    </div>
  );
}
