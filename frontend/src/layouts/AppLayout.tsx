import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { m } from "framer-motion";
import { AnimatedOutlet } from "@/components/AnimatedOutlet";
import {
  ChevronLeft,
  ChevronRight,
  Download,
  LayoutDashboard,
  ListTodo,
  LogOut,
  Menu,
  Moon,
  PlusCircle,
  Settings as SettingsIcon,
  Sun,
  User as UserIcon,
} from "lucide-react";

import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import { Logo } from "@/components/Logo";
import { TopProgressBar } from "@/components/TopProgressBar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

interface NavItem {
  title: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
}

const navItems: NavItem[] = [
  { title: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
  { title: "New Ticket Session", path: "/sessions/new", icon: PlusCircle },
  { title: "View Sessions", path: "/sessions", icon: ListTodo },
  { title: "Export", path: "/export", icon: Download },
  { title: "Settings", path: "/settings", icon: SettingsIcon },
];

function getPageTitle(pathname: string): string {
  if (pathname === "/dashboard") return "Dashboard";
  if (pathname === "/sessions/new") return "New Ticket Session";
  if (pathname.startsWith("/sessions")) return "View Sessions";
  if (pathname === "/export") return "Export Reports";
  if (pathname === "/settings") return "Settings";
  return "Testora";
}

export function AppLayout() {
  const { user, logout } = useAuth();
  const { theme, setTheme, resolvedTheme } = useTheme();
  const location = useLocation();

  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const pageTitle = getPageTitle(location.pathname);

  const toggleTheme = () => {
    if (theme === "system") {
      setTheme(resolvedTheme === "dark" ? "light" : "dark");
    } else {
      setTheme(theme === "dark" ? "light" : "dark");
    }
  };

  const SidebarContent = ({ onNavigate }: { onNavigate?: () => void }) => (
    <div className="flex h-full flex-col justify-between bg-card">
      <div>
        {/* Brand Header */}
        <div
          className={cn(
            "flex h-16 items-center border-b border-border px-4 transition-all duration-200",
            collapsed ? "justify-center px-2" : "gap-3"
          )}
        >
          {collapsed ? (
            <Logo variant="icon" iconClassName="h-7 w-auto" />
          ) : (
            <Logo variant="full" className="h-7" />
          )}
        </div>

        {/* Navigation Links */}
        <TooltipProvider delayDuration={150}>
          <nav className="space-y-1.5 p-3">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive =
                location.pathname === item.path ||
                (item.path !== "/dashboard" &&
                  item.path !== "/sessions/new" &&
                  location.pathname.startsWith(item.path));

              const linkElement = (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={onNavigate}
                  className={cn(
                    "group relative flex items-center rounded-control px-3 py-2.5 text-sm font-medium transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ring select-none",
                    isActive
                      ? "text-primary-foreground font-semibold"
                      : "text-muted-foreground hover:bg-muted/60 hover:text-foreground",
                    collapsed ? "justify-center px-2" : "gap-3"
                  )}
                >
                  {/* Active sliding indicator pill */}
                  {isActive && (
                    <m.div
                      layoutId="activeNavIndicator"
                      className="absolute inset-0 rounded-control bg-primary elevation-xs"
                      transition={{
                        type: "spring",
                        stiffness: 400,
                        damping: 34,
                      }}
                    />
                  )}

                  <Icon
                    className={cn(
                      "relative z-10 h-5 w-5 shrink-0 transition-transform group-hover:scale-105",
                      isActive
                        ? "text-primary-foreground"
                        : "text-muted-foreground group-hover:text-foreground"
                    )}
                  />
                  {!collapsed && (
                    <span className="relative z-10 truncate">{item.title}</span>
                  )}
                </Link>
              );

              if (collapsed) {
                return (
                  <Tooltip key={item.path}>
                    <TooltipTrigger asChild>{linkElement}</TooltipTrigger>
                    <TooltipContent side="right">{item.title}</TooltipContent>
                  </Tooltip>
                );
              }

              return linkElement;
            })}
          </nav>
        </TooltipProvider>
      </div>

      {/* Footer / User Profile Card */}
      <div className="border-t border-border p-3">
        {!collapsed ? (
          <div className="flex items-center gap-3 rounded-control bg-surface-raised border border-border/60 p-2.5 elevation-xs">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary-foreground bg-primary font-bold text-xs uppercase shadow-xs">
              {user?.name ? user.name[0] : "U"}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-semibold text-foreground">
                {user?.name}
              </p>
              <p className="truncate text-[11px] text-muted-foreground capitalize">
                {user?.role}
              </p>
            </div>
          </div>
        ) : (
          <TooltipProvider delayDuration={150}>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex justify-center py-1">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground font-bold text-xs uppercase elevation-xs">
                    {user?.name ? user.name[0] : "U"}
                  </div>
                </div>
              </TooltipTrigger>
              <TooltipContent side="right">
                {user?.name} ({user?.role})
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>
    </div>
  );

  return (
    <div className="flex min-h-screen bg-background">
      <TopProgressBar />

      {/* Desktop Collapsible Sidebar */}
      <aside
        className={cn(
          "hidden md:flex flex-col border-r border-border bg-card transition-[width] duration-250 ease-custom shrink-0 sticky top-0 h-screen z-20",
          collapsed ? "w-16" : "w-64"
        )}
      >
        <SidebarContent />

        {/* Desktop Collapse Toggle */}
        <button
          type="button"
          onClick={() => setCollapsed((prev) => !prev)}
          className="absolute -right-3 top-20 flex h-6 w-6 items-center justify-center rounded-full border border-border bg-surface text-muted-foreground elevation-xs hover:bg-muted hover:text-foreground transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <ChevronRight className="h-3.5 w-3.5" />
          ) : (
            <ChevronLeft className="h-3.5 w-3.5" />
          )}
        </button>
      </aside>

      {/* Mobile Drawer Sidebar */}
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" className="p-0 w-72">
          <SheetHeader className="sr-only">
            <SheetTitle>Navigation Menu</SheetTitle>
          </SheetHeader>
          <SidebarContent onNavigate={() => setMobileOpen(false)} />
        </SheetContent>
      </Sheet>

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col min-w-0 overflow-hidden">
        {/* Top Bar */}
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-surface/85 backdrop-blur-md px-4 sm:px-6">
          <div className="flex items-center gap-3">
            {/* Mobile Hamburger Toggle */}
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden"
              onClick={() => setMobileOpen(true)}
              aria-label="Open navigation drawer"
            >
              <Menu className="h-5 w-5" />
            </Button>

            <h1 className="text-lg font-semibold tracking-tight text-foreground sm:text-xl">
              {pageTitle}
            </h1>
          </div>

          {/* Right Header Controls */}
          <div className="flex items-center gap-2">
            {/* Theme Toggle Button */}
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              aria-label={`Switch to ${resolvedTheme === "dark" ? "light" : "dark"} mode`}
              className="text-muted-foreground hover:text-foreground"
            >
              {resolvedTheme === "dark" ? (
                <Sun className="h-5 w-5 text-amber-400 transition-transform hover:rotate-45" />
              ) : (
                <Moon className="h-5 w-5 text-slate-700 dark:text-slate-300 transition-transform hover:-rotate-12" />
              )}
            </Button>

            {/* User Dropdown Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  className="flex items-center gap-2 px-2 hover:bg-muted focus-visible:ring-2"
                >
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground font-bold text-xs uppercase elevation-xs">
                    {user?.name ? user.name[0] : "U"}
                  </div>
                  <span className="hidden text-sm font-medium text-foreground sm:inline-block max-w-[120px] truncate">
                    {user?.name}
                  </span>
                </Button>
              </DropdownMenuTrigger>

              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-semibold leading-none text-foreground">
                      {user?.name}
                    </p>
                    <p className="text-xs leading-none text-muted-foreground truncate">
                      {user?.email}
                    </p>
                    <span className="mt-1 w-fit rounded-full bg-primary/15 px-2 py-0.5 text-[10px] font-semibold text-brand-700 dark:text-brand-300 uppercase">
                      {user?.role}
                    </span>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link to="/settings" className="cursor-pointer">
                    <UserIcon className="mr-2 h-4 w-4" />
                    <span>Profile & Settings</span>
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={() => logout()}
                  className="text-destructive focus:bg-destructive/10 focus:text-destructive cursor-pointer"
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Log out</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* Page View Body with unified layout max-width and padding */}
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 py-6 lg:py-8 space-y-6">
            <AnimatedOutlet />
          </div>
        </main>
      </div>
    </div>
  );
}
