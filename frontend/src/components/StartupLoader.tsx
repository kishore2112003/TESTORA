import { m } from "framer-motion";
import { Logo } from "@/components/Logo";

export function StartupLoader() {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background">
      <div className="relative flex flex-col items-center justify-center">
        {/* Subtle radial teal pulse glow */}
        <div className="absolute -inset-4 rounded-full bg-brand-500/15 blur-xl animate-pulse pointer-events-none" />

        <m.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
          className="relative flex flex-col items-center gap-4"
        >
          <Logo variant="full" className="h-9" />
          <div className="h-1 w-20 overflow-hidden rounded-full bg-muted">
            <m.div
              className="h-full bg-primary"
              initial={{ x: "-100%" }}
              animate={{ x: "100%" }}
              transition={{
                repeat: Infinity,
                duration: 1.2,
                ease: "easeInOut",
              }}
            />
          </div>
        </m.div>
      </div>
    </div>
  );
}
