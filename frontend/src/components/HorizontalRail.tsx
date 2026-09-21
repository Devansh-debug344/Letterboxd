import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useEffect, useRef, useState, type ReactNode } from 'react';

type HorizontalRailProps = {
  children: ReactNode;
  className?: string;
  labelledBy?: string;
};

export function HorizontalRail({ children, className = '', labelledBy }: HorizontalRailProps) {
  const railRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  const updateScrollState = () => {
    const rail = railRef.current;
    if (!rail) return;
    setCanScrollLeft(rail.scrollLeft > 4);
    setCanScrollRight(rail.scrollLeft + rail.clientWidth < rail.scrollWidth - 4);
  };

  useEffect(() => {
    updateScrollState();
    const rail = railRef.current;
    if (!rail) return undefined;
    const resizeObserver = new ResizeObserver(updateScrollState);
    resizeObserver.observe(rail);
    return () => resizeObserver.disconnect();
  }, [children]);

  const scroll = (direction: number) => {
    const rail = railRef.current;
    if (rail) rail.scrollBy({ left: direction * Math.max(rail.clientWidth * 0.75, 240), behavior: 'smooth' });
  };

  return <div className={`horizontal-rail ${className}`} data-left={canScrollLeft} data-right={canScrollRight}>
    <button type="button" className="rail-arrow rail-arrow-left" aria-label="Scroll left" aria-controls={labelledBy} disabled={!canScrollLeft} onClick={() => scroll(-1)}><ChevronLeft size={18} /></button>
    <div id={labelledBy} ref={railRef} className="horizontal-rail-content" onScroll={updateScrollState}>
      {children}
    </div>
    <button type="button" className="rail-arrow rail-arrow-right" aria-label="Scroll right" aria-controls={labelledBy} disabled={!canScrollRight} onClick={() => scroll(1)}><ChevronRight size={18} /></button>
  </div>;
}