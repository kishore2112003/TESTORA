import { useEffect, useState } from "react";
import { m, AnimatePresence } from "framer-motion";
import { useRouteLoading } from "@/context/LoadingContext";

export function TopProgressBar() {
  const { isLoading } = useRouteLoading();
  const [progress, setProgress] = useState(0);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isLoading) {
      setVisible(true);
      setProgress(25);
      timer = setTimeout(() => {
        setProgress(75);
      }, 150);
    } else if (visible) {
      setProgress(100);
      timer = setTimeout(() => {
        setVisible(false);
        setProgress(0);
      }, 200);
    }
    return () => clearTimeout(timer);
  }, [isLoading, visible]);

  return (
    <AnimatePresence>
      {visible && (
        <div className="fixed top-0 left-0 right-0 z-[100] h-[2.5px] bg-transparent pointer-events-none">
          <m.div
            className="h-full bg-primary shadow-[0_0_8px_hsl(var(--primary))]"
            initial={{ width: "0%" }}
            animate={{ width: `${progress}%` }}
            exit={{ opacity: 0 }}
            transition={{
              duration: progress === 100 ? 0.15 : 0.4,
              ease: [0.16, 1, 0.3, 1],
            }}
          />
        </div>
      )}
    </AnimatePresence>
  );
}
