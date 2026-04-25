import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";
import { Shell } from "@/components/shell";

export const metadata: Metadata = {
  title: "DashForge Core",
  description: "Expert-grade glass-box data-to-dashboard accelerator"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}
