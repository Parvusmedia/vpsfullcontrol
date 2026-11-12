import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

const PRODUCTION_HOST = "digitanimal.pmediaplus.com";

/** El hosting estático de Cursor Apps no ejecuta API routes; redirigimos al VPS. */
export function middleware(request: NextRequest) {
  const host = (request.headers.get("host") ?? "").split(":")[0].toLowerCase();
  if (host === PRODUCTION_HOST || host === "localhost" || host === "127.0.0.1") {
    return NextResponse.next();
  }
  if (host.endsWith(".apps.grok.bot") || host.includes("cursor")) {
    const target = new URL(request.url);
    target.protocol = "https:";
    target.host = PRODUCTION_HOST;
    return NextResponse.redirect(target, 308);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
