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
import { useCreateCard, useUpdateCard } from "@/hooks/use-cards";
import type { CreditCard, CardNetwork } from "@/lib/types";

interface CardFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  cardToEdit?: CreditCard | null;
}

const COMMON_ISSUERS = [
  "HDFC Bank",
  "ICICI Bank",
  "SBI Card",
  "Axis Bank",
  "American Express",
  "HSBC Bank",
  "Kotak Mahindra",
  "Standard Chartered",
  "IDFC FIRST Bank",
  "RBL Bank",
];

const NETWORKS: { label: string; value: CardNetwork }[] = [
  { label: "Visa", value: "visa" },
  { label: "Mastercard", value: "mastercard" },
  { label: "American Express", value: "amex" },
  { label: "RuPay", value: "rupay" },
  { label: "Diners Club", value: "diners_club" },
];

export function CardFormDialog({
  open,
  onOpenChange,
  cardToEdit,
}: CardFormDialogProps) {
  const isEditing = Boolean(cardToEdit);
  const createCard = useCreateCard();
  const updateCard = useUpdateCard();

  const [issuer, setIssuer] = useState("");
  const [cardName, setCardName] = useState("");
  const [network, setNetwork] = useState<CardNetwork>("visa");
  const [lastFourDigits, setLastFourDigits] = useState("");
  const [billingCycleDay, setBillingCycleDay] = useState(15);
  const [paymentDueDays, setPaymentDueDays] = useState(20);
  const [creditLimit, setCreditLimit] = useState("");
  const [currentBalance, setCurrentBalance] = useState("0");
  const [annualFee, setAnnualFee] = useState("0");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (cardToEdit) {
      setIssuer(cardToEdit.issuer);
      setCardName(cardToEdit.card_name);
      setNetwork(cardToEdit.network);
      setLastFourDigits(cardToEdit.last_four_digits);
      setBillingCycleDay(cardToEdit.billing_cycle_day);
      setPaymentDueDays(cardToEdit.payment_due_days);
      setCreditLimit(cardToEdit.credit_limit);
      setCurrentBalance(cardToEdit.current_balance);
      setAnnualFee(cardToEdit.annual_fee);
    } else {
      setIssuer("");
      setCardName("");
      setNetwork("visa");
      setLastFourDigits("");
      setBillingCycleDay(15);
      setPaymentDueDays(20);
      setCreditLimit("");
      setCurrentBalance("0");
      setAnnualFee("0");
    }
    setError(null);
  }, [cardToEdit, open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!issuer.trim()) {
      setError("Please specify the card issuer bank.");
      return;
    }
    if (!cardName.trim()) {
      setError("Please enter the card name/variant.");
      return;
    }
    if (!/^\d{4}$/.test(lastFourDigits)) {
      setError("Last 4 digits must be exactly 4 numbers.");
      return;
    }
    const limitNum = parseFloat(creditLimit);
    if (isNaN(limitNum) || limitNum <= 0) {
      setError("Total credit limit must be greater than zero.");
      return;
    }
    if (billingCycleDay < 1 || billingCycleDay > 28) {
      setError("Billing cycle day must be between 1 and 28.");
      return;
    }
    if (paymentDueDays < 1 || paymentDueDays > 60) {
      setError("Payment due days must be between 1 and 60.");
      return;
    }

    try {
      if (isEditing && cardToEdit) {
        await updateCard.mutateAsync({
          id: cardToEdit.id,
          data: {
            issuer: issuer.trim(),
            card_name: cardName.trim(),
            network,
            last_four_digits: lastFourDigits,
            billing_cycle_day: Number(billingCycleDay),
            payment_due_days: Number(paymentDueDays),
            credit_limit: creditLimit,
            current_balance: currentBalance,
            annual_fee: annualFee,
          },
        });
      } else {
        await createCard.mutateAsync({
          issuer: issuer.trim(),
          card_name: cardName.trim(),
          network,
          last_four_digits: lastFourDigits,
          billing_cycle_day: Number(billingCycleDay),
          payment_due_days: Number(paymentDueDays),
          credit_limit: creditLimit,
          current_balance: currentBalance || "0",
          annual_fee: annualFee || "0",
        });
      }
      onOpenChange(false);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to save card. Please check your inputs.");
      }
    }
  };

  const isPending = createCard.isPending || updateCard.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEditing ? "Edit Credit Card" : "Add New Credit Card"}</DialogTitle>
          <DialogDescription>
            {isEditing
              ? "Update credit card parameters, limits, or billing dates."
              : "Register your credit card to track balances, billing cycles, and rewards."}
          </DialogDescription>
        </DialogHeader>

        {error && (
          <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Issuer */}
            <div className="space-y-1 sm:col-span-2">
              <Label htmlFor="issuer">Card Issuer / Bank *</Label>
              <Input
                id="issuer"
                list="issuers-list"
                placeholder="e.g. HDFC Bank, ICICI Bank"
                value={issuer}
                onChange={(e) => setIssuer(e.target.value)}
                required
              />
              <datalist id="issuers-list">
                {COMMON_ISSUERS.map((bank) => (
                  <option key={bank} value={bank} />
                ))}
              </datalist>
            </div>

            {/* Card Name */}
            <div className="space-y-1 sm:col-span-2">
              <Label htmlFor="cardName">Card Name / Variant *</Label>
              <Input
                id="cardName"
                placeholder="e.g. Sapphiro, Millennia, Amazon Pay"
                value={cardName}
                onChange={(e) => setCardName(e.target.value)}
                required
              />
            </div>

            {/* Network */}
            <div className="space-y-1">
              <Label htmlFor="network">Network *</Label>
              <select
                id="network"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                value={network}
                onChange={(e) => setNetwork(e.target.value as CardNetwork)}
              >
                {NETWORKS.map((n) => (
                  <option key={n.value} value={n.value}>
                    {n.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Last 4 Digits */}
            <div className="space-y-1">
              <Label htmlFor="lastFourDigits">Last 4 Digits *</Label>
              <Input
                id="lastFourDigits"
                maxLength={4}
                placeholder="1234"
                value={lastFourDigits}
                onChange={(e) => setLastFourDigits(e.target.value.replace(/\D/g, "").slice(0, 4))}
                required
              />
            </div>

            {/* Credit Limit */}
            <div className="space-y-1">
              <Label htmlFor="creditLimit">Total Credit Limit (₹) *</Label>
              <Input
                id="creditLimit"
                type="number"
                min="1"
                step="1"
                placeholder="150000"
                value={creditLimit}
                onChange={(e) => setCreditLimit(e.target.value)}
                required
              />
            </div>

            {/* Current Balance */}
            <div className="space-y-1">
              <Label htmlFor="currentBalance">Current Outstanding (₹)</Label>
              <Input
                id="currentBalance"
                type="number"
                min="0"
                step="1"
                placeholder="0"
                value={currentBalance}
                onChange={(e) => setCurrentBalance(e.target.value)}
              />
            </div>

            {/* Billing Cycle Day */}
            <div className="space-y-1">
              <Label htmlFor="billingCycleDay">Statement Date (Day 1–28) *</Label>
              <Input
                id="billingCycleDay"
                type="number"
                min={1}
                max={28}
                value={billingCycleDay}
                onChange={(e) => setBillingCycleDay(Number(e.target.value))}
                required
              />
            </div>

            {/* Payment Due Days */}
            <div className="space-y-1">
              <Label htmlFor="paymentDueDays">Days to Pay after Statement *</Label>
              <Input
                id="paymentDueDays"
                type="number"
                min={1}
                max={60}
                value={paymentDueDays}
                onChange={(e) => setPaymentDueDays(Number(e.target.value))}
                required
              />
            </div>

            {/* Annual Fee */}
            <div className="space-y-1 sm:col-span-2">
              <Label htmlFor="annualFee">Annual Fee (₹)</Label>
              <Input
                id="annualFee"
                type="number"
                min="0"
                step="1"
                placeholder="0"
                value={annualFee}
                onChange={(e) => setAnnualFee(e.target.value)}
              />
            </div>
          </div>

          <DialogFooter className="pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? "Saving..." : isEditing ? "Save Changes" : "Add Card"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
