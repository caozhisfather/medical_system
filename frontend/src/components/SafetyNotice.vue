<script setup lang="ts">
import { ShieldCheck } from '@lucide/vue';

defineProps<{ compact?: boolean }>();
</script>

<template>
  <div class="safety-notice" :class="{ compact }">
    <ShieldCheck :size="16" aria-hidden="true" />
    <span>本系统仅用于医学教育训练，不用于真实临床诊断</span>
  </div>
</template>
