/**
 * Resizable Panel Component
 *
 * A component that allows users to drag-resize content vertically.
 * Can be used to wrap any content that needs to be resizable.
 */

'use client';

import { useState, useRef, useCallback, useEffect, ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface ResizablePanelProps {
  children: ReactNode;
  defaultHeight?: number;
  minHeight?: number;
  maxHeight?: number;
  className?: string;
}

export function ResizablePanel({
  children,
  defaultHeight = 384, // default ~96 in Tailwind (24rem * 16px = 384px)
  minHeight = 96, // min ~24 in Tailwind (6rem * 16px = 96px)
  maxHeight = 1200, // max ~300 in Tailwind
  className,
}: ResizablePanelProps): JSX.Element {
  const [height, setHeight] = useState(defaultHeight);
  const [isResizing, setIsResizing] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const startYRef = useRef(0);
  const startHeightRef = useRef(0);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
    startYRef.current = e.clientY;
    startHeightRef.current = height;
  }, [height]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isResizing) return;

    const deltaY = e.clientY - startYRef.current;
    const newHeight = Math.max(
      minHeight,
      Math.min(maxHeight, startHeightRef.current + deltaY)
    );
    setHeight(newHeight);
  }, [isResizing, minHeight, maxHeight]);

  const handleMouseUp = useCallback(() => {
    setIsResizing(false);
  }, []);

  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      // Prevent text selection while resizing
      document.body.style.userSelect = 'none';
      document.body.style.cursor = 'ns-resize';

      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
        document.body.style.userSelect = '';
        document.body.style.cursor = '';
      };
    }
  }, [isResizing, handleMouseMove, handleMouseUp]);

  return (
    <div ref={panelRef} className={cn('relative', className)}>
      {/* Content Container */}
      <div
        className="overflow-auto scrollbar-thin"
        style={{ height: `${height}px` }}
      >
        {children}
      </div>

      {/* Resize Handle */}
      <div
        className={cn(
          'h-1.5 w-full cursor-ns-resize transition-colors',
          'hover:bg-blue-400 active:bg-blue-500',
          'border-t border-gray-300',
          isResizing ? 'bg-blue-500' : 'bg-gray-200'
        )}
        onMouseDown={handleMouseDown}
        title="Drag to resize"
      >
        {/* Visual indicator */}
        <div className="flex items-center justify-center h-full">
          <div className={cn(
            'w-12 h-1 rounded-full transition-colors',
            isResizing ? 'bg-blue-600' : 'bg-gray-400'
          )} />
        </div>
      </div>
    </div>
  );
}
