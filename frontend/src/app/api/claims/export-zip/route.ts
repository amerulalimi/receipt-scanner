import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

import { env } from "@/env";

export async function GET(request: NextRequest) {
  const taxYear = request.nextUrl.searchParams.get("tax_year");

  if (!taxYear || !/^\d{4}$/.test(taxYear)) {
    return NextResponse.json(
      { message: "tax_year query parameter is required." },
      { status: 400 },
    );
  }

  const cookieStore = await cookies();
  const session = cookieStore.get(env.SESSION_COOKIE_NAME);

  if (!session?.value) {
    return NextResponse.json({ message: "Unauthorized" }, { status: 401 });
  }

  const upstream = await fetch(
    `${env.FASTAPI_URL}/api/v1/claims/export-zip?tax_year=${taxYear}`,
    {
      headers: {
        Cookie: `${env.SESSION_COOKIE_NAME}=${session.value}`,
      },
      cache: "no-store",
    },
  );

  if (!upstream.ok) {
    return NextResponse.json(
      { message: "Failed to export receipts." },
      { status: upstream.status },
    );
  }

  const body = await upstream.arrayBuffer();
  const contentType =
    upstream.headers.get("content-type") ?? "application/zip";
  const disposition = upstream.headers.get("content-disposition");

  return new NextResponse(body, {
    status: upstream.status,
    headers: {
      "Content-Type": contentType,
      ...(disposition ? { "Content-Disposition": disposition } : {}),
      "Cache-Control": "private, no-store",
    },
  });
}
