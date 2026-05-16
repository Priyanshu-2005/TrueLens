"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";

interface TrustScoreGaugeProps {
  score: number;
  size?: number;
  animated?: boolean;
}

export default function TrustScoreGauge({ score, size = 200, animated = true }: TrustScoreGaugeProps) {
  const [displayScore, setDisplayScore] = useState(animated ? 0 : score);
  
  const radius = (size - 20) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (displayScore / 100) * circumference;

  const getColor = (s: number) => {
    if (s >= 70) return "#10B981";
    if (s >= 40) return "#F59E0B";
    return "#EF4444";
  };

  const getLabel = (s: number) => {
    if (s >= 70) return "Authentic";
    if (s >= 40) return "Suspicious";
    return "AI-Generated";
  };

  const getGlow = (s: number) => {
    if (s >= 70) return "0 0 30px rgba(16, 185, 129, 0.3)";
    if (s >= 40) return "0 0 30px rgba(245, 158, 11, 0.3)";
    return "0 0 30px rgba(239, 68, 68, 0.3)";
  };

  useEffect(() => {
    if (!animated) return;
    const duration = 2000;
    const startTime = Date.now();
    const timer = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayScore(Math.round(eased * score));
      if (progress >= 1) clearInterval(timer);
    }, 16);
    return () => clearInterval(timer);
  }, [score, animated]);

  const color = getColor(displayScore);
  const center = size / 2;

  return (
    <div className="flex flex-col items-center gap-4">
      <motion.div
        initial={animated ? { scale: 0.8, opacity: 0 } : {}}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        style={{ filter: `drop-shadow(${getGlow(displayScore)})` }}
      >
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {/* Background circle */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.05)"
            strokeWidth="10"
          />
          
          {/* Score arc */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            transform={`rotate(-90 ${center} ${center})`}
            style={{ transition: "stroke-dashoffset 0.3s ease" }}
          />
          
          {/* Inner glow circle */}
          <circle
            cx={center}
            cy={center}
            r={radius - 20}
            fill="rgba(24, 24, 27, 0.6)"
            stroke="rgba(139, 92, 246, 0.1)"
            strokeWidth="1"
          />
          
          {/* Score text */}
          <text
            x={center}
            y={center - 8}
            textAnchor="middle"
            fill={color}
            fontSize={size * 0.22}
            fontWeight="800"
            fontFamily="Inter, sans-serif"
          >
            {displayScore}
          </text>
          
          {/* Label */}
          <text
            x={center}
            y={center + size * 0.1}
            textAnchor="middle"
            fill="rgba(255,255,255,0.5)"
            fontSize={size * 0.06}
            fontWeight="500"
            fontFamily="Inter, sans-serif"
            letterSpacing="0.1em"
            style={{ textTransform: "uppercase" as const }}
          >
            TRUST SCORE
          </text>
        </svg>
      </motion.div>
      
      <motion.div
        initial={animated ? { y: 10, opacity: 0 } : {}}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.5, duration: 0.4 }}
        className="text-center"
      >
        <span
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-semibold uppercase tracking-wider"
          style={{
            background: `${color}15`,
            color: color,
            border: `1px solid ${color}30`,
          }}
        >
          <span className="w-2 h-2 rounded-full" style={{ background: color }} />
          {getLabel(displayScore)}
        </span>
      </motion.div>
    </div>
  );
}
