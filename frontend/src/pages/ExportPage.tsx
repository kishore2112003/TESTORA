import { Download } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { Badge } from "@/components/ui/badge";
import { SkeletonCard, SkeletonTable } from "@/components/ui/skeleton";

export function ExportPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Export Reports"
        description="Generate formatted reports across single or multiple test sessions."
        badge={
          <Badge variant="outline" className="border-brand-500/30 text-brand-700 dark:text-brand-300 bg-brand-50/50 dark:bg-brand-900/20 font-semibold">
            Phase 5
          </Badge>
        }
      />

      <div className="relative">
        {/* Prominent Overlay Card */}
        <div className="absolute inset-0 z-10 flex items-center justify-center p-4">
          <div className="max-w-md w-full rounded-card border border-border bg-surface/95 backdrop-blur-md p-6 sm:p-8 text-center elevation-lg space-y-4">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/15 text-primary elevation-xs">
              <Download className="h-7 w-7" />
            </div>
            <div className="space-y-2">
              <h2 className="text-xl font-bold tracking-tight text-foreground">
                Coming in Phase 5
              </h2>
              <p className="text-sm text-muted-foreground leading-relaxed">
                The multi-session export selector, live in-app preview table, and Excel (.xlsx), Markdown (.md), and JIRA CSV generators will arrive in Phase 5.
              </p>
            </div>
          </div>
        </div>

        {/* Static Dimmed Skeleton Layout */}
        <div className="space-y-6 opacity-40 select-none pointer-events-none filter blur-[0.5px]">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>

          <SkeletonTable rows={4} />
        </div>
      </div>
    </div>
  );
}
