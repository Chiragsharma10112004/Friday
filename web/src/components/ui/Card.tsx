import React from "react";
import { cn } from "@/lib/utils";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverEffect?: boolean;
  glow?: "cyan" | "emerald" | "amber" | "rose" | "none";
}

export const Card: React.FC<CardProps> = ({
  className,
  hoverEffect = false,
  glow = "none",
  children,
  ...props
}) => {
  const glowStyles = {
    none: "",
    cyan: "hover:border-cyan-500/50 hover:shadow-glow-cyan",
    emerald: "hover:border-emerald-500/50 hover:shadow-glow-emerald",
    amber: "hover:border-amber-500/50 hover:shadow-glow-amber",
    rose: "hover:border-rose-500/50 hover:shadow-glow-rose",
  };

  return (
    <div
      className={cn(
        "rounded-xl bg-slate-900/70 backdrop-blur-md border border-slate-800/80 p-5 text-slate-200 transition-all duration-200",
        hoverEffect && "hover:bg-slate-900/90 hover:border-slate-700 hover:-translate-y-0.5",
        glowStyles[glow],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  children,
  ...props
}) => (
  <div className={cn("flex items-center justify-between pb-3 border-b border-slate-800/60 mb-4", className)} {...props}>
    {children}
  </div>
);

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({
  className,
  children,
  ...props
}) => (
  <h3 className={cn("text-base font-semibold text-slate-100 flex items-center gap-2", className)} {...props}>
    {children}
  </h3>
);

export const CardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({
  className,
  children,
  ...props
}) => (
  <p className={cn("text-xs text-slate-400 mt-0.5", className)} {...props}>
    {children}
  </p>
);
