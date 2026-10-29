import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { z } from "zod";
import { Eye, EyeOff, Loader2, Sparkles, CheckCircle2, ShieldCheck } from "lucide-react";
import { m, useReducedMotion } from "framer-motion";

import { useAuth } from "@/context/AuthContext";
import { ApiError } from "@/lib/api";
import { Logo } from "@/components/Logo";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const loginSchema = z.object({
  email: z
    .string()
    .min(1, "Email is required")
    .email("Please enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginPage() {
  const { user, isInitialColdLoad, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const shouldReduceMotion = useReducedMotion();

  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Retrieve path from location.state if redirected by ProtectedRoute
  const fromLocation =
    (location.state as { from?: { pathname: string; search?: string } })?.from;
  const redirectTarget = fromLocation
    ? `${fromLocation.pathname}${fromLocation.search || ""}`
    : "/dashboard";

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  // Redirect away from login if already authenticated
  if (!isInitialColdLoad && user) {
    return <Navigate to={redirectTarget} replace />;
  }

  const onSubmit = async (data: LoginFormData) => {
    setErrorMessage(null);
    try {
      await login(data);
      navigate(redirectTarget, { replace: true });
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message || "Invalid email or password.");
      } else {
        setErrorMessage("An unexpected error occurred. Please try again.");
      }
    }
  };

  return (
    <div className="flex min-h-screen w-full bg-background">
      {/* Brand Showcase Hero (Left Panel >= 1024px) */}
      <div className="hidden lg:flex lg:w-1/2 relative flex-col justify-between p-12 bg-surface border-r border-border overflow-hidden">
        {/* Subtle decorative background glow */}
        <div className="absolute -top-24 -left-24 h-96 w-96 rounded-full bg-brand-500/10 blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 h-96 w-96 rounded-full bg-brand-800/10 blur-3xl pointer-events-none" />

        <div className="relative z-10">
          <Logo variant="full" className="h-8" />
        </div>

        <div className="relative z-10 max-w-lg space-y-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-border bg-surface-raised px-3 py-1 text-xs font-medium text-brand-700 dark:text-brand-300 elevation-xs">
            <Sparkles className="h-3.5 w-3.5 text-primary" />
            <span>AI-Powered Test Case Platform</span>
          </div>

          <h1 className="text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl leading-tight">
            Elevate quality assurance from ticket to execution.
          </h1>

          <p className="text-base text-muted-foreground leading-relaxed">
            Generate comprehensive, structured test suites from ticket specifications in seconds. Execute steps, record evidence, and export directly into your workflow.
          </p>

          <div className="space-y-3.5 pt-2">
            <div className="flex items-center gap-3 text-sm text-foreground/90">
              <CheckCircle2 className="h-4 w-4 text-primary shrink-0" />
              <span>Multi-type coverage: Functional, Edge, Security, and UI</span>
            </div>
            <div className="flex items-center gap-3 text-sm text-foreground/90">
              <CheckCircle2 className="h-4 w-4 text-primary shrink-0" />
              <span>Step-by-step interactive test runner with real-time pass/fail states</span>
            </div>
            <div className="flex items-center gap-3 text-sm text-foreground/90">
              <CheckCircle2 className="h-4 w-4 text-primary shrink-0" />
              <span>Multi-format export: Excel workbook, Markdown report, and JIRA CSV</span>
            </div>
          </div>
        </div>

        <div className="relative z-10 flex items-center justify-between text-xs text-muted-foreground pt-8 border-t border-border/60">
          <p>© 2026 Testora. All rights reserved.</p>
          <div className="flex items-center gap-2 font-medium">
            <ShieldCheck className="h-4 w-4 text-primary" />
            <span>Enterprise QA Platform</span>
          </div>
        </div>
      </div>

      {/* Auth Form (Right Panel) */}
      <div className="flex w-full lg:w-1/2 items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-md">
          {/* Mobile Logo Header */}
          <div className="lg:hidden flex justify-center mb-8">
            <Logo variant="full" className="h-8" />
          </div>

          <Card className="border-border elevation-sm">
            <CardHeader className="space-y-1.5 text-center pb-6">
              <CardTitle className="text-2xl font-bold tracking-tight text-foreground">
                Welcome back
              </CardTitle>
              <CardDescription className="text-sm">
                Enter your credentials to access your testing workspace
              </CardDescription>
            </CardHeader>

            <form onSubmit={handleSubmit(onSubmit)} noValidate>
              <CardContent className="space-y-4">
                {errorMessage && (
                  <m.div
                    role="alert"
                    initial={{ opacity: 0 }}
                    animate={
                      shouldReduceMotion
                        ? { opacity: 1 }
                        : { opacity: 1, x: [0, -8, 8, -6, 6, -3, 3, 0] }
                    }
                    transition={{ duration: 0.35, ease: "easeInOut" }}
                    className="rounded-control border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive font-medium flex items-center gap-2.5"
                  >
                    <span className="h-2 w-2 rounded-full bg-destructive shrink-0" />
                    <span>{errorMessage}</span>
                  </m.div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="email" className="text-foreground">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="admin@testora.local"
                    autoComplete="email"
                    disabled={isSubmitting}
                    aria-invalid={!!errors.email}
                    className={errors.email ? "border-destructive focus-visible:ring-destructive/30" : ""}
                    {...register("email")}
                  />
                  {errors.email && (
                    <p className="text-xs text-destructive font-medium">
                      {errors.email.message}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="password" className="text-foreground">Password</Label>
                  </div>
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      placeholder="••••••••"
                      autoComplete="current-password"
                      disabled={isSubmitting}
                      aria-invalid={!!errors.password}
                      className={`pr-10 ${
                        errors.password ? "border-destructive focus-visible:ring-destructive/30" : ""
                      }`}
                      {...register("password")}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((prev) => !prev)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors focus:outline-none"
                      aria-label={showPassword ? "Hide password" : "Show password"}
                      tabIndex={0}
                    >
                      {showPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                  {errors.password && (
                    <p className="text-xs text-destructive font-medium">
                      {errors.password.message}
                    </p>
                  )}
                </div>
              </CardContent>

              <CardFooter className="pt-2">
                <Button
                  type="submit"
                  className="w-full h-10 font-semibold relative"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <span className="inline-flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Signing in...</span>
                    </span>
                  ) : (
                    <span>Sign In</span>
                  )}
                </Button>
              </CardFooter>
            </form>
          </Card>
        </div>
      </div>
    </div>
  );
}
