import React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?:
    | "default"
    | "cyan"
    | "emerald"
    | "amber"
    | "rose"
    | "violet"
    | "outline";
  size?: "sm" | "md";
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = "default",
  size = "sm",
  children,
  ...props
}) => {
  const variantStyles = {
    default: "bg-slate-800 text-slate-300 border-slate-700",
    cyan: "bg-cyan-950/80 text-cyan-300 border-cyan-800/60 shadow-sm",
    emerald: "bg-emerald-950/80 text-emerald-300 border-emerald-800/60 shadow-sm",
    amber: "bg-amber-950/80 text-amber-300 border-amber-800/60 shadow-sm",
    rose: "bg-rose-950/80 text-rose-300 border-rose-800/60 shadow-sm",
    violet: "bg-purple-950/80 text-purple-300 border-purple-800/60 shadow-sm",
    outline: "bg-transparent text-slate-300 border-slate-700",
  };

  const sizeStyles = {
    sm: "text-xs px-2 py-0.5",
    md: "text-xs px-2.5 py-1 font-medium",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border font-mono tracking-tight",
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
};
