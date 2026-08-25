import type { ReactNode } from "react";

interface DetailFieldProps {
  label: string;
  children: ReactNode;
}

export function DetailField({ label, children }: DetailFieldProps) {
  return (
    <div className="py-2 border-b border-slate-100 last:border-0">
      <div className="text-xs uppercase tracking-wide text-slate-400">{label}</div>
      <div className="text-sm text-slate-800 mt-0.5">{children}</div>
    </div>
  );
}

interface BackButtonProps {
  label: string;
  onClick: () => void;
}

export function BackButton({ label, onClick }: BackButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="text-sm text-slate-500 hover:text-slate-800 mb-4"
    >
      ← Back to {label}
    </button>
  );
}
