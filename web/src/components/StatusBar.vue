<script setup lang="ts">
defineProps<{
  workflowId: string;
  status: string;
}>();
</script>

<template>
  <section class="panel">
    <h2>当前状态</h2>
    <div class="status-bar">
      <div class="status-bar__item">
        <span class="status-bar__label">workflow_id</span>
        <span class="status-bar__value">{{ workflowId || "—" }}</span>
      </div>
      <div class="status-bar__item">
        <span class="status-bar__label">status</span>
        <span class="badge" :class="`badge--${status || 'idle'}`">{{ status || "idle" }}</span>
      </div>
    </div>
  </section>
</template>
