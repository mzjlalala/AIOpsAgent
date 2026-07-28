<script setup lang="ts">
import { computed, ref } from "vue";
import { streamChat, streamOneClick, type SseEvent } from "./api/client";
import ChatMain, { type ChatMessage } from "./components/ChatMain.vue";
import Sidebar from "./components/Sidebar.vue";

interface SessionState {
  id: string;
  title: string;
  conversationId: string | null;
  messages: ChatMessage[];
}

const sessions = ref<SessionState[]>([]);
const activeId = ref("");
const draft = ref("");
const running = ref(false);
let abort: AbortController | null = null;
let msgSeq = 0;
/** 当前轮次流式结论气泡 id */
let streamingAssistantId: string | null = null;

const active = computed(
  () => sessions.value.find((s) => s.id === activeId.value) ?? null,
);
const messages = computed(() => active.value?.messages ?? []);
const sessionList = computed(() =>
  sessions.value.map(({ id, title }) => ({ id, title })),
);

function uid(prefix: string) {
  msgSeq += 1;
  return `${prefix}-${Date.now()}-${msgSeq}`;
}

function ensureSession(title: string): SessionState {
  if (active.value) return active.value;
  const session: SessionState = {
    id: uid("s"),
    title: title.slice(0, 28) || "新对话",
    conversationId: null,
    messages: [],
  };
  sessions.value = [session, ...sessions.value];
  activeId.value = session.id;
  return session;
}

function pushMessage(session: SessionState, role: ChatMessage["role"], content: string) {
  session.messages = [
    ...session.messages,
    { id: uid("m"), role, content },
  ];
}

function newChat() {
  abort?.abort();
  running.value = false;
  draft.value = "";
  activeId.value = "";
}

function selectSession(id: string) {
  if (running.value) return;
  activeId.value = id;
  draft.value = "";
}

function appendAssistantDelta(session: SessionState, delta: string) {
  if (!streamingAssistantId) {
    streamingAssistantId = uid("m");
    session.messages = [
      ...session.messages,
      { id: streamingAssistantId, role: "assistant", content: delta },
    ];
    return;
  }
  const msg = session.messages.find((m) => m.id === streamingAssistantId);
  if (!msg) return;
  msg.content += delta;
  session.messages = [...session.messages];
}

function handleEvent(session: SessionState, ev: SseEvent) {
  if (ev.type === "session") {
    const cid = ev.payload.conversation_id;
    if (typeof cid === "string" && cid) {
      session.conversationId = cid;
    }
    return;
  }
  if (
    ev.type === "step_started" ||
    ev.type === "step_succeeded" ||
    ev.type === "step_failed" ||
    ev.type === "tool_call" ||
    ev.type === "tool_result"
  ) {
    pushMessage(session, "progress", ev.message);
    return;
  }
  if (ev.type === "answer_delta") {
    appendAssistantDelta(session, ev.message || "");
    return;
  }
  if (ev.type === "answer") {
    if (streamingAssistantId) {
      const msg = session.messages.find((m) => m.id === streamingAssistantId);
      if (msg) {
        msg.content = ev.message || msg.content || "（无结论）";
        session.messages = [...session.messages];
      }
      streamingAssistantId = null;
      return;
    }
    pushMessage(session, "assistant", ev.message || "（无结论）");
    return;
  }
  if (ev.type === "error") {
    pushMessage(session, "error", ev.message || "请求失败");
  }
}

async function runAsk(text: string, mode: "chat" | "oneClick") {
  const content = text.trim();
  if (running.value) return;
  if (mode === "chat" && !content) return;

  const title = mode === "oneClick" ? "一键运维巡检" : content;
  const session = ensureSession(title);
  if (!session.title || session.title === "新对话") {
    session.title = title.slice(0, 28);
  }

  const userText =
    mode === "oneClick"
      ? "请对默认服务做一键健康巡检，并给出问题判断与解决建议。"
      : content;
  pushMessage(session, "user", userText);
  draft.value = "";
  running.value = true;
  streamingAssistantId = null;
  abort?.abort();
  abort = new AbortController();

  try {
    if (mode === "oneClick") {
      await streamOneClick((ev) => handleEvent(session, ev), abort.signal);
    } else {
      await streamChat(
        content,
        (ev) => handleEvent(session, ev),
        abort.signal,
        session.conversationId,
      );
    }
  } catch (err) {
    if ((err as Error).name === "AbortError") return;
    pushMessage(
      session,
      "error",
      err instanceof Error ? err.message : String(err),
    );
  } finally {
    running.value = false;
  }
}

function onSend() {
  void runAsk(draft.value, "chat");
}

function onOneClick() {
  void runAsk("", "oneClick");
}
</script>

<template>
  <div class="app-shell">
    <Sidebar
      :sessions="sessionList"
      :active-id="activeId"
      @new-chat="newChat"
      @select="selectSession"
    />
    <ChatMain
      :messages="messages"
      :running="running"
      :draft="draft"
      @update:draft="draft = $event"
      @send="onSend"
      @one-click="onOneClick"
    />
  </div>
</template>
