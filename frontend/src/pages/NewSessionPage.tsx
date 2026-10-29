import { PlusCircle } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Skeleton, SkeletonTable } from "@/components/ui/skeleton";

export function NewSessionPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="New Ticket Session"
        description="Initialize a test session, configure testing scopes, and execute test cases."
        badge={
          <Badge variant="outline" className="border-brand-500/30 text-brand-700 dark:text-brand-300 bg-brand-50/50 dark:bg-brand-900/20 font-semibold">
            Phase 3
          </Badge>
        }
      />

      <div className="relative">
        {/* Prominent Overlay Card */}
        <div className="absolute inset-0 z-10 flex items-center justify-center p-4">
          <div className="max-w-md w-full rounded-card border border-border bg-surface/95 backdrop-blur-md p-6 sm:p-8 text-center elevation-lg space-y-4">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/15 text-primary elevation-xs">
              <PlusCircle className="h-7 w-7" />
            </div>
            <div className="space-y-2">
              <h2 className="text-xl font-bold tracking-tight text-foreground">
                Coming in Phase 3
              </h2>
              <p className="text-sm text-muted-foreground leading-relaxed">
                The unified session header, autosaving inline test case grid, AI test generation, and step executions will arrive in Phase 3.
              </p>
            </div>
          </div>
        </div>

        {/* Static Dimmed Skeleton Layout */}
        <div className="space-y-6 opacity-40 select-none pointer-events-none filter blur-[0.5px]">
          <div className="rounded-card border border-border bg-card p-6 space-y-5">
            <Skeleton className="h-5 w-40" />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-9 w-full" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-9 w-full" />
              </div>
            </div>
            <div className="space-y-2">
              <Skeleton className="h-4 w-28" />
              <Skeleton className="h-20 w-full" />
            </div>
          </div>

          <SkeletonTable rows={5} />
        </div>
      </div>
    </div>
  );
}
