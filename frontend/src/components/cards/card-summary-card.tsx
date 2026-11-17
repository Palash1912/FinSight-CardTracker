"use client";

import React, { useState } from "react";
import type { CreditCard } from "@/lib/types";
import { CardVisual } from "@/components/cards/card-visual";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { formatCurrency, formatDate } from "@/lib/utils";
import { useArchiveCard } from "@/hooks/use-cards";
import {
  Calendar,
  AlertTriangle,
  Clock,
  Edit2,
  Archive,
  CreditCard as CardIcon,
  CheckCircle2,
} from "lucide-react";

interface CardSummaryCardProps {
  card: CreditCard;
  onEdit: (card: CreditCard) => void;
}

export function CardSummaryCard({ card, onEdit }: CardSummaryCardProps) {
  const archiveCard = useArchiveCard();
  const [confirmArchive, setConfirmArchive] = useState(false);

  const limitNum = parseFloat(card.credit_limit) || 0;
  const balanceNum = parseFloat(card.current_balance) || 0;
  const availableNum = parseFloat(card.available_credit) || (limitNum - balanceNum);
  const utilizationRatio = limitNum > 0 ? (balanceNum / limitNum) * 100 : 0;
  const clampedUtilization = Math.min(Math.max(utilizationRatio, 0), 100);

  // Utilization color logic
  const getUtilizationColor = (util: number) => {
    if (util > 70) return "bg-rose-500";
    if (util > 30) return "bg-amber-500";
    return "bg-emerald-500";
  };

  // Due date proximity calculation
  const getDaysUntilDue = (dueDateStr: string) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const due = new Date(dueDateStr);
    due.setHours(0, 0, 0, 0);
    const diffTime = due.getTime() - today.getTime();
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  };

  const daysUntilDue = getDaysUntilDue(card.next_due_date);
  const isDueSoon = daysUntilDue >= 0 && daysUntilDue <= 5 && balanceNum > 0;
  const isOverdue = daysUntilDue < 0 && balanceNum > 0;

  const handleArchive = async () => {
    try {
      await archiveCard.mutateAsync(card.id);
      setConfirmArchive(false);
    } catch (err) {
      console.error("Failed to archive card:", err);
    }
  };

  return (
    <Card className="flex flex-col justify-between overflow-hidden transition-all duration-200 hover:shadow-md border-border/80">
      <CardHeader className="p-5 pb-3">
        {/* Physical card visual rendering */}
        <div className="flex justify-center">
          <CardVisual
            issuer={card.issuer}
            cardName={card.card_name}
            network={card.network}
            lastFourDigits={card.last_four_digits}
            status={card.status}
          />
        </div>
      </CardHeader>

      <CardContent className="space-y-4 px-5 py-2">
        {/* Balances & Limit */}
        <div className="space-y-2 rounded-xl bg-muted/40 p-3.5 border border-muted">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">Outstanding Balance</span>
            <span className="text-base font-bold text-foreground">
              {formatCurrency(balanceNum)}
            </span>
          </div>

          {/* Utilization Progress Bar */}
          <div className="space-y-1">
            <div className="flex justify-between text-[11px] text-muted-foreground">
              <span>Utilization: {utilizationRatio.toFixed(1)}%</span>
              <span>Available: {formatCurrency(availableNum)}</span>
            </div>
            <Progress
              value={clampedUtilization}
              indicatorClassName={getUtilizationColor(utilizationRatio)}
              className="h-1.5"
            />
          </div>

          <div className="flex items-center justify-between pt-1 border-t border-muted/80 text-xs">
            <span className="text-muted-foreground">Credit Limit</span>
            <span className="font-semibold text-foreground">
              {formatCurrency(limitNum)}
            </span>
          </div>
        </div>

        {/* Due Date & Billing Dates */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="rounded-lg border border-border/60 p-2.5 space-y-1">
            <div className="flex items-center gap-1.5 text-muted-foreground">
              <Calendar className="h-3.5 w-3.5" />
              <span>Next Due Date</span>
            </div>
            <div className="font-semibold text-foreground">
              {formatDate(card.next_due_date)}
            </div>
            {isOverdue ? (
              <Badge variant="destructive" className="text-[10px] py-0 px-1.5">
                Overdue
              </Badge>
            ) : isDueSoon ? (
              <Badge variant="warning" className="text-[10px] py-0 px-1.5 flex items-center gap-1">
                <AlertTriangle className="h-3 w-3" />
                Due in {daysUntilDue}d
              </Badge>
            ) : (
              <span className="text-[10px] text-muted-foreground">
                In {daysUntilDue} days
              </span>
            )}
          </div>

          <div className="rounded-lg border border-border/60 p-2.5 space-y-1">
            <div className="flex items-center gap-1.5 text-muted-foreground">
              <Clock className="h-3.5 w-3.5" />
              <span>Statement Date</span>
            </div>
            <div className="font-semibold text-foreground">
              {formatDate(card.next_statement_date)}
            </div>
            <span className="text-[10px] text-muted-foreground">
              Day {card.billing_cycle_day} of month
            </span>
          </div>
        </div>

        {/* Annual fee note */}
        <div className="flex items-center justify-between text-xs text-muted-foreground px-1">
          <span>Annual Fee:</span>
          <span className="font-medium text-foreground">
            {parseFloat(card.annual_fee) > 0
              ? formatCurrency(card.annual_fee)
              : "Free / Waived"}
          </span>
        </div>
      </CardContent>

      <CardFooter className="flex items-center justify-between border-t bg-muted/20 p-4">
        {confirmArchive ? (
          <div className="flex items-center gap-2 w-full justify-between">
            <span className="text-xs font-medium text-destructive">Archive this card?</span>
            <div className="flex gap-1.5">
              <Button
                size="sm"
                variant="outline"
                className="h-8 px-2.5 text-xs"
                onClick={() => setConfirmArchive(false)}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                variant="destructive"
                className="h-8 px-2.5 text-xs"
                onClick={handleArchive}
                disabled={archiveCard.isPending}
              >
                {archiveCard.isPending ? "Archiving..." : "Confirm"}
              </Button>
            </div>
          </div>
        ) : (
          <>
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5 h-8 text-xs"
              onClick={() => onEdit(card)}
            >
              <Edit2 className="h-3.5 w-3.5" />
              Edit
            </Button>

            {card.status === "active" && (
              <Button
                variant="ghost"
                size="sm"
                className="gap-1.5 h-8 text-xs text-muted-foreground hover:text-destructive"
                onClick={() => setConfirmArchive(true)}
              >
                <Archive className="h-3.5 w-3.5" />
                Archive
              </Button>
            )}
          </>
        )}
      </CardFooter>
    </Card>
  );
}
