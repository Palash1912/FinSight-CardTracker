"use client";

import React, { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useStatementReview, useConfirmStatement, useDeleteStatement } from "@/hooks/use-statements";
import { useCards } from "@/hooks/use-cards";
import { formatCurrency, formatDate } from "@/lib/utils";
import {
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  FileCheck,
  Calendar,
  Wallet,
  Clock,
  Trash2,
  ShieldAlert,
} from "lucide-react";

const CATEGORY_OPTIONS = [
  "Shopping",
  "Dining",
  "Groceries",
  "Travel",
  "Entertainment",
  "Utilities",
  "Fuel",
  "Fees & Charges",
  "Payment",
  "Uncategorized",
];

export default function StatementReviewPage() {
  const params = useParams();
  const router = useRouter();
  const statementId = params.id as string;

  const { data: statement, isLoading, error } = useStatementReview(statementId);
  const { data: cards } = useCards(true);
  const confirmMutation = useConfirmStatement();
  const deleteMutation = useDeleteStatement();

  const [excludedIds, setExcludedIds] = useState<string[]>([]);
  const [updateBalance, setUpdateBalance] = useState<boolean>(true);

  const card = cards?.find((c) => c.id === statement?.card_id);

  const toggleExclude = (txId: string) => {
    setExcludedIds((prev) =>
      prev.includes(txId) ? prev.filter((id) => id !== txId) : [...prev, txId]
    );
  };

  const handleConfirm = async () => {
    if (!statement) return;
    try {
      await confirmMutation.mutateAsync({
        id: statement.id,
        request: {
          excluded_transaction_ids: excludedIds,
          update_card_balance: updateBalance,
        },
      });
      router.push(`/transactions?statement_id=${statement.id}`);
    } catch (err) {
      alert("Failed to confirm import. Please try again.");
    }
  };

  const handleDiscard = async () => {
    if (!statement) return;
    if (confirm("Discard this statement and discard extracted transactions?")) {
      try {
        await deleteMutation.mutateAsync(statement.id);
        router.push("/statements");
      } catch (err) {
        alert("Failed to discard statement.");
      }
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-screen overflow-hidden bg-background">
        <Sidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
          <Header title="Statement Review" />
          <main className="flex-1 p-8">
            <Card className="h-96 animate-pulse bg-muted/40" />
          </main>
        </div>
      </div>
    );
  }

  if (error || !statement) {
    return (
      <div className="flex h-screen overflow-hidden bg-background">
        <Sidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
          <Header title="Statement Review" />
          <main className="flex-1 p-8">
            <Card className="border-destructive/40 bg-destructive/10 p-8 text-center">
              <ShieldAlert className="mx-auto h-12 w-12 text-destructive" />
              <h3 className="mt-3 text-lg font-semibold text-destructive">
                Failed to load statement review
              </h3>
              <p className="mt-1 text-sm text-muted-foreground">
                {error instanceof Error ? error.message : "Statement not found"}
              </p>
              <Button variant="outline" className="mt-4" asChild>
                <Link href="/statements">Back to Statements</Link>
              </Button>
            </Card>
          </main>
        </div>
      </div>
    );
  }

  const activeTransactions = statement.transactions.filter(
    (t) => !excludedIds.includes(t.id)
  );

  const activeDebits = activeTransactions
    .filter((t) => t.txn_type === "debit")
    .reduce((sum, t) => sum + (parseFloat(t.amount) || 0), 0);

  const activeCredits = activeTransactions
    .filter((t) => t.txn_type === "credit")
    .reduce((sum, t) => sum + (parseFloat(t.amount) || 0), 0);

  const activeNet = activeDebits - activeCredits;
  const targetDue = parseFloat(statement.total_amount_due) || 0;
  const isReconciled = targetDue > 0 ? Math.abs(activeNet - targetDue) < 1.0 : true;

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header title="Statement Review & Reconciliation" />
        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
          <div className="mx-auto max-w-7xl space-y-6">
            {/* Top Navigation */}
            <div className="flex items-center justify-between">
              <Button variant="ghost" size="sm" asChild className="gap-2">
                <Link href="/statements">
                  <ArrowLeft className="h-4 w-4" />
                  Back to Statements
                </Link>
              </Button>

              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="text-destructive hover:bg-destructive/10"
                  onClick={handleDiscard}
                  disabled={confirmMutation.isPending || deleteMutation.isPending}
                >
                  <Trash2 className="h-4 w-4 mr-1.5" />
                  Discard Statement
                </Button>
                <Button
                  size="sm"
                  className="gap-2 shadow-sm"
                  onClick={handleConfirm}
                  disabled={confirmMutation.isPending}
                >
                  <FileCheck className="h-4 w-4" />
                  {confirmMutation.isPending ? "Confirming..." : "Confirm & Import to Ledger"}
                </Button>
              </div>
            </div>

            {/* Reconciliation Summary Card */}
            <Card className="border-border/80 overflow-hidden">
              <CardHeader className="bg-muted/30 pb-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <CardTitle className="text-xl font-bold flex items-center gap-2">
                      {card ? `${card.issuer} ${card.card_name}` : "Credit Card"}
                      {card && (
                        <span className="font-mono text-sm text-muted-foreground font-normal">
                          (•••• {card.last_four_digits})
                        </span>
                      )}
                    </CardTitle>
                    <p className="text-xs text-muted-foreground mt-1">
                      File: {statement.file_name} • Parser: {statement.parser_used.toUpperCase()}
                    </p>
                  </div>

                  {isReconciled ? (
                    <Badge variant="success" className="gap-1.5 py-1 px-3 text-xs w-fit">
                      <CheckCircle2 className="h-4 w-4" />
                      Reconciliation Matched
                    </Badge>
                  ) : (
                    <Badge variant="warning" className="gap-1.5 py-1 px-3 text-xs w-fit">
                      <AlertTriangle className="h-4 w-4" />
                      Discrepancy Detected
                    </Badge>
                  )}
                </div>
              </CardHeader>

              <CardContent className="p-6">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center sm:text-left">
                  <div className="rounded-xl bg-muted/40 p-3.5 border">
                    <span className="text-xs text-muted-foreground">Statement Due Amount</span>
                    <div className="text-lg font-bold text-foreground mt-0.5">
                      {formatCurrency(statement.total_amount_due)}
                    </div>
                  </div>

                  <div className="rounded-xl bg-muted/40 p-3.5 border">
                    <span className="text-xs text-muted-foreground">Extracted Debits</span>
                    <div className="text-lg font-bold text-rose-600 dark:text-rose-400 mt-0.5">
                      {formatCurrency(activeDebits)}
                    </div>
                  </div>

                  <div className="rounded-xl bg-muted/40 p-3.5 border">
                    <span className="text-xs text-muted-foreground">Extracted Credits</span>
                    <div className="text-lg font-bold text-emerald-600 dark:text-emerald-400 mt-0.5">
                      {formatCurrency(activeCredits)}
                    </div>
                  </div>

                  <div className="rounded-xl bg-muted/40 p-3.5 border">
                    <span className="text-xs text-muted-foreground">Net Calculated</span>
                    <div className="text-lg font-bold text-foreground mt-0.5">
                      {formatCurrency(activeNet)}
                    </div>
                  </div>
                </div>

                {/* Import options */}
                <div className="mt-4 pt-4 border-t flex items-center justify-between text-xs text-muted-foreground">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={updateBalance}
                      onChange={(e) => setUpdateBalance(e.target.checked)}
                      className="rounded border-input text-primary focus:ring-primary h-4 w-4"
                    />
                    <span className="font-medium text-foreground">
                      Update card outstanding balance to statement total ({formatCurrency(statement.total_amount_due)})
                    </span>
                  </label>
                  <span>
                    Showing {activeTransactions.length} of {statement.transactions.length} extracted transactions
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* Extracted Transactions Review Table */}
            <Card className="border-border/80">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-semibold">
                  Extracted Transactions ({statement.transactions.length})
                </CardTitle>
                <p className="text-xs text-muted-foreground">
                  Review extracted records. Deselect any item to exclude it from the final import.
                </p>
              </CardHeader>

              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-muted/40 text-xs font-semibold text-muted-foreground border-y">
                      <tr>
                        <th className="py-3 px-4 w-10">Include</th>
                        <th className="py-3 px-4">Date</th>
                        <th className="py-3 px-4">Description</th>
                        <th className="py-3 px-4">Merchant</th>
                        <th className="py-3 px-4">Category</th>
                        <th className="py-3 px-4 text-right">Amount</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/60">
                      {statement.transactions.map((tx) => {
                        const isExcluded = excludedIds.includes(tx.id);
                        const isDebit = tx.txn_type === "debit";

                        return (
                          <tr
                            key={tx.id}
                            className={`transition-colors hover:bg-muted/20 ${
                              isExcluded ? "opacity-40 line-through bg-muted/10" : ""
                            }`}
                          >
                            <td className="py-3 px-4">
                              <input
                                type="checkbox"
                                checked={!isExcluded}
                                onChange={() => toggleExclude(tx.id)}
                                className="rounded border-input text-primary focus:ring-primary h-4 w-4"
                              />
                            </td>
                            <td className="py-3 px-4 whitespace-nowrap text-xs font-medium">
                              {formatDate(tx.transaction_date)}
                            </td>
                            <td className="py-3 px-4 max-w-xs truncate" title={tx.original_description}>
                              <div className="font-medium text-foreground truncate">
                                {tx.cleaned_description}
                              </div>
                              <div className="text-[11px] text-muted-foreground font-mono truncate">
                                {tx.original_description}
                              </div>
                            </td>
                            <td className="py-3 px-4 whitespace-nowrap text-xs">
                              {tx.merchant_name ? (
                                <Badge variant="secondary" className="font-normal text-[11px]">
                                  {tx.merchant_name}
                                </Badge>
                              ) : (
                                <span className="text-muted-foreground">—</span>
                              )}
                            </td>
                            <td className="py-3 px-4 whitespace-nowrap text-xs">
                              <Badge variant="outline" className="text-[11px]">
                                {tx.category}
                              </Badge>
                            </td>
                            <td className="py-3 px-4 text-right whitespace-nowrap">
                              <span
                                className={`font-semibold ${
                                  isDebit
                                    ? "text-foreground"
                                    : "text-emerald-600 dark:text-emerald-400"
                                }`}
                              >
                                {!isDebit && "+"}
                                {formatCurrency(tx.amount)}
                              </span>
                              <span className="ml-1 text-[10px] text-muted-foreground uppercase">
                                {tx.txn_type}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
}
