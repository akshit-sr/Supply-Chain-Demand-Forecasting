import { ReactNode } from "react";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`card ${className}`}>{children}</div>;
}

export function Stat({
  label,
  value,
  sub,
  accent = "blue",
}: {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  accent?: "blue" | "green" | "orange" | "red" | "purple";
}) {
  const dot = {
    blue: "bg-mac-blue",
    green: "bg-mac-green",
    orange: "bg-mac-orange",
    red: "bg-mac-red",
    purple: "bg-mac-purple",
  }[accent];
  return (
    <Card className="flex flex-col gap-1">
      <div className="flex items-center gap-2">
        <span className={`h-2 w-2 rounded-full ${dot}`} />
        <span className="text-xs font-medium uppercase tracking-wide text-mac-sub">
          {label}
        </span>
      </div>
      <div className="text-2xl font-semibold text-mac-ink dark:text-white">{value}</div>
      {sub && <div className="text-xs text-mac-sub">{sub}</div>}
    </Card>
  );
}

const riskStyles: Record<string, string> = {
  low: "bg-mac-green/15 text-mac-green",
  medium: "bg-mac-orange/15 text-mac-orange",
  high: "bg-mac-red/15 text-mac-red",
  critical: "bg-mac-red/20 text-mac-red animate-pulse-glow shadow-glow font-bold",
  ok: "bg-mac-green/15 text-mac-green",
  soon: "bg-mac-orange/15 text-mac-orange",
  urgent: "bg-mac-red/20 text-mac-red animate-pulse-glow shadow-glow font-bold",
};

export function Badge({ kind }: { kind: string }) {
  return (
    <span className={`pill ${riskStyles[kind] ?? "bg-black/5 text-mac-sub"}`}>
      {kind}
    </span>
  );
}

export function Field({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-xs font-medium text-mac-sub">{label}</span>
      {children}
    </label>
  );
}

export function Spinner() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-mac-blue border-t-transparent" />
    </div>
  );
}

export function PageTitle({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-1">
      <h1 className="text-2xl font-semibold text-mac-ink dark:text-white">{title}</h1>
      {subtitle && <p className="text-sm text-mac-sub">{subtitle}</p>}
    </div>
  );
}
