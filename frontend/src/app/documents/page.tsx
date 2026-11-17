"use client";

import React, { useState } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  useDeleteDocument,
  useDiscrepancies,
  useDocuments,
  useSearchPolicies,
  useSeedPolicies,
  useUploadDocument,
} from "@/hooks/use-documents";
import type { PolicySearchResponse } from "@/lib/types";
import {
  BookOpen,
  Search,
  Upload,
  Sparkles,
  FileText,
  AlertTriangle,
  CheckCircle,
  ExternalLink,
  Trash2,
  RefreshCw,
  Sliders,
  Bookmark,
  ShieldCheck,
  HelpCircle,
} from "lucide-react";

const SAMPLE_POLICY_QUERIES = [
  "Are fuel and rent excluded on Amazon Pay ICICI?",
  "What is the partner spend cap on HDFC Millennia?",
  "Does HSBC Cashback give 10% on Swiggy and Zomato?",
  "Do reward points expire if not redeemed?",
];

export default function DocumentsPage() {
  const [activeTab, setActiveTab] = useState<"search" | "discrepancies" | "library">("search");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResult, setSearchResult] = useState<PolicySearchResponse | null>(null);
  const [seedSuccess, setSeedSuccess] = useState<string | null>(null);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);

  // Upload form states
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadDocType, setUploadDocType] = useState("policy");

  const { data: documents = [], isLoading: docsLoading, refetch: refetchDocs } = useDocuments();
  const { data: discrepancies, isLoading: discLoading } = useDiscrepancies();
  const searchMutation = useSearchPolicies();
  const seedMutation = useSeedPolicies();
  const uploadMutation = useUploadDocument();
  const deleteMutation = useDeleteDocument();

  const handleSearch = async (queryText?: string) => {
    const q = (queryText || searchQuery).trim();
    if (!q || searchMutation.isPending) return;

    try {
      const res = await searchMutation.mutateAsync({ query: q, limit: 4 });
      setSearchResult(res);
      setSearchQuery(q);
    } catch (err) {
      console.error("Policy search failed", err);
    }
  };

  const handleSeed = async () => {
    try {
      const res = await seedMutation.mutateAsync();
      setSeedSuccess(res.message);
      setTimeout(() => setSeedSuccess(null), 5000);
      refetchDocs();
    } catch (err) {
      console.error("Seeding failed", err);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;

    const formData = new FormData();
    formData.append("file", uploadFile);
    formData.append("title", uploadTitle || uploadFile.name);
    formData.append("doc_type", uploadDocType);

    try {
      await uploadMutation.mutateAsync(formData);
      setUploadDialogOpen(false);
      setUploadFile(null);
      setUploadTitle("");
    } catch (err) {
      console.error("Upload failed", err);
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm("Delete this document and all its indexed semantic chunks?")) {
      await deleteMutation.mutateAsync(id);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header title="Policy Knowledge & Document RAG" />

        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
          <div className="mx-auto max-w-7xl space-y-6">
            {/* Page Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-foreground">
                  Policy Knowledge & RAG Grounding
                </h1>
                <p className="text-sm text-muted-foreground mt-1">
                  Query official bank cardholder agreements with page-level citations and monitor rule discrepancies.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSeed}
                  disabled={seedMutation.isPending}
                  className="text-xs gap-1.5 h-8 font-semibold"
                >
                  <RefreshCw className={`h-3.5 w-3.5 ${seedMutation.isPending ? "animate-spin" : ""}`} />
                  {seedMutation.isPending ? "Seeding..." : "Seed Bank Policies"}
                </Button>
                <Button
                  size="sm"
                  onClick={() => setUploadDialogOpen(true)}
                  className="text-xs gap-1.5 h-8 font-semibold shadow-sm"
                >
                  <Upload className="h-3.5 w-3.5" />
                  Upload Policy PDF
                </Button>
              </div>
            </div>

            {seedSuccess && (
              <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
                <CheckCircle className="h-4 w-4" />
                <span>{seedSuccess}</span>
              </div>
            )}

            {/* Navigation Tabs */}
            <div className="flex border-b">
              <button
                onClick={() => setActiveTab("search")}
                className={`pb-3 px-4 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
                  activeTab === "search"
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                <Search className="h-4 w-4" />
                Policy RAG Search
              </button>
              <button
                onClick={() => setActiveTab("discrepancies")}
                className={`pb-3 px-4 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
                  activeTab === "discrepancies"
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                <AlertTriangle className="h-4 w-4" />
                Rule Discrepancies ({discrepancies?.total_discrepancies || 0})
              </button>
              <button
                onClick={() => setActiveTab("library")}
                className={`pb-3 px-4 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
                  activeTab === "library"
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                <BookOpen className="h-4 w-4" />
                Document Library ({documents.length})
              </button>
            </div>

            {/* Tab 1: Policy Search & Citations */}
            {activeTab === "search" && (
              <div className="space-y-6">
                <Card className="border-border/80 bg-gradient-to-br from-card to-card/60">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base font-semibold">
                      Ask Any Question on Bank Policy Terms
                    </CardTitle>
                    <CardDescription className="text-xs">
                      Answers are grounded strictly in uploaded terms sheets with page citations. Zero hallucinated terms.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        handleSearch();
                      }}
                      className="flex gap-2"
                    >
                      <Input
                        type="text"
                        placeholder="e.g. Which merchant transactions are excluded from reward points?"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="text-sm bg-background"
                      />
                      <Button
                        type="submit"
                        disabled={!searchQuery.trim() || searchMutation.isPending}
                        className="gap-2 font-semibold shadow-sm shrink-0"
                      >
                        <Search className="h-4 w-4" />
                        {searchMutation.isPending ? "Searching..." : "Search Policy"}
                      </Button>
                    </form>

                    {/* Quick Sample Questions */}
                    <div className="flex flex-wrap items-center gap-2 pt-1">
                      <span className="text-xs text-muted-foreground flex items-center gap-1 font-medium">
                        <Sparkles className="h-3.5 w-3.5 text-amber-500" />
                        Try asking:
                      </span>
                      {SAMPLE_POLICY_QUERIES.map((q, idx) => (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => handleSearch(q)}
                          className="text-xs bg-muted/60 hover:bg-muted text-muted-foreground hover:text-foreground px-2.5 py-1 rounded-md transition-colors"
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Search Results & Citations */}
                {searchResult && (
                  <div className="space-y-4 animate-in fade-in-50 duration-300">
                    {/* Synthesized Answer */}
                    <Card className="border-primary/30 bg-primary/5">
                      <CardHeader className="pb-2">
                        <div className="flex items-center gap-2">
                          <ShieldCheck className="h-5 w-5 text-primary" />
                          <CardTitle className="text-sm font-semibold">
                            Grounded Policy Answer
                          </CardTitle>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="text-sm leading-relaxed whitespace-pre-wrap">
                          {searchResult.synthesized_explanation}
                        </div>
                      </CardContent>
                    </Card>

                    {/* Citations List */}
                    {searchResult.citations.length > 0 && (
                      <div className="space-y-2">
                        <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                          Source Citations ({searchResult.citations.length} Verified Pages)
                        </div>

                        <div className="grid gap-3 sm:grid-cols-2">
                          {searchResult.citations.map((cite, idx) => (
                            <Card key={idx} className="border-border/80">
                              <CardContent className="p-4 space-y-2">
                                <div className="flex items-center justify-between text-xs">
                                  <Badge variant="outline" className="text-primary border-primary/30 font-medium">
                                    Page {cite.page_number}
                                  </Badge>
                                  <span className="text-muted-foreground text-[11px]">
                                    Match Score: {cite.relevance_score}
                                  </span>
                                </div>
                                <div className="font-semibold text-xs text-foreground truncate">
                                  {cite.document_title}
                                </div>
                                <p className="text-xs text-muted-foreground line-clamp-3 italic bg-muted/30 p-2 rounded">
                                  &ldquo;{cite.snippet}&rdquo;
                                </p>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Tab 2: Rule Discrepancies */}
            {activeTab === "discrepancies" && (
              <div className="space-y-4">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base font-semibold">
                      Policy Discrepancy & Devaluation Audit
                    </CardTitle>
                    <CardDescription className="text-xs">
                      Automatically detects conflicts between your configured RewardRules and official bank policy texts.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="p-0">
                    {discLoading ? (
                      <div className="p-8 text-center text-muted-foreground animate-pulse">
                        Scanning policy documents for rule discrepancies...
                      </div>
                    ) : !discrepancies || discrepancies.items.length === 0 ? (
                      <div className="p-12 text-center text-muted-foreground">
                        <CheckCircle className="h-10 w-10 mx-auto mb-2 text-emerald-500 opacity-80" />
                        <p className="font-medium text-foreground">Zero Discrepancies Detected!</p>
                        <p className="text-xs mt-1">
                          All configured reward rules, rates, caps, and exclusions match your official policy circulars.
                        </p>
                      </div>
                    ) : (
                      <div className="divide-y">
                        {discrepancies.items.map((item, idx) => (
                          <div key={idx} className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-3 text-sm">
                            <div className="space-y-1">
                              <div className="flex items-center gap-2">
                                <Badge variant="destructive" className="text-[10px] uppercase font-bold">
                                  {item.discrepancy_type.replace("_", " ")}
                                </Badge>
                                <span className="font-semibold text-foreground">
                                  {item.card_name} • {item.rule_name}
                                </span>
                              </div>
                              <p className="text-xs text-muted-foreground">{item.description}</p>
                              <div className="text-xs text-primary font-medium">
                                💡 Recommendation: {item.recommended_action}
                              </div>
                            </div>
                            <div className="text-xs text-muted-foreground whitespace-nowrap bg-muted/40 p-2 rounded shrink-0">
                              <div>Doc: {item.policy_document}</div>
                              <div>Citation: Page {item.policy_page}</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Tab 3: Document Library */}
            {activeTab === "library" && (
              <div className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {documents.map((doc) => (
                    <Card key={doc.id} className="relative overflow-hidden">
                      <CardHeader className="pb-2">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <div className="p-2 rounded-lg bg-primary/10 text-primary">
                              <FileText className="h-4 w-4" />
                            </div>
                            <div>
                              <CardTitle className="text-sm font-semibold truncate max-w-[200px]">
                                {doc.title}
                              </CardTitle>
                              <Badge variant="outline" className="text-[10px] capitalize mt-0.5">
                                {doc.doc_type.replace("_", " ")}
                              </Badge>
                            </div>
                          </div>
                          <button
                            type="button"
                            onClick={() => handleDelete(doc.id)}
                            className="text-muted-foreground hover:text-destructive p-1 rounded"
                            title="Delete document"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-2 pt-1 text-xs text-muted-foreground">
                        <div className="flex justify-between">
                          <span>Total Pages:</span>
                          <span className="font-medium text-foreground">{doc.total_pages}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Semantic Chunks:</span>
                          <span className="font-medium text-foreground">{doc.chunks_count}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>File Size:</span>
                          <span>{(doc.file_size_bytes / 1024).toFixed(1)} KB</span>
                        </div>
                        <div className="border-t pt-2 text-[11px] truncate">
                          {doc.file_name}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Upload Dialog Modal */}
      {uploadDialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <Card className="w-full max-w-md bg-card">
            <CardHeader>
              <CardTitle className="text-base font-semibold">Upload Policy Document</CardTitle>
              <CardDescription className="text-xs">
                Upload official bank cardmember agreements or terms sheets (PDF) to chunk and index for RAG.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleUploadSubmit} className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-muted-foreground">Document Title</label>
                  <Input
                    type="text"
                    required
                    placeholder="e.g. HDFC Millennia Rewards Circular 2026"
                    value={uploadTitle}
                    onChange={(e) => setUploadTitle(e.target.value)}
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-muted-foreground">Document Type</label>
                  <select
                    value={uploadDocType}
                    onChange={(e) => setUploadDocType(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="policy">General Policy</option>
                    <option value="terms_and_conditions">Terms & Conditions</option>
                    <option value="fee_schedule">Fee Schedule</option>
                    <option value="exclusion_circular">Exclusion Circular</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-muted-foreground">Select PDF File</label>
                  <Input
                    type="file"
                    accept=".pdf,application/pdf"
                    required
                    onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setUploadDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={!uploadFile || uploadMutation.isPending}>
                    {uploadMutation.isPending ? "Indexing..." : "Upload & Index"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
