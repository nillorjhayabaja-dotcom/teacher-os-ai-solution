import { cn } from "@/lib/utils";
import { Check } from "lucide-react";

export type Step = { id: number; title: string; desc?: string };

export function WorkflowStepper({
  steps,
  current,
  onSelect,
}: {
  steps: Step[];
  current: number;
  onSelect?: (n: number) => void;
}) {
  return (
    <ol className="flex flex-wrap gap-2">
      {steps.map((s) => {
        const done = s.id < current;
        const active = s.id === current;
        return (
          <li key={s.id} className="flex-1 min-w-[180px]">
            <button
              onClick={() => onSelect?.(s.id)}
              className={cn(
                "w-full text-left rounded-lg border p-3 transition-all",
                active && "border-primary bg-primary-soft shadow-elegant",
                done && "border-success/30 bg-success/5",
                !active && !done && "border-border bg-card hover:border-input",
              )}
            >
              <div className="flex items-center gap-2">
                <span
                  className={cn(
                    "size-6 rounded-full grid place-items-center text-[11px] font-semibold",
                    active && "bg-primary text-primary-foreground",
                    done && "bg-success text-success-foreground",
                    !active && !done && "bg-muted text-muted-foreground",
                  )}
                >
                  {done ? <Check className="size-3.5" /> : s.id}
                </span>
                <span className={cn("text-sm font-medium", active && "text-primary")}>
                  {s.title}
                </span>
              </div>
              {s.desc && <p className="mt-1 text-xs text-muted-foreground pl-8">{s.desc}</p>}
            </button>
          </li>
        );
      })}
    </ol>
  );
}
