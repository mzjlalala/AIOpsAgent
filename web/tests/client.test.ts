import assert from "node:assert/strict";
import test from "node:test";

import { streamChat, type SseEvent } from "../src/api/client.ts";

test("streamChat parses CRLF SSE frames split across chunks", async () => {
  const encoder = new TextEncoder();
  const first =
    'event: answer_delta\r\ndata: {"workflow_id":"w1","type":"answer_delta","node":"chat","message":"你好","payload":{}}\r';
  const second =
    '\n\r\nevent: answer\r\ndata: {"workflow_id":"w1","type":"answer","node":"chat","message":"你好！","payload":{}}\r\n\r\n';
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(encoder.encode(first));
      controller.enqueue(encoder.encode(second));
      controller.close();
    },
  });
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () =>
    new Response(body, {
      status: 200,
      headers: { "Content-Type": "text/event-stream" },
    });
  const events: SseEvent[] = [];

  try {
    await streamChat("hi", (event) => events.push(event));
  } finally {
    globalThis.fetch = originalFetch;
  }

  assert.deepEqual(
    events.map((event) => [event.type, event.message]),
    [
      ["answer_delta", "你好"],
      ["answer", "你好！"],
    ],
  );
});
