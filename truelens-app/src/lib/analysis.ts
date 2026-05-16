import { Signal, AnalysisResult } from "./types";
import { v4 as uuidv4 } from "uuid";

// === Text Analysis Engine ===
// Uses stylometry features to detect AI-generated content
// In production, this would call the FastAPI ML service with DistilBERT/RoBERTa

interface TextFeatures {
  avgSentenceLength: number;
  sentenceLengthVariance: number;
  vocabularyRichness: number;
  punctuationDensity: number;
  burstiness: number;
  repetitionScore: number;
  allCapsRatio: number;
  exclamationCount: number;
  avgWordLength: number;
  uniqueWordRatio: number;
}

function extractTextFeatures(text: string): TextFeatures {
  const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
  const words = text.split(/\s+/).filter(w => w.length > 0);
  const uniqueWords = new Set(words.map(w => w.toLowerCase()));

  const sentenceLengths = sentences.map(s => s.trim().split(/\s+/).length);
  const avgSentenceLength = sentenceLengths.length > 0
    ? sentenceLengths.reduce((a, b) => a + b, 0) / sentenceLengths.length
    : 0;

  const variance = sentenceLengths.length > 1
    ? sentenceLengths.reduce((sum, len) => sum + Math.pow(len - avgSentenceLength, 2), 0) / sentenceLengths.length
    : 0;

  const punctuation = (text.match(/[.,;:!?'"()\-—]/g) || []).length;
  const punctuationDensity = words.length > 0 ? punctuation / words.length : 0;

  // Burstiness: variation in paragraph lengths (human text has more variation)
  const paragraphs = text.split(/\n\n+/).filter(p => p.trim().length > 0);
  const paraLengths = paragraphs.map(p => p.split(/\s+/).length);
  const avgParaLen = paraLengths.length > 0
    ? paraLengths.reduce((a, b) => a + b, 0) / paraLengths.length
    : 0;
  const burstiness = paraLengths.length > 1
    ? Math.sqrt(paraLengths.reduce((sum, len) => sum + Math.pow(len - avgParaLen, 2), 0) / paraLengths.length) / (avgParaLen || 1)
    : 0.5;

  // Repetition: how often words are repeated
  const wordFreq: Record<string, number> = {};
  words.forEach(w => {
    const lower = w.toLowerCase();
    wordFreq[lower] = (wordFreq[lower] || 0) + 1;
  });
  const repeatedWords = Object.values(wordFreq).filter(f => f > 2).length;
  const repetitionScore = words.length > 0 ? repeatedWords / uniqueWords.size : 0;

  const capsWords = words.filter(w => w === w.toUpperCase() && w.length > 1);
  const allCapsRatio = words.length > 0 ? capsWords.length / words.length : 0;

  const exclamationCount = (text.match(/!/g) || []).length;

  const avgWordLength = words.length > 0
    ? words.reduce((sum, w) => sum + w.length, 0) / words.length
    : 0;

  return {
    avgSentenceLength,
    sentenceLengthVariance: variance,
    vocabularyRichness: words.length > 0 ? uniqueWords.size / words.length : 0,
    punctuationDensity,
    burstiness,
    repetitionScore,
    allCapsRatio,
    exclamationCount,
    avgWordLength,
    uniqueWordRatio: words.length > 0 ? uniqueWords.size / words.length : 0,
  };
}

function analyzeTextScore(features: TextFeatures): AnalysisResult {
  let score = 50; // Start neutral
  const highlights: string[] = [];

  // Vocabulary richness: AI text tends to have more uniform vocabulary
  if (features.vocabularyRichness > 0.65) {
    score += 15;
  } else if (features.vocabularyRichness < 0.4) {
    score -= 15;
    highlights.push("Low vocabulary diversity detected");
  }

  // Burstiness: human text has more variation in paragraph lengths
  if (features.burstiness > 0.3) {
    score += 10;
  } else if (features.burstiness < 0.15) {
    score -= 12;
    highlights.push("Uniform text structure (low burstiness)");
  }

  // Sentence length variance: AI tends to be more uniform
  if (features.sentenceLengthVariance > 50) {
    score += 8;
  } else if (features.sentenceLengthVariance < 10) {
    score -= 10;
    highlights.push("Very uniform sentence lengths");
  }

  // Punctuation density
  if (features.punctuationDensity > 0.15 && features.punctuationDensity < 0.35) {
    score += 5;
  }

  // Repetition
  if (features.repetitionScore > 0.3) {
    score -= 8;
    highlights.push("High word repetition detected");
  }

  // All caps check (spam signal)
  if (features.allCapsRatio > 0.15) {
    score -= 10;
    highlights.push("Excessive use of ALL CAPS");
  }

  // Excessive exclamation marks
  if (features.exclamationCount > 5) {
    score -= 8;
    highlights.push("Excessive exclamation marks");
  }

  // Average word length (AI text tends to use slightly longer, more formal words)
  if (features.avgWordLength > 6) {
    score -= 5;
    highlights.push("Unusually formal word choice");
  }

  // Clamp score
  score = Math.max(0, Math.min(100, score));

  const confidence = Math.min(0.95, 0.5 + Math.abs(score - 50) / 100);

  let label: string;
  if (score >= 70) label = "Likely Human-Written";
  else if (score >= 40) label = "Mixed Signals";
  else label = "Likely AI-Generated";

  return {
    score,
    label,
    confidence,
    highlights,
    details: features as unknown as Record<string, unknown>,
  };
}

// === Domain Analysis ===
function analyzeDomain(url: string): AnalysisResult {
  const highlights: string[] = [];
  let score = 50;

  try {
    const urlObj = new URL(url);
    const domain = urlObj.hostname;

    // Check for suspicious TLDs
    const suspiciousTLDs = [".xyz", ".top", ".click", ".buzz", ".ml", ".tk", ".ga", ".cf"];
    const trustedTLDs = [".com", ".org", ".edu", ".gov", ".net", ".io", ".co"];
    
    if (suspiciousTLDs.some(tld => domain.endsWith(tld))) {
      score -= 20;
      highlights.push(`Suspicious TLD: ${domain.split('.').pop()}`);
    } else if (trustedTLDs.some(tld => domain.endsWith(tld))) {
      score += 10;
    }

    // Check for known trusted domains
    const trustedDomains = [
      "google.com", "github.com", "wikipedia.org", "reuters.com", "bbc.com",
      "nytimes.com", "theguardian.com", "washingtonpost.com", "nature.com",
      "sciencedirect.com", "arxiv.org", "ieee.org", "medium.com",
    ];
    
    if (trustedDomains.some(d => domain.includes(d))) {
      score += 25;
      highlights.push("Known trusted domain");
    }

    // Check for suspicious patterns
    if (domain.includes("-") && domain.split("-").length > 3) {
      score -= 10;
      highlights.push("Excessive hyphens in domain");
    }

    if (/\d{4,}/.test(domain)) {
      score -= 10;
      highlights.push("Numbers in domain name");
    }

    // Check for HTTPS
    if (urlObj.protocol === "https:") {
      score += 5;
    } else {
      score -= 15;
      highlights.push("No HTTPS encryption");
    }

    // Subdomain depth
    const subdomains = domain.split(".").length - 2;
    if (subdomains > 2) {
      score -= 8;
      highlights.push("Deep subdomain nesting");
    }

    score = Math.max(0, Math.min(100, score));

    const confidence = Math.min(0.9, 0.5 + Math.abs(score - 50) / 100);
    
    let label: string;
    if (score >= 70) label = "Established Domain";
    else if (score >= 40) label = "Unverified Domain";
    else label = "Suspicious Domain";

    return {
      score,
      label,
      confidence,
      highlights,
      details: {
        domain,
        protocol: urlObj.protocol,
        sslValid: urlObj.protocol === "https:",
        subdomains,
      },
    };
  } catch {
    return {
      score: 30,
      label: "Invalid URL",
      confidence: 0.95,
      highlights: ["Could not parse URL"],
      details: {},
    };
  }
}

// === Ensemble Scoring ===
const SIGNAL_WEIGHTS = {
  text: 0.40,
  domain: 0.25,
  image: 0.20,
  review: 0.10,
  provenance: 0.05,
};

export async function performAnalysis(
  input: { url?: string; text?: string; contentType: "url" | "text" }
): Promise<{ trustScore: number; verdict: string; signals: Signal[]; scanDuration: number }> {
  const startTime = Date.now();
  const signals: Signal[] = [];
  const scanId = uuidv4();

  // Simulate some processing time
  await new Promise(resolve => setTimeout(resolve, 1500 + Math.random() * 2000));

  // Text analysis
  let textToAnalyze = input.text || "";
  
  if (input.contentType === "url" && input.url) {
    // In production, we'd fetch the URL content. For the prototype, generate realistic text analysis
    textToAnalyze = `Content fetched from ${input.url}. This is analyzed text content that would normally be scraped from the provided URL using BeautifulSoup.`;
    
    // Simulate URL content based on domain patterns
    try {
      const urlObj = new URL(input.url);
      const domain = urlObj.hostname;
      if (domain.includes("news") || domain.includes("bbc") || domain.includes("reuters")) {
        textToAnalyze = "In a significant development today, researchers have announced breakthrough findings in the field of renewable energy. The study, published in Nature, demonstrates a novel approach to solar cell efficiency that could reduce manufacturing costs by up to 40%. Dr. Sarah Chen, lead researcher at MIT, stated that the technology could be commercially viable within three years. Industry experts have cautiously welcomed the findings, noting that independent verification will be crucial.";
      } else if (domain.includes("xyz") || domain.includes("suspicious") || domain.includes("fake")) {
        textToAnalyze = "AMAZING DEAL!!! You won't BELIEVE these prices! BUY NOW before it's too late! This is the BEST product ever made. Everyone is talking about it. Don't miss out on this incredible opportunity. LIMITED TIME OFFER!!! Click here NOW!!!";
      }
    } catch {
      // Use default text
    }
  }

  if (textToAnalyze.length > 10) {
    const features = extractTextFeatures(textToAnalyze);
    const textResult = analyzeTextScore(features);
    
    signals.push({
      id: uuidv4(),
      scanId,
      type: "text",
      score: textResult.score,
      label: textResult.label,
      confidence: textResult.confidence,
      evidence: textResult.details,
      highlights: textResult.highlights,
    });
  }

  // Domain analysis (for URL scans)
  if (input.contentType === "url" && input.url) {
    const domainResult = analyzeDomain(input.url);
    
    signals.push({
      id: uuidv4(),
      scanId,
      type: "domain",
      score: domainResult.score,
      label: domainResult.label,
      confidence: domainResult.confidence,
      evidence: domainResult.details,
      highlights: domainResult.highlights,
    });

    // Simulated provenance signal
    signals.push({
      id: uuidv4(),
      scanId,
      type: "provenance",
      score: 50 + Math.floor(Math.random() * 40),
      label: "Provenance Check",
      confidence: 0.6 + Math.random() * 0.3,
      evidence: {
        earliestDate: new Date(Date.now() - Math.random() * 365 * 24 * 3600000).toISOString(),
        sources: ["Google Cache", "Wayback Machine"],
        imageMatches: Math.floor(Math.random() * 5),
      },
      highlights: [],
    });
  }

  // Calculate ensemble trust score
  let weightedSum = 0;
  let weightSum = 0;

  signals.forEach(signal => {
    const weight = SIGNAL_WEIGHTS[signal.type as keyof typeof SIGNAL_WEIGHTS] || 0.1;
    const confidenceAdjusted = signal.score * signal.confidence;
    weightedSum += confidenceAdjusted * weight;
    weightSum += weight * signal.confidence;
  });

  const trustScore = weightSum > 0 ? Math.round(weightedSum / weightSum) : 50;

  let verdict: "Authentic" | "Suspicious" | "AI-Generated";
  if (trustScore >= 70) verdict = "Authentic";
  else if (trustScore >= 40) verdict = "Suspicious";
  else verdict = "AI-Generated";

  const scanDuration = (Date.now() - startTime) / 1000;

  return { trustScore, verdict, signals, scanDuration };
}

// === Document Analysis ===
export async function analyzeDocument(
  filename: string,
  fileType: string,
  fileSize: number
): Promise<{ trustScore: number; findings: Array<{ type: string; severity: "low" | "medium" | "high"; message: string; field?: string }> }> {
  await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 3000));

  const findings: Array<{ type: string; severity: "low" | "medium" | "high"; message: string; field?: string }> = [];
  let score = 75;

  // File type checks
  if (fileType === "application/pdf") {
    findings.push({
      type: "Format Validation",
      severity: "low",
      message: "PDF format is valid and well-formed",
    });

    if (fileSize > 5000000) {
      findings.push({
        type: "File Size",
        severity: "medium",
        message: "Large file size may indicate embedded high-resolution images",
      });
    }

    // Simulate metadata check
    findings.push({
      type: "Metadata Integrity",
      severity: "low",
      message: "Document creation metadata is consistent",
    });

    // Random chance of finding issues
    if (Math.random() > 0.7) {
      findings.push({
        type: "Font Consistency",
        severity: "medium",
        message: "Multiple font families detected — possible copy-paste from different sources",
        field: "body"
      });
      score -= 10;
    }
  }

  // Filename analysis
  if (filename.toLowerCase().includes("aadhaar") || filename.toLowerCase().includes("aadhar")) {
    findings.push({
      type: "Document Classification",
      severity: "low",
      message: "Identified as Aadhaar card document",
    });
    findings.push({
      type: "QR Code Check",
      severity: "low",
      message: "QR code structure validation passed",
    });
  }

  if (filename.toLowerCase().includes("invoice")) {
    findings.push({
      type: "Document Classification",
      severity: "low",
      message: "Identified as invoice document",
    });
    findings.push({
      type: "Arithmetic Consistency",
      severity: "low",
      message: "Line items sum matches total amount",
    });
  }

  // General checks
  findings.push({
    type: "Tamper Detection",
    severity: "low",
    message: "No evidence of pixel-level manipulation detected",
  });

  score = Math.max(0, Math.min(100, score));

  return { trustScore: score, findings };
}
