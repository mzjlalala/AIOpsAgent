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
  submit: [];
  reset: [];
}>();

const query = ref(props.modelQuery);
const scenario = ref<Scenario>(props.modelScenario);

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

function onSubmit() {
  emit("update:modelQuery", query.value.trim());
  emit("update:modelScenario", scenario.value);
  emit("submit");
}
</script>

<template>
  <section class="panel">
    <h2>发起排查</h2>
    <div class="form-grid">
      <div class="field">
        <label for="query">故障描述</label>
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
          <option value="cpu_high">cpu_high（无审批）</option>
          <option value="memory_leak">memory_leak（需审批）</option>
        </select>
      </div>
      <div class="actions">
        <button class="btn btn--primary" type="button" :disabled="disabled || !query.trim()" @click="onSubmit">
          开始排查
        </button>
        <button class="btn btn--ghost" type="button" :disabled="disabled" @click="emit('reset')">
          清空重来
        </button>
      </div>
    </div>
  </section>
</template>
