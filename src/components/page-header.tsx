import type { ReactNode } from "react";

export function PageHeader({
  eyebrow, title, description, actions,
}: { eyebrow?: string; title: string; description?: string; actions?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4 pb-6 border-b border-border">
      <div className="min-w-0">
        {eyebrow && (
          <div className="text-[11px] uppercase tracking-wider font-semibold text-primary mb-1.5">
            {eyebrow}
          </div>
        )}
        <h1 className="text-2xl lg:text-3xl font-display font-semibold text-foreground">{title}</h1>
        {description && <p className="mt-2 text-sm text-muted-foreground max-w-2xl">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}
