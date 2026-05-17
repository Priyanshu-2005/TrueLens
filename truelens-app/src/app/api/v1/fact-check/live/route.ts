import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

// GET /api/v1/fact-check/live — Proxy to FastAPI backend
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const query = searchParams.get("query");

    if (!query || query.trim().length < 3) {
      return NextResponse.json(
        { detail: "Please provide a valid query (min 3 characters)." },
        { status: 400 }
      );
    }

    // Proxy the request to the Python backend
    const response = await fetch(`${BACKEND_URL}/api/v1/fact-check/live?query=${encodeURIComponent(query)}`);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        { detail: errorData.detail || "Failed to execute live AI fact-check in backend." },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Live Fact-check proxy error:", error);
    return NextResponse.json(
      { detail: "Internal server error connecting to backend." },
      { status: 500 }
    );
  }
}
