import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Quality Engineering Lab",
  description: "Intent Classification & Routing Instability Simulator",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-[#09090B] text-[#F4F4F5] antialiased">{children}</body>
    </html>
  );
}
