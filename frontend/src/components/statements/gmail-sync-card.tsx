"use client";

import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  useDeleteEmailConnection,
  useEmailConnections,
  useEmailImports,
  useGmailAuthUrl,
  useSyncGmail,
} from "@/hooks/use-email";
import type { GmailSyncResponse } from "@/lib/types";
import {
  Mail,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Trash2,
  Sparkles,
  Inbox,
  ShieldCheck,
  FileText,
  Clock,
} from "lucide-react";

export function GmailSyncCard() {
  const [syncResult, setSyncResult] = useState<GmailSyncResponse | null>(null);
  const [showImports, setShowImports] = useState(false);

  const { data: connections = [], isLoading, refetch } = useEmailConnections();
  const { data: imports = [] } = useEmailImports(20);
  const { refetch: fetchAuthUrl } = useGmailAuthUrl();
  const syncMutation = useSyncGmail();
  const deleteMutation = useDeleteEmailConnection();

  const activeConnection = connections.length > 0 ? connections[0] : null;

  const handleConnect = async () => {
    try {
      const res = await fetchAuthUrl();
      if (res.data?.auth_url) {
        window.location.href = res.data.auth_url;
      }
    } catch (err) {
      console.error("Failed to fetch auth URL", err);
    }
  };

  const handleSync = async () => {
    try {
      const res = await syncMutation.mutateAsync({
        connection_id: activeConnection?.id || null,
        days_back: 90,
      });
      setSyncResult(res);
      setTimeout(() => setSyncResult(null), 8000);
      refetch();
    } catch (err) {
      console.error("Sync failed", err);
    }
  };

  const handleDisconnect = async (id: string) => {
    if (confirm("Disconnect this email account? Antigravity will stop monitoring it for statements.")) {
      try {
        await deleteMutation.mutateAsync(id);
      } catch (err) {
        console.error("Failed to disconnect", err);
      }
    }
  };

  return (
    <Card className="border-border/80 bg-gradient-to-br from-card to-card/60 overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-500/10 text-rose-500">
              <Mail className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <CardTitle className="text-base font-semibold">
                  Automated Gmail Statement Ingestion
                </CardTitle>
                <Badge variant="outline" className="text-[10px] text-muted-foreground">
                  Read-Only
                </Badge>
              </div>
              <CardDescription className="text-xs">
                Auto-discover and ingest password-protected/e-statements directly from bank emails.
              </CardDescription>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {activeConnection ? (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSync}
                  disabled={syncMutation.isPending || activeConnection.sync_status === "syncing"}
                  className="text-xs gap-1.5 h-8 font-semibold"
                >
                  <RefreshCw
                    className={`h-3.5 w-3.5 ${
                      syncMutation.isPending || activeConnection.sync_status === "syncing"
                        ? "animate-spin"
                        : ""
                    }`}
                  />
                  {syncMutation.isPending ? "Scanning Mailbox..." : "Sync Statements"}
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-muted-foreground hover:text-destructive"
                  onClick={() => handleDisconnect(activeConnection.id)}
                  title="Disconnect account"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </>
            ) : (
              <div className="flex gap-2">
                <Button
                  variant="default"
                  size="sm"
                  onClick={handleConnect}
                  className="text-xs gap-1.5 h-8 font-semibold"
                >
                  <Mail className="h-3.5 w-3.5" />
                  Connect Gmail
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSync}
                  disabled={syncMutation.isPending}
                  className="text-xs gap-1.5 h-8 font-semibold border-dashed"
                  title="Test discovery workflow in sandbox environment"
                >
                  <Sparkles className="h-3.5 w-3.5 text-amber-500" />
                  Simulate Discovery
                </Button>
              </div>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3 pt-0">
        {activeConnection && (
          <div className="flex flex-wrap items-center justify-between text-xs text-muted-foreground p-3 rounded-lg bg-muted/40 border">
            <div className="flex items-center gap-2 font-medium text-foreground">
              <ShieldCheck className="h-4 w-4 text-emerald-500" />
              <span>Connected: {activeConnection.email_address}</span>
            </div>
            <div className="flex items-center gap-3">
              <span>
                Last scanned:{" "}
                {activeConnection.last_synced_at
                  ? new Date(activeConnection.last_synced_at).toLocaleString("en-IN", {
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })
                  : "Never"}
              </span>
              <button
                type="button"
                onClick={() => setShowImports(!showImports)}
                className="text-primary hover:underline font-semibold"
              >
                {showImports ? "Hide History" : `Discovery Log (${imports.length})`}
              </button>
            </div>
          </div>
        )}

        {/* Sync Result Banner */}
        {syncResult && (
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-xs text-emerald-600 dark:text-emerald-400 flex items-start gap-2 animate-in fade-in-50">
            <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5" />
            <div className="space-y-0.5">
              <p className="font-semibold">Statement Discovery Completed</p>
              <p>
                Found {syncResult.messages_found} email(s), downloaded{" "}
                {syncResult.attachments_downloaded} attachment(s), created{" "}
                <span className="font-bold">{syncResult.statements_created}</span> new statement(s),{" "}
                {syncResult.duplicates_skipped} duplicates skipped.
              </p>
            </div>
          </div>
        )}

        {/* Discovery History Drawer */}
        {showImports && (
          <div className="border rounded-lg p-3 bg-background/50 space-y-2 mt-2">
            <div className="flex items-center justify-between text-xs font-semibold text-muted-foreground">
              <span>Recent Discovered Statements</span>
              <span>Status</span>
            </div>
            {imports.length === 0 ? (
              <p className="text-xs text-muted-foreground text-center py-4">
                No statement emails discovered yet. Click &quot;Sync Statements&quot; to scan.
              </p>
            ) : (
              <div className="divide-y max-h-48 overflow-y-auto">
                {imports.map((imp) => (
                  <div key={imp.id} className="py-2 flex items-center justify-between text-xs">
                    <div className="space-y-0.5 max-w-md">
                      <div className="font-medium text-foreground truncate">{imp.subject}</div>
                      <div className="text-[11px] text-muted-foreground truncate">
                        {imp.sender} • {imp.attachment_name}
                      </div>
                    </div>
                    <Badge
                      variant={
                        imp.status === "ingested"
                          ? "default"
                          : imp.status === "skipped_duplicate"
                          ? "secondary"
                          : "destructive"
                      }
                      className="text-[10px] uppercase font-bold"
                    >
                      {imp.status.replace("_", " ")}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
