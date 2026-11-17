"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { formatCurrency } from "@/lib/utils";
import type { CapUtilizationItem } from "@/lib/types";
import { ShieldAlert, RefreshCw, Calendar } from "lucide-react";

interface CapUtilizationListProps {
  caps: CapUtilizationItem[];
  isLoading?: boolean;
}

export function CapUtilizationList({ caps, isLoading }: CapUtilizationListProps) {
  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2">
        {[1, 2].map((i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader className="h-14 bg-muted/40" />
            <CardContent className="h-28 bg-muted/20" />
          </Card>
        ))}
      </div>
    );
  }

  if (!caps || caps.length === 0) {
    return (
      <Card className="border-dashed">
        <CardContent className="py-8 text-center text-muted-foreground">
          <p className="text-sm">No active reward caps configured.</p>
          <p className="text-xs mt-1">Caps automatically monitor monthly and statement cycle limits.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {caps.map((cap) => {
        const isNearCap = cap.utilization_percentage >= 80;
        const isExhausted = cap.utilization_percentage >= 100;

        let statusBadge = (
          <Badge variant="outline" className="text-emerald-500 border-emerald-500/30 text-xs">
            Healthy
          </Badge>
        );
        let barColor = "bg-emerald-500";

        if (isExhausted) {
          statusBadge = (
            <Badge variant="destructive" className="text-xs">
              <ShieldAlert className="w-3 h-3 mr-1" />
              Exhausted
            </Badge>
          );
          barColor = "bg-rose-500";
        } else if (isNearCap) {
          statusBadge = (
            <Badge variant="outline" className="text-amber-500 border-amber-500/30 text-xs">
              <ShieldAlert className="w-3 h-3 mr-1" />
              {cap.utilization_percentage}% Used
            </Badge>
          );
          barColor = "bg-amber-500";
        }

        return (
          <Card key={`${cap.card_id}-${cap.cap_name}`} className="relative overflow-hidden">
            <CardHeader className="pb-2">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    {cap.issuer} • {cap.card_name}
                  </div>
                  <CardTitle className="text-base font-semibold mt-0.5">{cap.cap_name}</CardTitle>
                </div>
                {statusBadge}
              </div>
            </CardHeader>
            <CardContent className="space-y-3 pt-1">
              <div>
                <div className="flex justify-between text-xs mb-1.5 font-medium">
                  <span className="text-muted-foreground">
                    Consumed: {formatCurrency(cap.consumed_amount)} of {formatCurrency(cap.cap_amount)}
                  </span>
                  <span className="font-semibold">{cap.utilization_percentage}%</span>
                </div>
                <Progress value={cap.utilization_percentage} indicatorClassName={barColor} className="h-2" />
              </div>

              <div className="flex items-center justify-between pt-1 border-t text-xs text-muted-foreground">
                <span className="font-medium text-foreground">
                  Remaining: <span className="text-emerald-500">{formatCurrency(cap.remaining_amount)}</span>
                </span>
                <span className="flex items-center gap-1">
                  <Calendar className="w-3 h-3 text-muted-foreground" />
                  Resets {new Date(cap.next_reset_date).toLocaleDateString("en-IN", { month: "short", day: "numeric" })}
                </span>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
