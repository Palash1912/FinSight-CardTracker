"use client";

import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { formatCurrency } from "@/lib/utils";
import {
  useRewardCaps,
  useRewardPrograms,
  useRewardSummary,
  useSeedRewards,
} from "@/hooks/use-rewards";
import { PurchaseSimulator } from "@/components/rewards/purchase-simulator";
import { CapUtilizationList } from "@/components/rewards/cap-utilization-card";
import { RewardReconciliationView } from "@/components/rewards/reward-reconciliation-view";
import {
  Gift,
  Coins,
  ShieldCheck,
  Zap,
  Sparkles,
  RefreshCw,
  CheckCircle,
  Percent,
  Sliders,
  ChevronRight,
  FileCheck2,
} from "lucide-react";

export default function RewardsPage() {
  const [activeTab, setActiveTab] = useState<"advisor" | "reconciliation" | "caps" | "programs">("advisor");
  const [seedSuccessMsg, setSeedSuccessMsg] = useState<string | null>(null);

  const { data: summary, isLoading: summaryLoading } = useRewardSummary();
  const { data: caps = [], isLoading: capsLoading } = useRewardCaps();
  const { data: programs = [], isLoading: programsLoading } = useRewardPrograms();
  const seedMutation = useSeedRewards();

  const handleSeed = async () => {
    try {
      const res = await seedMutation.mutateAsync();
      setSeedSuccessMsg(res.message);
      setTimeout(() => setSeedSuccessMsg(null), 5000);
    } catch (err) {
      console.error("Failed to seed rules", err);
    }
  };

  return (
    <div className="space-y-8">
      {/* Page Title & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Rewards Intelligence</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Pre-purchase card advisor, live spend cap tracking, and versioned bank reward rules.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={handleSeed}
            disabled={seedMutation.isPending}
            className="text-xs gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${seedMutation.isPending ? "animate-spin" : ""}`} />
            {seedMutation.isPending ? "Configuring..." : "Seed Bank Rules"}
          </Button>
        </div>
      </div>

      {seedSuccessMsg && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-xs text-emerald-500 flex items-center gap-2">
          <CheckCircle className="w-4 h-4" />
          <span>{seedSuccessMsg}</span>
        </div>
      )}

      {/* Top Overview KPI Metrics */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Total Cashback Earned
            </CardTitle>
            <div className="p-1.5 bg-emerald-500/10 text-emerald-500 rounded-md">
              <Gift className="w-4 h-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-500">
              {summaryLoading ? "..." : formatCurrency(summary?.total_cashback_earned || "0")}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Realized statement credits</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Points Balance
            </CardTitle>
            <div className="p-1.5 bg-amber-500/10 text-amber-500 rounded-md">
              <Coins className="w-4 h-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-500">
              {summaryLoading ? "..." : (summary?.total_points_balance || 0).toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Accumulated reward points</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Total Rewards Value
            </CardTitle>
            <div className="p-1.5 bg-primary/10 text-primary rounded-md">
              <Percent className="w-4 h-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">
              {summaryLoading ? "..." : formatCurrency(summary?.total_inr_value || "0")}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Cashback + Points net INR</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Active Programs
            </CardTitle>
            <div className="p-1.5 bg-blue-500/10 text-blue-500 rounded-md">
              <ShieldCheck className="w-4 h-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">
              {summaryLoading ? "..." : summary?.active_programs_count || programs.length}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Configured issuer reward terms</p>
          </CardContent>
        </Card>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b">
        <button
          onClick={() => setActiveTab("advisor")}
          className={`pb-3 px-4 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === "advisor"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Zap className="w-4 h-4" />
          Pre-Purchase Card Advisor
        </button>
        <button
          onClick={() => setActiveTab("reconciliation")}
          className={`pb-3 px-4 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === "reconciliation"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <FileCheck2 className="w-4 h-4" />
          Reconciliation Audit
        </button>
        <button
          onClick={() => setActiveTab("caps")}
          className={`pb-3 px-4 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === "caps"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Sliders className="w-4 h-4" />
          Reward Cap Utilization ({caps.length})
        </button>
        <button
          onClick={() => setActiveTab("programs")}
          className={`pb-3 px-4 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === "programs"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          Card Programs & Rules ({programs.length})
        </button>
      </div>

      {/* Tab 1: Pre-Purchase Simulator */}
      {activeTab === "advisor" && <PurchaseSimulator />}

      {/* Tab 2: Reward Reconciliation Audit */}
      {activeTab === "reconciliation" && <RewardReconciliationView />}

      {/* Tab 3: Cap Trackers */}
      {activeTab === "caps" && (
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold">Active Cap Monitoring</h2>
            <p className="text-xs text-muted-foreground">
              Tracks consumed vs remaining benefits across calendar months, quarters, and billing cycles.
            </p>
          </div>
          <CapUtilizationList caps={caps} isLoading={capsLoading} />
        </div>
      )}

      {/* Tab 3: Configured Reward Rules */}
      {activeTab === "programs" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">Configured Card Reward Rules</h2>
              <p className="text-xs text-muted-foreground">
                All reward rates and exclusions are deterministic, versioned, and effective-dated.
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleSeed}
              disabled={seedMutation.isPending}
              className="text-xs"
            >
              Reload Default Terms
            </Button>
          </div>

          {programsLoading ? (
            <div className="space-y-4">
              {[1, 2].map((i) => (
                <Card key={i} className="animate-pulse h-32 bg-muted/30" />
              ))}
            </div>
          ) : programs.length === 0 ? (
            <Card className="border-dashed text-center py-10">
              <CardContent className="space-y-3">
                <Gift className="w-10 h-10 mx-auto text-muted-foreground" />
                <h3 className="font-semibold text-base">No Reward Rules Configured Yet</h3>
                <p className="text-xs text-muted-foreground max-w-md mx-auto">
                  Click below to automatically configure realistic reward programs and caps for your existing cards (Amazon Pay ICICI 5%, Millennia 5%, HSBC Cashback, Flipkart Axis).
                </p>
                <Button size="sm" onClick={handleSeed} disabled={seedMutation.isPending} className="mt-2">
                  Seed Card Reward Rules
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-6">
              {programs.map((program) => (
                <Card key={program.id} className="overflow-hidden">
                  <CardHeader className="bg-muted/20 pb-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-base font-semibold">{program.program_name}</CardTitle>
                        <CardDescription className="text-xs">
                          Reward Type: <span className="capitalize font-medium text-foreground">{program.reward_type}</span>
                          {program.reward_type === "reward_points" && ` • Valuation: ₹${program.point_value_inr}/pt`}
                        </CardDescription>
                      </div>
                      <Badge variant="outline" className="text-xs capitalize">
                        {program.rules.length} Rules Active
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="p-0">
                    <div className="divide-y">
                      {program.rules.map((rule) => (
                        <div key={rule.id} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-sm">
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-foreground">{rule.rule_name}</span>
                              <Badge
                                variant={rule.rule_type === "base" ? "secondary" : "default"}
                                className="text-[10px] uppercase font-bold"
                              >
                                {rule.rule_type.replace("_", " ")}
                              </Badge>
                            </div>
                            <div className="text-xs text-muted-foreground">
                              Effective from: {rule.effective_from} • Version: v{rule.version}
                              {rule.confidence_notes && ` • ${rule.confidence_notes}`}
                            </div>
                            {rule.exclusions && rule.exclusions.length > 0 && (
                              <div className="text-xs text-muted-foreground">
                                <span className="text-amber-500 font-medium">Excludes: </span>
                                {rule.exclusions.join(", ")}
                              </div>
                            )}
                          </div>

                          <div className="flex items-center gap-4 shrink-0">
                            <div className="text-right">
                              <div className="font-bold text-emerald-500 text-base">
                                {rule.reward_rate_type === "percentage"
                                  ? `${(parseFloat(rule.reward_rate) * 100).toFixed(1)}%`
                                  : `${rule.reward_rate} pts/₹100`}
                              </div>
                              {rule.caps && rule.caps.length > 0 && (
                                <div className="text-[11px] text-muted-foreground">
                                  Cap: {formatCurrency(rule.caps[0].cap_amount)} / {rule.caps[0].cap_period}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
