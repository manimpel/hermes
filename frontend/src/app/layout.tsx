import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Hermes — AI Freelance Matchmaking",
  description: "Find the perfect freelancer for your project, powered by AI",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-950 text-white min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}
