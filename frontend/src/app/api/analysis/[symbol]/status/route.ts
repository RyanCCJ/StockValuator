import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ symbol: string }> }
) {
    const { symbol } = await params;

    try {
        const response = await fetch(`${BACKEND_URL}/analysis/${symbol}/status`);
        const data = await response.json();
        return NextResponse.json(data);
    } catch {
        return NextResponse.json({ symbol, cached: false, fetching: false });
    }
}
