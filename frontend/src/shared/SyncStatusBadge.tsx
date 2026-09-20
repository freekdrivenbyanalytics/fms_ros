interface SyncStatusBadgeProps {
  label: string;
  synced: boolean;
}

// Reflects the persistent "still needs syncing" signal (the relevant
// *_id field being null) - not a one-time toast, so it stays accurate
// even after the page reloads. See local-first-masterdata-sync's
// design.md.
export function SyncStatusBadge({ label, synced }: SyncStatusBadgeProps) {
  return (
    <span
      className={
        synced
          ? "inline-block rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700"
          : "inline-block rounded-full bg-amber-50 px-2 py-0.5 text-xs text-amber-700"
      }
    >
      {synced ? `${label}: Synced` : `${label}: Not synced`}
    </span>
  );
}
