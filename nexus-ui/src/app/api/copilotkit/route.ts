import {
  CopilotRuntime,
  copilotRuntimeNextJSAppRouterEndpoint,
  OpenAIAdapter,
} from "@copilotkit/runtime";
import { NextRequest } from "next/server";
import { HttpAgent } from "@ag-ui/client";

const agnoAgent = new HttpAgent({
  url: process.env.AGNO_AGUI_URL || "http://localhost:7777/agui",
});

const serviceAdapter = new OpenAIAdapter();

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const runtime = new CopilotRuntime({
  agents: {
    nexus: agnoAgent,
  },
} as any);

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });
  return handleRequest(req);
};
