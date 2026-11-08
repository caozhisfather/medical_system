<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{ nodeId?: string }>();

const icons: Record<string, string[]> = {
  root: [
    'M14.5 4a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0Z',
    'M9 22l1-8H8l-2 4-2-1 3-7a3 3 0 0 1 3-2h4a3 3 0 0 1 3 2l3 7-2 1-2-4h-2l1 8M12 16v6'
  ],
  locomotor: [
    'm8 10 2 2 4-4-2-2a2.5 2.5 0 0 1 3.5-3.5l1 1a2.5 2.5 0 0 1 3.5 3.5l1 1a2.5 2.5 0 0 1-3.5 3.5l-2-2-4 4 2 2A2.5 2.5 0 0 1 10 19l-1-1a2.5 2.5 0 0 1-3.5-3.5l-1-1A2.5 2.5 0 0 1 8 10Z'
  ],
  circulatory: [
    'M12 21s-8-4.6-8-10.2A4.5 4.5 0 0 1 12 8a4.5 4.5 0 0 1 8 2.8C20 16.4 12 21 12 21Z',
    'M6 13h3l1.5-3 2 6 1.5-3H18'
  ],
  respiratory: [
    'M12 2v8m0-1-4 4m4-4 4 4',
    'M9 10V7c0-1-1-1.5-2-.5C4 9 2 12 2 17a3 3 0 0 0 3 3c2 0 4-1 4-3v-3m6-4V7c0-1 1-1.5 2-.5 3 2.5 5 5.5 5 10.5a3 3 0 0 1-3 3c-2 0-4-1-4-3v-3'
  ],
  digestive: [
    'M10 2v5c0 2 1 3 3 3 2 0 1-4 4-4 3 0 4 3 4 6 0 5-4 8-9 8-2 0-4-1-6-1s-2 1-2 3m3-20v6c0 4 2 5 4 6 1 .5 1 2-.5 2H7c-3 0-5 2-5 5v1'
  ],
  urinary: [
    'M8 4C5 2 2 6 2 10s2 6 4 5c1-.5 1-2 1-3 0-2 2-2 2-5 0-1-.3-2.5-1-3Zm8 0c3-2 6 2 6 6s-2 6-4 5c-1-.5-1-2-1-3 0-2-2-2-2-5 0-1 .3-2.5 1-3Z',
    'M8 10c2 2 2 4 2 7m6-7c-2 2-2 4-2 7m-5 1c0-1 6-1 6 0 0 2-1 3-3 3s-3-1-3-3Z'
  ],
  reproductive: [
    'M8 8c2-1 6-1 8 0v3c0 3-2 4-3 6v3h-2v-3c-1-2-3-3-3-6V8Zm0 1C6 5 3 6 3 9m13 0c2-4 5-3 5 0',
    'M5 11a2 2 0 1 1-4 0 2 2 0 0 1 4 0Zm18 0a2 2 0 1 1-4 0 2 2 0 0 1 4 0Z'
  ],
  nervous: [
    'M12 6c0-4-6-4-7 0-3 1-3 5-2 6-2 3 0 7 3 7 1 3 6 3 6-1V6Zm0 0c0-4 6-4 7 0 3 1 3 5 2 6 2 3 0 7-3 7-1 3-6 3-6-1',
    'M5 6c2 0 3 1 3 3m-5 3c2-1 4 0 4 2m-1 5c1-2 2-3 4-3m9-10c-2 0-3 1-3 3m5 3c-2-1-4 0-4 2m1 5c-1-2-2-3-4-3'
  ],
  endocrine: [
    'M12 10C9 10 9 5 5 5c-3 0-4 5-2 8 2 3 5 4 7 1l2-2 2 2c2 3 5 2 7-1 2-3 1-8-2-8-4 0-4 5-7 5Zm0 2v7'
  ],
  lymphatic: [
    'm5 7 5 4m4 0 5-4m-7 7v4',
    'M6 5a2 2 0 1 1-4 0 2 2 0 0 1 4 0Zm16 0a2 2 0 1 1-4 0 2 2 0 0 1 4 0Zm-7 7a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm-1 8a2 2 0 1 1-4 0 2 2 0 0 1 4 0Z'
  ]
};

const paths = computed(() => {
  const id = props.nodeId;
  if (id === 'anatomy_root') return icons.root;
  return icons[id?.replace(/^anatomy_system_/, '') ?? ''] ?? ['M4 7h16M4 12h16M4 17h16M8 4v6m8-1v6m-6-1v6'];
});
</script>

<template>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.55" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
    <path v-for="path in paths" :key="path" :d="path" />
  </svg>
</template>
