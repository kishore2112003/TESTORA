import { cn } from "@/lib/utils";

interface LogoProps {
  variant?: "full" | "icon";
  className?: string;
  iconClassName?: string;
  alt?: string;
}

export function Logo({
  variant = "full",
  className,
  iconClassName,
  alt = "Testora",
}: LogoProps) {
  if (variant === "icon") {
    return (
      <img
        src="/logo-icon.png"
        alt={alt}
        className={cn("h-8 w-auto object-contain select-none", iconClassName, className)}
      />
    );
  }

  return (
    <div className={cn("inline-flex items-center select-none", className)}>
      {/* Light mode version */}
      <img
        src="/logo-full.png"
        alt={alt}
        className="h-7 w-auto object-contain dark:hidden"
      />
      {/* Dark mode version */}
      <img
        src="/logo-full-dark.png"
        alt={alt}
        className="h-7 w-auto object-contain hidden dark:block"
      />
    </div>
  );
}
