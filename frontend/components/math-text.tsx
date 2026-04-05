"use client";

import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeRaw from "rehype-raw";
import "katex/dist/katex.min.css";

/**
 * Renders question text with full markdown formatting AND LaTeX math.
 *
 * Handles:
 *   - Tables  (pipe syntax: | A | B | C |)
 *   - Bold / italic  (**bold**, *italic*)
 *   - Line breaks and paragraphs
 *   - Inline math   \( ... \)
 *   - Display math  \[ ... \]
 *   - Bullet lists
 */

interface MathTextProps {
  text: string;
  className?: string;
  block?: boolean; // kept for API compatibility — always renders as block internally
}

export function MathText({ text, className }: MathTextProps) {
  return (
    <div className={className}>
      <ReactMarkdown
        remarkPlugins={[remarkMath]}
        rehypePlugins={[rehypeKatex, rehypeRaw]}
        components={{
          // Tables — styled to look like clean exam-paper tables
          table: ({ children }) => (
            <div className="overflow-x-auto my-3">
              <table className="w-full border-collapse text-sm">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-muted/60">{children}</thead>
          ),
          th: ({ children }) => (
            <th className="border border-border px-3 py-2 text-left font-semibold text-foreground">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="border border-border px-3 py-2 text-foreground">
              {children}
            </td>
          ),
          tr: ({ children }) => (
            <tr className="even:bg-muted/20">{children}</tr>
          ),
          // Paragraphs — avoid double spacing inside question text
          p: ({ children }) => (
            <p className="mb-1 last:mb-0 leading-relaxed">{children}</p>
          ),
          // Bold
          strong: ({ children }) => (
            <strong className="font-semibold text-foreground">{children}</strong>
          ),
          // Unordered lists (e.g. bullet points in multi-part questions)
          ul: ({ children }) => (
            <ul className="list-disc pl-5 space-y-0.5 my-1">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal pl-5 space-y-0.5 my-1">{children}</ol>
          ),
          li: ({ children }) => (
            <li className="leading-relaxed">{children}</li>
          ),
          // Blockquotes — used for indented sub-parts sometimes
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-border pl-3 text-muted-foreground my-1">
              {children}
            </blockquote>
          ),
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  );
}
