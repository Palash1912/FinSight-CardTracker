"use client";

import React, { useEffect, useRef, useState } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  useConversation,
  useConversations,
  useDeleteConversation,
  useSendMessage,
} from "@/hooks/use-assistant";
import type { ChatMessage } from "@/lib/types";
import {
  Bot,
  User,
  Send,
  Sparkles,
  Plus,
  Trash2,
  Zap,
  ShieldCheck,
  ChevronRight,
  CreditCard,
  Calendar,
  AlertTriangle,
  HelpCircle,
} from "lucide-react";

const QUICK_PROMPTS = [
  {
    title: "Amazon Spend",
    prompt: "Which card gives the highest reward for ₹10,000 on Amazon?",
    icon: Sparkles,
  },
  {
    title: "Upcoming Dues",
    prompt: "What are my upcoming credit card bills and due dates?",
    icon: Calendar,
  },
  {
    title: "Spend Analytics",
    prompt: "Show my spending breakdown by category this month.",
    icon: Zap,
  },
  {
    title: "Cap Monitoring",
    prompt: "Are any of my card reward caps close to being exhausted?",
    icon: ShieldCheck,
  },
  {
    title: "Reward Audit",
    prompt: "Did I lose any rewards on my statements due to exclusions?",
    icon: AlertTriangle,
  },
];

export default function AssistantPage() {
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [inputMessage, setInputMessage] = useState("");
  const [localMessages, setLocalMessages] = useState<ChatMessage[]>([]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: conversations = [], refetch: refetchConversations } = useConversations();
  const { data: conversationData, isLoading: convLoading } = useConversation(selectedConversationId);

  const sendMutation = useSendMessage();
  const deleteMutation = useDeleteConversation();

  // Sync messages when active conversation changes
  useEffect(() => {
    if (conversationData?.messages) {
      setLocalMessages(conversationData.messages);
    } else if (!selectedConversationId) {
      setLocalMessages([]);
    }
  }, [conversationData, selectedConversationId]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [localMessages, sendMutation.isPending]);

  const handleSend = async (messageText?: string) => {
    const text = (messageText || inputMessage).trim();
    if (!text || sendMutation.isPending) return;

    // Optimistically add user message
    const tempUserMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    };
    setLocalMessages((prev) => [...prev, tempUserMsg]);
    setInputMessage("");

    try {
      const res = await sendMutation.mutateAsync({
        conversation_id: selectedConversationId,
        message: text,
      });

      setSelectedConversationId(res.conversation_id);
      setLocalMessages((prev) => [...prev, res.message]);
      refetchConversations();
    } catch (err) {
      console.error("Failed to send message", err);
    }
  };

  const handleNewChat = () => {
    setSelectedConversationId(null);
    setLocalMessages([]);
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (confirm("Delete this conversation?")) {
      await deleteMutation.mutateAsync(id);
      if (selectedConversationId === id) {
        handleNewChat();
      }
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header title="AI Financial Advisor" />

        <div className="flex flex-1 overflow-hidden">
          {/* Conversation History Sidebar */}
          <div className="hidden md:flex w-72 flex-col border-r bg-card/40 p-4 space-y-3">
            <Button
              onClick={handleNewChat}
              variant="outline"
              className="w-full justify-start gap-2 font-semibold shadow-sm"
            >
              <Plus className="h-4 w-4" />
              New Advisory Session
            </Button>

            <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-1 pt-2">
              Recent Sessions
            </div>

            <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
              {conversations.length === 0 ? (
                <div className="text-xs text-muted-foreground p-3 text-center">
                  No previous sessions.
                </div>
              ) : (
                conversations.map((conv) => {
                  const isSelected = conv.id === selectedConversationId;
                  return (
                    <div
                      key={conv.id}
                      onClick={() => setSelectedConversationId(conv.id)}
                      className={`group flex items-center justify-between p-2.5 rounded-lg text-xs cursor-pointer transition-colors ${
                        isSelected
                          ? "bg-primary/10 text-primary font-semibold"
                          : "hover:bg-muted text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      <div className="truncate flex-1 pr-2">{conv.title}</div>
                      <button
                        type="button"
                        onClick={(e) => handleDelete(e, conv.id)}
                        className="opacity-0 group-hover:opacity-100 hover:text-destructive transition-opacity"
                        title="Delete session"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Main Chat Pane */}
          <div className="flex flex-1 flex-col overflow-hidden bg-background">
            {/* Chat Messages View */}
            <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4">
              {localMessages.length === 0 ? (
                <div className="max-w-2xl mx-auto py-12 text-center space-y-6 animate-in fade-in-50">
                  <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary shadow-inner">
                    <Bot className="h-8 w-8" />
                  </div>

                  <div className="space-y-2">
                    <h2 className="text-2xl font-bold tracking-tight">FinSight AI Advisor</h2>
                    <p className="text-sm text-muted-foreground max-w-md mx-auto">
                      Intelligent rewards optimization and card management powered by verified bank rules and zero LLM arithmetic.
                    </p>
                  </div>

                  {/* Quick Prompt Cards */}
                  <div className="grid gap-2.5 sm:grid-cols-2 text-left pt-4">
                    {QUICK_PROMPTS.map((qp, idx) => {
                      const Icon = qp.icon;
                      return (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => handleSend(qp.prompt)}
                          className="flex items-start gap-3 p-3.5 rounded-xl border border-border/80 bg-card/60 hover:bg-card hover:border-primary/50 text-left transition-all shadow-sm group"
                        >
                          <div className="p-2 rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors shrink-0">
                            <Icon className="h-4 w-4" />
                          </div>
                          <div>
                            <div className="text-xs font-semibold text-foreground">
                              {qp.title}
                            </div>
                            <div className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                              {qp.prompt}
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <div className="max-w-3xl mx-auto space-y-4">
                  {localMessages.map((msg, index) => {
                    const isUser = msg.role === "user";
                    return (
                      <div
                        key={msg.id || index}
                        className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}
                      >
                        {!isUser && (
                          <div className="flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-lg bg-primary/10 text-primary mt-0.5">
                            <Bot className="h-4 w-4" />
                          </div>
                        )}

                        <div
                          className={`rounded-2xl px-4 py-3 max-w-[85%] text-sm leading-relaxed space-y-2 shadow-sm ${
                            isUser
                              ? "bg-primary text-primary-foreground ml-12"
                              : "bg-card border border-border/70 text-foreground mr-12"
                          }`}
                        >
                          {/* Tool call indicator badge */}
                          {msg.tool_calls && msg.tool_calls.length > 0 && (
                            <div className="flex flex-wrap gap-1.5 pb-1">
                              {msg.tool_calls.map((tc, tcIdx) => (
                                <Badge
                                  key={tcIdx}
                                  variant="secondary"
                                  className="text-[10px] font-mono gap-1"
                                >
                                  <Zap className="h-3 w-3 text-amber-500" />
                                  Tool: {tc.tool}
                                </Badge>
                              ))}
                            </div>
                          )}

                          {/* Message Content */}
                          <div className="whitespace-pre-wrap font-sans text-[13.5px]">
                            {msg.content}
                          </div>
                        </div>

                        {isUser && (
                          <div className="flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-lg bg-muted text-muted-foreground mt-0.5">
                            <User className="h-4 w-4" />
                          </div>
                        )}
                      </div>
                    );
                  })}

                  {sendMutation.isPending && (
                    <div className="flex gap-3 justify-start animate-in fade-in-50">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                        <Bot className="h-4 w-4" />
                      </div>
                      <div className="rounded-2xl px-4 py-3 bg-card border border-border/70 text-sm text-muted-foreground flex items-center gap-2">
                        <div className="h-2 w-2 rounded-full bg-primary animate-ping" />
                        <span>Querying deterministic financial engines...</span>
                      </div>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>

            {/* Message Input Bar */}
            <div className="p-4 border-t bg-card/60">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSend();
                }}
                className="max-w-3xl mx-auto flex items-center gap-2"
              >
                <Input
                  type="text"
                  placeholder="Ask about best cards, reward rates, spend analytics, or upcoming bills..."
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  disabled={sendMutation.isPending}
                  className="flex-1 text-sm bg-background"
                />
                <Button
                  type="submit"
                  disabled={!inputMessage.trim() || sendMutation.isPending}
                  className="gap-2 font-semibold shadow-sm"
                >
                  <Send className="h-4 w-4" />
                  <span className="hidden sm:inline">Send</span>
                </Button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
