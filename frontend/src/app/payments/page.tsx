"use client";

import React, { useState } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { RecordPaymentDialog } from "@/components/payments/record-payment-dialog";
import { useCardBills, usePayments, useDeletePayment } from "@/hooks/use-payments";
import { useCards } from "@/hooks/use-cards";
import { formatCurrency, formatDate } from "@/lib/utils";
import type { CardBillStatus, Payment } from "@/lib/types";
import {
  Wallet,
  Plus,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Trash2,
  Calendar,
  CreditCard as CardIcon,
  ShieldAlert,
} from "lucide-react";

export default function PaymentsPage() {
  const [recordOpen, setRecordOpen] = useState(false);
  const [selectedBill, setSelectedBill] = useState<CardBillStatus | null>(null);

  const { data: bills, isLoading: billsLoading, error: billsError } = useCardBills();
  const { data: payments, isLoading: paymentsLoading } = usePayments();
  const { data: cards } = useCards(true);
  const deleteMutation = useDeletePayment();

  const handleOpenRecordForBill = (bill: CardBillStatus) => {
    setSelectedBill(bill);
    setRecordOpen(true);
  };

  const handleOpenNewPayment = () => {
    setSelectedBill(null);
    setRecordOpen(true);
  };

  const handleDeletePayment = async (id: string) => {
    if (confirm("Delete this payment record? The card outstanding balance will be restored.")) {
      try {
        await deleteMutation.mutateAsync(id);
      } catch (err) {
        alert("Failed to delete payment.");
      }
    }
  };

  const getCardInfo = (cardId: string) => {
    return cards?.find((c) => c.id === cardId);
  };

  const getBillBadge = (status: CardBillStatus["status"], isOverdue: boolean) => {
    if (isOverdue) {
      return (
        <Badge variant="destructive" className="gap-1 text-xs">
          <AlertTriangle className="h-3 w-3" />
          Overdue
        </Badge>
      );
    }
    switch (status) {
      case "PAID":
        return (
          <Badge variant="success" className="gap-1 text-xs">
            <CheckCircle2 className="h-3 w-3" />
            Paid
          </Badge>
        );
      case "PARTIALLY_PAID":
        return (
          <Badge variant="warning" className="gap-1 text-xs">
            <Clock className="h-3 w-3" />
            Partially Paid
          </Badge>
        );
      case "UNPAID":
        return (
          <Badge variant="outline" className="border-amber-500 text-amber-600 dark:text-amber-400 text-xs">
            Unpaid
          </Badge>
        );
      case "NO_BILL":
      default:
        return (
          <Badge variant="outline" className="text-muted-foreground text-xs">
            No Active Dues
          </Badge>
        );
    }
  };

  const overdueBills = bills?.filter((b) => b.is_overdue) || [];
  const urgentBills = bills?.filter(
    (b) => !b.is_overdue && b.days_until_due >= 0 && b.days_until_due <= 5 && parseFloat(b.remaining_balance) > 0
  ) || [];

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header title="Payments & Bill Tracking" />
        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
          <div className="mx-auto max-w-7xl space-y-8">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-foreground">
                  Payments & Bill Tracking
                </h1>
                <p className="text-sm text-muted-foreground mt-1">
                  Monitor upcoming payment due dates, track partial settlements, and view payment logs.
                </p>
              </div>
              <Button onClick={handleOpenNewPayment} className="gap-2 shadow-sm">
                <Plus className="h-4 w-4" />
                Record Payment
              </Button>
            </div>

            {/* Overdue / Urgent Alert Banner */}
            {overdueBills.length > 0 && (
              <div className="flex items-center gap-3 rounded-xl border border-destructive/40 bg-destructive/10 p-4 text-destructive">
                <AlertTriangle className="h-5 w-5 shrink-0" />
                <div className="text-sm">
                  <span className="font-semibold">Action Required: </span>
                  You have {overdueBills.length} overdue credit card bill{overdueBills.length > 1 ? "s" : ""}. Pay immediately to prevent late payment charges.
                </div>
              </div>
            )}

            {urgentBills.length > 0 && overdueBills.length === 0 && (
              <div className="flex items-center gap-3 rounded-xl border border-amber-500/40 bg-amber-500/10 p-4 text-amber-700 dark:text-amber-400">
                <Clock className="h-5 w-5 shrink-0" />
                <div className="text-sm">
                  <span className="font-semibold">Upcoming Due Date: </span>
                  {urgentBills.length} credit card bill{urgentBills.length > 1 ? "s are" : " is"} due within the next 5 days.
                </div>
              </div>
            )}

            {/* Active Card Bills & Dues Table */}
            <Card className="border-border/80">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-semibold">
                  Card Bills & Outstanding Due Dates
                </CardTitle>
                <p className="text-xs text-muted-foreground">
                  Current statement billing cycle status and unpaid balance per credit card.
                </p>
              </CardHeader>

              <CardContent className="p-0">
                {billsLoading ? (
                  <div className="space-y-3 p-6">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="h-10 animate-pulse bg-muted/40 rounded" />
                    ))}
                  </div>
                ) : billsError ? (
                  <div className="p-6 text-center text-sm text-destructive">
                    Failed to load billing status.
                  </div>
                ) : !bills || bills.length === 0 ? (
                  <div className="p-8 text-center text-sm text-muted-foreground">
                    No active credit cards registered.
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead className="bg-muted/40 text-xs font-semibold text-muted-foreground border-y">
                        <tr>
                          <th className="py-3 px-4">Card</th>
                          <th className="py-3 px-4">Statement Due</th>
                          <th className="py-3 px-4">Paid</th>
                          <th className="py-3 px-4">Remaining Balance</th>
                          <th className="py-3 px-4">Due Date</th>
                          <th className="py-3 px-4">Status</th>
                          <th className="py-3 px-4 text-right">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/60">
                        {bills.map((bill) => {
                          const remainingNum = parseFloat(bill.remaining_balance) || 0;
                          return (
                            <tr key={bill.card_id} className="transition-colors hover:bg-muted/20">
                              <td className="py-3.5 px-4 whitespace-nowrap">
                                <div className="font-medium text-foreground">
                                  {bill.issuer} {bill.card_name}
                                </div>
                                <div className="text-[11px] font-mono text-muted-foreground">
                                  •••• {bill.last_four_digits}
                                </div>
                              </td>

                              <td className="py-3.5 px-4 whitespace-nowrap font-medium text-foreground">
                                {formatCurrency(bill.statement_amount)}
                              </td>

                              <td className="py-3.5 px-4 whitespace-nowrap font-medium text-emerald-600 dark:text-emerald-400">
                                {formatCurrency(bill.total_paid)}
                              </td>

                              <td className="py-3.5 px-4 whitespace-nowrap font-bold text-foreground">
                                {formatCurrency(bill.remaining_balance)}
                              </td>

                              <td className="py-3.5 px-4 whitespace-nowrap text-xs">
                                <div className="font-medium text-foreground">
                                  {formatDate(bill.due_date)}
                                </div>
                                <div className="text-[11px] text-muted-foreground">
                                  {bill.days_until_due >= 0
                                    ? `In ${bill.days_until_due} days`
                                    : `${Math.abs(bill.days_until_due)} days ago`}
                                </div>
                              </td>

                              <td className="py-3.5 px-4 whitespace-nowrap">
                                {getBillBadge(bill.status, bill.is_overdue)}
                              </td>

                              <td className="py-3.5 px-4 text-right whitespace-nowrap">
                                {remainingNum > 0 ? (
                                  <Button
                                    size="sm"
                                    className="h-8 text-xs gap-1"
                                    onClick={() => handleOpenRecordForBill(bill)}
                                  >
                                    <Wallet className="h-3.5 w-3.5" />
                                    Pay Bill
                                  </Button>
                                ) : (
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    className="h-8 text-xs"
                                    onClick={() => handleOpenRecordForBill(bill)}
                                  >
                                    Log Payment
                                  </Button>
                                )}
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

            {/* Historical Payment Log */}
            <Card className="border-border/80">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-semibold">
                  Payment History & Settlement Records
                </CardTitle>
                <p className="text-xs text-muted-foreground">
                  Audit log of all payments recorded against your credit cards.
                </p>
              </CardHeader>

              <CardContent className="p-0">
                {paymentsLoading ? (
                  <div className="space-y-3 p-6">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="h-10 animate-pulse bg-muted/40 rounded" />
                    ))}
                  </div>
                ) : !payments || payments.length === 0 ? (
                  <div className="p-8 text-center text-sm text-muted-foreground">
                    No payment records logged yet.
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead className="bg-muted/40 text-xs font-semibold text-muted-foreground border-y">
                        <tr>
                          <th className="py-3 px-4">Payment Date</th>
                          <th className="py-3 px-4">Card</th>
                          <th className="py-3 px-4">Method</th>
                          <th className="py-3 px-4">Reference / UTR</th>
                          <th className="py-3 px-4">Amount</th>
                          <th className="py-3 px-4 text-right">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/60">
                        {payments.map((p) => {
                          const card = getCardInfo(p.card_id);
                          return (
                            <tr key={p.id} className="transition-colors hover:bg-muted/20">
                              <td className="py-3 px-4 whitespace-nowrap text-xs font-medium">
                                {formatDate(p.payment_date)}
                              </td>

                              <td className="py-3 px-4 whitespace-nowrap text-xs">
                                {card ? `${card.issuer} ${card.card_name}` : "Credit Card"}
                              </td>

                              <td className="py-3 px-4 whitespace-nowrap">
                                <Badge variant="outline" className="text-[11px] uppercase">
                                  {p.payment_method.replace("_", " ")}
                                </Badge>
                              </td>

                              <td className="py-3 px-4 whitespace-nowrap text-xs font-mono text-muted-foreground">
                                {p.reference_number || "—"}
                              </td>

                              <td className="py-3 px-4 whitespace-nowrap font-semibold text-emerald-600 dark:text-emerald-400">
                                {formatCurrency(p.amount)}
                              </td>

                              <td className="py-3 px-4 text-right whitespace-nowrap">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive"
                                  title="Delete payment"
                                  onClick={() => handleDeletePayment(p.id)}
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
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
        </main>
      </div>

      <RecordPaymentDialog
        open={recordOpen}
        onOpenChange={setRecordOpen}
        preselectedBill={selectedBill}
      />
    </div>
  );
}
