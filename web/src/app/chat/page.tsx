"use client";

import React, { useState, useEffect, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  Send,
  Bot,
  User,
  Sparkles,
  RefreshCw,
  Terminal,
  ShieldCheck,
  Zap,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { chatApi, memoryApi } from "@/lib/api";
import { ChatMessage, ChatHistoryItem } from "@/types";

const SUGGESTED_PROMPTS = [
  "Run the full Phase 1-9 test suite and report results",
  "Summarize the health status of my active job applications",
  "Inspect the repository AST for self-healing methods",
  "What permanent facts are currently stored in my memory?",
];

function ChatContent() {
  const searchParams = useSearchParams();
  const initialPrompt = searchParams?.get("initialPrompt") ?? null;

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const history = await memoryApi.getChatHistory(15);
        if (history && history.length > 0) {
          setMessages(
            history.map((h: ChatHistoryItem, i: number) => ({
              id: `history-${i}`,
              role: (h.role === "user" ? "user" : "assistant") as "user" | "assistant",
              content: h.content,
              timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            }))
          );
        } else {
          setMessages([
            {
              id: "welcome",
              role: "assistant",
              content:
                "Greetings, Operator. I am FRIDAY, your Autonomous AI Personal Operating System. How may I assist with your development, career workflows, or system diagnostics today?",
              timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            },
          ]);
        }
      } catch {
        setMessages([
          {
            id: "welcome",
            role: "assistant",
            content:
              "Greetings, Operator. I am FRIDAY. Ready to assist with coding intelligence, diagnostics, or autonomous workflows.",
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          },
        ]);
      }
    };

    loadHistory();
  }, []);

  useEffect(() => {
    if (initialPrompt && initialPrompt.trim()) {
      sendMessage(initialPrompt.trim());
    }
  }, [initialPrompt]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await chatApi.sendMessage(text);
      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: response.reply || "Operation completed.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: `Error executing instruction: ${err?.message || "Failed to reach FRIDAY backend"}`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col space-y-4">
      <div className="flex items-center justify-between px-4 py-3 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-cyan-950 border border-cyan-800 flex items-center justify-center">
            <Bot className="w-4 h-4 text-cyan-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-semibold text-slate-100 font-mono">FRIDAY REASONING CORE</h3>
              <Badge variant="cyan" size="sm">Gemini / Groq Multi-Model</Badge>
            </div>
            <p className="text-[10px] text-slate-400">Context Memory & Tool Orchestration Active</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="emerald" size="sm" className="hidden sm:inline-flex">
            <ShieldCheck className="w-3 h-3 text-emerald-400" />
            Safety Confined
          </Badge>
        </div>
      </div>

      <Card className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 flex flex-col">
        {messages.map((msg) => {
          const isUser = msg.role === "user";
          return (
            <div
              key={msg.id}
              className={`flex items-start gap-3 max-w-3xl ${
                isUser ? "self-end flex-row-reverse" : "self-start"
              }`}
            >
              <div
                className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
                  isUser
                    ? "bg-slate-800 text-slate-200 border border-slate-700"
                    : "bg-cyan-950 border border-cyan-800 text-cyan-400 shadow-glow-cyan"
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div
                className={`rounded-2xl p-4 text-xs sm:text-sm leading-relaxed space-y-1.5 shadow-md ${
                  isUser
                    ? "bg-cyan-600 text-slate-950 font-medium rounded-tr-none"
                    : "bg-slate-900/90 text-slate-200 border border-slate-800 rounded-tl-none"
                }`}
              >
                <div className="flex items-center justify-between gap-4 text-[10px] opacity-70">
                  <span className="font-mono font-semibold">{isUser ? "Operator" : "FRIDAY"}</span>
                  <span>{msg.timestamp}</span>
                </div>
                <div className="whitespace-pre-wrap">{msg.content}</div>
              </div>
            </div>
          );
        })}

        {isLoading ? (
          <div className="flex items-start gap-3 self-start max-w-lg">
            <div className="w-8 h-8 rounded-xl bg-cyan-950 border border-cyan-800 flex items-center justify-center text-cyan-400 shadow-glow-cyan">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-4 rounded-2xl rounded-tl-none bg-slate-900 border border-slate-800 flex items-center gap-2 text-xs text-cyan-400 font-mono">
              <span className="inline-block w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
              <span>FRIDAY is processing & reasoning...</span>
            </div>
          </div>
        ) : null}

        <div ref={messagesEndRef} />
      </Card>

      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
        <span className="text-[11px] text-slate-500 font-mono shrink-0">Suggestions:</span>
        {SUGGESTED_PROMPTS.map((p, i) => (
          <button
            key={i}
            onClick={() => sendMessage(p)}
            className="shrink-0 px-3 py-1 rounded-full bg-slate-900/80 border border-slate-800 text-slate-400 hover:text-cyan-300 hover:border-cyan-800 text-[11px] transition"
          >
            {p}
          </button>
        ))}
      </div>

      <form onSubmit={handleFormSubmit} className="relative">
        <textarea
          rows={2}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              sendMessage(input);
            }
          }}
          placeholder="Ask a question, request code modifications, or trigger autonomous tasks (Press Enter to send)..."
          className="w-full pl-4 pr-14 py-3 rounded-2xl bg-slate-950 border border-slate-700 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 resize-none font-sans"
        />
        <Button
          type="submit"
          variant="primary"
          size="icon"
          disabled={!input.trim() || isLoading}
          className="absolute right-3 top-1/2 -translate-y-1/2 rounded-xl"
        >
          <Send className="w-4 h-4" />
        </Button>
      </form>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs font-mono text-cyan-400">Loading chat stream...</div>}>
      <ChatContent />
    </Suspense>
  );
}
