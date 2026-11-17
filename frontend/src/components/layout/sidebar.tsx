"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  LayoutDashboard,
  CreditCard,
  FileText,
  ArrowLeftRight,
  Wallet,
  Gift,
  BarChart3,
  Bot,
  Settings,
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
  TrendingUp,
} from "lucide-react";

interface NavItem {
  label: string;
  icon: React.ElementType;
  href: string;
  badge?: string;
}

const navItems: NavItem[] = [
  { label: "Dashboard", icon: LayoutDashboard, href: "/" },
  { label: "Cards", icon: CreditCard, href: "/cards" },
  { label: "Statements", icon: FileText, href: "/statements" },
  { label: "Transactions", icon: ArrowLeftRight, href: "/transactions" },
  { label: "Payments", icon: Wallet, href: "/payments" },
  { label: "Rewards", icon: Gift, href: "/rewards" },
  { label: "Analytics", icon: BarChart3, href: "/analytics" },
  { label: "AI Assistant", icon: Bot, href: "/assistant", badge: "AI" },
];

const bottomNavItems: NavItem[] = [
  { label: "Settings", icon: Settings, href: "/settings" },
];

export function Sidebar() {
  const [expanded, setExpanded] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);
  // Default active route
  const activeHref = "/";

  return (
    <>
      {/* Mobile hamburger button */}
      <Button
        variant="ghost"
        size="icon"
        className="fixed left-4 top-4 z-50 md:hidden"
        onClick={() => setMobileOpen(!mobileOpen)}
        aria-label="Toggle navigation"
      >
        {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </Button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex flex-col border-r bg-card transition-all duration-300 md:relative md:translate-x-0",
          expanded ? "w-64" : "w-16",
          mobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        )}
      >
        {/* Logo / Brand */}
        <div className="flex h-16 items-center gap-3 border-b px-4">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <TrendingUp className="h-4 w-4" />
          </div>
          {expanded && (
            <span className="text-lg font-bold text-foreground">
              FinSight AI
            </span>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 overflow-y-auto px-2 py-4">
          {navItems.map((item) => {
            const isActive = activeHref === item.href;
            return (
              <a
                key={item.href}
                href={item.href}
                className={cn(
                  "group flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )}
                title={!expanded ? item.label : undefined}
              >
                <item.icon
                  className={cn(
                    "h-5 w-5 shrink-0",
                    isActive ? "text-primary" : "text-muted-foreground group-hover:text-accent-foreground"
                  )}
                />
                {expanded && (
                  <span className="flex-1 truncate">{item.label}</span>
                )}
                {expanded && item.badge && (
                  <Badge
                    variant="default"
                    className="ml-auto h-5 px-1.5 text-[10px]"
                  >
                    {item.badge}
                  </Badge>
                )}
              </a>
            );
          })}
        </nav>

        {/* Bottom navigation */}
        <div className="border-t px-2 py-4">
          {bottomNavItems.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="group flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
              title={!expanded ? item.label : undefined}
            >
              <item.icon className="h-5 w-5 shrink-0 text-muted-foreground group-hover:text-accent-foreground" />
              {expanded && <span className="truncate">{item.label}</span>}
            </a>
          ))}
        </div>

        {/* Collapse toggle — desktop only */}
        <div className="hidden border-t p-2 md:block">
          <Button
            variant="ghost"
            size="icon"
            className="w-full"
            onClick={() => setExpanded(!expanded)}
            aria-label={expanded ? "Collapse sidebar" : "Expand sidebar"}
          >
            {expanded ? (
              <ChevronLeft className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </Button>
        </div>
      </aside>
    </>
  );
}
