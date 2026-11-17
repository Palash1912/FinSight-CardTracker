"use client";

import React, { useState } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import {
  Download,
  FileSpreadsheet,
  Trash2,
  Database,
  ShieldAlert,
  ShieldCheck,
  CheckCircle,
  HardDrive,
  Terminal,
  Lock,
  Mail,
  AlertTriangle,
} from "lucide-react";

export default function SettingsPage() {
  const [exporting, setExporting] = useState(false);
  const [purging, setPurging] = useState(false);
  const [purgeSuccess, setPurgeSuccess] = useState(false);

  const handleJsonExport = async () => {
    try {
      setExporting(true);
      const data = await api.get<Record<string, unknown>>("/data/export");
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `finsight_export_${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export failed", err);
      alert("Failed to export JSON data.");
    } finally {
      setExporting(false);
    }
  };

  const handleCsvExport = () => {
    window.location.href = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/data/transactions.csv`;
  };

  const handlePurge = async () => {
    if (
      confirm(
        "⚠️ CAUTION: Are you absolutely sure you want to permanently purge all data? This deletes all cards, statements, transactions, payments, rewards, and files. This cannot be undone."
      )
    ) {
      try {
        setPurging(true);
        await api.delete("/data/purge");
        setPurgeSuccess(true);
        setTimeout(() => {
          window.location.href = "/";
        }, 2000);
      } catch (err) {
        console.error("Purge failed", err);
        alert("Failed to purge data.");
      } finally {
        setPurging(false);
      }
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header title="Settings & Security" />

        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
          <div className="mx-auto max-w-4xl space-y-8">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-foreground">
                Settings & Data Sovereignty
              </h1>
              <p className="text-sm text-muted-foreground mt-1">
                Manage data portability, database backups, security headers, and account privacy.
              </p>
            </div>

            {purgeSuccess && (
              <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs text-rose-500 flex items-center gap-2">
                <CheckCircle className="h-5 w-5 shrink-0" />
                <span>All user data and files have been permanently wiped. Redirecting...</span>
              </div>
            )}

            {/* Section 1: Data Portability & Export */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Download className="h-5 w-5 text-primary" />
                  <div>
                    <CardTitle className="text-base font-semibold">
                      Data Portability & Export (GDPR Compliant)
                    </CardTitle>
                    <CardDescription className="text-xs">
                      Export your complete financial records, cards, statement summaries, and transaction history.
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-xs text-muted-foreground leading-relaxed">
                  FinSight AI is self-hosted and privacy-first. Your financial data is stored locally in your private database and file storage. You can download an offline copy anytime.
                </p>

                <div className="flex flex-wrap gap-3">
                  <Button
                    onClick={handleJsonExport}
                    disabled={exporting}
                    className="gap-2 text-xs font-semibold shadow-sm"
                  >
                    <Download className="h-4 w-4" />
                    {exporting ? "Generating Export..." : "Download Full Data (JSON)"}
                  </Button>

                  <Button
                    variant="outline"
                    onClick={handleCsvExport}
                    className="gap-2 text-xs font-semibold shadow-sm"
                  >
                    <FileSpreadsheet className="h-4 w-4 text-emerald-500" />
                    Export Transactions (CSV)
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Section 2: Automated Database Backup & Recovery */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Database className="h-5 w-5 text-primary" />
                  <div>
                    <CardTitle className="text-base font-semibold">
                      Database Backup & Restoration
                    </CardTitle>
                    <CardDescription className="text-xs">
                      Snapshot and restore your PostgreSQL database via CLI utilities.
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-3 sm:grid-cols-2 text-xs">
                  <div className="p-3 rounded-lg bg-muted/40 border space-y-1">
                    <span className="font-semibold text-foreground flex items-center gap-1.5">
                      <HardDrive className="h-4 w-4 text-primary" />
                      Storage Provider
                    </span>
                    <p className="text-muted-foreground text-[11px]">
                      Local Filesystem Storage (`./storage`)
                    </p>
                  </div>

                  <div className="p-3 rounded-lg bg-muted/40 border space-y-1">
                    <span className="font-semibold text-foreground flex items-center gap-1.5">
                      <ShieldCheck className="h-4 w-4 text-emerald-500" />
                      Database Engine
                    </span>
                    <p className="text-muted-foreground text-[11px]">
                      PostgreSQL 16 (Single-User Isolated)
                    </p>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5">
                    <Terminal className="h-4 w-4" />
                    CLI Backup & Restore Commands:
                  </div>
                  <pre className="p-3 rounded-lg bg-zinc-950 text-zinc-100 font-mono text-xs overflow-x-auto">
                    <code>
                      # Create timestamped database backup in ./backups/&#10;
                      bash scripts/backup.sh&#10;&#10;
                      # Restore from backup archive&#10;
                      bash scripts/restore.sh backups/finsight_backup_YYYYMMDD_HHMMSS.sql.gz
                    </code>
                  </pre>
                </div>
              </CardContent>
            </Card>

            {/* Section 3: Security & Privacy Hardening */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Lock className="h-5 w-5 text-emerald-500" />
                  <div>
                    <CardTitle className="text-base font-semibold">
                      Security Hardening & Protection
                    </CardTitle>
                    <CardDescription className="text-xs">
                      Active cryptographic and HTTP defense measures.
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3 text-xs text-muted-foreground">
                <div className="grid gap-2">
                  <div className="flex items-center justify-between p-2.5 rounded-lg bg-muted/30">
                    <span className="font-medium text-foreground">OAuth Token Cryptography</span>
                    <Badge variant="outline" className="text-emerald-500 border-emerald-500/30">
                      Fernet AES-128-CBC + HMAC
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between p-2.5 rounded-lg bg-muted/30">
                    <span className="font-medium text-foreground">Credit Card Security</span>
                    <Badge variant="outline" className="text-emerald-500 border-emerald-500/30">
                      Zero PAN / CVV / PIN Storage
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between p-2.5 rounded-lg bg-muted/30">
                    <span className="font-medium text-foreground">Defensive Headers</span>
                    <Badge variant="outline" className="text-emerald-500 border-emerald-500/30">
                      CSP, X-Frame DENY, nosniff
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between p-2.5 rounded-lg bg-muted/30">
                    <span className="font-medium text-foreground">Financial Arithmetic</span>
                    <Badge variant="outline" className="text-emerald-500 border-emerald-500/30">
                      Strict Numeric(18, 4) & Zero LLM Math
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Section 4: Danger Zone */}
            <Card className="border-rose-500/40 bg-rose-500/5">
              <CardHeader>
                <div className="flex items-center gap-2 text-rose-500">
                  <AlertTriangle className="h-5 w-5" />
                  <CardTitle className="text-base font-semibold">Danger Zone</CardTitle>
                </div>
                <CardDescription className="text-xs">
                  Irreversible actions that permanently delete your financial data.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div>
                    <div className="text-sm font-semibold text-foreground">
                      Purge All User Financial Data
                    </div>
                    <div className="text-xs text-muted-foreground mt-0.5">
                      Permanently wipes all credit cards, statements, transactions, payments, rewards, and file storage.
                    </div>
                  </div>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={handlePurge}
                    disabled={purging}
                    className="gap-2 text-xs font-semibold shrink-0"
                  >
                    <Trash2 className="h-4 w-4" />
                    {purging ? "Purging..." : "Purge All Data"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
}
