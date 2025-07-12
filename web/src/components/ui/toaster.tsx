"use client";

import { useToast } from "@/frontend/hooks/use-toast";
import {
  Toast,
  ToastClose,
  ToastDescription,
  ToastProvider,
  ToastTitle,
  ToastViewport,
} from "@/frontend/components/ui/toast";

export function Toaster() {
  const { toasts } = useToast();

  return (
    <ToastProvider>
      {toasts.map(function ({ id, title, description, action, variant, duration, position, ...props }) {
        const isDestructive = variant === "destructive";

        return (
          <Toast
            key={id}
            variant={variant}
            duration={duration}
            position={position}
            {...props}
            className={`
              group relative flex w-full items-center justify-between overflow-hidden rounded-xl 
              border p-6 pr-8 shadow-xl transition-all text-base
              data-[swipe=cancel]:translate-x-0 data-[swipe=end]:translate-x-[var(--radix-toast-swipe-end-x)] 
              data-[swipe=move]:translate-x-[var(--radix-toast-swipe-move-x)] 
              data-[swipe=move]:transition-none data-[state=open]:animate-in 
              data-[state=closed]:animate-out data-[swipe=end]:animate-out 
              data-[state=closed]:fade-out-80 data-[state=closed]:slide-out-to-right-full 
              data-[state=open]:slide-in-from-right-full 
              ${
                isDestructive
                  ? "border-l-4 border-l-rose-500 bg-[rgba(255,245,245,0.98)] text-slate-800 backdrop-blur-md"
                  : "border-l-4 border-l-emerald-400 bg-[rgba(250,250,250,0.97)] text-slate-800 backdrop-blur-md"
              }
            `}
          >
            <div className="grid gap-1.5">
              {title && (
                <ToastTitle className={`text-lg font-semibold ${isDestructive ? "text-rose-700" : ""}`}>
                  {isDestructive && "⚠️ "}
                  {title}
                </ToastTitle>
              )}
              {description && (
                <ToastDescription className={`text-base ${isDestructive ? "opacity-100" : "opacity-90"}`}>
                  {description}
                </ToastDescription>
              )}
            </div>
            {action}
            <ToastClose className="absolute right-2.5 top-2.5 rounded-md p-1.5 text-slate-500 opacity-70 transition-opacity hover:opacity-100" />
          </Toast>
        );
      })}

      <ToastViewport className="fixed right-0 z-[100] flex max-h-screen w-full p-4 md:max-w-[500px]" />
    </ToastProvider>
  );
}
