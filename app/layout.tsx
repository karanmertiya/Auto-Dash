import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import { Zap, BarChart2 } from "lucide-react";

import "./globals.css";

export const metadata: Metadata = {
  title: "Auto-Dash: Data & Automation",
  description: "Next generation dashboard and automation builder",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900 font-sans antialiased selection:bg-indigo-100 selection:text-indigo-900">
        <nav className="sticky top-0 z-50 w-full border-b border-white/20 bg-white/60 backdrop-blur-md shadow-sm">
          <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
            <div className="flex h-16 items-center justify-between">
              <div className="flex items-center gap-8">
                <div className="flex-shrink-0 flex items-center gap-2">
                  <div className="bg-gradient-to-tr from-indigo-600 to-blue-500 text-white p-1.5 rounded-lg shadow-md shadow-indigo-500/30">
                    <Zap className="h-5 w-5" />
                  </div>
                  <span className="font-extrabold text-xl tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-slate-900 to-slate-600">
                    Auto-Dash
                  </span>
                </div>
                <div className="hidden md:block">
                  <div className="flex items-baseline space-x-2">
                    <Link
                      href="/"
                      className="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100/80 hover:text-slate-900 transition-colors"
                    >
                      <BarChart2 className="h-4 w-4" />
                      Dashboard
                    </Link>
                    <Link
                      href="/automation"
                      className="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100/80 hover:text-slate-900 transition-colors"
                    >
                      <Zap className="h-4 w-4" />
                      Automation
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </nav>
        <main>{children}</main>
      </body>
    </html>
  );
}
