<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import { renderMarkdown } from "../utils/markdown";

export type ChatRole = "user" | "assistant" | "progress" | "error";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
}

const props = defineProps<{
  messages: ChatMessage[];
  running: boolean;
  draft: string;
}>();

const emit = defineEmits<{
  "update:draft": [string];
  send: [];
  oneClick: [];
}>();

const box = ref<HTMLTextAreaElement | null>(null);
const scroller = ref<HTMLElement | null>(null);

const showThinking = computed(() => {
  if (!props.running) return false;
  const last = props.messages.at(-1);
  return last?.role !== "assistant";
});

const scrollKey = computed(() =>
  props.messages.map((m) => `${m.id}:${m.content.length}`).join("|"),
);

watch(scrollKey, async () => {
  await nextTick();
  if (scroller.value) {
    scroller.value.scrollTop = scroller.value.scrollHeight;
  }
});

function onKeydown(e: KeyboardEvent) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    if (!props.running && props.draft.trim()) emit("send");
  }
}

function autoGrow() {
  const el = box.value;
  if (!el) return;
  el.style.height = "auto";
  el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
}
</script>

<template>
  <main class="main">
    <header class="main__header">OpsAgent</header>

    <div ref="scroller" class="main__body">
      <div v-if="!messages.length" class="welcome">
        <h1>今天想排查点什么？</h1>
        <div class="composer-wrap">
          <div class="composer">
            <textarea
              ref="box"
              :value="draft"
              rows="1"
              placeholder="有问题，尽管问。例如：api 服务 CPU 打满怎么处理？"
              :disabled="running"
              @input="
                emit('update:draft', ($event.target as HTMLTextAreaElement).value);
                autoGrow();
              "
              @keydown="onKeydown"
            />
            <button
              class="composer__send"
              type="button"
              :disabled="running || !draft.trim()"
              title="发送"
              @click="emit('send')"
            >
              ↑
            </button>
          </div>
          <div class="chips">
            <button class="chip" type="button" :disabled="running" @click="emit('oneClick')">
              一键运维巡检
            </button>
            <button
              class="chip"
              type="button"
              :disabled="running"
              @click="emit('update:draft', '服务内存持续上涨疑似泄漏，帮我分析原因和处置建议'); emit('send')"
            >
              内存异常分析
            </button>
            <button
              class="chip"
              type="button"
              :disabled="running"
              @click="emit('update:draft', '最近发布后接口变慢，怎么排查？'); emit('send')"
            >
              接口变慢排查
            </button>
          </div>
        </div>
      </div>

      <div v-else class="thread">
        <article
          v-for="m in messages"
          :key="m.id"
          class="bubble"
          :class="`bubble--${m.role}`"
        >
          <div class="bubble__role">
            <template v-if="m.role === 'user'">你</template>
            <template v-else-if="m.role === 'progress'">排查中</template>
            <template v-else-if="m.role === 'error'">出错</template>
            <template v-else>OpsAgent</template>
          </div>
          <div
            v-if="m.role === 'assistant'"
            class="bubble__content md"
            v-html="renderMarkdown(m.content)"
          />
          <pre v-else class="bubble__content">{{ m.content }}</pre>
        </article>
        <article v-if="showThinking" class="bubble bubble--progress">
          <div class="bubble__role">排查中</div>
          <pre class="bubble__content">正在思考与汇总…</pre>
        </article>
      </div>
    </div>

    <div v-if="messages.length" class="dock">
      <div class="composer-wrap">
        <div class="composer">
          <textarea
            :value="draft"
            rows="1"
            placeholder="继续追问，或描述新的故障现象…"
            :disabled="running"
            @input="emit('update:draft', ($event.target as HTMLTextAreaElement).value)"
            @keydown="onKeydown"
          />
          <button
            class="composer__send"
            type="button"
            :disabled="running || !draft.trim()"
            @click="emit('send')"
          >
            ↑
          </button>
        </div>
        <div class="chips">
          <button class="chip" type="button" :disabled="running" @click="emit('oneClick')">
            一键运维巡检
          </button>
        </div>
        <p class="hint">OpsAgent 可能出错，重要变更请人工复核</p>
      </div>
    </div>
  </main>
</template>
