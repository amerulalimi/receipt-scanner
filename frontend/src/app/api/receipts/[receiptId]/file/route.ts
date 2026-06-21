import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

import { env } from "@/env";

type RouteContext = {
  params: Promise<{ receiptId: string }>;
};

async function proxyReceiptAsset(
  receiptId: string,
  asset: "file" | "thumbnail",
) {
  const cookieStore = await cookies();
  const session = cookieStore.get(env.SESSION_COOKIE_NAME);

  if (!session?.value) {
    return NextResponse.json({ message: "Unauthorized" }, { status: 401 });
  }

  const upstream = await fetch(
    `${env.FASTAPI_URL}/api/v1/receipts/${receiptId}/${asset}`,
    {
      headers: {
        Cookie: `${env.SESSION_COOKIE_NAME}=${session.value}`,
      },
      cache: "no-store",
    },
  );

  if (!upstream.ok) {
    return NextResponse.json(
      { message: "Receipt file not found." },
      { status: upstream.status },
    );
  }

  const body = await upstream.arrayBuffer();
  const contentType =
    upstream.headers.get("content-type") ?? "application/octet-stream";
  const disposition = upstream.headers.get("content-disposition");

  return new NextResponse(body, {
    status: upstream.status,
    headers: {
      "Content-Type": contentType,
      ...(disposition ? { "Content-Disposition": disposition } : {}),
      "Cache-Control": "private, max-age=300",
    },
  });
}

export async function GET(_request: NextRequest, context: RouteContext) {
  const { receiptId } = await context.params;
  return proxyReceiptAsset(receiptId, "file");
}
