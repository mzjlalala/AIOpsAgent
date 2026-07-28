<script setup lang="ts">
defineProps<{
  subtitle?: string;
}>();
</script>

<template>
  <header class="brand">
    <h1 class="brand__name">OpsAgent</h1>
    <p class="brand__tag">{{ subtitle || "事故排查演示控制台 · SSE + 人工审批" }}</p>
  </header>
</template>
