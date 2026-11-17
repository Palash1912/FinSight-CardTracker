"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { UploadStatementDialog } from "@/components/statements/upload-dialog";
import { useStatements, useDeleteStatement } from "@/hooks/use-statements";
import { useCards } from "@/hooks/use-cards";
import { formatCurrency, formatDate } from "@/lib/utils";
import type { Statement, StatementStatus } from "@/lib/types";
import {
  FileText,
  Upload,
  Calendar,
  AlertCircle,
  Trash2,
  ExternalLink,
  CheckCircle,
  Clock,
  ShieldAlert,
} from "lucide-react";

export default function StatementsPage() {
  const [uploadOpen, setUploadOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const { data: statements, isLoading, error, refetch } = useStatements();
  const { data: cards } = useCards(true);
  const deleteMutation = useDeleteStatement();

  const getCardInfo = (cardId: string) => {
    return cards?.find((c) => c.id === cardId);
  };

  const handleDelete = async (id: string) => {
    if (confirm("Are you sure you want to rollback and delete this statement and its staged transactions?")) {
      try {
        setDeletingId(id);
        await deleteMutation.mutateAsync(id);
      } catch (err) {
        alert("Failed to delete statement.");
      } finally {
        setDeletingId(null);
      }
    }
  };

  const getStatusBadge = (status: StatementStatus) => {
    switch (status) {
      case "imported":
        return (
          <Badge variant="success" className="gap-1 text-xs">
            <CheckCircle className="h-3 w-3" />
            Imported
          </Badge>
        );
      case "pending_review":
        return (
          <Badge variant="warning" className="gap-1 text-xs">
            <Clock className="h-3 w-3" />
            Pending Review
          </Badge>
        );
      case "failed":
      case "rejected":
        return (
          <Badge variant="destructive" className="gap-1 text-xs">
            <AlertCircle className="h-3 w-3" />
            {status}
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header title="Statements" />
        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
          <div className="mx-auto max-w-7xl space-y-6">
            {/* Header row */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-foreground">
                  Bank Statements
                </h1>
                <p className="text-sm text-muted-foreground mt-1">
                  Upload PDF statements to extract transactions, reconcile balances, and populate your ledger.
                </p>
              </div>
              <Button onClick={() => setUploadOpen(true)} className="gap-2 shadow-sm">
                <Upload className="h-4 w-4" />
                Upload Statement
              </Button>
            </div>

            {/* Content states */}
            {isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <Card key={i} className="h-20 animate-pulse bg-muted/40" />
                ))}
              </div>
            ) : error ? (
              <Card className="border-destructive/40 bg-destructive/10 p-8 text-center">
                <ShieldAlert className="mx-auto h-12 w-12 text-destructive" />
                <h3 className="mt-3 text-lg font-semibold text-destructive">
                  Unable to load statements
                </h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  {error instanceof Error ? error.message : "Network error"}
                </p>
                <Button variant="outline" className="mt-4" onClick={() => refetch()}>
                  Retry
                </Button>
              </Card>
            ) : !statements || statements.length === 0 ? (
              <Card className="border-dashed p-12 text-center">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <FileText className="h-8 w-8" />
                </div>
                <h3 className="mt-4 text-lg font-semibold text-foreground">
                  No statements uploaded yet
                </h3>
                <p className="mx-auto mt-2 max-w-sm text-sm text-muted-foreground">
                  Upload PDF bank statements from ICICI, HDFC, HSBC, or other banks to automatically extract and categorize transactions.
                </p>
                <Button onClick={() => setUploadOpen(true)} className="mt-6 gap-2">
                  <Upload className="h-4 w-4" />
                  Upload Your First Statement
                </Button>
              </Card>
            ) : (
              <div className="space-y-4">
                {statements.map((stmt) => {
                  const card = getCardInfo(stmt.card_id);
                  const isPending = stmt.status === "pending_review";

                  return (
                    <Card
                      key={stmt.id}
                      className="overflow-hidden transition-all hover:shadow-sm border-border/80"
                    >
                      <CardContent className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div className="flex items-start gap-3.5">
                          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary mt-0.5">
                            <FileText className="h-6 w-6" />
                          </div>

                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-base text-foreground">
                                {card ? `${card.issuer} ${card.card_name}` : "Credit Card"}
                              </span>
                              {card && (
                                <span className="font-mono text-xs text-muted-foreground">
                                  •••• {card.last_four_digits}
                                </span>
                              )}
                              {getStatusBadge(stmt.status)}
                            </div>

                            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                              <span className="flex items-center gap-1">
                                <Calendar className="h-3.5 w-3.5" />
                                Statement: {formatDate(stmt.statement_date)}
                              </span>
                              <span>Due: {formatDate(stmt.due_date)}</span>
                              <span>Parser: {stmt.parser_used.toUpperCase()}</span>
                              <span className="truncate max-w-[200px]">{stmt.file_name}</span>
                            </div>
                          </div>
                        </div>

                        <div className="flex flex-row md:flex-col md:items-end justify-between items-center gap-2 border-t md:border-t-0 pt-3 md:pt-0">
                          <div className="text-right">
                            <div className="text-xs text-muted-foreground">Amount Due</div>
                            <div className="text-lg font-bold text-foreground">
                              {formatCurrency(stmt.total_amount_due)}
                            </div>
                          </div>

                          <div className="flex items-center gap-2">
                            {isPending ? (
                              <Button size="sm" asChild className="gap-1.5 h-8 text-xs">
                                <Link href={`/statements/${stmt.id}/review`}>
                                  Review & Confirm
                                  <ExternalLink className="h-3.5 w-3.5" />
                                </Link>
                              </Button>
                            ) : (
                              <Button variant="outline" size="sm" asChild className="gap-1.5 h-8 text-xs">
                                <Link href={`/transactions?statement_id=${stmt.id}`}>
                                  Transactions
                                  <ExternalLink className="h-3.5 w-3.5" />
                                </Link>
                              </Button>
                            )}

                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive"
                              title="Delete statement and rollback"
                              onClick={() => handleDelete(stmt.id)}
                              disabled={deletingId === stmt.id}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </div>
        </main>
      </div>

      <UploadStatementDialog open={uploadOpen} onOpenChange={setUploadOpen} />
    </div>
  );
}
