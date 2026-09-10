"use client";

import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Link from "next/link";
import { ExternalLink, Check, Copy } from "lucide-react";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export function MarkdownRenderer({ content, className = "" }: MarkdownRendererProps) {
  return (
    <div className={`prose-friday text-xs sm:text-sm leading-relaxed space-y-2 select-text ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // 1. Real Clickable Links
          a({ href, children }) {
            const isExternal =
              href &&
              (href.startsWith("http://") ||
                href.startsWith("https://") ||
                href.startsWith("mailto:") ||
                href.startsWith("//"));

            if (isExternal) {
              return (
                <a
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="inline-flex items-center gap-1 font-medium text-cyan-400 hover:text-cyan-300 underline decoration-cyan-500/50 hover:decoration-cyan-400 underline-offset-2 transition-colors cursor-pointer"
                >
                  <span>{children}</span>
                  <ExternalLink className="w-3 h-3 inline-block shrink-0 opacity-70" />
                </a>
              );
            }

            if (href && (href.startsWith("/") || href.startsWith("#"))) {
              return (
                <Link
                  href={href}
                  className="font-medium text-cyan-400 hover:text-cyan-300 underline decoration-cyan-500/50 hover:decoration-cyan-400 underline-offset-2 transition-colors"
                >
                  {children}
                </Link>
              );
            }

            return (
              <span className="text-cyan-400 underline decoration-cyan-500/30">
                {children}
              </span>
            );
          },

          // 2. Headings
          h1({ children }) {
            return (
              <h1 className="text-base sm:text-lg font-bold text-slate-100 mt-4 mb-2 pb-1 border-b border-slate-800">
                {children}
              </h1>
            );
          },
          h2({ children }) {
            return (
              <h2 className="text-sm sm:text-base font-semibold text-slate-100 mt-3 mb-1.5">
                {children}
              </h2>
            );
          },
          h3({ children }) {
            return (
              <h3 className="text-xs sm:text-sm font-semibold text-cyan-300 mt-2.5 mb-1">
                {children}
              </h3>
            );
          },

          // 3. Paragraphs & Emphasis
          p({ children }) {
            return <p className="leading-relaxed mb-2 last:mb-0">{children}</p>;
          },
          strong({ children }) {
            return <strong className="font-semibold text-slate-100">{children}</strong>;
          },
          em({ children }) {
            return <em className="italic text-slate-200">{children}</em>;
          },

          // 4. Lists
          ul({ children }) {
            return (
              <ul className="list-disc list-outside ml-4 space-y-1 my-2 text-slate-300">
                {children}
              </ul>
            );
          },
          ol({ children }) {
            return (
              <ol className="list-decimal list-outside ml-4 space-y-1 my-2 text-slate-300">
                {children}
              </ol>
            );
          },
          li({ children }) {
            return <li className="leading-relaxed pl-0.5">{children}</li>;
          },

          // 5. Code & Code Blocks
          code({ className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || "");
            const codeString = String(children).replace(/\n$/, "");
            const isInline = !match && !codeString.includes("\n");

            if (isInline) {
              return (
                <code
                  className="px-1.5 py-0.5 rounded bg-slate-950/80 border border-slate-800 text-cyan-300 font-mono text-[11px] sm:text-xs"
                  {...props}
                >
                  {children}
                </code>
              );
            }

            return <CodeBlock language={match ? match[1] : ""} code={codeString} />;
          },

          // 6. Blockquote
          blockquote({ children }) {
            return (
              <blockquote className="border-l-2 border-cyan-500 pl-3 my-2.5 italic text-slate-400 bg-slate-950/40 py-1 rounded-r">
                {children}
              </blockquote>
            );
          },

          // 7. Tables (GitHub Flavored Markdown)
          table({ children }) {
            return (
              <div className="overflow-x-auto my-3 rounded-xl border border-slate-800 shadow-inner">
                <table className="min-w-full divide-y divide-slate-800 text-xs text-left">
                  {children}
                </table>
              </div>
            );
          },
          thead({ children }) {
            return <thead className="bg-slate-950 text-cyan-400 font-mono">{children}</thead>;
          },
          tbody({ children }) {
            return <tbody className="divide-y divide-slate-800/60 bg-slate-900/40">{children}</tbody>;
          },
          tr({ children }) {
            return <tr className="hover:bg-slate-800/30 transition-colors">{children}</tr>;
          },
          th({ children }) {
            return <th className="px-3 py-2 font-semibold tracking-wider">{children}</th>;
          },
          td({ children }) {
            return <td className="px-3 py-2 text-slate-300">{children}</td>;
          },
          hr() {
            return <hr className="my-3 border-slate-800" />;
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

function CodeBlock({ language, code }: { language: string; code: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  };

  return (
    <div className="my-3 rounded-xl bg-slate-950 border border-slate-800 overflow-hidden font-mono text-xs shadow-md">
      <div className="flex items-center justify-between px-3.5 py-1.5 bg-slate-900/80 border-b border-slate-800 text-[11px] text-slate-400">
        <span className="font-mono text-cyan-400 font-medium">
          {language || "code"}
        </span>
        <button
          type="button"
          onClick={handleCopy}
          aria-label="Copy code to clipboard"
          className="flex items-center gap-1 text-[10px] text-slate-400 hover:text-slate-200 transition-colors px-2 py-0.5 rounded bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-emerald-400" />
              <span className="text-emerald-400">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <div className="p-3.5 overflow-x-auto text-slate-200">
        <pre className="font-mono leading-relaxed">
          <code>{code}</code>
        </pre>
      </div>
    </div>
  );
}

