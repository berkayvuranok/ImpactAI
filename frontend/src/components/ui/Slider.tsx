import { useRef, type ReactNode } from "react";

interface SliderProps {
  title?: string;
  subtitle?: string;
  children: ReactNode;
  itemWidth?: string;
}

export function Slider({ title, subtitle, children, itemWidth = "min(85vw, 380px)" }: SliderProps) {
  const trackRef = useRef<HTMLDivElement>(null);

  const scroll = (direction: -1 | 1) => {
    const track = trackRef.current;
    if (!track) return;
    const amount = track.clientWidth * 0.85;
    track.scrollBy({ left: direction * amount, behavior: "smooth" });
  };

  return (
    <div className="relative">
      {(title || subtitle) && (
        <div className="mb-6 flex items-end justify-between gap-4">
          <div>
            {subtitle && <p className="section-label">{subtitle}</p>}
            {title && <h3 className="mt-1 font-heading text-2xl font-semibold text-ink-900">{title}</h3>}
          </div>
          <div className="hidden gap-2 sm:flex">
            <button
              type="button"
              onClick={() => scroll(-1)}
              aria-label="Previous slide"
              className="flex h-10 w-10 items-center justify-center rounded-full border border-ink-400 text-ink-700 transition hover:border-ink-700 hover:text-ink-900"
            >
              ←
            </button>
            <button
              type="button"
              onClick={() => scroll(1)}
              aria-label="Next slide"
              className="flex h-10 w-10 items-center justify-center rounded-full border border-ink-400 text-ink-700 transition hover:border-ink-700 hover:text-ink-900"
            >
              →
            </button>
          </div>
        </div>
      )}

      <div ref={trackRef} className="slide-track" style={{ scrollPaddingLeft: "1rem" }}>
        {Array.isArray(children)
          ? children.map((child, i) => (
              <div key={i} className="slide-item" style={{ width: itemWidth }}>
                {child}
              </div>
            ))
          : children}
      </div>

      <div className="mt-3 flex justify-center gap-1 sm:hidden">
        <span className="font-mono text-[10px] uppercase tracking-widest text-ink-500">
          Kaydır →
        </span>
      </div>
    </div>
  );
}
