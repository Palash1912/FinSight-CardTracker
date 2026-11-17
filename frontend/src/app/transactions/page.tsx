"use client";

import React, { useState } from "react";
import { useSearchParams } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useTransactions, useUpdateTransaction } from "@/hooks/use-transactions";
import { useCards } from "@/hooks/use-cards";
import { formatCurrency, formatDate } from "@/lib/utils";
import type { Transaction } from "@/lib/types";
import {
  ArrowLeftRight,
  Search,
  Filter,
  Calendar,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
} from "lucide-react";

const CATEGORIES = [
  "All Categories",
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

export default function TransactionsPage() {
  const searchParams = useSearchParams();
  const initialStatementId = searchParams.get("statement_id") || undefined;
  const initialCardId = searchParams.get("card_id") || undefined;

  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All Categories");
  const [selectedCardId, setSelectedCardId] = useState<string>(initialCardId || "");
  const [selectedType, setSelectedType] = useState<"all" | "debit" | "credit">("all");
  const [page, setPage] = useState(1);
  const pageSize = 25;

  const { data: cards } = useCards(true);
  const updateMutation = useUpdateTransaction();

  const { data, isLoading, error, refetch } = useTransactions({
    search: search.trim() || undefined,
    category: selectedCategory !== "All Categories" ? selectedCategory : undefined,
    cardId: selectedCardId || undefined,
    statementId: initialStatementId,
    txnType: selectedType !== "all" ? selectedType : undefined,
    page,
    pageSize,
  });

  const getCardInfo = (cardId: string) => {
    return cards?.find((c) => c.id === cardId);
  };

  const handleCategoryChange = async (txn: Transaction, newCategory: string) => {
    try {
      await updateMutation.mutateAsync({
        id: txn.id,
        data: { category: newCategory },
      });
    } catch (err) {
      console.error("Failed to update category:", err);
    }
  };

  const totalPages = data ? Math.ceil(data.total / pageSize) : 1;

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header title="Transactions" />
        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
          <div className="mx-auto max-w-7xl space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-foreground">
                  Transaction Management
                </h1>
                <p className="text-sm text-muted-foreground mt-1">
                  View, categorize, and audit imported card transactions.
                </p>
              </div>

              {initialStatementId && (
                <Badge variant="outline" className="h-7 px-3 text-xs">
                  Filtered by Statement: {initialStatementId.slice(0, 8)}...
                </Badge>
              )}
            </div>

            {/* Filters Bar */}
            <Card className="p-4 border-border/80">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {/* Search */}
                <div className="relative">
                  <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search merchant or description..."
                    className="pl-9"
                    value={search}
                    onChange={(e) => {
                      setSearch(e.target.value);
                      setPage(1);
                    }}
                  />
                </div>

                {/* Card Filter */}
                <div>
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    value={selectedCardId}
                    onChange={(e) => {
                      setSelectedCardId(e.target.value);
                      setPage(1);
                    }}
                  >
                    <option value="">All Cards</option>
                    {cards?.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.issuer} {c.card_name} (•••• {c.last_four_digits})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Category Filter */}
                <div>
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    value={selectedCategory}
                    onChange={(e) => {
                      setSelectedCategory(e.target.value);
                      setPage(1);
                    }}
                  >
                    {CATEGORIES.map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Type Filter */}
                <div className="flex rounded-md border bg-muted/40 p-1">
                  <button
                    type="button"
                    className={`flex-1 rounded-sm py-1 text-xs font-medium transition-colors ${
                      selectedType === "all"
                        ? "bg-background text-foreground shadow-sm"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                    onClick={() => {
                      setSelectedType("all");
                      setPage(1);
                    }}
                  >
                    All
                  </button>
                  <button
                    type="button"
                    className={`flex-1 rounded-sm py-1 text-xs font-medium transition-colors ${
                      selectedType === "debit"
                        ? "bg-background text-foreground shadow-sm"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                    onClick={() => {
                      setSelectedType("debit");
                      setPage(1);
                    }}
                  >
                    Debits
                  </button>
                  <button
                    type="button"
                    className={`flex-1 rounded-sm py-1 text-xs font-medium transition-colors ${
                      selectedType === "credit"
                        ? "bg-background text-foreground shadow-sm"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                    onClick={() => {
                      setSelectedType("credit");
                      setPage(1);
                    }}
                  >
                    Credits
                  </button>
                </div>
              </div>
            </Card>

            {/* Transactions Table */}
            <Card className="border-border/80 overflow-hidden">
              <CardContent className="p-0">
                {isLoading ? (
                  <div className="space-y-3 p-6">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <div key={i} className="h-10 animate-pulse bg-muted/40 rounded" />
                    ))}
                  </div>
                ) : error ? (
                  <div className="p-8 text-center">
                    <ShieldAlert className="mx-auto h-12 w-12 text-destructive" />
                    <h3 className="mt-3 text-lg font-semibold text-destructive">
                      Error loading transactions
                    </h3>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {error instanceof Error ? error.message : "Network error"}
                    </p>
                    <Button variant="outline" className="mt-4" onClick={() => refetch()}>
                      Retry
                    </Button>
                  </div>
                ) : !data || data.items.length === 0 ? (
                  <div className="p-12 text-center">
                    <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-muted text-muted-foreground">
                      <ArrowLeftRight className="h-7 w-7" />
                    </div>
                    <h3 className="mt-4 text-base font-semibold text-foreground">
                      No transactions found
                    </h3>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Try adjusting your search criteria or upload a new statement.
                    </p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead className="bg-muted/40 text-xs font-semibold text-muted-foreground border-b">
                        <tr>
                          <th className="py-3 px-4">Date</th>
                          <th className="py-3 px-4">Card</th>
                          <th className="py-3 px-4">Merchant / Description</th>
                          <th className="py-3 px-4">Category</th>
                          <th className="py-3 px-4">Status</th>
                          <th className="py-3 px-4 text-right">Amount</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/60">
                        {data.items.map((tx) => {
                          const card = getCardInfo(tx.card_id);
                          const isDebit = tx.txn_type === "debit";

                          return (
                            <tr key={tx.id} className="transition-colors hover:bg-muted/20">
                              <td className="py-3 px-4 whitespace-nowrap text-xs font-medium">
                                {formatDate(tx.transaction_date)}
                              </td>

                              <td className="py-3 px-4 whitespace-nowrap text-xs">
                                {card ? (
                                  <div className="font-medium text-foreground">
                                    {card.issuer}
                                    <span className="ml-1 text-muted-foreground font-mono text-[11px]">
                                      •••• {card.last_four_digits}
                                    </span>
                                  </div>
                                ) : (
                                  <span className="text-muted-foreground">—</span>
                                )}
                              </td>

                              <td className="py-3 px-4 max-w-sm">
                                <div className="font-medium text-foreground truncate">
                                  {tx.merchant_name || tx.cleaned_description}
                                </div>
                                <div className="text-[11px] text-muted-foreground truncate font-mono">
                                  {tx.cleaned_description}
                                </div>
                              </td>

                              <td className="py-3 px-4 whitespace-nowrap">
                                <select
                                  className="h-7 rounded border border-input bg-transparent px-2 text-xs font-medium focus:ring-1 focus:ring-primary"
                                  value={tx.category}
                                  onChange={(e) => handleCategoryChange(tx, e.target.value)}
                                >
                                  {CATEGORIES.filter((c) => c !== "All Categories").map((c) => (
                                    <option key={c} value={c}>
                                      {c}
                                    </option>
                                  ))}
                                </select>
                              </td>

                              <td className="py-3 px-4 whitespace-nowrap">
                                <Badge variant="outline" className="text-[10px] uppercase font-mono">
                                  {tx.status}
                                </Badge>
                              </td>

                              <td className="py-3 px-4 text-right whitespace-nowrap font-medium">
                                <span
                                  className={
                                    isDebit
                                      ? "text-foreground"
                                      : "text-emerald-600 dark:text-emerald-400"
                                  }
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
                )}
              </CardContent>

              {/* Pagination bar */}
              {data && data.total > pageSize && (
                <div className="flex items-center justify-between border-t p-4 text-xs text-muted-foreground">
                  <div>
                    Showing {(page - 1) * pageSize + 1} to{" "}
                    {Math.min(page * pageSize, data.total)} of {data.total} records
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-8 w-8 p-0"
                      disabled={page <= 1}
                      onClick={() => setPage((p) => Math.max(p - 1, 1))}
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <span className="font-medium text-foreground">
                      Page {page} of {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-8 w-8 p-0"
                      disabled={page >= totalPages}
                      onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
}
