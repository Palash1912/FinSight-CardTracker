"use client";

import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
  BarChart,
  Bar,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  useMonthlySpend,
  useCategorySpend,
  useCardSpend,
} from "@/hooks/use-analytics";
import { formatCurrency } from "@/lib/utils";
import { TrendingUp, PieChart as PieIcon, BarChart3 } from "lucide-react";

const CATEGORY_COLORS = [
  "#3b82f6", // blue
  "#10b981", // emerald
  "#f59e0b", // amber
  "#8b5cf6", // purple
  "#ec4899", // pink
  "#06b6d4", // cyan
  "#f97316", // orange
  "#64748b", // slate
];

export function SpendCharts() {
  const { data: monthlyData, isLoading: monthlyLoading } = useMonthlySpend();
  const { data: categoryData, isLoading: categoryLoading } = useCategorySpend();
  const { data: cardData, isLoading: cardLoading } = useCardSpend();

  const formattedMonthly = monthlyData?.map((m) => ({
    name: m.month,
    spend: parseFloat(m.total_spend) || 0,
  })) || [];

  const formattedCategory = categoryData?.map((c) => ({
    name: c.category,
    value: parseFloat(c.total_spend) || 0,
    percentage: c.percentage,
  })) || [];

  const formattedCard = cardData?.map((c) => ({
    name: `${c.issuer} ${c.card_name}`,
    spend: parseFloat(c.total_spend) || 0,
  })) || [];

  const hasSpendData = formattedMonthly.some((m) => m.spend > 0) || formattedCategory.length > 0;

  if (!hasSpendData && !monthlyLoading && !categoryLoading) {
    return null;
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Monthly Spend Trend */}
      <Card className="border-border/80">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-base font-semibold flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-primary" />
            Monthly Spending Trend
          </CardTitle>
          <span className="text-xs text-muted-foreground">Debits over time</span>
        </CardHeader>
        <CardContent className="pt-2">
          {monthlyLoading ? (
            <div className="h-64 animate-pulse bg-muted/40 rounded-lg" />
          ) : formattedMonthly.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-xs text-muted-foreground">
              No transaction history available yet.
            </div>
          ) : (
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={formattedMonthly}
                  margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="spendGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.2} />
                  <XAxis
                    dataKey="name"
                    tickLine={false}
                    axisLine={false}
                    tick={{ fontSize: 11, fill: "currentColor", opacity: 0.7 }}
                  />
                  <YAxis
                    tickLine={false}
                    axisLine={false}
                    tick={{ fontSize: 11, fill: "currentColor", opacity: 0.7 }}
                    tickFormatter={(val) => `₹${val >= 1000 ? `${(val / 1000).toFixed(0)}k` : val}`}
                  />
                  <Tooltip
                    formatter={(val: number | string | undefined) => [
                      formatCurrency(Number(val) || 0),
                      "Total Spend",
                    ]}
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      borderColor: "hsl(var(--border))",
                      borderRadius: "8px",
                      fontSize: "12px",
                      color: "hsl(var(--foreground))",
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="spend"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#spendGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Category Spend Breakdown */}
      <Card className="border-border/80">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-base font-semibold flex items-center gap-2">
            <PieIcon className="h-4 w-4 text-emerald-500" />
            Spend by Category
          </CardTitle>
          <span className="text-xs text-muted-foreground">All cards</span>
        </CardHeader>
        <CardContent className="pt-2">
          {categoryLoading ? (
            <div className="h-64 animate-pulse bg-muted/40 rounded-lg" />
          ) : formattedCategory.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-xs text-muted-foreground">
              No categorized transactions yet.
            </div>
          ) : (
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={formattedCategory}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {formattedCategory.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(val: number | string | undefined) => [
                      formatCurrency(Number(val) || 0),
                      "Spend",
                    ]}
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      borderColor: "hsl(var(--border))",
                      borderRadius: "8px",
                      fontSize: "12px",
                      color: "hsl(var(--foreground))",
                    }}
                  />
                  <Legend
                    layout="horizontal"
                    verticalAlign="bottom"
                    align="center"
                    iconType="circle"
                    formatter={(val: string) => (
                      <span className="text-xs text-muted-foreground">{val}</span>
                    )}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
