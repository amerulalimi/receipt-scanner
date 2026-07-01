import { NextResponse } from "next/server";

import type { NextRequest } from "next/server";

import {
  ADMIN_SESSION_COOKIE_NAME,
  SESSION_COOKIE_NAME,
} from "@/lib/constants/session-cookies";


const CLIENT_AUTH_ROUTES = ["/login", "/register"];

const ADMIN_AUTH_ROUTES = ["/admin/login"];



const PUBLIC_PREFIXES = [

  "/upload/session/",

  "/join/",

  "/verify-email",

];



function isPublicRoute(pathname: string): boolean {

  if (CLIENT_AUTH_ROUTES.includes(pathname) || ADMIN_AUTH_ROUTES.includes(pathname)) {

    return true;

  }

  return PUBLIC_PREFIXES.some(

    (prefix) => pathname === prefix || pathname.startsWith(prefix),

  );

}



function isClientProtectedRoute(pathname: string): boolean {

  return (

    pathname === "/dashboard" ||

    pathname.startsWith("/dashboard/") ||

    pathname === "/settings" ||

    pathname.startsWith("/settings/") ||

    pathname === "/org" ||

    pathname.startsWith("/org/")

  );

}



function isAdminProtectedRoute(pathname: string): boolean {

  if (pathname === "/admin/login") {

    return false;

  }

  return pathname === "/admin" || pathname.startsWith("/admin/");

}



export function middleware(request: NextRequest) {

  const { pathname } = request.nextUrl;



  if (isPublicRoute(pathname) && !CLIENT_AUTH_ROUTES.includes(pathname) && !ADMIN_AUTH_ROUTES.includes(pathname)) {

    return NextResponse.next();

  }



  const clientSession = request.cookies.get(SESSION_COOKIE_NAME);

  const adminSession = request.cookies.get(ADMIN_SESSION_COOKIE_NAME);

  const hasClientSession = Boolean(clientSession?.value);

  const hasAdminSession = Boolean(adminSession?.value);

  if (isAdminProtectedRoute(pathname) && !hasAdminSession) {

    const loginUrl = request.nextUrl.clone();

    loginUrl.pathname = "/admin/login";

    loginUrl.searchParams.set("redirect", pathname);

    return NextResponse.redirect(loginUrl);

  }



  if (isClientProtectedRoute(pathname) && !hasClientSession) {

    const loginUrl = request.nextUrl.clone();

    loginUrl.pathname = "/login";

    loginUrl.searchParams.set("redirect", pathname);

    return NextResponse.redirect(loginUrl);

  }



  if (CLIENT_AUTH_ROUTES.includes(pathname) && hasClientSession) {

    const dashboardUrl = request.nextUrl.clone();

    dashboardUrl.pathname = "/dashboard";

    dashboardUrl.search = "";

    return NextResponse.redirect(dashboardUrl);

  }



  if (ADMIN_AUTH_ROUTES.includes(pathname) && hasAdminSession) {

    const adminUrl = request.nextUrl.clone();

    adminUrl.pathname = "/admin";

    adminUrl.search = "";

    return NextResponse.redirect(adminUrl);

  }



  return NextResponse.next();

}



export const config = {

  matcher: [

    "/login",

    "/register",

    "/dashboard/:path*",

    "/settings/:path*",

    "/org/:path*",

    "/admin",

    "/admin/:path*",

    "/upload/session/:path*",

    "/join/:path*",

    "/verify-email",

  ],

};


