import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";

const assetBasePath = process.env.GITHUB_PAGES === "true" ? "/NTRM" : "";

export const metadata: Metadata = {
  title: "NTRM — Network Theory Resilience Metric Dashboard",
  description: "Interactive cascade prediction and mitigation control dashboard for the NTRM research prototype.",
  keywords: ["NTRM", "cascade prediction", "power systems", "resilience", "IEEE 39-bus", "machine learning"],
  authors: [{ name: "University of Sussex" }],
  icons: {
    icon: `${assetBasePath}/logo.svg`,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body
        className="antialiased"
        style={{ background: "oklch(0.1 0.01 260)" }}
      >
        {children}
        <Toaster />
      </body>
    </html>
  );
}
