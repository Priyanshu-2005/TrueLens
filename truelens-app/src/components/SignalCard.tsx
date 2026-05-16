"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronDown, FileText, Image, Globe, Star, Search,
  AlertTriangle, CheckCircle, Info
} from "lucide-react";
import { Signal } from "@/lib/types";

const signalIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  text: FileText,
  image: Image,
  domain: Globe,
  review: Star,
  provenance: Search,
  metadata: Info,
};

const signalLabels: Record<string, string> = {
  text: "Text Analysis",
  image: "Image Forensics",
  domain: "Domain Trust",
  review: "Review Detection",
  provenance: "Provenance Check",
  metadata: "Metadata Analysis",
};

interface SignalCardProps {
  signal: Signal;
  index: number;
}

export default function SignalCard({ signal, index }: SignalCardProps) {
  const [expanded, setExpanded] = useState(false);

  const Icon = signalIcons[signal.type] || Info;
  const label = signalLabels[signal.type] || signal.type;

  const getScoreColor = (score: number) => {
    if (score >= 70) return "#10B981";
    if (score >= 40) return "#F59E0B";
    return "#EF4444";
  };

  const color = getScoreColor(signal.score);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.4 }}
      className="glass-card overflow-hidden"
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-5 hover:bg-white/[0.02] transition-colors"
      >
        <div className="flex items-center gap-4">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: `${color}15`, border: `1px solid ${color}25` }}
          >
            <div style={{ color }}>
              <Icon className="w-5 h-5" />
            </div>
          </div>
          <div className="text-left">
            <h3 className="text-sm font-semibold text-text-primary">{label}</h3>
            <p className="text-xs text-text-muted mt-0.5">{signal.label}</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-lg font-bold" style={{ color }}>{signal.score}</p>
            <p className="text-[10px] text-text-muted uppercase tracking-wider">
              {Math.round(signal.confidence * 100)}% conf.
            </p>
          </div>
          <motion.div
            animate={{ rotate: expanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronDown className="w-4 h-4 text-text-muted" />
          </motion.div>
        </div>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-5 border-t border-border-color pt-4 space-y-4">
              {/* Evidence details */}
              {signal.evidence && Object.keys(signal.evidence).length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">
                    Evidence
                  </h4>
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(signal.evidence).map(([key, value]) => (
                      <div
                        key={key}
                        className="p-3 rounded-lg"
                        style={{ background: "rgba(255,255,255,0.02)" }}
                      >
                        <p className="text-[10px] text-text-muted uppercase tracking-wider">{key.replace(/([A-Z])/g, ' $1').trim()}</p>
                        <p className="text-sm font-mono text-brand-light mt-1">
                          {typeof value === 'boolean' ? (value ? '✓ Yes' : '✗ No') :
                           typeof value === 'number' ? (Number.isInteger(value) ? value : (value as number).toFixed(2)) :
                           value === null ? 'N/A' : String(value)}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Highlights */}
              {signal.highlights && signal.highlights.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">
                    Flagged Content
                  </h4>
                  <div className="space-y-2">
                    {signal.highlights.map((highlight, i) => (
                      <div
                        key={i}
                        className="flex items-start gap-2 p-3 rounded-lg"
                        style={{ background: "rgba(239, 68, 68, 0.05)", border: "1px solid rgba(239, 68, 68, 0.1)" }}
                      >
                        <AlertTriangle className="w-4 h-4 text-danger mt-0.5 shrink-0" />
                        <p className="text-sm text-text-secondary">{highlight}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Score bar */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-text-muted">Score</span>
                  <span className="text-xs font-mono" style={{ color }}>{signal.score}/100</span>
                </div>
                <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${signal.score}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className="h-full rounded-full"
                    style={{ background: `linear-gradient(90deg, ${color}80, ${color})` }}
                  />
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
