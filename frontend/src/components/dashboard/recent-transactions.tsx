"use client";

import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ReceiptText, ArrowRight } from "lucide-react";
import { useTransactions } from "@/hooks/use-transactions";
import { formatCurrency, formatDate } from "@/lib/utils";

export function RecentTransactions() {
  const { data, isLoading } = useTransactions({ pageSize: 5 });

  const transactions = data?.items || [];

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6 space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-10 animate-pulse bg-muted/40 rounded" />
          ))}
        </CardContent>
      </Card>
    );
  }

  if (transactions.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-16">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
            <ReceiptText className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="mt-4 text-lg font-semibold text-foreground">
            No transactions yet
          </h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Upload a bank statement to see your transactions here
          </p>
          <Button variant="outline" size="sm" asChild className="mt-4">
            <Link href="/statements">Upload Statement</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-muted/40 text-xs font-semibold text-muted-foreground border-b">
            <tr>
              <th className="py-3 px-4">Date</th>
              <th className="py-3 px-4">Merchant / Description</th>
              <th className="py-3 px-4">Category</th>
              <th className="py-3 px-4 text-right">Amount</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/60">
            {transactions.map((tx) => {
              const isDebit = tx.txn_type === "debit";
              return (
                <tr key={tx.id} className="transition-colors hover:bg-muted/20">
                  <td className="py-3 px-4 whitespace-nowrap text-xs text-muted-foreground">
                    {formatDate(tx.transaction_date)}
                  </td>
                  <td className="py-3 px-4 max-w-xs truncate font-medium text-foreground">
                    {tx.merchant_name || tx.cleaned_description}
                  </td>
                  <td className="py-3 px-4 whitespace-nowrap">
                    <Badge variant="outline" className="text-[11px]">
                      {tx.category}
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

      <div className="border-t p-3 bg-muted/20 text-center">
        <Button variant="ghost" size="sm" asChild className="gap-1.5 text-xs">
          <Link href="/transactions">
            View All Transactions
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </Button>
      </div>
    </Card>
  );
}
