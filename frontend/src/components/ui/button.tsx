import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-control text-sm font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 select-none",
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground font-semibold elevation-xs hover:bg-brand-600 dark:hover:bg-brand-400 hover:elevation-sm active:scale-[0.98]",
        destructive:
          "bg-destructive text-destructive-foreground elevation-xs hover:bg-destructive/90 active:scale-[0.98]",
        outline:
          "border border-border bg-surface text-foreground elevation-xs hover:bg-muted/70 hover:border-border-strong active:scale-[0.98]",
        secondary:
          "bg-surface-raised text-foreground border border-border/70 hover:bg-muted active:scale-[0.98]",
        ghost:
          "text-foreground hover:bg-muted/70 active:scale-[0.98]",
        link:
          "text-brand-700 dark:text-brand-400 underline-offset-4 hover:underline hover:text-brand-800 dark:hover:text-brand-300 font-medium p-0 h-auto",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-control px-3 text-xs",
        lg: "h-10 rounded-control px-6 text-base",
        icon: "h-9 w-9 p-0",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
