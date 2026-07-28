<script setup lang="ts">
import { ref, watch } from "vue";
import type { Scenario } from "../api/client";

const props = defineProps<{
  disabled?: boolean;
  modelQuery: string;
  modelScenario: Scenario;
}>();

const emit = defineEmits<{
  "update:modelQuery": [string];
  "update:modelScenario": [Scenario];
  oneClick: [];
  submitAdvanced: [];
  reset: [];
}>();

const query = ref(props.modelQuery);
const scenario = ref<Scenario>(props.modelScenario);
const showAdvanced = ref(false);

watch(
  () => props.modelQuery,
  (v) => {
    query.value = v;
  },
);
watch(
  () => props.modelScenario,
  (v) => {
    scenario.value = v;
  },
);

function onAdvancedSubmit() {
  emit("update:modelQuery", query.value.trim());
  emit("update:modelScenario", scenario.value);
  emit("submitAdvanced");
}
</script>

<template>
  <section class="panel">
    <h2>一键运维</h2>
    <p class="empty" style="margin-bottom: 0.9rem">
      Agent 将自主查看指标面板、检索日志与知识库（查询类，无需审批）。
    </p>
    <div class="actions">
      <button
        class="btn btn--primary"
        type="button"
        :disabled="disabled"
        @click="emit('oneClick')"
      >
        一键运维
      </button>
      <button class="btn btn--ghost" type="button" :disabled="disabled" @click="emit('reset')">
        清空重来
      </button>
      <button
        class="btn btn--ghost"
        type="button"
        :disabled="disabled"
        @click="showAdvanced = !showAdvanced"
      >
        {{ showAdvanced ? "收起高级" : "高级选项" }}
      </button>
    </div>

    <div v-if="showAdvanced" class="form-grid" style="margin-top: 1rem">
      <div class="field">
        <label for="query">自定义故障描述</label>
        <textarea
          id="query"
          v-model="query"
          :disabled="disabled"
          placeholder="例如：线上服务 CPU 突然打满 100%"
        />
      </div>
      <div class="field">
        <label for="scenario">Mock 场景</label>
        <select id="scenario" v-model="scenario" :disabled="disabled">
          <option value="auto_ops">auto_ops（一键巡检）</option>
          <option value="cpu_high">cpu_high（无审批）</option>
          <option value="memory_leak">memory_leak（需审批）</option>
        </select>
      </div>
      <div class="actions">
        <button
          class="btn btn--amber"
          type="button"
          :disabled="disabled || !query.trim()"
          @click="onAdvancedSubmit"
        >
          按自定义描述排查
        </button>
      </div>
    </div>
  </section>
</template>
