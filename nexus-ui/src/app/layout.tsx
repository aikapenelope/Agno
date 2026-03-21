import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NEXUS — AikaLabs",
  description:
    "Multi-agent system: research, analytics, content, support, and more.",
};

/**
 * NEXUS UI Layout
 *
 * Connects directly to AgentOS REST API.
 * No CopilotKit middleware needed — talks to AgentOS endpoints directly.
 *
 * Backend: python nexus.py (runs on port 7777)
 * API: POST http://localhost:7777/teams/nexus/runs (form-data)
 */
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
