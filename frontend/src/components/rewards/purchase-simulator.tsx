"use client";

import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { formatCurrency } from "@/lib/utils";
import { useRecommendCard } from "@/hooks/use-rewards";
import type { CardRecommendationResponse } from "@/lib/types";
import {
  Sparkles,
  Trophy,
  ArrowRight,
  ShieldCheck,
  Info,
  CheckCircle2,
  AlertTriangle,
  Zap,
} from "lucide-react";

const CATEGORIES = [
  "Shopping",
  "Food & Dining",
  "Travel",
  "Bills & Utilities",
  "Groceries",
  "Entertainment",
  "Fuel",
  "Other",
];

const PRESETS = [
  { merchant: "Amazon India", category: "Shopping", amount: "5000", channel: "online" as const },
  { merchant: "Swiggy", category: "Food & Dining", amount: "1200", channel: "online" as const },
  { merchant: "Flipkart", category: "Shopping", amount: "15000", channel: "online" as const },
  { merchant: "HPCL Petrol", category: "Fuel", amount: "2500", channel: "offline" as const },
];

export function PurchaseSimulator() {
  const [amount, setAmount] = useState<string>("5000");
  const [merchant, setMerchant] = useState<string>("Amazon India");
  const [category, setCategory] = useState<string>("Shopping");
  const [channel, setChannel] = useState<"online" | "offline">("online");
  const [result, setResult] = useState<CardRecommendationResponse | null>(null);

  const recommendMutation = useRecommendCard();

  const handleSimulate = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const numAmount = parseFloat(amount);
    if (isNaN(numAmount) || numAmount <= 0) return;

    try {
      const res = await recommendMutation.mutateAsync({
        amount: numAmount.toFixed(4),
        merchant: merchant.trim(),
        category,
        channel,
      });
      setResult(res);
    } catch (err) {
      console.error("Evaluation failed", err);
    }
  };

  const applyPreset = (p: (typeof PRESETS)[number]) => {
    setMerchant(p.merchant);
    setCategory(p.category);
    setAmount(p.amount);
    setChannel(p.channel);
  };

  return (
    <div className="space-y-6">
      {/* Simulation Input Card */}
      <Card className="border-border/60 bg-gradient-to-br from-card to-card/50">
        <CardHeader>
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Zap className="w-5 h-5" />
            </div>
            <div>
              <CardTitle>Pre-Purchase Card Advisor</CardTitle>
              <CardDescription>
                Simulate a planned spend to find which of your cards yields the highest net reward.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSimulate} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Spend Amount (₹)
                </label>
                <Input
                  type="number"
                  step="100"
                  min="1"
                  required
                  placeholder="e.g. 5000"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="font-medium"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Merchant Name
                </label>
                <Input
                  type="text"
                  placeholder="e.g. Amazon, Swiggy, Apple"
                  value={merchant}
                  onChange={(e) => setMerchant(e.target.value)}
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Category
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  {CATEGORIES.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Channel
                </label>
                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant={channel === "online" ? "default" : "outline"}
                    className="flex-1 text-xs"
                    onClick={() => setChannel("online")}
                  >
                    Online
                  </Button>
                  <Button
                    type="button"
                    variant={channel === "offline" ? "default" : "outline"}
                    className="flex-1 text-xs"
                    onClick={() => setChannel("offline")}
                  >
                    In-Store
                  </Button>
                </div>
              </div>
            </div>

            {/* Quick Presets */}
            <div className="flex flex-wrap items-center gap-2 pt-2">
              <span className="text-xs text-muted-foreground flex items-center gap-1 font-medium">
                <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                Quick test:
              </span>
              {PRESETS.map((p, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => applyPreset(p)}
                  className="text-xs bg-muted/60 hover:bg-muted text-muted-foreground hover:text-foreground px-2.5 py-1 rounded-md transition-colors"
                >
                  {p.merchant} (₹{p.amount})
                </button>
              ))}
            </div>

            <Button
              type="submit"
              disabled={recommendMutation.isPending}
              className="w-full sm:w-auto font-semibold gap-2"
            >
              <Zap className="w-4 h-4" />
              {recommendMutation.isPending ? "Calculating Best Card..." : "Evaluate Best Card"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Results View */}
      {result && (
        <div className="space-y-4 animate-in fade-in-50 duration-300">
          {/* Winner Card Spotlight */}
          {result.best_card ? (
            <Card className="border-amber-500/40 bg-gradient-to-r from-amber-500/10 via-card to-card relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-amber-500/10 rounded-full blur-2xl -mr-10 -mt-10" />
              <CardContent className="p-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Badge className="bg-amber-500 hover:bg-amber-600 text-black font-semibold gap-1">
                        <Trophy className="w-3.5 h-3.5" />
                        Best Card to Use
                      </Badge>
                      <Badge variant="outline" className="border-emerald-500/30 text-emerald-500">
                        Rank #1
                      </Badge>
                    </div>

                    <div>
                      <h3 className="text-2xl font-bold">
                        {result.best_card.card_name}
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        {result.best_card.issuer} • Ending in ****{result.best_card.last_four_digits}
                      </p>
                    </div>

                    <p className="text-sm font-medium text-foreground/90 max-w-xl">
                      {result.best_card.explanation}
                    </p>
                  </div>

                  <div className="bg-card/80 border border-border/80 rounded-xl p-4 text-center md:min-w-[180px] shadow-sm">
                    <div className="text-xs text-muted-foreground uppercase font-semibold tracking-wider">
                      Net Reward Value
                    </div>
                    <div className="text-3xl font-extrabold text-emerald-500 mt-1">
                      {formatCurrency(result.best_card.inr_value)}
                    </div>
                    <div className="text-xs font-semibold text-muted-foreground mt-0.5">
                      {result.best_card.effective_rate_percent.toFixed(1)}% Effective Return
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card className="border-dashed">
              <CardContent className="py-8 text-center text-muted-foreground">
                <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-amber-500" />
                <p className="font-medium">No active cards found or spend is excluded.</p>
                <p className="text-xs mt-1">Check your active cards or configured reward rules.</p>
              </CardContent>
            </Card>
          )}

          {/* All Cards Comparison Table */}
          {result.cards.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-semibold">
                  Card Comparison ({result.cards.length} Active Cards)
                </CardTitle>
                <CardDescription>
                  Comparison for a spend of {formatCurrency(result.purchase_amount)} on {merchant || "planned purchase"}.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/40 text-xs text-muted-foreground">
                        <th className="py-3 px-4 text-left font-semibold">Rank</th>
                        <th className="py-3 px-4 text-left font-semibold">Card</th>
                        <th className="py-3 px-4 text-right font-semibold">Rate</th>
                        <th className="py-3 px-4 text-right font-semibold">Estimated Return</th>
                        <th className="py-3 px-4 text-left font-semibold">Applied Rule & Reason</th>
                        <th className="py-3 px-4 text-left font-semibold">Cap Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {result.cards.map((card) => {
                        const isWinner = card.is_recommended;
                        return (
                          <tr
                            key={card.card_id}
                            className={`hover:bg-muted/30 transition-colors ${
                              isWinner ? "bg-amber-500/5 font-medium" : ""
                            }`}
                          >
                            <td className="py-3.5 px-4 font-semibold">
                              {isWinner ? (
                                <Badge className="bg-amber-500 text-black font-bold text-xs">#1</Badge>
                              ) : (
                                <span className="text-muted-foreground">#{card.rank}</span>
                              )}
                            </td>
                            <td className="py-3.5 px-4">
                              <div className="font-medium text-foreground">{card.card_name}</div>
                              <div className="text-xs text-muted-foreground">
                                {card.issuer} • ****{card.last_four_digits}
                              </div>
                            </td>
                            <td className="py-3.5 px-4 text-right font-semibold">
                              {card.effective_rate_percent.toFixed(1)}%
                            </td>
                            <td className="py-3.5 px-4 text-right">
                              <div className="font-bold text-emerald-500">
                                {formatCurrency(card.inr_value)}
                              </div>
                              <div className="text-xs text-muted-foreground capitalize">
                                {card.reward_type}
                              </div>
                            </td>
                            <td className="py-3.5 px-4 max-w-xs text-xs text-muted-foreground">
                              {card.explanation}
                            </td>
                            <td className="py-3.5 px-4 text-xs">
                              {card.remaining_cap_before !== null ? (
                                <div className="space-y-0.5">
                                  <span className="text-muted-foreground">
                                    Remaining: {formatCurrency(card.remaining_cap_after || "0")}
                                  </span>
                                  <div className="text-[10px] text-muted-foreground capitalize">
                                    ({card.cap_period} cap)
                                  </div>
                                </div>
                              ) : (
                                <span className="text-muted-foreground">No cap</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Disclaimer */}
          <div className="flex items-start gap-2 p-3 rounded-lg bg-muted/40 border text-xs text-muted-foreground">
            <Info className="w-4 h-4 shrink-0 mt-0.5 text-primary" />
            <span>{result.disclaimer}</span>
          </div>
        </div>
      )}
    </div>
  );
}
