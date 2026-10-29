import { useLocation, useOutlet } from "react-router-dom";
import { AnimatePresence, m } from "framer-motion";
import { pageVariants } from "@/lib/motion";

export function AnimatedOutlet() {
  const location = useLocation();
  const element = useOutlet();

  return (
    <AnimatePresence mode="wait" initial={false}>
      {element && (
        <m.div
          key={location.pathname}
          variants={pageVariants}
          initial="initial"
          animate="animate"
          exit="exit"
          className="w-full"
        >
          {element}
        </m.div>
      )}
    </AnimatePresence>
  );
}
