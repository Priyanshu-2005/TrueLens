import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

// GET /api/v1/scans/[id] — Proxy Get a specific scan
export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    
    const response = await fetch(`${BACKEND_URL}/api/v1/scans/${id}`, {
      headers: { "Content-Type": "application/json" },
    });

    if (response.status === 404) {
      return NextResponse.json(
        { error: "Scan not found in backend." },
        { status: 404 }
      );
    }

    if (!response.ok) {
      return NextResponse.json(
        { error: "Failed to fetch scan from backend." },
        { status: response.status }
      );
    }

    const data = await response.json();
    
    // Map snake_case to camelCase for Next.js UI compatibility
    const scan = {
      ...data,
      contentType: data.content_type,
      trustScore: data.trust_score,
      scanDuration: data.scan_duration,
      createdAt: data.created_at,
      completedAt: data.completed_at
    };

    return NextResponse.json({ scan });
  } catch (error) {
    console.error("Error fetching scan:", error);
    return NextResponse.json(
      { error: "Failed to fetch scan." },
      { status: 500 }
    );
  }
}
