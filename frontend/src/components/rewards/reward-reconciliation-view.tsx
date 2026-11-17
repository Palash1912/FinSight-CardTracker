"use client";

import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { formatCurrency } from "@/lib/utils";
import { useRewardReconciliation, useRunReconciliation } from "@/hooks/use-rewards";
import { useCards } from "@/hooks/use-cards";
import {
  AlertTriangle,
  CheckCircle2,
  Filter,
  RefreshCw,
  Search,
  Sparkles,
  Zap,
  Info,
  DollarSign,
  TrendingDown,
  ShieldAlert,
} from "lucide-react";

export function RewardReconciliationView() {
  const [selectedCardId, setSelectedCardId] = useState<string>("");
  const [discrepancyOnly, setDiscrepancyOnly] = useState<boolean>(false);

  const { data: cards = [] } = useCards();
  const {
    data: report,
    isLoading,
    isRefetching,
  } = useRewardReconciliation(selectedCardId || undefined);

  const runReconcileMutation = useRunReconciliation();

  const handleRunReconcile = async () => {
    try {
      await runReconcileMutation.mutateAsync({
        card_id: selectedCardId || null,
        force_recalculate: true,
      });
    } catch (err) {
      console.error("Reconciliation failed", err);
    }
  };

  const filteredItems = (report?.items || []).filter((item) => {
    if (discrepancyOnly && !item.is_discrepancy) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Top Aggregation KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Total Expected Rewards
            </CardTitle>
            <div className="p-1.5 bg-emerald-500/10 text-emerald-500 rounded-md">
              <Sparkles className="w-4 h-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-500">
              {isLoading ? "..." : formatCurrency(report?.total_rewards_inr || "0")}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Calculated across {report?.total_transactions || 0} transactions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Excluded Spend
            </CardTitle>
            <div className="p-1.5 bg-amber-500/10 text-amber-500 rounded-md">
              <TrendingDown className="w-4 h-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-500">
              {isLoading ? "..." : formatCurrency(report?.total_excluded_spend || "0")}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Fuel, rent, wallet loads, etc.</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Cap Losses
            </CardTitle>
            <div className="p-1.5 bg-rose-500/10 text-rose-500 rounded-md">
              <DollarSign className="w-4 h-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">
              {isLoading ? "..." : formatCurrency(report?.total_capped_lost_inr || "0")}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Rewards forfeited due to caps</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Audit Flags
            </CardTitle>
            <div className="p-1.5 bg-purple-500/10 text-purple-500 rounded-md">
              <ShieldAlert className="w-4 h-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">
              {isLoading ? "..." : report?.discrepancy_count || 0}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Exclusions & cap alerts</p>
          </CardContent>
        </Card>
      </div>

      {/* Audit & Controls Card */}
      <Card>
        <CardHeader className="pb-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <CardTitle className="text-base font-semibold">
                Transaction Reward Reconciliation Audit
              </CardTitle>
              <CardDescription>
                Deterministic audit matching each transaction against issuer terms and detecting reward leaks.
              </CardDescription>
            </div>
            <Button
              variant="default"
              size="sm"
              onClick={handleRunReconcile}
              disabled={runReconcileMutation.isPending || isRefetching}
              className="text-xs gap-1.5 font-semibold"
            >
              <RefreshCw
                className={`w-3.5 h-3.5 ${
                  runReconcileMutation.isPending || isRefetching ? "animate-spin" : ""
                }`}
              />
              {runReconcileMutation.isPending ? "Auditing..." : "Recalculate & Reconcile"}
            </Button>
          </div>

          {/* Filter Bar */}
          <div className="flex flex-wrap items-center gap-3 pt-4 border-t mt-4">
            <div className="flex items-center gap-2">
              <Filter className="w-3.5 h-3.5 text-muted-foreground" />
              <select
                value={selectedCardId}
                onChange={(e) => setSelectedCardId(e.target.value)}
                className="h-8 rounded-md border border-input bg-background px-2.5 text-xs ring-offset-background focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              >
                <option value="">All Credit Cards</option>
                {cards.map((card) => (
                  <option key={card.id} value={card.id}>
                    {card.issuer} {card.card_name} (****{card.last_four_digits})
                  </option>
                ))}
              </select>
            </div>

            <Button
              variant={discrepancyOnly ? "secondary" : "outline"}
              size="sm"
              onClick={() => setDiscrepancyOnly(!discrepancyOnly)}
              className="text-xs h-8 gap-1.5"
            >
              <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
              {discrepancyOnly ? "Showing Discrepancies Only" : "Filter Discrepancies"}
            </Button>
          </div>
        </CardHeader>

        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 text-center text-muted-foreground animate-pulse">
              Loading reward reconciliation audit...
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="p-12 text-center text-muted-foreground">
              <CheckCircle2 className="w-10 h-10 mx-auto mb-2 text-emerald-500 opacity-80" />
              <p className="font-medium text-foreground">No reconciled transactions found.</p>
              <p className="text-xs mt-1">
                Upload credit card statements or click "Recalculate & Reconcile" above.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/40 text-xs text-muted-foreground">
                    <th className="py-3 px-4 text-left font-semibold">Date</th>
                    <th className="py-3 px-4 text-left font-semibold">Transaction & Card</th>
                    <th className="py-3 px-4 text-left font-semibold">Category</th>
                    <th className="py-3 px-4 text-right font-semibold">Amount</th>
                    <th className="py-3 px-4 text-left font-semibold">Applied Rule</th>
                    <th className="py-3 px-4 text-right font-semibold">Rate</th>
                    <th className="py-3 px-4 text-right font-semibold">Expected Reward</th>
                    <th className="py-3 px-4 text-left font-semibold">Audit Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {filteredItems.map((item) => {
                    const isCredit = item.txn_type === "credit";
                    let badge = (
                      <Badge variant="outline" className="text-emerald-500 border-emerald-500/30 text-[10px]">
                        Confirmed
                      </Badge>
                    );

                    if (item.status === "excluded") {
                      badge = (
                        <Badge variant="outline" className="text-amber-500 border-amber-500/30 text-[10px]">
                          Excluded
                        </Badge>
                      );
                    } else if (item.status === "credited") {
                      badge = (
                        <Badge variant="outline" className="text-blue-500 border-blue-500/30 text-[10px]">
                          Credited
                        </Badge>
                      );
                    } else if (item.status === "reversed") {
                      badge = (
                        <Badge variant="outline" className="text-purple-500 border-purple-500/30 text-[10px]">
                          Reversed
                        </Badge>
                      );
                    }

                    return (
                      <tr
                        key={item.transaction_id}
                        className={`hover:bg-muted/30 transition-colors ${
                          item.is_discrepancy ? "bg-amber-500/5" : ""
                        }`}
                      >
                        <td className="py-3 px-4 text-xs text-muted-foreground whitespace-nowrap">
                          {item.transaction_date}
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-medium text-foreground line-clamp-1">
                            {item.description}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {item.card_name}
                            {item.merchant_name && ` • ${item.merchant_name}`}
                          </div>
                        </td>
                        <td className="py-3 px-4 text-xs">
                          <Badge variant="secondary" className="text-[10px]">
                            {item.category}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-right font-medium whitespace-nowrap">
                          <span className={isCredit ? "text-emerald-500" : ""}>
                            {isCredit ? "+" : ""}
                            {formatCurrency(item.amount)}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-xs text-muted-foreground max-w-xs">
                          <div className="font-medium text-foreground">{item.rule_name || "—"}</div>
                          {item.notes && <div className="text-[10px] truncate">{item.notes}</div>}
                        </td>
                        <td className="py-3 px-4 text-right text-xs font-semibold">
                          {item.rate_percent > 0 ? `${item.rate_percent.toFixed(1)}%` : "—"}
                        </td>
                        <td className="py-3 px-4 text-right font-bold text-emerald-500 whitespace-nowrap">
                          {formatCurrency(item.inr_value)}
                        </td>
                        <td className="py-3 px-4 text-xs whitespace-nowrap">
                          <div className="flex flex-col items-start gap-1">
                            {badge}
                            {item.is_discrepancy && item.discrepancy_reason && (
                              <span className="text-[10px] text-amber-500 flex items-center gap-1">
                                <AlertTriangle className="w-3 h-3" />
                                {item.discrepancy_reason}
                              </span>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
