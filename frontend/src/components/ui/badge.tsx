import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { CheckCircle2, XCircle, AlertOctagon, MinusCircle, CircleDashed } from "lucide-react";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors select-none",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground font-semibold shadow",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground",
        outline: "text-foreground border-border",
        pass: "border-status-pass-fg/20 bg-status-pass-bg text-status-pass-fg font-semibold",
        fail: "border-status-fail-fg/20 bg-status-fail-bg text-status-fail-fg font-semibold",
        blocked: "border-status-blocked-fg/20 bg-status-blocked-bg text-status-blocked-fg font-semibold",
        skipped: "border-status-skipped-fg/20 bg-status-skipped-bg text-status-skipped-fg font-semibold",
        not_run: "border-status-not-run-fg/20 bg-status-not-run-bg text-status-not-run-fg font-semibold",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export type StatusType = "pass" | "fail" | "blocked" | "skipped" | "not_run";

interface StatusBadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  status: StatusType;
  label?: string;
  showIcon?: boolean;
}

const statusConfig: Record<
  StatusType,
  { label: string; icon: React.ComponentType<{ className?: string }> }
> = {
  pass: { label: "Pass", icon: CheckCircle2 },
  fail: { label: "Fail", icon: XCircle },
  blocked: { label: "Blocked", icon: AlertOctagon },
  skipped: { label: "Skipped", icon: MinusCircle },
  not_run: { label: "Not Run", icon: CircleDashed },
};

export function StatusBadge({
  status,
  label,
  showIcon = true,
  className,
  ...props
}: StatusBadgeProps) {
  const config = statusConfig[status] ?? statusConfig.not_run;
  const Icon = config.icon;

  return (
    <Badge variant={status} className={cn("tabular-nums", className)} {...props}>
      {showIcon && <Icon className="h-3 w-3 shrink-0" />}
      <span>{label || config.label}</span>
    </Badge>
  );
}

export { Badge, badgeVariants };
