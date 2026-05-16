import { Scan, Signal, Document } from "./types";

// In-memory data store for the prototype
// In production, this would be PostgreSQL via Prisma
class DataStore {
  private scans: Map<string, Scan> = new Map();
  private documents: Map<string, Document> = new Map();

  constructor() {
    // Seed with some demo data
    this.seedDemoData();
  }

  private seedDemoData() {
    const demoScans: Scan[] = [
      {
        id: "scan_demo_001",
        url: "https://example-news.com/article/breaking-news",
        contentType: "url",
        rawText: "This is a sample article about recent developments in AI technology...",
        trustScore: 82,
        verdict: "Authentic",
        signals: [
          {
            id: "sig_001", scanId: "scan_demo_001", type: "text",
            score: 85, label: "Likely Human-Written", confidence: 0.88,
            evidence: { avgSentenceLength: 18.5, vocabularyRichness: 0.72, burstiness: 0.65 },
            highlights: []
          },
          {
            id: "sig_002", scanId: "scan_demo_001", type: "domain",
            score: 78, label: "Established Domain", confidence: 0.82,
            evidence: { domainAge: "5 years", sslValid: true, rank: 15000 },
            highlights: []
          }
        ],
        status: "completed",
        createdAt: new Date(Date.now() - 3600000).toISOString(),
        completedAt: new Date(Date.now() - 3595000).toISOString(),
        scanDuration: 5.2,
      },
      {
        id: "scan_demo_002",
        url: "https://suspicious-site.xyz/too-good-deals",
        contentType: "url",
        rawText: "BUY NOW!!! AMAZING DEAL!!! This is the BEST product EVER!!!",
        trustScore: 28,
        verdict: "AI-Generated",
        signals: [
          {
            id: "sig_003", scanId: "scan_demo_002", type: "text",
            score: 22, label: "Likely AI-Generated", confidence: 0.91,
            evidence: { avgSentenceLength: 8.2, vocabularyRichness: 0.28, burstiness: 0.15 },
            highlights: ["BUY NOW!!!", "BEST product EVER!!!"]
          },
          {
            id: "sig_004", scanId: "scan_demo_002", type: "domain",
            score: 15, label: "Suspicious Domain", confidence: 0.95,
            evidence: { domainAge: "2 months", sslValid: false, rank: null },
            highlights: []
          },
          {
            id: "sig_005", scanId: "scan_demo_002", type: "review",
            score: 30, label: "Fake Review Patterns", confidence: 0.78,
            evidence: { totalReviews: 50, fakeCount: 35, avgRating: 4.9 },
            highlights: []
          }
        ],
        status: "completed",
        createdAt: new Date(Date.now() - 7200000).toISOString(),
        completedAt: new Date(Date.now() - 7193000).toISOString(),
        scanDuration: 7.1,
      },
      {
        id: "scan_demo_003",
        text: "The implications of quantum computing on modern cryptography are profound...",
        contentType: "text",
        rawText: "The implications of quantum computing on modern cryptography are profound. As quantum processors become more powerful, traditional encryption methods may become vulnerable to quantum attacks. Researchers are actively developing post-quantum cryptographic algorithms to address these challenges.",
        trustScore: 55,
        verdict: "Suspicious",
        signals: [
          {
            id: "sig_006", scanId: "scan_demo_003", type: "text",
            score: 55, label: "Mixed Signals", confidence: 0.62,
            evidence: { avgSentenceLength: 15.3, vocabularyRichness: 0.58, burstiness: 0.42 },
            highlights: ["As quantum processors become more powerful"]
          }
        ],
        status: "completed",
        createdAt: new Date(Date.now() - 86400000).toISOString(),
        completedAt: new Date(Date.now() - 86396000).toISOString(),
        scanDuration: 3.8,
      }
    ];

    demoScans.forEach(scan => this.scans.set(scan.id, scan));

    const demoDocuments: Document[] = [
      {
        id: "doc_demo_001",
        filename: "contract_2024.pdf",
        fileSize: 245000,
        fileType: "application/pdf",
        hash: "a3f2b8c9d1e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9",
        status: "verified",
        trustScore: 92,
        findings: [
          { type: "Font Consistency", severity: "low", message: "All fonts are consistent throughout the document" },
          { type: "Metadata Check", severity: "low", message: "Document metadata is intact and consistent" }
        ],
        signature: {
          documentHash: "a3f2b8c9d1e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9",
          signature: "MEUCIQDx...base64signature...",
          timestamp: new Date(Date.now() - 172800000).toISOString(),
          publicKey: "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...",
          scanId: "doc_demo_001",
          verdict: "verified"
        },
        createdAt: new Date(Date.now() - 172800000).toISOString(),
      }
    ];

    demoDocuments.forEach(doc => this.documents.set(doc.id, doc));
  }

  // Scans
  getAllScans(): Scan[] {
    return Array.from(this.scans.values()).sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );
  }

  getScan(id: string): Scan | undefined {
    return this.scans.get(id);
  }

  createScan(scan: Scan): Scan {
    this.scans.set(scan.id, scan);
    return scan;
  }

  updateScan(id: string, updates: Partial<Scan>): Scan | undefined {
    const scan = this.scans.get(id);
    if (!scan) return undefined;
    const updated = { ...scan, ...updates };
    this.scans.set(id, updated);
    return updated;
  }

  // Documents
  getAllDocuments(): Document[] {
    return Array.from(this.documents.values()).sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );
  }

  getDocument(id: string): Document | undefined {
    return this.documents.get(id);
  }

  createDocument(doc: Document): Document {
    this.documents.set(doc.id, doc);
    return doc;
  }

  updateDocument(id: string, updates: Partial<Document>): Document | undefined {
    const doc = this.documents.get(id);
    if (!doc) return undefined;
    const updated = { ...doc, ...updates };
    this.documents.set(id, updated);
    return updated;
  }

  // Stats
  getStats() {
    const scans = this.getAllScans();
    const totalScans = scans.length;
    const avgScore = scans.length > 0
      ? Math.round(scans.reduce((sum, s) => sum + s.trustScore, 0) / scans.length)
      : 0;
    const flaggedCount = scans.filter(s => s.verdict !== "Authentic").length;
    const authenticCount = scans.filter(s => s.verdict === "Authentic").length;

    return { totalScans, avgScore, flaggedCount, authenticCount };
  }
}

// Singleton pattern
const globalStore = globalThis as unknown as { dataStore: DataStore };
if (!globalStore.dataStore) {
  globalStore.dataStore = new DataStore();
}

export const dataStore = globalStore.dataStore;
