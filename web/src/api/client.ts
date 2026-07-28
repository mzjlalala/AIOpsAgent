export type Scenario = "cpu_high" | "memory_leak" | "auto_ops";

export type SseEventType =
  | "step_started"
  | "step_succeeded"
  | "step_failed"
  | "waiting_approval"
  | "completed"
  | "answer"
  | "answer_delta"
  | "session"
  | "tool_call"
  | "tool_result"
  | "error"
  | "snapshot";

export interface SseEvent {
  workflow_id: string;
  type: SseEventType;
  node: string;
  step_id?: string | null;
  agent?: string | null;
  message: string;
  payload: Record<string, unknown>;
}

export interface WorkflowRun {
  workflow_id: string;
  thread_id: string;
  status: string;
  user_query: string;
  plan_steps: Record<string, unknown>[];
  artifacts: Record<string, unknown>[];
  pending_approval: Record<string, unknown> | null;
  error: string | null;
  current_step_id: string | null;
}

export async function streamChat(
  message: string,
  onEvent: (event: SseEvent) => void,
  signal?: AbortSignal,
  conversationId?: string | null,
): Promise<void> {
  const response = await fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({
      message,
      conversation_id: conversationId || null,
    }),
    signal,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  if (!response.body) {
    throw new Error("响应无 body，无法读取 SSE");
  }
  await readSseStream(response.body, onEvent, signal);
}

export async function streamIncident(
  query: string,
  scenario: Scenario,
  onEvent: (event: SseEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch("/incident", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({ query, scenario }),
    signal,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  if (!response.body) {
    throw new Error("响应无 body，无法读取 SSE");
  }
  await readSseStream(response.body, onEvent, signal);
}

export async function streamOneClick(
  onEvent: (event: SseEvent) => void,
  signal?: AbortSignal,
  service?: string,
): Promise<void> {
  const response = await fetch("/ops/one-click", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({ service: service || null }),
    signal,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  if (!response.body) {
    throw new Error("响应无 body，无法读取 SSE");
  }
  await readSseStream(response.body, onEvent, signal);
}

export async function getWorkflow(workflowId: string): Promise<WorkflowRun> {
  const response = await fetch(`/workflows/${workflowId}`);
  if (!response.ok) {
    throw new Error(await response.text() || `HTTP ${response.status}`);
  }
  return (await response.json()) as WorkflowRun;
}

export async function approveWorkflow(
  workflowId: string,
  approved: boolean,
  comment?: string,
): Promise<WorkflowRun> {
  const response = await fetch(`/workflows/${workflowId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ approved, comment: comment || null }),
  });
  if (!response.ok) {
    throw new Error((await response.text()) || `HTTP ${response.status}`);
  }
  return (await response.json()) as WorkflowRun;
}

async function readSseStream(
  body: ReadableStream<Uint8Array>,
  onEvent: (event: SseEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    if (signal?.aborted) {
      await reader.cancel();
      break;
    }
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split(/\r?\n\r?\n/);
    buffer = parts.pop() ?? "";
    for (const block of parts) {
      const event = parseSseBlock(block);
      if (event) onEvent(event);
    }
  }
  if (buffer.trim()) {
    const event = parseSseBlock(buffer);
    if (event) onEvent(event);
  }
}

function parseSseBlock(block: string): SseEvent | null {
  const lines = block.split(/\r?\n/);
  let eventType: string | undefined;
  const dataLines: string[] = [];
  for (const line of lines) {
    if (line.startsWith("event:")) {
      eventType = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trim());
    }
  }
  if (!dataLines.length) return null;
  try {
    const payload = JSON.parse(dataLines.join("\n")) as SseEvent;
    if (eventType && payload.type !== eventType) {
      payload.type = eventType as SseEventType;
    }
    return payload;
  } catch {
    return null;
  }
}
