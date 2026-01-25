import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export const maxDuration = 120;

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ symbol: string }> }
) {
    const { symbol } = await params;

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 90000);

        const response = await fetch(`${BACKEND_URL}/analysis/${symbol}/value`, {
            signal: controller.signal,
            headers: {
                "Content-Type": "application/json",
            },
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            return NextResponse.json(
                { error: `Backend returned ${response.status}` },
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        if (error instanceof Error && error.name === "AbortError") {
            return NextResponse.json(
                { error: "Request timeout - data is being fetched, please retry in 30 seconds" },
                { status: 504 }
            );
        }
        return NextResponse.json(
            { error: "Failed to fetch value analysis" },
            { status: 500 }
        );
    }
}
