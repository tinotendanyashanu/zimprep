"use client";

import { useMemo } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";

/**
 * Renders text that may contain LaTeX math expressions.
 *
 * Supported delimiters (matching the extraction pipeline output):
 *   \( ... \)   — inline math
 *   \[ ... \]   — display (block) math
 *
 * Everything outside delimiters is rendered as escaped plain text.
 */

interface MathTextProps {
  text: string;
  className?: string;
  block?: boolean; // Use <div> instead of <span> for block-level content
}

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderMathText(text: string): string {
  // Split on \( \) and \[ \] delimiters
  // We process left-to-right, finding whichever opening delimiter comes first.
  let html = "";
  let rest = text;

  while (rest.length > 0) {
    const inlinePos = rest.indexOf("\\(");
    const displayPos = rest.indexOf("\\[");

    const hasInline = inlinePos !== -1;
    const hasDisplay = displayPos !== -1;

    // No more math delimiters — append the remainder as plain text
    if (!hasInline && !hasDisplay) {
      html += escapeHtml(rest);
      break;
    }

    // Determine which delimiter comes first
    const nextPos =
      hasInline && hasDisplay
        ? Math.min(inlinePos, displayPos)
        : hasInline
        ? inlinePos
        : displayPos;

    const isDisplay = hasDisplay && displayPos === nextPos;

    // Append plain text before the delimiter
    html += escapeHtml(rest.slice(0, nextPos));

    if (isDisplay) {
      // Display math: \[ ... \]
      rest = rest.slice(nextPos + 2);
      const end = rest.indexOf("\\]");
      if (end === -1) {
        // Unclosed — treat literally
        html += escapeHtml("\\[" + rest);
        break;
      }
      const math = rest.slice(0, end);
      rest = rest.slice(end + 2);
      try {
        html += katex.renderToString(math.trim(), {
          displayMode: true,
          throwOnError: false,
        });
      } catch {
        html += escapeHtml("\\[" + math + "\\]");
      }
    } else {
      // Inline math: \( ... \)
      rest = rest.slice(nextPos + 2);
      const end = rest.indexOf("\\)");
      if (end === -1) {
        html += escapeHtml("\\(" + rest);
        break;
      }
      const math = rest.slice(0, end);
      rest = rest.slice(end + 2);
      try {
        html += katex.renderToString(math.trim(), {
          displayMode: false,
          throwOnError: false,
        });
      } catch {
        html += escapeHtml("\\(" + math + "\\)");
      }
    }
  }

  return html;
}

export function MathText({ text, className, block }: MathTextProps) {
  const html = useMemo(() => renderMathText(text), [text]);

  if (block) {
    return (
      <div
        className={className}
        dangerouslySetInnerHTML={{ __html: html }}
      />
    );
  }

  return (
    <span
      className={className}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
