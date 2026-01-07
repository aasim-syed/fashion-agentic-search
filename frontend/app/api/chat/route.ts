import { NextResponse } from "next/server";

export const runtime = "nodejs";

export async function POST(req: Request) {
  try {
    const form = await req.formData();
    const message = (form.get("message") ?? "").toString();
    const image = form.get("image") as File | null;

    if (!message && !image) {
      return NextResponse.json({ error: "Missing message or image" }, { status: 400 });
    }

    // Backend URL (change if your backend runs somewhere else)
    const BACKEND_URL = process.env.BACKEND_URL ?? "http://127.0.0.1:8000/api/chat";

    const fwd = new FormData();
    if (message) fwd.append("message", message);
    if (image) fwd.append("image", image);

    const r = await fetch(BACKEND_URL, {
      method: "POST",
      body: fwd,
    });

    const text = await r.text();
    // Pass through backend response
    return new NextResponse(text, {
      status: r.status,
      headers: { "content-type": r.headers.get("content-type") ?? "application/json" },
    });
  } catch (e: any) {
    return NextResponse.json({ error: e?.message ?? "Proxy failed" }, { status: 500 });
  }
}
