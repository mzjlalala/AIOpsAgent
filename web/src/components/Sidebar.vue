<script setup lang="ts">
export interface ChatSession {
  id: string;
  title: string;
}

defineProps<{
  sessions: ChatSession[];
  activeId: string;
}>();

const emit = defineEmits<{
  newChat: [];
  select: [id: string];
}>();
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar__top">
      <button class="sidebar__btn sidebar__btn--primary" type="button" @click="emit('newChat')">
        <span aria-hidden="true">＋</span>
        新聊天
      </button>
    </div>
    <p class="sidebar__label">最近</p>
    <ul class="sidebar__list">
      <li v-for="s in sessions" :key="s.id">
        <button
          class="sidebar__item"
          type="button"
          :class="{ 'is-active': s.id === activeId }"
          @click="emit('select', s.id)"
        >
          {{ s.title }}
        </button>
      </li>
      <li v-if="!sessions.length">
        <span class="sidebar__item" style="cursor: default">暂无对话</span>
      </li>
    </ul>
    <div class="sidebar__foot">OpsAgent</div>
  </aside>
</template>
