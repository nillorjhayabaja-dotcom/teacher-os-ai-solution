import { Link } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/page-header";
import { ArrowRight, Sparkles, type LucideIcon } from "lucide-react";

export function ModulePreview({
  eyebrow, title, description, steps, icon: Icon, primaryLink = "/agents",
}: {
  eyebrow: string;
  title: string;
  description: string;
  steps: { title: string; desc: string }[];
  icon: LucideIcon;
  primaryLink?: string;
}) {
  return (
    <div className="px-4 lg:px-8 py-6 lg:py-8 max-w-[1600px] mx-auto space-y-6">
      <PageHeader
        eyebrow={eyebrow}
        title={title}
        description={description}
        actions={
          <Link to={primaryLink as string}>
            <Button className="gap-2"><Sparkles className="size-4"/>Open AI Agent</Button>
          </Link>
        }
      />

      <div className="rounded-xl border border-primary/20 bg-gradient-to-br from-primary-soft to-card p-6 lg:p-10">
        <div className="flex items-center gap-3">
          <div className="size-12 rounded-xl bg-gradient-primary grid place-items-center shadow-glow">
            <Icon className="size-6 text-primary-foreground"/>
          </div>
          <div>
            <div className="text-sm font-semibold text-primary">Workflow preview</div>
            <div className="text-xs text-muted-foreground">This pipeline is scaffolded — full editor lands in the next release.</div>
          </div>
        </div>

        <div className="mt-8 grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {steps.map((s, i) => (
            <div key={s.title} className="rounded-lg border border-border bg-card p-4">
              <div className="flex items-center gap-2">
                <span className="size-6 rounded-full bg-primary/10 text-primary grid place-items-center text-xs font-semibold">{i+1}</span>
                <span className="font-medium text-sm">{s.title}</span>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">{s.desc}</p>
            </div>
          ))}
        </div>

        <div className="mt-6 flex items-center gap-2 text-sm text-muted-foreground">
          <Link to={"/" as string} className="inline-flex items-center gap-1 text-primary font-medium hover:underline">
            Back to Dashboard <ArrowRight className="size-3"/>
          </Link>
        </div>
      </div>
    </div>
  );
}
