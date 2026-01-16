/**
 * API Proxy Route - Forwards all /api/* requests to the backend
 * This allows runtime configuration of the backend URL
 */

import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

async function proxyRequest(request: NextRequest, path: string) {
    const url = new URL(path, BACKEND_URL);

    // Copy query parameters
    request.nextUrl.searchParams.forEach((value, key) => {
        url.searchParams.set(key, value);
    });

    // Prepare headers (exclude host and other problematic headers)
    const headers = new Headers();
    request.headers.forEach((value, key) => {
        if (!['host', 'connection', 'transfer-encoding'].includes(key.toLowerCase())) {
            headers.set(key, value);
        }
    });

    // Forward the request
    const response = await fetch(url.toString(), {
        method: request.method,
        headers,
        body: request.body,
        // @ts-expect-error - duplex is required for streaming body
        duplex: 'half',
    });

    // Create response with the same headers
    const responseHeaders = new Headers();
    response.headers.forEach((value, key) => {
        if (!['transfer-encoding', 'content-encoding'].includes(key.toLowerCase())) {
            responseHeaders.set(key, value);
        }
    });

    return new NextResponse(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: responseHeaders,
    });
}

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ path: string[] }> }
) {
    const { path } = await params;
    return proxyRequest(request, '/' + path.join('/'));
}

export async function POST(
    request: NextRequest,
    { params }: { params: Promise<{ path: string[] }> }
) {
    const { path } = await params;
    return proxyRequest(request, '/' + path.join('/'));
}

export async function PUT(
    request: NextRequest,
    { params }: { params: Promise<{ path: string[] }> }
) {
    const { path } = await params;
    return proxyRequest(request, '/' + path.join('/'));
}

export async function PATCH(
    request: NextRequest,
    { params }: { params: Promise<{ path: string[] }> }
) {
    const { path } = await params;
    return proxyRequest(request, '/' + path.join('/'));
}

export async function DELETE(
    request: NextRequest,
    { params }: { params: Promise<{ path: string[] }> }
) {
    const { path } = await params;
    return proxyRequest(request, '/' + path.join('/'));
}
