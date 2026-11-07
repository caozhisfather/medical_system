<script setup lang="ts">
withDefaults(defineProps<{
  alt?: string;
  variant?: 'full' | 'compact';
  subtitle?: string;
}>(), {
  alt: '临思智训：教材可追溯的解剖学习平台',
  variant: 'full',
  subtitle: '教材可追溯的解剖学习平台'
});
</script>

<template>
  <span class="brand-logo" :class="`brand-logo-${variant}`">
    <span class="brand-logo-mark" :aria-hidden="variant === 'compact' ? true : undefined">
      <img src="../assets/brand/lin-si-zhi-xun-logo.png" :alt="variant === 'compact' ? '' : alt" width="256" height="256" />
    </span>
    <span v-if="variant === 'compact'" class="brand-logo-copy">
      <strong>临思智训</strong>
      <small>{{ subtitle }}</small>
    </span>
  </span>
</template>
