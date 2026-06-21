import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

import { env } from "@/env";

const VALID_TEMPLATES = new Set(["generic", "sql_payroll", "kakitangan"]);

export async function GET(request: NextRequest) {
  const taxYear = request.nextUrl.searchParams.get("tax_year");
  const template = request.nextUrl.searchParams.get("template") ?? "generic";

  if (!taxYear || !/^\d{4}$/.test(taxYear)) {
    return NextResponse.json(
      { message: "tax_year query parameter is required." },
      { status: 400 },
    );
  }

  if (!VALID_TEMPLATES.has(template)) {
    return NextResponse.json(
      { message: "Invalid export template." },
      { status: 400 },
    );
  }

  const cookieStore = await cookies();
  const session = cookieStore.get(env.SESSION_COOKIE_NAME);

  if (!session?.value) {
    return NextResponse.json({ message: "Unauthorized" }, { status: 401 });
  }

  const params = new URLSearchParams({
    tax_year: taxYear,
    template,
  });

  const upstream = await fetch(
    `${env.FASTAPI_URL}/api/v1/org/export/csv?${params.toString()}`,
    {
      headers: {
        Cookie: `${env.SESSION_COOKIE_NAME}=${session.value}`,
      },
      cache: "no-store",
    },
  );

  if (!upstream.ok) {
    return NextResponse.json(
      { message: "Failed to export payroll CSV." },
      { status: upstream.status },
    );
  }

  const body = await upstream.arrayBuffer();
  const contentType = upstream.headers.get("content-type") ?? "text/csv";
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
