import type { ReactNode } from "react";
import { useScrollReveal } from "../../hooks/useScrollReveal";

interface ScrollSectionProps {
  children: ReactNode;
  className?: string;
  id?: string;
  delay?: number;
}

export function ScrollSection({ children, className = "", id, delay = 0 }: ScrollSectionProps) {
  const { ref, visible } = useScrollReveal<HTMLElement>();

  return (
    <section
      id={id}
      ref={ref}
      className={`reveal py-16 md:py-24 ${visible ? "reveal-visible" : ""} ${className}`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {children}
    </section>
  );
}
