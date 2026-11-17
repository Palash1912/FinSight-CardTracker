"use client";

import React, { useState } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { CardSummaryCard } from "@/components/cards/card-summary-card";
import { CardFormDialog } from "@/components/cards/card-form-dialog";
import { useCards } from "@/hooks/use-cards";
import type { CreditCard } from "@/lib/types";
import { formatCurrency } from "@/lib/utils";
import {
  CreditCard as CardIcon,
  Plus,
  ShieldAlert,
  Wallet,
  IndianRupee,
  Layers,
  Sparkles,
} from "lucide-react";

export default function CardsPage() {
  const [includeArchived, setIncludeArchived] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedCard, setSelectedCard] = useState<CreditCard | null>(null);

  const { data: cards, isLoading, error, refetch } = useCards(includeArchived);

  const handleOpenAdd = () => {
    setSelectedCard(null);
    setDialogOpen(true);
  };

  const handleOpenEdit = (card: CreditCard) => {
    setSelectedCard(card);
    setDialogOpen(true);
  };

  // Calculate aggregated metrics
  const activeCards = cards?.filter((c) => c.status === "active") || [];
  const archivedCards = cards?.filter((c) => c.status === "archived") || [];
  const displayCards = includeArchived ? cards || [] : activeCards;

  const totalLimit = activeCards.reduce(
    (acc, c) => acc + (parseFloat(c.credit_limit) || 0),
    0
  );
  const totalBalance = activeCards.reduce(
    (acc, c) => acc + (parseFloat(c.current_balance) || 0),
    0
  );
  const totalAvailable = activeCards.reduce(
    (acc, c) => acc + (parseFloat(c.available_credit) || (parseFloat(c.credit_limit) - parseFloat(c.current_balance))),
    0
  );
  const overallUtilization = totalLimit > 0 ? (totalBalance / totalLimit) * 100 : 0;

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header title="Credit Cards" />
        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
          <div className="mx-auto max-w-7xl space-y-8">
            {/* Header row with Add Card button */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-foreground">
                  Your Credit Cards
                </h1>
                <p className="text-sm text-muted-foreground mt-1">
                  Manage your cards, billing cycles, available credit limits, and rewards.
                </p>
              </div>
              <Button onClick={handleOpenAdd} className="gap-2 shadow-sm">
                <Plus className="h-4 w-4" />
                Add New Card
              </Button>
            </div>

            {/* Quick Metrics Bar across all active cards */}
            {activeCards.length > 0 && (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <Card className="p-4 bg-card/60 backdrop-blur">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-muted-foreground">Total Credit Limit</span>
                    <Wallet className="h-4 w-4 text-primary" />
                  </div>
                  <div className="mt-2 text-xl font-bold text-foreground">
                    {formatCurrency(totalLimit)}
                  </div>
                </Card>

                <Card className="p-4 bg-card/60 backdrop-blur">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-muted-foreground">Total Outstanding</span>
                    <IndianRupee className="h-4 w-4 text-amber-500" />
                  </div>
                  <div className="mt-2 text-xl font-bold text-foreground">
                    {formatCurrency(totalBalance)}
                  </div>
                </Card>

                <Card className="p-4 bg-card/60 backdrop-blur">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-muted-foreground">Total Available</span>
                    <Sparkles className="h-4 w-4 text-emerald-500" />
                  </div>
                  <div className="mt-2 text-xl font-bold text-emerald-600 dark:text-emerald-400">
                    {formatCurrency(totalAvailable)}
                  </div>
                </Card>

                <Card className="p-4 bg-card/60 backdrop-blur">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-muted-foreground">Overall Utilization</span>
                    <Layers className="h-4 w-4 text-blue-500" />
                  </div>
                  <div className="mt-2 text-xl font-bold text-foreground">
                    {overallUtilization.toFixed(1)}%
                  </div>
                </Card>
              </div>
            )}

            {/* Filter Tabs: Active vs Archived */}
            <div className="flex items-center justify-between border-b pb-3">
              <div className="flex items-center gap-2">
                <Button
                  variant={!includeArchived ? "default" : "outline"}
                  size="sm"
                  onClick={() => setIncludeArchived(false)}
                  className="h-8 text-xs"
                >
                  Active ({activeCards.length})
                </Button>
                <Button
                  variant={includeArchived ? "default" : "outline"}
                  size="sm"
                  onClick={() => setIncludeArchived(true)}
                  className="h-8 text-xs"
                >
                  All Cards ({cards?.length || 0})
                </Button>
              </div>
            </div>

            {/* Content Area: Loading / Error / Empty / Grid */}
            {isLoading ? (
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {[1, 2, 3].map((i) => (
                  <Card key={i} className="h-96 animate-pulse bg-muted/40" />
                ))}
              </div>
            ) : error ? (
              <Card className="border-destructive/40 bg-destructive/10 p-8 text-center">
                <ShieldAlert className="mx-auto h-12 w-12 text-destructive" />
                <h3 className="mt-3 text-lg font-semibold text-destructive">
                  Unable to load credit cards
                </h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  {error instanceof Error ? error.message : "Network error"}
                </p>
                <Button variant="outline" className="mt-4" onClick={() => refetch()}>
                  Retry
                </Button>
              </Card>
            ) : displayCards.length === 0 ? (
              <Card className="border-dashed p-12 text-center">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <CardIcon className="h-8 w-8" />
                </div>
                <h3 className="mt-4 text-lg font-semibold text-foreground">
                  {includeArchived ? "No cards found" : "No active credit cards yet"}
                </h3>
                <p className="mx-auto mt-2 max-w-sm text-sm text-muted-foreground">
                  Add your credit cards to track balances, billing cycles, payment due dates, and maximize reward rules.
                </p>
                <Button onClick={handleOpenAdd} className="mt-6 gap-2">
                  <Plus className="h-4 w-4" />
                  Add Your First Card
                </Button>
              </Card>
            ) : (
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {displayCards.map((card) => (
                  <CardSummaryCard
                    key={card.id}
                    card={card}
                    onEdit={handleOpenEdit}
                  />
                ))}
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Add / Edit Card Dialog */}
      <CardFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        cardToEdit={selectedCard}
      />
    </div>
  );
}
