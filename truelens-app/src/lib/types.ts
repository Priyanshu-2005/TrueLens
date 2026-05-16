export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  plan: "free" | "pro" | "enterprise";
  createdAt: string;
}

export interface Signal {
  id: string;
  scanId: string;
  type: "text" | "image" | "metadata" | "review" | "domain" | "provenance";
  score: number;
  label: string;
  confidence: number;
  evidence: Record<string, unknown>;
  highlights?: string[];
}

export interface Scan {
  id: string;
  userId?: string;
  url?: string;
  text?: string;
  contentType: "url" | "text" | "file";
  rawText?: string;
  trustScore: number;
  verdict: "Authentic" | "Suspicious" | "AI-Generated";
  signals: Signal[];
  status: "pending" | "processing" | "completed" | "failed";
  createdAt: string;
  completedAt?: string;
  scanDuration?: number;
}

export interface Document {
  id: string;
  userId?: string;
  filename: string;
  fileSize: number;
  fileType: string;
  hash: string;
  status: "pending" | "analyzing" | "verified" | "flagged";
  trustScore?: number;
  findings: DocumentFinding[];
  signature?: DocumentSignature;
  createdAt: string;
}

export interface DocumentFinding {
  type: string;
  severity: "low" | "medium" | "high";
  message: string;
  field?: string;
}

export interface DocumentSignature {
  documentHash: string;
  signature: string;
  timestamp: string;
  publicKey: string;
  scanId: string;
  verdict: string;
}

export interface ApiKey {
  id: string;
  userId: string;
  name: string;
  keyPrefix: string;
  scopes: string[];
  rateLimit: number;
  lastUsedAt?: string;
  createdAt: string;
  expiresAt?: string;
}

export interface ScanRequest {
  url?: string;
  text?: string;
  contentType: "url" | "text";
}

export interface AnalysisResult {
  score: number;
  label: string;
  confidence: number;
  highlights: string[];
  details: Record<string, unknown>;
}
