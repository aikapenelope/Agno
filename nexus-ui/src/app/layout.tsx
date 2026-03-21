import type { Metadata } from "next";
import { CopilotKit } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "NEXUS — AikaLabs",
  description:
    "Multi-agent system: research, analytics, content, support, and more.",
};

/**
 * NEXUS UI Layout
 *
 * CopilotKit connects to the AgentOS AGUI endpoint.
 * The NEXUS Master Team (12 specialist agents) handles all requests.
 *
 * Backend: python nexus.py (runs on port 7777)
 * AGUI endpoint: POST http://localhost:7777/agui
 *
 * To change the backend URL, set NEXT_PUBLIC_AGUI_URL env var:
 *   NEXT_PUBLIC_AGUI_URL=https://your-server.com npm run dev
 */
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const aguiUrl =
    process.env.NEXT_PUBLIC_AGUI_URL || "http://localhost:7777";

  return (
    <html lang="es">
      <body>
        <CopilotKit runtimeUrl={`${aguiUrl}/agui`}>
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}
