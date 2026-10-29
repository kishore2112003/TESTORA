import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import {
  Eye,
  EyeOff,
  KeyRound,
  Laptop,
  Loader2,
  Lock,
  Moon,
  Sparkles,
  Sun,
  User as UserIcon,
} from "lucide-react";

import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import { api, ApiError } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const changePasswordSchema = z
  .object({
    current_password: z.string().min(1, "Current password is required"),
    new_password: z
      .string()
      .min(8, "New password must be at least 8 characters long"),
    confirm_password: z.string().min(1, "Please confirm your new password"),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "New passwords do not match",
    path: ["confirm_password"],
  })
  .refine((data) => data.new_password !== data.current_password, {
    message: "New password cannot be the same as the current password",
    path: ["new_password"],
  });

type ChangePasswordFormData = z.infer<typeof changePasswordSchema>;

export function SettingsPage() {
  const { user } = useAuth();
  const { theme, setTheme } = useTheme();

  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ChangePasswordFormData>({
    resolver: zodResolver(changePasswordSchema),
    defaultValues: {
      current_password: "",
      new_password: "",
      confirm_password: "",
    },
  });

  const onChangePassword = async (data: ChangePasswordFormData) => {
    try {
      await api.post("/api/v1/auth/change-password", {
        current_password: data.current_password,
        new_password: data.new_password,
      });

      toast.success("Password changed successfully", {
        description: "Your password has been updated. Use the new password for future logins.",
      });
      reset();
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error("Failed to change password", {
          description: err.message,
        });
      } else {
        toast.error("Failed to change password", {
          description: "An unexpected error occurred. Please try again.",
        });
      }
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        description="Manage your account credentials, workspace preferences, and application themes."
      />

      {/* Section 1: User Profile (Read-only) */}
      <Card className="elevation-xs">
        <CardHeader>
          <div className="flex items-center gap-2">
            <UserIcon className="h-5 w-5 text-primary" />
            <CardTitle>User Profile</CardTitle>
          </div>
          <CardDescription>
            Your current account credentials and role assignments.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">
                Full Name
              </Label>
              <Input
                value={user?.name ?? ""}
                readOnly
                disabled
                className="bg-muted/50 cursor-not-allowed font-medium text-foreground"
              />
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">
                Email Address
              </Label>
              <Input
                value={user?.email ?? ""}
                readOnly
                disabled
                className="bg-muted/50 cursor-not-allowed font-medium text-foreground"
              />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 pt-1">
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">
                Role
              </Label>
              <div className="flex items-center h-9">
                <Badge variant="outline" className="border-primary/30 bg-primary/10 text-brand-700 dark:text-brand-300 font-bold uppercase tracking-wider">
                  {user?.role ?? "User"}
                </Badge>
              </div>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">
                Account Created
              </Label>
              <p className="text-sm text-muted-foreground flex items-center h-9 font-medium">
                {user?.created_at
                  ? new Date(user.created_at).toLocaleDateString(undefined, {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })
                  : "N/A"}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Section 2: Change Password Form */}
      <Card className="elevation-xs">
        <CardHeader>
          <div className="flex items-center gap-2">
            <KeyRound className="h-5 w-5 text-primary" />
            <CardTitle>Change Password</CardTitle>
          </div>
          <CardDescription>
            Update your account password. Must be at least 8 characters long.
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit(onChangePassword)} noValidate>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="current_password">Current Password</Label>
              <div className="relative">
                <Input
                  id="current_password"
                  type={showCurrent ? "text" : "password"}
                  placeholder="Enter current password"
                  autoComplete="current-password"
                  disabled={isSubmitting}
                  className={`pr-10 ${
                    errors.current_password
                      ? "border-destructive focus-visible:ring-destructive/30"
                      : ""
                  }`}
                  {...register("current_password")}
                />
                <button
                  type="button"
                  onClick={() => setShowCurrent((prev) => !prev)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  aria-label={showCurrent ? "Hide current password" : "Show current password"}
                >
                  {showCurrent ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.current_password && (
                <p className="text-xs text-destructive font-medium">
                  {errors.current_password.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="new_password">New Password</Label>
              <div className="relative">
                <Input
                  id="new_password"
                  type={showNew ? "text" : "password"}
                  placeholder="At least 8 characters"
                  autoComplete="new-password"
                  disabled={isSubmitting}
                  className={`pr-10 ${
                    errors.new_password
                      ? "border-destructive focus-visible:ring-destructive/30"
                      : ""
                  }`}
                  {...register("new_password")}
                />
                <button
                  type="button"
                  onClick={() => setShowNew((prev) => !prev)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  aria-label={showNew ? "Hide new password" : "Show new password"}
                >
                  {showNew ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.new_password && (
                <p className="text-xs text-destructive font-medium">
                  {errors.new_password.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirm_password">Confirm New Password</Label>
              <div className="relative">
                <Input
                  id="confirm_password"
                  type={showConfirm ? "text" : "password"}
                  placeholder="Re-enter new password"
                  autoComplete="new-password"
                  disabled={isSubmitting}
                  className={`pr-10 ${
                    errors.confirm_password
                      ? "border-destructive focus-visible:ring-destructive/30"
                      : ""
                  }`}
                  {...register("confirm_password")}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm((prev) => !prev)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  aria-label={showConfirm ? "Hide confirmation password" : "Show confirmation password"}
                >
                  {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.confirm_password && (
                <p className="text-xs text-destructive font-medium">
                  {errors.confirm_password.message}
                </p>
              )}
            </div>

            <div className="pt-2">
              <Button type="submit" disabled={isSubmitting} className="font-semibold">
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Updating password...
                  </>
                ) : (
                  <>
                    <Lock className="mr-2 h-4 w-4" />
                    Update Password
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </form>
      </Card>

      {/* Section 3: Appearance */}
      <Card className="elevation-xs">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Sun className="h-5 w-5 text-primary" />
            <CardTitle>Appearance</CardTitle>
          </div>
          <CardDescription>
            Customize your interface theme. Automatically synchronizes with system preference by default.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-3 max-w-md">
            <button
              type="button"
              onClick={() => setTheme("light")}
              className={`flex flex-col items-center justify-center gap-2 rounded-control border p-3.5 text-sm font-medium transition-all ${
                theme === "light"
                  ? "border-primary bg-primary/10 text-primary shadow-xs ring-1 ring-primary/20"
                  : "border-border text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              <Sun className="h-5 w-5" />
              <span>Light</span>
            </button>

            <button
              type="button"
              onClick={() => setTheme("dark")}
              className={`flex flex-col items-center justify-center gap-2 rounded-control border p-3.5 text-sm font-medium transition-all ${
                theme === "dark"
                  ? "border-primary bg-primary/10 text-primary shadow-xs ring-1 ring-primary/20"
                  : "border-border text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              <Moon className="h-5 w-5" />
              <span>Dark</span>
            </button>

            <button
              type="button"
              onClick={() => setTheme("system")}
              className={`flex flex-col items-center justify-center gap-2 rounded-control border p-3.5 text-sm font-medium transition-all ${
                theme === "system"
                  ? "border-primary bg-primary/10 text-primary shadow-xs ring-1 ring-primary/20"
                  : "border-border text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              <Laptop className="h-5 w-5" />
              <span>System</span>
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Section 4: AI Writing Style (Disabled placeholder) */}
      <Card className="opacity-80 elevation-xs">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              <CardTitle>Writing Style (AI)</CardTitle>
            </div>
            <Badge variant="outline" className="text-muted-foreground border-border bg-muted/40">
              Available in a later phase
            </Badge>
          </div>
          <CardDescription>
            Customize generative AI instructions and prompts for automated test scenario drafting.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="ai_prompt" className="text-muted-foreground">
              Custom AI Persona & Prompt Guidance
            </Label>
            <textarea
              id="ai_prompt"
              disabled
              rows={3}
              placeholder="e.g. Focus on edge-case discovery, security validation, and explicit step preconditions..."
              className="w-full rounded-control border border-input bg-muted/30 p-3 text-sm text-muted-foreground opacity-60 cursor-not-allowed resize-none"
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
