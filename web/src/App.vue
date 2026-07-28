<script setup lang="ts">
import { computed, ref } from "vue";
import {
  getWorkflow,
  streamIncident,
  streamOneClick,
  type Scenario,
  type SseEvent,
} from "./api/client";
import BrandHeader from "./components/BrandHeader.vue";
import EventTimeline from "./components/EventTimeline.vue";
import IncidentForm from "./components/IncidentForm.vue";
import StatusBar from "./components/StatusBar.vue";

const query = ref("线上服务 CPU 突然打满 100%");
const scenario = ref<Scenario>("auto_ops");
const events = ref<SseEvent[]>([]);
const workflowId = ref("");
const status = ref("idle");
const running = ref(false);
const errorMsg = ref("");
let abort: AbortController | null = null;

const formDisabled = computed(() => running.value);

function handleEvent(ev: SseEvent) {
  events.value = [...events.value, ev];
  if (ev.workflow_id) workflowId.value = ev.workflow_id;
  if (ev.type === "completed") {
    const s = (ev.payload?.status as string) || "completed";
    status.value = s;
  } else if (ev.type === "error") {
    status.value = "error";
    errorMsg.value = ev.message || "执行出错";
  }
}

async function runStream(starter: () => Promise<void>) {
  if (running.value) return;
  errorMsg.value = "";
  events.value = [];
  workflowId.value = "";
  status.value = "running";
  running.value = true;
  abort?.abort();
  abort = new AbortController();

  try {
    await starter();
    if (workflowId.value && status.value === "running") {
      const run = await getWorkflow(workflowId.value);
      status.value = run.status;
    }
  } catch (err) {
    if ((err as Error).name === "AbortError") return;
    status.value = "error";
    errorMsg.value = err instanceof Error ? err.message : String(err);
  } finally {
    running.value = false;
  }
}

async function startOneClick() {
  await runStream(() => streamOneClick(handleEvent, abort?.signal));
}

async function startAdvanced() {
  if (!query.value.trim()) return;
  await runStream(() =>
    streamIncident(
      query.value.trim(),
      scenario.value,
      handleEvent,
      abort?.signal,
    ),
  );
}

function resetAll() {
  abort?.abort();
  running.value = false;
  events.value = [];
  workflowId.value = "";
  status.value = "idle";
  errorMsg.value = "";
}
</script>

<template>
  <div class="shell">
    <BrandHeader subtitle="一键运维演示 · Agent 自主查询指标 / 日志 / 知识库" />
    <IncidentForm
      v-model:model-query="query"
      v-model:model-scenario="scenario"
      :disabled="formDisabled"
      @one-click="startOneClick"
      @submit-advanced="startAdvanced"
      @reset="resetAll"
    />
    <StatusBar :workflow-id="workflowId" :status="status" />
    <p v-if="errorMsg" class="error-banner">{{ errorMsg }}</p>
    <EventTimeline :events="events" />
  </div>
</template>
