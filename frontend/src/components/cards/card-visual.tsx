"use client";

import React from "react";
import { cn } from "@/lib/utils";
import type { CardNetwork, CardStatus } from "@/lib/types";
import { Badge } from "@/components/ui/badge";

interface CardVisualProps {
  issuer: string;
  cardName: string;
  network: CardNetwork;
  lastFourDigits: string;
  status?: CardStatus;
  className?: string;
}

export function CardVisual({
  issuer,
  cardName,
  network,
  lastFourDigits,
  status = "active",
  className,
}: CardVisualProps) {
  // Color themes based on network or card prestige
  const getGradient = (net: CardNetwork) => {
    switch (net) {
      case "amex":
        return "from-slate-900 via-sky-950 to-slate-800 text-sky-100 border-sky-800/40";
      case "mastercard":
        return "from-neutral-900 via-zinc-800 to-amber-950 text-amber-50 border-amber-900/40";
      case "rupay":
        return "from-slate-900 via-emerald-950 to-teal-900 text-emerald-100 border-emerald-800/40";
      case "diners_club":
        return "from-slate-900 via-indigo-950 to-slate-950 text-indigo-100 border-indigo-800/40";
      case "visa":
      default:
        return "from-slate-950 via-blue-950 to-indigo-950 text-blue-50 border-blue-800/40";
    }
  };

  const getNetworkLabel = (net: CardNetwork) => {
    switch (net) {
      case "visa":
        return "VISA";
      case "mastercard":
        return "Mastercard";
      case "amex":
        return "AMEX";
      case "rupay":
        return "RuPay";
      case "diners_club":
        return "Diners Club";
      default:
        return (net as string).toUpperCase();
    }
  };

  return (
    <div
      className={cn(
        "relative flex h-48 w-full max-w-sm flex-col justify-between overflow-hidden rounded-2xl border p-5 shadow-lg transition-transform duration-300 hover:scale-[1.02] bg-gradient-to-br",
        getGradient(network),
        status === "archived" && "opacity-60 saturate-50",
        className
      )}
    >
      {/* Decorative background glow rings */}
      <div className="pointer-events-none absolute -right-10 -top-10 h-36 w-36 rounded-full bg-white/5 blur-2xl" />
      <div className="pointer-events-none absolute -bottom-12 -left-12 h-36 w-36 rounded-full bg-white/5 blur-2xl" />

      {/* Top row: Issuer & Status */}
      <div className="relative z-10 flex items-center justify-between">
        <span className="font-semibold tracking-wider text-xs uppercase opacity-90">
          {issuer}
        </span>
        {status === "archived" ? (
          <Badge variant="outline" className="border-amber-400 text-amber-300 text-[10px] px-1.5 py-0">
            Archived
          </Badge>
        ) : (
          <div className="flex h-2 w-2 rounded-full bg-emerald-400 ring-2 ring-emerald-400/30" />
        )}
      </div>

      {/* Middle row: EMV Chip & Card Name */}
      <div className="relative z-10 my-auto flex items-center gap-3">
        {/* EMV Chip graphic */}
        <div className="flex h-7 w-9 flex-col justify-between rounded-md border border-amber-300/60 bg-gradient-to-tr from-amber-400 to-amber-200 p-1 shadow-inner">
          <div className="h-0.5 w-full bg-amber-600/40 rounded-full" />
          <div className="flex justify-between">
            <div className="h-3 w-0.5 bg-amber-600/40" />
            <div className="h-3 w-0.5 bg-amber-600/40" />
          </div>
          <div className="h-0.5 w-full bg-amber-600/40 rounded-full" />
        </div>

        {/* Contactless waves symbol */}
        <svg
          className="h-4 w-4 opacity-75"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M8.5 16.5a5 5 0 0 1 0-7" />
          <path d="M12 19a8.5 8.5 0 0 0 0-14" />
          <path d="M15.5 21.5a12 12 0 0 0 0-19" />
        </svg>

        <span className="truncate font-medium text-sm tracking-wide">
          {cardName}
        </span>
      </div>

      {/* Bottom row: Masked PAN & Network Logo */}
      <div className="relative z-10 flex items-end justify-between pt-2">
        <div>
          <p className="font-mono text-xs tracking-widest opacity-70">
            •••• •••• ••••
          </p>
          <p className="font-mono text-base font-semibold tracking-wider">
            {lastFourDigits}
          </p>
        </div>

        <div className="text-right">
          <span className="font-bold text-sm tracking-widest italic opacity-95">
            {getNetworkLabel(network)}
          </span>
        </div>
      </div>
    </div>
  );
}
