import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { PageHeader } from "@/components/page-header";
import { WorkflowStepper } from "@/components/workflow-stepper";
import { Button } from "@/components/ui/button";
import { mockStudents, mockParentLogs } from "@/lib/mock-data";
import {
  MessageSquare,
  Send,
  Sparkles,
  Check,
  ChevronRight,
  User,
  History,
  Edit,
  Smartphone,
  MessageCircle,
  FileText,
  RefreshCw,
} from "lucide-react";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/parents")({
  head: () => ({
    meta: [
      { title: "Parent Communication · TeacherOS" },
      {
        name: "description",
        content:
          "AI-drafted parent messages in Tagalog/English, with SMS/Messenger preview and communication history.",
      },
    ],
  }),
  component: ParentsPage,
});

const steps = [
  { id: 1, title: "Select Student", desc: "Choose learner" },
  { id: 2, title: "Select Issue", desc: "Absence, grade, etc." },
  { id: 3, title: "AI Draft", desc: "Auto-generated message" },
  { id: 4, title: "Preview", desc: "SMS/Messenger view" },
  { id: 5, title: "Send", desc: "Send or schedule" },
  { id: 6, title: "History", desc: "Communication log" },
];

const issues = [
  {
    id: "absence",
    label: "Absence",
    icon: "🚫",
    sub: ["1 day", "2-3 consecutive", "4+ days", "Frequent tardiness"],
  },
  {
    id: "grade",
    label: "Grade Drop",
    icon: "📉",
    sub: ["Below 75 warning", "Significant drop", "Missing requirements"],
  },
  {
    id: "behavior",
    label: "Behavior",
    icon: "⚠️",
    sub: ["Class disruption", "Peer conflict", "Disrespect"],
  },
  {
    id: "achievement",
    label: "Achievement",
    icon: "🏆",
    sub: ["Academic award", "Improvement notice", "Leadership role"],
  },
];

const sampleMessages: Record<string, string> = {
  absence:
    "Mahal naming Ginoong/Ginang Dela Cruz,\n\nKami po ay sumusulat upang ipaalam na ang inyong anak na si Juan ay hindi po pumasok noong Setyembre 23, 24, at 25. Ito ay kanyang ika-3, 4, at 5 na pagliban ngayong buwan.\n\nMaaari po ba kayong makipagkita sa amin para sa isang conference?\n\nSalamat po,\nT. Mariel Reyes\nSampaloc Elementary School",
  grade:
    "Mahal naming Ginoong/Ginang Dela Cruz,\n\nIkinagagalak naming ipaalam na ang inyong anak ay may makabuluhang pagbaba sa kanyang grado sa Mathematics ngayong Quarter 1 — mula 89% noong nakaraang quarter ay naging 78%.\n\nNais po naming magkaroon ng remediation session tuwing Biyernes pagkatapos ng klase.\n\nSalamat po,\nT. Mariel Reyes",
  behavior:
    "Mahal naming Ginoong/Ginang Dela Cruz,\n\nSumusulat po kami upang ipaalam ang ilang alalahanin tungkol sa pag-uugali ng inyong anak sa klase.\n\nMaaari po ba tayong mag-set ng meeting para pag-usapan ito?\n\nSalamat po,\nT. Mariel Reyes",
  achievement:
    "Mahal naming Ginoong/Ginang Dela Cruz,\n\nIkinagagalak naming ipaalam na ang inyong anak na si Juan ay nagpakita ng kahanga-hangang pag-unlad sa Mathematics ngayong quarter!\n\nBinabati namin siya at umaasa na magpapatuloy ang kanyang kasipagan.\n\nSalamat po,\nT. Mariel Reyes",
};

function ParentsPage() {
  const [step, setStep] = useState(1);
  const [selectedStudent, setSelectedStudent] = useState(mockStudents[0]);
  const [selectedIssue, setSelectedIssue] = useState("absence");
  const [selectedSubIssue, setSelectedSubIssue] = useState("");
  const [language, setLanguage] = useState<"Tagalog" | "English">("Tagalog");
  const [tone, setTone] = useState<"Formal" | "Casual">("Formal");
  const [previewMode, setPreviewMode] = useState<"SMS" | "Messenger" | "Letter">("SMS");
  const [draftMessage, setDraftMessage] = useState(sampleMessages.absence);
  const [generating, setGenerating] = useState(false);
  const [sendStatus, setSendStatus] = useState<"idle" | "sending" | "sent">("idle");

  const studentLogs = mockParentLogs.filter((l) => l.studentId === selectedStudent.id);

  function generateMessage() {
    setGenerating(true);
    setTimeout(() => {
      setDraftMessage(sampleMessages[selectedIssue] || sampleMessages.absence);
      setGenerating(false);
      setStep(4);
    }, 800);
  }

  function handleSend() {
    setSendStatus("sending");
    setTimeout(() => {
      setSendStatus("sent");
      setStep(6);
    }, 1000);
  }

  return (
    <div className="px-4 lg:px-8 py-6 lg:py-8 max-w-[1600px] mx-auto space-y-6">
      <PageHeader
        eyebrow="Parent Communication"
        title="AI-Powered Parent Messaging"
        description="Draft, preview, and send Tagalog/English messages to parents — SMS, Messenger, or printable letter."
        actions={
          <Button variant="outline" className="gap-2">
            <History className="size-4" />
            View All Logs
          </Button>
        }
      />

      <WorkflowStepper steps={steps} current={step} onSelect={setStep} />

      {/* Step 1: Select Student */}
      {step === 1 && (
        <div className="rounded-xl border border-border bg-card p-6">
          <h2 className="font-semibold mb-4">Step 1 · Select Student</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2 max-h-[400px] overflow-y-auto">
            {mockStudents.slice(0, 20).map((s) => (
              <button
                key={s.id}
                onClick={() => {
                  setSelectedStudent(s);
                  setStep(2);
                }}
                className={cn(
                  "flex items-center gap-3 p-3 rounded-lg border text-left transition-all hover:border-primary",
                  selectedStudent.id === s.id
                    ? "border-primary bg-primary-soft"
                    : "border-border bg-card",
                )}
              >
                <div
                  className={cn(
                    "size-9 rounded-full grid place-items-center text-xs font-semibold",
                    s.risk === "high"
                      ? "bg-destructive/10 text-destructive"
                      : s.risk === "medium"
                        ? "bg-warning/15 text-warning-foreground"
                        : "bg-success/10 text-success",
                  )}
                >
                  {s.name.split(",")[0].slice(0, 2).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">{s.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {s.section} · Avg {s.averageGrade}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Step 2: Select Issue */}
      {step === 2 && (
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 rounded-xl border border-border bg-card p-6">
            <h2 className="font-semibold mb-1">Step 2 · Select Issue</h2>
            <p className="text-sm text-muted-foreground mb-5">
              Student: <strong>{selectedStudent.name}</strong> · Avg {selectedStudent.averageGrade}{" "}
              · Att {selectedStudent.attendance}%
            </p>
            <div className="grid sm:grid-cols-2 gap-3">
              {issues.map((issue) => (
                <div key={issue.id}>
                  <button
                    onClick={() => setSelectedIssue(issue.id)}
                    className={cn(
                      "w-full flex items-center gap-3 p-4 rounded-lg border text-left transition-all",
                      selectedIssue === issue.id
                        ? "border-primary bg-primary-soft"
                        : "border-border bg-card hover:border-input",
                    )}
                  >
                    <span className="text-xl">{issue.icon}</span>
                    <span className="text-sm font-medium">{issue.label}</span>
                  </button>
                  {selectedIssue === issue.id && (
                    <div className="mt-2 ml-4 space-y-1">
                      {issue.sub.map((sub) => (
                        <button
                          key={sub}
                          onClick={() => setSelectedSubIssue(sub)}
                          className={cn(
                            "block w-full text-left text-xs px-3 py-1.5 rounded hover:bg-muted/40",
                            selectedSubIssue === sub
                              ? "bg-primary-soft text-primary font-medium"
                              : "text-muted-foreground",
                          )}
                        >
                          {sub}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
            <div className="flex justify-between mt-6">
              <Button variant="outline" onClick={() => setStep(1)}>
                ← Back
              </Button>
              <Button
                onClick={() => {
                  setStep(3);
                  generateMessage();
                }}
                className="gap-2"
              >
                Generate AI Message <Sparkles className="size-4" />
              </Button>
            </div>
          </div>
          <div className="rounded-xl border border-primary/20 bg-primary-soft/40 p-5">
            <div className="flex items-center gap-2 text-sm font-semibold text-primary">
              <Sparkles className="size-4" /> AI Context
            </div>
            <ul className="mt-3 space-y-2 text-xs text-muted-foreground">
              <li>• Messages generated in Tagalog (formal register)</li>
              <li>• English version also available</li>
              <li>• Tone adjusts based on issue severity</li>
              <li>• Guardian name auto-filled from records</li>
            </ul>
          </div>
        </div>
      )}

      {/* Step 3: AI Draft - Loading */}
      {step === 3 && generating && (
        <div className="rounded-xl border border-border bg-card p-8 text-center">
          <Sparkles className="size-8 text-primary mx-auto animate-pulse" />
          <h2 className="font-semibold mt-4">AI is drafting your message…</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Analyzing student context and generating appropriate tone…
          </p>
          <div className="mt-6 max-w-md mx-auto h-2 rounded-full bg-muted overflow-hidden">
            <div className="h-full bg-gradient-primary animate-pulse" style={{ width: "70%" }} />
          </div>
        </div>
      )}

      {/* Step 4: Preview */}
      {step === 4 && (
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <div className="rounded-xl border border-border bg-card p-6">
              <h2 className="font-semibold mb-3">Step 4 · Preview & Edit</h2>
              <div className="flex items-center gap-2 mb-4">
                {(["SMS", "Messenger", "Letter"] as const).map((mode) => (
                  <button
                    key={mode}
                    onClick={() => setPreviewMode(mode)}
                    className={cn(
                      "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all",
                      previewMode === mode
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground hover:bg-muted/80",
                    )}
                  >
                    {mode === "SMS" ? (
                      <Smartphone className="size-3" />
                    ) : mode === "Messenger" ? (
                      <MessageCircle className="size-3" />
                    ) : (
                      <FileText className="size-3" />
                    )}
                    {mode}
                  </button>
                ))}
              </div>

              {previewMode === "SMS" && (
                <div className="max-w-sm mx-auto">
                  <div className="rounded-2xl border-2 border-muted-foreground/20 p-3 bg-background">
                    <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
                      <span className="font-semibold text-foreground">T. Mariel Reyes</span>
                      <span className="ml-auto">3:45 PM</span>
                    </div>
                    <div className="rounded-xl bg-primary/10 p-3 text-sm">
                      <p className="whitespace-pre-wrap">{draftMessage}</p>
                    </div>
                    <div className="text-[10px] text-right text-muted-foreground mt-1">
                      Delivered
                    </div>
                  </div>
                </div>
              )}

              {previewMode === "Messenger" && (
                <div className="max-w-sm mx-auto">
                  <div className="rounded-2xl border-2 border-primary/30 p-3 bg-primary-soft/30">
                    <div className="flex items-center gap-2 text-xs font-semibold mb-2">
                      <MessageCircle className="size-4 text-primary" />
                      <span>Messenger Chat</span>
                    </div>
                    <div className="space-y-2">
                      <div className="rounded-lg bg-primary text-primary-foreground p-3 text-sm ml-8">
                        <p className="whitespace-pre-wrap">{draftMessage}</p>
                      </div>
                      <div className="text-[10px] text-muted-foreground text-right">
                        Seen 3:46 PM
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {previewMode === "Letter" && (
                <div className="max-w-lg mx-auto border border-foreground/20 p-6 font-serif text-sm bg-background">
                  <div className="text-center border-b border-foreground/20 pb-3 mb-3">
                    <div className="font-bold">Republic of the Philippines</div>
                    <div>Department of Education</div>
                    <div>Region III · Sampaloc Elementary School</div>
                  </div>
                  <p className="whitespace-pre-wrap">{draftMessage}</p>
                  <div className="mt-8 flex justify-between">
                    <div className="text-center">
                      <div className="border-t border-foreground/40 pt-1 text-xs">
                        Parent/Guardian Signature
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="border-t border-foreground/40 pt-1 text-xs">
                        Adviser Signature
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div className="flex flex-wrap gap-3 mt-4 items-center">
                <div className="flex gap-2">
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value as typeof language)}
                    className="h-8 px-2 rounded border border-input bg-background text-xs"
                  >
                    <option>Tagalog</option>
                    <option>English</option>
                    <option>Bisaya</option>
                  </select>
                  <select
                    value={tone}
                    onChange={(e) => setTone(e.target.value as typeof tone)}
                    className="h-8 px-2 rounded border border-input bg-background text-xs"
                  >
                    <option>Formal</option>
                    <option>Casual</option>
                    <option>Urgent</option>
                  </select>
                </div>
                <Button size="sm" variant="outline" className="gap-1.5">
                  <RefreshCw className="size-3" />
                  Regenerate
                </Button>
                <Button size="sm" variant="outline" className="gap-1.5">
                  <Edit className="size-3" />
                  Edit
                </Button>
              </div>
            </div>

            <div className="flex justify-between">
              <Button variant="outline" onClick={() => setStep(2)}>
                ← Back
              </Button>
              <Button
                onClick={() => {
                  handleSend();
                }}
                className="gap-2"
              >
                <Send className="size-4" />
                Send Message
              </Button>
            </div>
          </div>

          <div className="rounded-xl border border-border bg-card p-5">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <User className="size-4 text-primary" /> Student Summary
            </div>
            <div className="mt-3 space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Name</span>
                <span className="font-medium">{selectedStudent.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Guardian</span>
                <span className="font-medium">{selectedStudent.guardian}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Contact</span>
                <span className="font-medium">{selectedStudent.contact}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Avg Grade</span>
                <span className="font-medium">{selectedStudent.averageGrade}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Attendance</span>
                <span className="font-medium">{selectedStudent.attendance}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Issue</span>
                <span className="font-medium">
                  {issues.find((i) => i.id === selectedIssue)?.label}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Step 5: Sending */}
      {step === 5 && sendStatus === "sending" && (
        <div className="rounded-xl border border-border bg-card p-8 text-center">
          <Send className="size-8 text-primary mx-auto animate-pulse" />
          <h2 className="font-semibold mt-4">Sending message…</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Delivering via {previewMode} to {selectedStudent.guardian}
          </p>
          <div className="mt-6 max-w-md mx-auto h-2 rounded-full bg-muted overflow-hidden">
            <div className="h-full bg-gradient-primary animate-pulse" style={{ width: "90%" }} />
          </div>
        </div>
      )}

      {/* Step 6: History */}
      {step === 6 && (
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 rounded-xl border border-border bg-card p-6">
            <h2 className="font-semibold mb-1">Step 6 · Communication History</h2>
            <p className="text-sm text-muted-foreground mb-4">
              All messages sent to {selectedStudent.guardian} regarding {selectedStudent.name}
            </p>

            {sendStatus === "sent" && (
              <div className="mb-4 p-3 rounded-lg bg-success/10 border border-success/30 flex items-center gap-2 text-sm">
                <Check className="size-4 text-success" /> Message sent successfully via{" "}
                {previewMode}
              </div>
            )}

            <div className="divide-y divide-border">
              {studentLogs.length === 0 && (
                <div className="py-8 text-center text-sm text-muted-foreground">
                  No previous communication history for this student.
                </div>
              )}
              {[...studentLogs].reverse().map((log) => (
                <div key={log.id} className="py-4">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      {log.channel === "SMS" ? (
                        <Smartphone className="size-4 text-primary" />
                      ) : log.channel === "Messenger" ? (
                        <MessageCircle className="size-4 text-info" />
                      ) : (
                        <FileText className="size-4 text-warning-foreground" />
                      )}
                      <span className="font-medium">{log.channel}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{new Date(log.date).toLocaleDateString()}</span>
                      <span
                        className={cn(
                          "px-1.5 py-0.5 rounded text-[10px] font-medium",
                          log.status === "sent"
                            ? "bg-success/10 text-success"
                            : "bg-muted text-muted-foreground",
                        )}
                      >
                        {log.status}
                      </span>
                    </div>
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground line-clamp-2">{log.message}</p>
                </div>
              ))}
            </div>

            <div className="flex justify-between mt-6 pt-4 border-t border-border">
              <Button
                variant="outline"
                onClick={() => {
                  setStep(1);
                  setSendStatus("idle");
                }}
              >
                ← New Message
              </Button>
              <Button onClick={() => setStep(1)}>Back to Student Selection</Button>
            </div>
          </div>
          <div className="rounded-xl border border-border bg-card p-5">
            <h3 className="text-sm font-semibold mb-3">Quick Stats</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total messages</span>
                <span className="font-medium">{studentLogs.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">SMS sent</span>
                <span className="font-medium">
                  {studentLogs.filter((l) => l.channel === "SMS").length}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Messenger</span>
                <span className="font-medium">
                  {studentLogs.filter((l) => l.channel === "Messenger").length}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Letters</span>
                <span className="font-medium">
                  {studentLogs.filter((l) => l.channel === "Letter").length}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Response rate</span>
                <span className="font-medium text-success">80%</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
