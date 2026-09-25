"use client";

import React, { useEffect, useRef } from "react";
import katex from "katex";

interface MathRendererProps {
  content: string;
  className?: string;
}

export const MathRenderer: React.FC<MathRendererProps> = ({ content, className = "" }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || !content) return;

    // Divide texto e fórmulas matemáticas
    // Padrões: $$...$$ (bloco) ou $...$ (inline)
    const regex = /(\$\$[\s\S]*?\$\$|\$[^\$]+?\$)/g;
    const parts = content.split(regex);

    containerRef.current.innerHTML = "";

    parts.forEach((part) => {
      if (!part) return;

      if (part.startsWith("$$") && part.endsWith("$$")) {
        const math = part.slice(2, -2);
        const span = document.createElement("div");
        span.className = "my-2 overflow-x-auto text-center";
        try {
          katex.render(math, span, { displayMode: true, throwOnError: false });
        } catch (e) {
          span.textContent = part;
        }
        containerRef.current?.appendChild(span);
      } else if (part.startsWith("$") && part.endsWith("$")) {
        const math = part.slice(1, -1);
        const span = document.createElement("span");
        try {
          katex.render(math, span, { displayMode: false, throwOnError: false });
        } catch (e) {
          span.textContent = part;
        }
        containerRef.current?.appendChild(span);
      } else {
        const textSpan = document.createElement("span");
        textSpan.textContent = part;
        containerRef.current?.appendChild(textSpan);
      }
    });
  }, [content]);

  return <div ref={containerRef} className={`whitespace-pre-wrap leading-relaxed ${className}`} />;
};
