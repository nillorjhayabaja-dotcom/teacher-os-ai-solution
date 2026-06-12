// ============================================================
// TeacherOS — Providers
// ============================================================
import type { ReactNode } from "react";
import { Toaster } from "sonner";

export function Providers({ children }: { children: ReactNode }) {
  return (
    <>
      {children}
      <Toaster
        position="top-right"
        richColors
        closeButton
        duration={5000}
        toastOptions={{
          style: {
            borderRadius: "0.75rem",
            border: "1px solid var(--border)",
            boxShadow: "0 8px 32px -8px rgba(0,0,0,0.12)",
          },
        }}
      />
    </>
  );
}