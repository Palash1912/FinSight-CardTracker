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
import { cn } from "@/lib/utils";

interface MetricCard {
  label: string;
  value: string;
  change?: string;
  changeType?: "positive" | "negative" | "neutral";
  icon: React.ElementType;
  iconColor: string;
}

const metrics: MetricCard[] = [
  {
    label: "Total Outstanding",
    value: "₹0.00",
    change: undefined,
    icon: IndianRupee,
    iconColor: "text-blue-600 bg-blue-100",
  },
  {
    label: "Upcoming Dues",
    value: "0 cards",
    change: undefined,
    icon: CalendarClock,
    iconColor: "text-amber-600 bg-amber-100",
  },
  {
    label: "Monthly Spend",
    value: "₹0.00",
    change: undefined,
    icon: TrendingDown,
    iconColor: "text-emerald-600 bg-emerald-100",
  },
  {
    label: "Rewards Earned",
    value: "₹0.00",
    change: undefined,
    icon: Award,
    iconColor: "text-purple-600 bg-purple-100",
  },
];

export function OverviewCards() {
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
              <p
                className={cn(
                  "mt-1 text-xs",
                  metric.changeType === "positive"
                    ? "text-success"
                    : metric.changeType === "negative"
                      ? "text-destructive"
                      : "text-muted-foreground"
                )}
              >
                {metric.change}
              </p>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
