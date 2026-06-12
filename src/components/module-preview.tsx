// ============================================================
// TeacherOS — Module Preview Component
// ============================================================
import { cn } from "@/lib/utils";
import { Sparkles, ArrowRight, type LucideIcon } from "lucide-react";

interface ModulePreviewProps {
  icon: LucideIcon;
  title: string;
  description: string;
  status?: "active" | "coming-soon" | "maintenance";
  href?: string;
  accent?: boolean;
  badge?: string;
  onClick?: () => void;
}

export function ModulePreview({
  icon: Icon,
  title,
  description,
  status = "active",
  accent,
  badge,
  onClick,
}: ModulePreviewProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "group relative rounded-xl border p-5 text-left transition-all w-full",
        accent
          ? "border-primary/30 bg-gradient-to-br from-primary-soft to-card hover:border-primary"
          : "border-border bg-card hover:border-primary/50 hover:shadow-elegant",
        status === "coming-soon" && "opacity-60 pointer-events-none",
        status === "maintenance" && "opacity-70",
      )}
    >
      {badge && (
        <span className="absolute top-3 right-3 text-[10px] font-medium px-1.5 py-0.5 rounded bg-primary/10 text-primary">
          {badge}
        </span>
      )}

      <div
        className={cn(
          "size-10 rounded-lg grid place-items-center mb-3",
          accent ? "bg-gradient-primary text-primary-foreground" : "bg-primary/10 text-primary",
        )}
      >
        <Icon className="size-5" />
      </div>

      <h3 className="font-semibold text-sm text-foreground">{title}</h3>
      <p className="mt-1 text-xs text-muted-foreground leading-relaxed">{description}</p>

      {status === "active" && (
        <div className="mt-3 flex items-center gap-1 text-[11px] font-medium text-primary group-hover:gap-2 transition-all">
          Open module <ArrowRight className="size-3" />
        </div>
      )}

      {status === "coming-soon" && (
        <div className="mt-3 flex items-center gap-1 text-[11px] text-muted-foreground">
          <Sparkles className="size-3" /> Coming soon
        </div>
      )}
    </button>
  );
}