"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Shield, Search, CheckCircle, XCircle, AlertTriangle,
  Hash, Clock, FileText, Loader2
} from "lucide-react";
import { formatDate } from "@/lib/utils";

interface VerificationResult {
  verified: boolean;
  message: string;
  document?: {
    id: string;
    filename: string;
    hash: string;
    trustScore: number;
    status: string;
    verifiedAt?: string;
    signatureValid?: boolean;
  };
}

export default function VerifyPage() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VerificationResult | null>(null);

  const handleVerify = async () => {
    if (!input.trim()) return;
    setLoading(true);
    setResult(null);

    try {
      const isHash = input.length === 64 && /^[a-f0-9]+$/.test(input);
      const res = await fetch("/api/v1/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(isHash ? { hash: input } : { scanId: input }),
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setResult({
        verified: false,
        message: "Verification service is currently unavailable. Please try again later.",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] py-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6"
            style={{ background: "rgba(16, 185, 129, 0.1)", border: "1px solid rgba(16, 185, 129, 0.2)" }}>
            <Shield className="w-8 h-8 text-success" />
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-text-primary mb-3">
            Verify Document
          </h1>
          <p className="text-text-muted text-lg">
            Verify the authenticity of a TrueLens-signed document
          </p>
        </motion.div>

        {/* Input */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card p-6 mb-6"
        >
          <label className="text-sm font-medium text-text-secondary mb-2 block">
            Document Hash or Scan ID
          </label>
          <div className="relative">
            <Hash className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Enter SHA-256 hash or doc_xxx scan ID"
              className="input-field !pl-12 font-mono text-sm"
              onKeyDown={(e) => e.key === "Enter" && handleVerify()}
            />
          </div>
          <p className="text-xs text-text-muted mt-2">
            Enter the document&apos;s SHA-256 hash or TrueLens scan ID to verify its authenticity
          </p>
        </motion.div>

        {/* Verify Button */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <button
            onClick={handleVerify}
            disabled={loading || !input.trim()}
            className="btn-primary w-full justify-center text-base !py-4 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin relative z-10" />
            ) : (
              <Search className="w-5 h-5 relative z-10" />
            )}
            <span>{loading ? "Verifying..." : "Verify Document"}</span>
          </button>
        </motion.div>

        {/* Result */}
        <AnimatePresence>
          {result && (
            <motion.div
              initial={{ opacity: 0, y: 20, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.4 }}
              className="mt-8"
            >
              <div className={`glass-card p-8 ${
                result.verified
                  ? "border-green-500/20"
                  : "border-red-500/20"
              }`}
                style={{
                  borderColor: result.verified ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)",
                }}
              >
                {/* Status Icon */}
                <div className="flex flex-col items-center text-center mb-6">
                  <div className={`w-20 h-20 rounded-full flex items-center justify-center mb-4 ${
                    result.verified ? "pulse-glow" : ""
                  }`}
                    style={{
                      background: result.verified ? "rgba(16, 185, 129, 0.1)" : "rgba(239, 68, 68, 0.1)",
                    }}
                  >
                    {result.verified ? (
                      <CheckCircle className="w-10 h-10 text-success" />
                    ) : (
                      <XCircle className="w-10 h-10 text-danger" />
                    )}
                  </div>
                  <h2 className={`text-xl font-bold ${
                    result.verified ? "text-success" : "text-danger"
                  }`}>
                    {result.verified ? "Document Verified ✓" : "Verification Failed"}
                  </h2>
                  <p className="text-text-muted text-sm mt-2">{result.message}</p>
                </div>

                {/* Document Details */}
                {result.document && (
                  <div className="space-y-3">
                    <div className="p-4 rounded-lg" style={{ background: "rgba(255,255,255,0.02)" }}>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-[10px] text-text-muted uppercase tracking-wider">Filename</p>
                          <p className="text-sm text-text-primary mt-1 flex items-center gap-1">
                            <FileText className="w-3.5 h-3.5" />
                            {result.document.filename}
                          </p>
                        </div>
                        <div>
                          <p className="text-[10px] text-text-muted uppercase tracking-wider">Trust Score</p>
                          <p className="text-sm font-bold mt-1"
                            style={{ color: result.document.trustScore >= 70 ? "#10B981" : result.document.trustScore >= 40 ? "#F59E0B" : "#EF4444" }}>
                            {result.document.trustScore}/100
                          </p>
                        </div>
                        <div>
                          <p className="text-[10px] text-text-muted uppercase tracking-wider">Status</p>
                          <p className="text-sm text-text-primary mt-1 capitalize">{result.document.status}</p>
                        </div>
                        {result.document.verifiedAt && (
                          <div>
                            <p className="text-[10px] text-text-muted uppercase tracking-wider">Verified At</p>
                            <p className="text-sm text-text-primary mt-1 flex items-center gap-1">
                              <Clock className="w-3.5 h-3.5" />
                              {formatDate(result.document.verifiedAt)}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="p-4 rounded-lg" style={{ background: "rgba(255,255,255,0.02)" }}>
                      <p className="text-[10px] text-text-muted uppercase tracking-wider mb-1">Document Hash</p>
                      <p className="text-xs font-mono text-brand-light break-all">{result.document.hash}</p>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Example */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mt-8 text-center"
        >
          <p className="text-xs text-text-muted mb-2">Try verifying:</p>
          <button
            onClick={() => setInput("doc_demo_001")}
            className="text-xs text-brand-light/60 hover:text-brand-light transition-colors font-mono"
          >
            doc_demo_001
          </button>
        </motion.div>
      </div>
    </div>
  );
}
