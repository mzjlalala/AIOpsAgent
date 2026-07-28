<script setup lang="ts">
import type { SseEvent } from "../api/client";

defineProps<{
  events: SseEvent[];
}>();

function itemClass(type: string) {
  if (type === "waiting_approval") return "is-waiting";
  if (type === "error" || type === "step_failed") return "is-error";
  return "";
}
</script>

<template>
  <section class="panel">
    <h2>事件流</h2>
    <p v-if="!events.length" class="empty">尚未开始。提交故障描述后，这里会实时滚动 SSE 事件。</p>
    <ul v-else class="timeline">
      <li
        v-for="(ev, idx) in events"
        :key="`${ev.type}-${idx}-${ev.step_id || ''}`"
        class="timeline__item"
        :class="itemClass(ev.type)"
      >
        <span class="timeline__dot" />
        <div class="timeline__body">
          <p class="timeline__msg">{{ ev.message || ev.type }}</p>
          <p class="timeline__meta">
            {{ ev.type }}
            <template v-if="ev.agent"> · {{ ev.agent }}</template>
            <template v-if="ev.step_id"> · step {{ ev.step_id }}</template>
          </p>
        </div>
      </li>
    </ul>
  </section>
</template>
