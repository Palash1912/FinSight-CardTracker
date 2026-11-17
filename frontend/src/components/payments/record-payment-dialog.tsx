"use client";

import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCards } from "@/hooks/use-cards";
import { useRecordPayment } from "@/hooks/use-payments";
import { formatCurrency } from "@/lib/utils";
import type { CardBillStatus, PaymentMethod } from "@/lib/types";
import { Loader2, AlertCircle } from "lucide-react";

interface RecordPaymentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  preselectedBill?: CardBillStatus | null;
}

const PAYMENT_METHODS: { label: string; value: PaymentMethod }[] = [
  { label: "Net Banking", value: "net_banking" },
  { label: "UPI", value: "upi" },
  { label: "NEFT / RTGS", value: "neft" },
  { label: "IMPS", value: "imps" },
  { label: "Auto-Debit", value: "auto_debit" },
  { label: "Debit Card", value: "debit_card" },
  { label: "Cheque", value: "cheque" },
  { label: "Cash", value: "cash" },
];

export function RecordPaymentDialog({
  open,
  onOpenChange,
  preselectedBill,
}: RecordPaymentDialogProps) {
  const { data: cards } = useCards();
  const recordMutation = useRecordPayment();

  const [cardId, setCardId] = useState("");
  const [statementId, setStatementId] = useState<string | null>(null);
  const [amount, setAmount] = useState("");
  const [paymentDate, setPaymentDate] = useState(
    new Date().toISOString().split("T")[0]
  );
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("net_banking");
  const [refNumber, setRefNumber] = useState("");
  const [notes, setNotes] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (preselectedBill) {
      setCardId(preselectedBill.card_id);
      setStatementId(preselectedBill.statement_id);
      setAmount(preselectedBill.remaining_balance || "");
    } else if (cards && cards.length > 0 && !cardId) {
      setCardId(cards[0].id);
      setStatementId(null);
      setAmount("");
    }
    setErrorMessage(null);
  }, [preselectedBill, cards, open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!cardId) {
      setErrorMessage("Please select a credit card.");
      return;
    }

    const numAmount = parseFloat(amount);
    if (isNaN(numAmount) || numAmount <= 0) {
      setErrorMessage("Payment amount must be greater than zero.");
      return;
    }

    try {
      await recordMutation.mutateAsync({
        card_id: cardId,
        statement_id: statementId || null,
        payment_date: paymentDate,
        amount: amount,
        payment_method: paymentMethod,
        reference_number: refNumber.trim() || null,
        notes: notes.trim() || null,
      });

      onOpenChange(false);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Failed to record payment.");
      }
    }
  };

  const activeCards = cards?.filter((c) => c.status === "active") || [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Record Card Payment</DialogTitle>
          <DialogDescription>
            Log a settlement payment against your credit card bill or outstanding balance.
          </DialogDescription>
        </DialogHeader>

        {errorMessage && (
          <div className="flex items-center gap-2 rounded-md bg-destructive/15 p-3 text-xs font-medium text-destructive">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Card Selector */}
          <div className="space-y-1">
            <Label htmlFor="payment-card">Credit Card *</Label>
            <select
              id="payment-card"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={cardId}
              onChange={(e) => setCardId(e.target.value)}
              required
            >
              {activeCards.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.issuer} {c.card_name} (•••• {c.last_four_digits})
                </option>
              ))}
            </select>
          </div>

          {/* Amount & Quick fill buttons */}
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <Label htmlFor="payment-amount">Payment Amount (₹) *</Label>
              {preselectedBill && parseFloat(preselectedBill.remaining_balance) > 0 && (
                <button
                  type="button"
                  className="text-xs text-primary hover:underline font-medium"
                  onClick={() => setAmount(preselectedBill.remaining_balance)}
                >
                  Pay Remaining ({formatCurrency(preselectedBill.remaining_balance)})
                </button>
              )}
            </div>
            <Input
              id="payment-amount"
              type="number"
              step="0.01"
              min="0.01"
              placeholder="e.g. 15000"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              required
            />
          </div>

          {/* Payment Date */}
          <div className="space-y-1">
            <Label htmlFor="payment-date">Payment Date *</Label>
            <Input
              id="payment-date"
              type="date"
              value={paymentDate}
              onChange={(e) => setPaymentDate(e.target.value)}
              required
            />
          </div>

          {/* Payment Method */}
          <div className="space-y-1">
            <Label htmlFor="payment-method">Payment Channel / Mode *</Label>
            <select
              id="payment-method"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={paymentMethod}
              onChange={(e) => setPaymentMethod(e.target.value as PaymentMethod)}
            >
              {PAYMENT_METHODS.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label}
                </option>
              ))}
            </select>
          </div>

          {/* Reference Number */}
          <div className="space-y-1">
            <Label htmlFor="payment-ref">UTR / Reference Number (Optional)</Label>
            <Input
              id="payment-ref"
              placeholder="e.g. UPI/1234567890 or NEFT-REF"
              value={refNumber}
              onChange={(e) => setRefNumber(e.target.value)}
            />
          </div>

          <DialogFooter className="pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={recordMutation.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={recordMutation.isPending} className="gap-2">
              {recordMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Recording...
                </>
              ) : (
                "Record Payment"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
