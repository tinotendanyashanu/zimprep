const mathSegmentRegex = /(\$\$[\s\S]*?\$\$|\$[\s\S]*?\$)/g;
const latexInlineRegex = /\\\(([\s\S]+?)\\\)/g;
const latexBlockRegex = /\\\[([\s\S]+?)\\\]/g;
const rawLatexRegex = /(\\[A-Za-z]+(?:\{[^{}]+\}|[A-Za-z0-9^_()+\-=/:])*(?:\s*\\[A-Za-z]+(?:\{[^{}]+\}|[A-Za-z0-9^_()+\-=/:])*)*)/g;
const scientificNotationRegex = /\b(\d+(?:\.\d+)?)\s*(?:x|×)\s*10\^\{?(-?\d+)\}?\b/g;
const powerExpressionRegex = /\b([A-Za-z][A-Za-z0-9/]*(?:\s+[A-Za-z][A-Za-z0-9/]*)*)\^(-?\d+)\b/g;
const subscriptExpressionRegex = /\b([A-Za-z]+)_([A-Za-z0-9]+)\b/g;
const chemistryRegex = /\b(?:[A-Z][a-z]?\d*){2,}\b/g;
const unicodeSquaredCubedRegex = /\b([A-Za-z][A-Za-z0-9/]*)([²³])\b/g;

const superscriptMap: Record<string, string> = {
  "²": "2",
  "³": "3",
};

function normalizeMathBody(body: string): string {
  return body
    .replaceAll("×", "\\times ")
    .replace(/([_^])(?!\{)(-?[A-Za-z0-9]+)/g, (_, operator: string, value: string) => {
      return `${operator}{${value}}`;
    })
    .replace(/\s+/g, " ")
    .trim();
}

function wrapInlineMath(expr: string): string {
  return `$${normalizeMathBody(expr)}$`;
}

function wrapBlockMath(expr: string): string {
  return `$$${normalizeMathBody(expr)}$$`;
}

function normalizeChemistryFormula(formula: string): string {
  return formula.replace(/(\d+)/g, (_, digits: string) => `$_${digits}$`);
}

function normalizePlainText(text: string): string {
  return text
    .replace(rawLatexRegex, (match) => wrapInlineMath(match))
    .replace(scientificNotationRegex, (_, base: string, exponent: string) => {
      return wrapInlineMath(`${base} \\times 10^{${exponent}}`);
    })
    .replace(unicodeSquaredCubedRegex, (_, unit: string, exponentChar: string) => {
      return wrapInlineMath(`${unit}^{${superscriptMap[exponentChar]}}`);
    })
    .replace(powerExpressionRegex, (_, base: string, exponent: string) => {
      return wrapInlineMath(`${base}^{${exponent}}`);
    })
    .replace(subscriptExpressionRegex, (_, base: string, suffix: string) => {
      return wrapInlineMath(`${base}_{${suffix}}`);
    })
    .replace(chemistryRegex, (formula) => normalizeChemistryFormula(formula));
}

function preserveSoftLineBreaks(text: string): string {
  return text
    .split("\n")
    .map((line, index, lines) => {
      const next = lines[index + 1];
      if (next === undefined || line.trim() === "" || next.trim() === "") {
        return line;
      }

      const blockLike = /^(\s*[-*+] |\s*\d+\. |\s*>|\s*#|\s*\|)/;
      if (blockLike.test(line) || blockLike.test(next)) {
        return line;
      }

      return `${line}  `;
    })
    .join("\n");
}

export function normalizeRenderableText(text: string): string {
  if (!text) {
    return "";
  }

  const normalized = text
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n")
    .replace(latexBlockRegex, (_, expr: string) => wrapBlockMath(expr))
    .replace(latexInlineRegex, (_, expr: string) => wrapInlineMath(expr));

  const parts = normalized.split(mathSegmentRegex);
  const rebuilt = parts
    .filter(Boolean)
    .map((part) => {
      if (part.startsWith("$$") && part.endsWith("$$")) {
        return wrapBlockMath(part.slice(2, -2));
      }
      if (part.startsWith("$") && part.endsWith("$")) {
        return wrapInlineMath(part.slice(1, -1));
      }
      return normalizePlainText(part);
    })
    .join("")
    .replace(/[ \t]+\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();

  return preserveSoftLineBreaks(rebuilt);
}
