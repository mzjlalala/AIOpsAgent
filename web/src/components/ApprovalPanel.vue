<script setup lang="ts">
import { ref } from "vue";

defineProps<{
  busy?: boolean;
  pending?: Record<string, unknown> | null;
}>();

const emit = defineEmits<{
  approve: [comment: string];
  reject: [comment: string];
}>();

const comment = ref("");
</script>

<template>
  <section class="panel approval">
    <h2>人工审批</h2>
    <p class="approval__hint">高风险步骤等待确认（Waiting Approval…）</p>
    <p v-if="pending" class="timeline__meta" style="margin-bottom: 0.75rem">
      <template v-if="pending.agent">agent: {{ pending.agent }} · </template>
      <template v-if="pending.goal">{{ pending.goal }}</template>
      <template v-if="pending.step_id"> · step {{ pending.step_id }}</template>
    </p>
    <div class="form-grid">
      <div class="field">
        <label for="comment">备注（可选）</label>
        <input id="comment" v-model="comment" :disabled="busy" placeholder="拒绝原因或审批说明" />
      </div>
      <div class="actions">
        <button class="btn btn--amber" type="button" :disabled="busy" @click="emit('approve', comment)">
          通过
        </button>
        <button class="btn btn--danger" type="button" :disabled="busy" @click="emit('reject', comment)">
          拒绝
        </button>
      </div>
    </div>
  </section>
</template>
