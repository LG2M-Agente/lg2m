"use client";

import React, { useMemo } from "react";
import katex from "katex";
import { marked } from "marked";

interface MathRendererProps {
  content: string;
  className?: string;
}

export const MathRenderer: React.FC<MathRendererProps> = ({ content, className = "" }) => {
  const renderedHtml = useMemo(() => {
    if (!content) return "";

    const mathPlaceholders: { placeholder: string; html: string }[] = [];

    // 1. Math em Bloco: $$ ... $$
    let text = content.replace(/\$\$([\s\S]*?)\$\$/g, (_, math) => {
      let rendered = "";
      try {
        rendered = `<div class="my-3 overflow-x-auto text-center">${katex.renderToString(math.trim(), {
          displayMode: true,
          throwOnError: false,
        })}</div>`;
      } catch (e) {
        rendered = `<div class="my-3 overflow-x-auto text-center font-mono">$$${math}$$</div>`;
      }
      const placeholder = `%%KATEX_BLOCK_${mathPlaceholders.length}%%`;
      mathPlaceholders.push({ placeholder, html: rendered });
      return `\n\n${placeholder}\n\n`;
    });

    // 2. Math Inline: $ ... $
    text = text.replace(/\$([^\$\n]+?)\$/g, (match, math) => {
      if (/^\s|\s$/.test(math) && !math.includes("\\")) {
        return match;
      }
      let rendered = "";
      try {
        rendered = katex.renderToString(math.trim(), {
          displayMode: false,
          throwOnError: false,
        });
      } catch (e) {
        rendered = `$${math}$`;
      }
      const placeholder = `%%KATEX_INLINE_${mathPlaceholders.length}%%`;
      mathPlaceholders.push({ placeholder, html: rendered });
      return placeholder;
    });

    // 3. Renderiza o Markdown completo via marked
    let parsed = marked.parse(text, { breaks: true, gfm: true }) as string;

    // 4. Restaura as fórmulas matemáticas
    for (const item of mathPlaceholders) {
      // Remove parágrafos <p> desnecessários em volta de blocos <div>
      parsed = parsed.replace(
        new RegExp(`<p>\\s*${item.placeholder}\\s*<\\/p>`, "g"),
        item.html
      );
      parsed = parsed.replace(new RegExp(item.placeholder, "g"), item.html);
    }

    return parsed;
  }, [content]);

  return (
    <div
      className={`markdown-content leading-relaxed ${className}`}
      dangerouslySetInnerHTML={{ __html: renderedHtml }}
    />
  );
};
