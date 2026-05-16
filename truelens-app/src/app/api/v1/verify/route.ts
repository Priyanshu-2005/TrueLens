import { NextRequest, NextResponse } from "next/server";
import { dataStore } from "@/lib/store";

// POST /api/v1/verify — Verify a document by hash or scanId
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { hash, scanId } = body;

    if (!hash && !scanId) {
      return NextResponse.json(
        { error: "Provide either a document hash or scanId for verification." },
        { status: 400 }
      );
    }

    const documents = dataStore.getAllDocuments();
    let doc;

    if (scanId) {
      doc = documents.find(d => d.id === scanId);
    } else if (hash) {
      doc = documents.find(d => d.hash === hash);
    }

    if (!doc) {
      return NextResponse.json({
        verified: false,
        message: "No matching document found in TrueLens records.",
      });
    }

    if (doc.signature && doc.status === "verified") {
      return NextResponse.json({
        verified: true,
        document: {
          id: doc.id,
          filename: doc.filename,
          hash: doc.hash,
          trustScore: doc.trustScore,
          status: doc.status,
          verifiedAt: doc.signature.timestamp,
          signatureValid: true,
        },
        message: "Document is verified and has a valid TrueLens signature.",
      });
    }

    return NextResponse.json({
      verified: false,
      document: {
        id: doc.id,
        filename: doc.filename,
        hash: doc.hash,
        trustScore: doc.trustScore,
        status: doc.status,
      },
      message: doc.status === "flagged"
        ? "Document has been flagged for potential tampering."
        : "Document found but not yet verified.",
    });
  } catch (error) {
    console.error("Verification error:", error);
    return NextResponse.json(
      { error: "Verification failed." },
      { status: 500 }
    );
  }
}
