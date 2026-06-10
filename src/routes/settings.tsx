import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/settings")({
  head: () => ({ meta: [{ title: "Settings · TeacherOS" }] }),
  component: SettingsPage,
});

function SettingsPage() {
  return (
    <div className="px-4 lg:px-8 py-6 lg:py-8 max-w-[1200px] mx-auto space-y-6">
      <PageHeader
        eyebrow="Settings"
        title="Workspace & teacher profile"
        description="Configure your school, sections, AI preferences, and offline behavior."
      />

      <div className="grid lg:grid-cols-2 gap-6">
        <Section title="Teacher profile">
          <Row label="Name" value="Mariel Reyes" />
          <Row label="Position" value="Teacher I" />
          <Row label="DepEd ID" value="0023-4587-201" />
          <Row label="School" value="Sampaloc Elementary School" />
          <Row label="Division" value="Bulacan" />
        </Section>

        <Section title="Sections & subjects">
          <Row label="Advisory" value="Grade 6 – Sampaguita" />
          <Row label="Subjects" value="Math 6, Science 6, English 6" />
          <Row label="Co-teachers" value="3 linked" />
        </Section>

        <Section title="AI preferences">
          <Row label="Default language" value="English + Tagalog" />
          <Row label="Auto-generate DLL on Sunday" value="Enabled" />
          <Row label="Risk scan frequency" value="Daily 6:00 AM" />
        </Section>

        <Section title="Offline & sync">
          <Row label="Cache lessons offline" value="On" />
          <Row label="Cache forms offline" value="On" />
          <Row label="Last sync" value="2 min ago" />
          <div className="pt-2">
            <Button size="sm" variant="outline">
              Force sync
            </Button>
          </div>
        </Section>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <h2 className="font-semibold mb-3">{title}</h2>
      <div className="space-y-2 text-sm">{children}</div>
    </div>
  );
}
function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-border last:border-0 pb-2 last:pb-0">
      <span className="text-muted-foreground text-xs">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
