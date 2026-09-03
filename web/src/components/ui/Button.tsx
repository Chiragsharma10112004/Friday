import React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger" | "success";
  size?: "sm" | "md" | "lg" | "icon";
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  className,
  variant = "primary",
  size = "md",
  isLoading = false,
  disabled,
  children,
  ...props
}) => {
  const variantStyles = {
    primary:
      "bg-cyan-500 text-slate-950 font-semibold hover:bg-cyan-400 active:bg-cyan-600 shadow-glow-cyan border border-cyan-400/40",
    secondary:
      "bg-slate-800 text-slate-200 hover:bg-slate-700 active:bg-slate-800/80 border border-slate-700",
    outline:
      "bg-transparent text-slate-300 hover:text-cyan-400 hover:bg-slate-800/50 border border-slate-700 hover:border-cyan-500/50",
    ghost:
      "bg-transparent text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 border border-transparent",
    danger:
      "bg-rose-600 text-white font-medium hover:bg-rose-500 active:bg-rose-700 shadow-glow-rose border border-rose-500/40",
    success:
      "bg-emerald-600 text-white font-medium hover:bg-emerald-500 active:bg-emerald-700 shadow-glow-emerald border border-emerald-500/40",
  };

  const sizeStyles = {
    sm: "text-xs px-2.5 py-1.5 rounded-lg",
    md: "text-sm px-4 py-2 rounded-lg",
    lg: "text-base px-5 py-2.5 rounded-xl",
    icon: "p-2 rounded-lg",
  };

  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 font-medium transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-cyan-500/50",
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <span className="inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
      ) : null}
      {children}
    </button>
  );
};
