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
import { useDashboardSummary } from "@/hooks/use-analytics";

export function OverviewCards() {
  const { data: summary, isLoading } = useDashboardSummary();

  const metrics = [
    {
      label: "Total Outstanding",
      value: isLoading ? "..." : formatCurrency(summary?.total_outstanding || "0"),
      change: summary && summary.active_cards_count > 0
        ? `Across ${summary.active_cards_count} active card${summary.active_cards_count > 1 ? "s" : ""}`
        : "No active cards",
      icon: IndianRupee,
      iconColor: "text-blue-600 bg-blue-100 dark:bg-blue-950/50 dark:text-blue-400",
    },
    {
      label: "Upcoming Dues",
      value: isLoading
        ? "..."
        : `${summary?.upcoming_dues_count || 0} bill${(summary?.upcoming_dues_count || 0) === 1 ? "" : "s"}`,
      change: (summary?.upcoming_dues_count || 0) > 0
        ? `${formatCurrency(summary?.upcoming_dues_total || "0")} due soon`
        : "All dues settled",
      icon: CalendarClock,
      iconColor: (summary?.upcoming_dues_count || 0) > 0
        ? "text-amber-600 bg-amber-100 dark:bg-amber-950/50 dark:text-amber-400"
        : "text-emerald-600 bg-emerald-100 dark:bg-emerald-950/50 dark:text-emerald-400",
    },
    {
      label: "Monthly Spend",
      value: isLoading ? "..." : formatCurrency(summary?.current_month_spend || "0"),
      change: summary?.spend_change_percentage != null
        ? `${summary.spend_change_percentage > 0 ? "+" : ""}${summary.spend_change_percentage}% vs last month`
        : "Current month debits",
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
