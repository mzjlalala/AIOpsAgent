<script setup lang="ts">
import { computed, ref } from "vue";
import {
  approveWorkflow,
  getWorkflow,
  streamIncident,
  type Scenario,
  type SseEvent,
} from "./api/client";
import ApprovalPanel from "./components/ApprovalPanel.vue";
import BrandHeader from "./components/BrandHeader.vue";
import EventTimeline from "./components/EventTimeline.vue";
import IncidentForm from "./components/IncidentForm.vue";
import StatusBar from "./components/StatusBar.vue";

const query = ref("线上服务 CPU 突然打满 100%");
const scenario = ref<Scenario>("cpu_high");
const events = ref<SseEvent[]>([]);
const workflowId = ref("");
const status = ref("idle");
const pending = ref<Record<string, unknown> | null>(null);
const running = ref(false);
const approving = ref(false);
const errorMsg = ref("");
let abort: AbortController | null = null;

const showApproval = computed(() => status.value === "waiting_approval");
const formDisabled = computed(() => running.value || approving.value);

async function startRun() {
  if (!query.value.trim() || running.value) return;
  errorMsg.value = "";
  events.value = [];
  workflowId.value = "";
  status.value = "running";
  pending.value = null;
  running.value = true;
  abort?.abort();
  abort = new AbortController();

  try {
    await streamIncident(
      query.value.trim(),
      scenario.value,
      (ev) => {
        events.value = [...events.value, ev];
        if (ev.workflow_id) workflowId.value = ev.workflow_id;
        if (ev.type === "waiting_approval") {
          status.value = "waiting_approval";
          pending.value = ev.payload ?? null;
        } else if (ev.type === "completed") {
          const s = (ev.payload?.status as string) || "completed";
          status.value = s;
        } else if (ev.type === "error") {
          status.value = "error";
          errorMsg.value = ev.message || "执行出错";
        }
      },
      abort.signal,
    );
    if (workflowId.value && status.value === "running") {
      const run = await getWorkflow(workflowId.value);
      status.value = run.status;
      pending.value = run.pending_approval;
    }
  } catch (err) {
    if ((err as Error).name === "AbortError") return;
    status.value = "error";
    errorMsg.value = err instanceof Error ? err.message : String(err);
  } finally {
    running.value = false;
  }
}

async function onApprove(comment: string) {
  await decide(true, comment);
}

async function onReject(comment: string) {
  await decide(false, comment);
}

async function decide(approved: boolean, comment: string) {
  if (!workflowId.value || approving.value) return;
  approving.value = true;
  errorMsg.value = "";
  try {
    const run = await approveWorkflow(workflowId.value, approved, comment);
    status.value = run.status;
    pending.value = run.pending_approval;
    events.value = [
      ...events.value,
      {
        workflow_id: run.workflow_id,
        type: "completed",
        node: "approve",
        message: `审批${approved ? "通过" : "拒绝"} · ${run.status}`,
        payload: { status: run.status },
      },
    ];
  } catch (err) {
    errorMsg.value = err instanceof Error ? err.message : String(err);
  } finally {
    approving.value = false;
  }
}

function resetAll() {
  abort?.abort();
  running.value = false;
  approving.value = false;
  events.value = [];
  workflowId.value = "";
  status.value = "idle";
  pending.value = null;
  errorMsg.value = "";
}
</script>

<template>
  <div class="shell">
    <BrandHeader />
    <IncidentForm
      v-model:model-query="query"
      v-model:model-scenario="scenario"
      :disabled="formDisabled"
      @submit="startRun"
      @reset="resetAll"
    />
    <StatusBar :workflow-id="workflowId" :status="status" />
    <p v-if="errorMsg" class="error-banner">{{ errorMsg }}</p>
    <EventTimeline :events="events" />
    <ApprovalPanel
      v-if="showApproval"
      :busy="approving"
      :pending="pending"
      @approve="onApprove"
      @reject="onReject"
    />
  </div>
</template>
