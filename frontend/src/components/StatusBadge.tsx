type StatusBadgeProps = {
  connected: boolean;
  label: string;
};

export function StatusBadge({ connected, label }: StatusBadgeProps) {
  return (
    <span className={`status-badge ${connected ? "connected" : "disconnected"}`}>
      {label}
    </span>
  );
}
