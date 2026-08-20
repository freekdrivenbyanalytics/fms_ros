import { useState, type KeyboardEvent, type ReactNode } from "react";

interface InfoBoxProps {
  summary: ReactNode;
  children: ReactNode;
}

export function InfoBox({ summary, children }: InfoBoxProps) {
  const [expanded, setExpanded] = useState(false);

  function toggle() {
    setExpanded((prev) => !prev);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      toggle();
    }
  }

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        aria-expanded={expanded}
        onClick={toggle}
        onKeyDown={handleKeyDown}
        className="cursor-pointer select-none"
      >
        {summary}
      </div>
      {expanded && (
        <div className="mt-2 pt-2 border-t border-slate-100 text-xs text-slate-600 space-y-0.5">
          {children}
        </div>
      )}
    </div>
  );
}
