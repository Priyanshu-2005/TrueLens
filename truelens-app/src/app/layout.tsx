import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

export const metadata: Metadata = {
  title: "TrueLens — Verifying Authenticity in the Age of AI",
  description:
    "TrueLens is an AI-powered platform that detects AI-generated content, fake reviews, manipulated images, and fraudulent documents. Get trust scores, cryptographic signing, and more.",
  keywords: [
    "AI detection",
    "fake news detector",
    "trust score",
    "content verification",
    "document signing",
    "AI-generated content",
    "fake review detection",
  ],
  authors: [
    { name: "Aryam Agarwal" },
    { name: "Priyanshu Agarwal" },
    { name: "Hitarth Singh Rajput" },
    { name: "Akshat Singh" },
    { name: "Piyush Kumar" },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
      </head>
      <body className="min-h-screen flex flex-col" style={{ background: "var(--bg-primary)", overflowX: "hidden" }}>
        <Navbar />
        <main className="flex-1 w-full" style={{ paddingTop: "64px" }}>{children}</main>
        <Footer />
      </body>
    </html>
  );
}
