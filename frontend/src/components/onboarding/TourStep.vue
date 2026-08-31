<script setup lang="ts">
import { ArrowLeft, ArrowRight, Check, X } from '@lucide/vue';

defineProps<{
  title: string;
  body: string;
  index: number;
  total: number;
}>();

const emit = defineEmits<{
  previous: [];
  next: [];
  finish: [];
  skip: [];
}>();
</script>

<template>
  <aside class="tour-popover" role="dialog" aria-modal="true" aria-live="polite" aria-label="首次使用引导">
    <button class="tour-close" type="button" title="跳过引导" @click="emit('skip')"><X :size="16" /></button>
    <small>{{ index + 1 }} / {{ total }}</small>
    <h2>{{ title }}</h2>
    <p>{{ body }}</p>
    <div class="tour-progress" aria-hidden="true"><i :style="{ width: ((index + 1) / total * 100) + '%' }"></i></div>
    <div class="tour-actions">
      <button type="button" :disabled="index === 0" @click="emit('previous')"><ArrowLeft :size="15" /> 上一步</button>
      <button v-if="index < total - 1" class="primary" type="button" @click="emit('next')">下一步 <ArrowRight :size="15" /></button>
      <button v-else class="primary" type="button" @click="emit('finish')">完成 <Check :size="15" /></button>
    </div>
  </aside>
</template>

