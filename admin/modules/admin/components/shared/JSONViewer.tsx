/**
 * JSON Viewer Component
 *
 * Reusable component for displaying JSON data with:
 * - Syntax highlighting
 * - Copy to clipboard functionality
 * - Scrollable content with height limits
 * - Collapsible sections
 */

'use client';

import { useState } from 'react';
import { cn, formatJSON } from '@/lib/utils';

interface JSONViewerProps {
  data: any;
  title?: string;
  maxHeight?: string;
  className?: string;
  showCopy?: boolean;
  collapsed?: boolean;
}

export function JSONViewer({ 
  data, 
  title, 
  maxHeight = 'max-h-96', 
  className,
  showCopy = true,
  collapsed = false 
}: JSONViewerProps) {
  const [isCollapsed, setIsCollapsed] = useState(collapsed);
  const [copied, setCopied] = useState(false);

  const jsonString = formatJSON(data);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(jsonString);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  if (!data) {
    return (
      <div className={cn('text-sm text-gray-500 italic', className)}>
        No data available
      </div>
    );
  }

  return (
    <div className={cn('border border-gray-200 rounded-lg', className)}>
      {/* Header */}
      {(title || showCopy) && (
        <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border-b border-gray-200 rounded-t-lg">
          <div className="flex items-center space-x-2">
            {title && (
              <>
                <button
                  onClick={() => setIsCollapsed(!isCollapsed)}
                  className="text-gray-600 hover:text-gray-900"
                >
                  <svg
                    className={cn(
                      'w-4 h-4 transition-transform',
                      isCollapsed ? 'rotate-0' : 'rotate-90'
                    )}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </button>
                <h4 className="text-sm font-medium text-gray-900">{title}</h4>
              </>
            )}
          </div>
          
          {showCopy && (
            <button
              onClick={handleCopy}
              className={cn(
                'flex items-center space-x-1 px-2 py-1 text-xs rounded transition-colors',
                copied
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              )}
            >
              {copied ? (
                <>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span>Copied!</span>
                </>
              ) : (
                <>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  <span>Copy</span>
                </>
              )}
            </button>
          )}
        </div>
      )}

      {/* Content */}
      {!isCollapsed && (
        <div className={cn('overflow-auto scrollbar-thin', maxHeight)}>
          <pre className="json-viewer p-4 text-xs font-mono whitespace-pre-wrap break-words">
            {jsonString}
          </pre>
        </div>
      )}
    </div>
  );
}
