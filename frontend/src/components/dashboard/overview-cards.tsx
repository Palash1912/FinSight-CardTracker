"use client";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  IndianRupee,
  CalendarClock,
  TrendingDown,
  Award,
} from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";
import { useCards } from "@/hooks/use-cards";

export function OverviewCards() {
  const { data: cards, isLoading } = useCards();

  const activeCards = cards?.filter((c) => c.status === "active") || [];

  const totalOutstanding = activeCards.reduce(
    (sum, c) => sum + (parseFloat(c.current_balance) || 0),
    0
  );

  // Cards with upcoming dues in next 10 days
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const upcomingDueCards = activeCards.filter((c) => {
    if ((parseFloat(c.current_balance) || 0) <= 0) return false;
    const due = new Date(c.next_due_date);
    due.setHours(0, 0, 0, 0);
    const diffDays = Math.ceil((due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    return diffDays >= 0 && diffDays <= 10;
  });

  const metrics = [
    {
      label: "Total Outstanding",
      value: isLoading ? "..." : formatCurrency(totalOutstanding),
      change: activeCards.length > 0 ? `Across ${activeCards.length} active cards` : "No active cards",
      icon: IndianRupee,
      iconColor: "text-blue-600 bg-blue-100 dark:bg-blue-950/50 dark:text-blue-400",
    },
    {
      label: "Upcoming Dues",
      value: isLoading ? "..." : `${upcomingDueCards.length} card${upcomingDueCards.length === 1 ? "" : "s"}`,
      change: upcomingDueCards.length > 0 ? "Due within next 10 days" : "All dues settled",
      icon: CalendarClock,
      iconColor: upcomingDueCards.length > 0
        ? "text-amber-600 bg-amber-100 dark:bg-amber-950/50 dark:text-amber-400"
        : "text-emerald-600 bg-emerald-100 dark:bg-emerald-950/50 dark:text-emerald-400",
    },
    {
      label: "Monthly Spend",
      value: "₹0.00",
      change: "Import statements to track spend",
      icon: TrendingDown,
      iconColor: "text-emerald-600 bg-emerald-100 dark:bg-emerald-950/50 dark:text-emerald-400",
    },
    {
      label: "Rewards Earned",
      value: "₹0.00",
      change: "Phase 5 Rewards engine",
      icon: Award,
      iconColor: "text-purple-600 bg-purple-100 dark:bg-purple-950/50 dark:text-purple-400",
    },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {metrics.map((metric) => (
        <Card key={metric.label} className="transition-shadow hover:shadow-md">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {metric.label}
            </CardTitle>
            <div
              className={cn(
                "flex h-9 w-9 items-center justify-center rounded-lg",
                metric.iconColor
              )}
            >
              <metric.icon className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">
              {metric.value}
            </div>
            {metric.change && (
              <p className="mt-1 text-xs text-muted-foreground">
                {metric.change}
              </p>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
