"use client";

import React, { useState, useEffect, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  Send,
  Bot,
  User,
  ShieldCheck,
  Volume2,
  VolumeX,
  Database,
  Briefcase,
  Layers,
  Code2,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { chatApi, memoryApi } from "@/lib/api";
import { ChatMessage, ChatHistoryItem } from "@/types";
import { MarkdownRenderer } from "@/components/chat/MarkdownRenderer";
import { useFridayVoice } from "@/lib/voice";

const CATEGORIZED_SUGGESTIONS = [
  {
    category: "Career Intelligence",
    icon: Briefcase,
    prompts: [
      "Summarize the health status of my active job applications",
      "Analyze matches for Senior Python Engineer roles",
    ],
  },
  {
    category: "Profile & Memory",
    icon: Database,
    prompts: [
      "What permanent facts are currently stored in my memory?",
      "Recall my profile preferences and skills",
    ],
  },
  {
    category: "Architecture & Concepts",
    icon: Layers,
    prompts: [
      "Explain the AST-guarded self-healing workflow",
      "Explain FRIDAY's multi-model AI architecture and fallback mechanism",
    ],
  },
  {
    category: "Code & Verification",
    icon: Code2,
    prompts: [
      "How does the AST Guard prevent invalid code modifications?",
      "What verification phases are implemented in the test suite?",
    ],
  },
];

function ChatContent() {
  const searchParams = useSearchParams();
  const initialPrompt = searchParams?.get("initialPrompt") ?? null;

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [activeCategory, setActiveCategory] = useState<string>("Career Intelligence");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Default Voice Experience
  const { isVoiceEnabled, isSpeaking, toggleVoice, speak, stop } = useFridayVoice();

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
                "Greetings, Operator. I am **FRIDAY**, your Autonomous AI Software-Engineering & Career Intelligence Partner. How may I assist with your codebases, applications, or system diagnostics today?",
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
              "Greetings, Operator. I am **FRIDAY**. Ready to assist with coding intelligence, diagnostics, or autonomous workflows.",
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

    // Interrupt previous speech if a new query is submitted
    stop();

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
      const replyContent = response.reply || "Operation completed.";
      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: replyContent,
        context_sources: response.context_sources,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, assistantMsg]);

      // Speak assistant reply if voice is enabled
      speak(replyContent);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: `Error executing instruction: ${err?.message || "Failed to reach FRIDAY backend. Please check network connectivity and backend service status."}`,
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

  const currentCategorySuggestions =
    CATEGORIZED_SUGGESTIONS.find((c) => c.category === activeCategory)?.prompts ||
    CATEGORIZED_SUGGESTIONS[0].prompts;

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col space-y-3">
      {/* 1. TOP HEADER & TELEMETRY */}
      <div className="flex items-center justify-between px-4 py-2.5 rounded-2xl bg-slate-900/70 border border-slate-800/80 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-cyan-950 border border-cyan-800 flex items-center justify-center">
            <Bot className="w-4 h-4 text-cyan-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-semibold text-slate-100 font-mono">FRIDAY REASONING CORE</h3>
              <Badge variant="cyan" size="sm">Gemini / Groq / OpenRouter</Badge>
            </div>
            <p className="text-[10px] text-slate-400">AST Guard • Self-Healing • Truthful Context</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Default Voice Experience Toggle */}
          <button
            type="button"
            onClick={toggleVoice}
            aria-label={isVoiceEnabled ? "Mute voice assistant" : "Unmute voice assistant"}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-mono border transition-all ${
              isVoiceEnabled
                ? "bg-cyan-950/80 border-cyan-700/80 text-cyan-300 shadow-[0_0_12px_rgba(0,240,255,0.2)]"
                : "bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200"
            }`}
          >
            {isVoiceEnabled ? (
              <>
                <Volume2 className="w-3.5 h-3.5 text-cyan-400" />
                <span>Voice ON</span>
                {isSpeaking && (
                  <span className="flex items-center gap-0.5 ml-1">
                    <span className="w-1 h-2 bg-cyan-400 animate-pulse rounded-full" />
                    <span className="w-1 h-3 bg-cyan-300 animate-pulse delay-75 rounded-full" />
                    <span className="w-1 h-1.5 bg-cyan-400 animate-pulse delay-150 rounded-full" />
                  </span>
                )}
              </>
            ) : (
              <>
                <VolumeX className="w-3.5 h-3.5 text-slate-500" />
                <span>Voice OFF</span>
              </>
            )}
          </button>

          <Badge variant="emerald" size="sm" className="hidden sm:inline-flex">
            <ShieldCheck className="w-3 h-3 text-emerald-400" />
            Safety Confined
          </Badge>
        </div>
      </div>

      {/* 2. CHAT STREAM CARD */}
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
                className={`rounded-2xl p-4 text-xs sm:text-sm leading-relaxed space-y-2 shadow-md ${
                  isUser
                    ? "bg-cyan-600 text-slate-950 font-medium rounded-tr-none"
                    : "bg-slate-900/90 text-slate-200 border border-slate-800 rounded-tl-none"
                }`}
              >
                <div className="flex items-center justify-between gap-4 text-[10px] opacity-70">
                  <span className="font-mono font-semibold">{isUser ? "Operator" : "FRIDAY"}</span>
                  <span>{msg.timestamp}</span>
                </div>

                {isUser ? (
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                ) : (
                  <MarkdownRenderer content={msg.content} />
                )}

                {/* Truthful Context Indicator Pill */}
                {!isUser && msg.context_sources && msg.context_sources.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5 pt-2 mt-2 border-t border-slate-800/80 text-[11px] font-mono">
                    <span className="flex items-center gap-1 text-[10px] text-slate-400 font-sans uppercase tracking-wider">
                      <Database className="w-3 h-3 text-cyan-400" /> Grounded Context:
                    </span>
                    {msg.context_sources.map((src, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center px-2 py-0.5 rounded-md bg-cyan-950/70 border border-cyan-800/70 text-cyan-300 text-[10px]"
                      >
                        {src}
                      </span>
                    ))}
                  </div>
                )}
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

      {/* 3. CATEGORIZED SUGGESTIONS */}
      <div className="space-y-1.5">
        {/* Category Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs scrollbar-none">
          {CATEGORIZED_SUGGESTIONS.map((cat) => {
            const Icon = cat.icon;
            const isActive = activeCategory === cat.category;
            return (
              <button
                key={cat.category}
                type="button"
                onClick={() => setActiveCategory(cat.category)}
                className={`shrink-0 flex items-center gap-1.5 px-3 py-1 rounded-lg text-[11px] font-mono transition-all ${
                  isActive
                    ? "bg-slate-800 text-cyan-300 border border-cyan-700/60 shadow-sm"
                    : "bg-slate-950/60 border border-slate-800/60 text-slate-400 hover:text-slate-200"
                }`}
              >
                <Icon className="w-3 h-3 text-cyan-400" />
                <span>{cat.category}</span>
              </button>
            );
          })}
        </div>

        {/* Actionable Suggestion Prompts */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
          {currentCategorySuggestions.map((prompt, i) => (
            <button
              key={i}
              type="button"
              onClick={() => sendMessage(prompt)}
              className="shrink-0 px-3 py-1.5 rounded-full bg-slate-900/90 border border-slate-800 text-slate-300 hover:text-cyan-300 hover:border-cyan-700/80 hover:bg-cyan-950/40 text-[11px] transition-all font-sans"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* 4. CHAT INPUT FORM */}
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
