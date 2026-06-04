import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "JobOps AI",
  description: "Score jobs, generate outreach, track applications.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
