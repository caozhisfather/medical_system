<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{ nodeId?: string; light?: boolean }>();

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
  ],
  skull: ['M4 10a8 8 0 1 1 16 0c0 3-2 4-3 5v4h-3v2h-4v-2H7v-4c-1-1-3-2-3-5Z', 'M8 11h2m4 0h2m-5 4 1-1 1 1'],
  spine: ['M9 2h6v4H9zm-1 6h8v4H8zm0 6h8v4H8zm1 6h6v2H9zM12 6v2m0 4v2m0 4v2'],
  liver: ['M3 9c2-5 5-6 9-5 3 1 6 1 9 1v3c0 3-2 5-7 5l-2 4c-2 3-6 4-9 1Z', 'M12 5v5c0 2 1 3 3 3'],
  bladder: ['M8 8a4 4 0 0 0-4 4v2c0 3 3 5 6 5l2 3 2-3c3 0 6-2 6-5v-2a4 4 0 0 0-4-4Z', 'm7 8-3-5m13 5 3-5'],
  bowel: ['M5 6c0-2 2-3 4-2l3 1 3-1c2-1 4 0 4 2v10a3 3 0 0 1-3 3h-4v3M5 6v10a3 3 0 0 0 3 3m0-12h8m-8 4h8m-8 4h8'],
  airway: ['M10 2v10l-6 7m10-17v10l6 7M10 6h4m-4 4h4m-8 6v5m12-5v5'],
  vessel: ['M10 22V11L5 6V2m9 20V11l5-5V2m-7 5V2'],
  testis: ['M15 8a6 8 0 1 0 0 14 6 8 0 0 0 0-14Z', 'M17 15c4-2 4-7 0-10-2-1-3-2-3-4'],
  gland: ['M8 5c3-3 9-1 10 3 3 3 2 7-1 9-1 4-6 5-9 2-4 0-6-5-4-8 0-3 2-5 4-6Z', 'M8 12h.01m4-3h.01m4 5h.01m-5 3h.01'],
  kidney: ['M15 3c-5-1-10 3-10 10 0 5 3 8 7 7 2 0 3-2 3-4 0-3-3-3-3-5 0-1 1-2 3-2s4-1 4-3c0-1-2-3-4-3Z', 'M13 11c4 1 6 4 6 9']
};

const organIconGroups: Record<string, string[]> = {
  skull: ['skull'],
  spine: ['vertebral-column'],
  locomotor: ['thorax', 'pelvis'],
  circulatory: ['heart'],
  vessel: ['aorta', 'pulmonary-vessels', 'vena-cava'],
  airway: ['trachea', 'right-bronchial-tree', 'left-bronchial-tree'],
  respiratory: ['right-lung', 'left-lung'],
  digestive: ['esophagus', 'stomach'],
  bowel: ['duodenum', 'jejunum', 'ileum', 'colon', 'rectum', 'appendix'],
  liver: ['liver', 'gallbladder', 'pancreas'],
  kidney: ['right-kidney', 'left-kidney'],
  bladder: ['right-ureter', 'left-ureter', 'bladder', 'urethra'],
  testis: ['right-testis', 'left-testis', 'right-epididymis', 'left-epididymis'],
  nervous: ['telencephalon', 'diencephalon', 'cerebellum', 'midbrain', 'pons', 'medulla'],
  gland: ['pituitary', 'pineal', 'adrenal', 'seminal-vesicle', 'prostate'],
  lymphatic: ['thymus', 'spleen']
};
const organIcons = new Map(Object.entries(organIconGroups).flatMap(([key, ids]) => ids.map(id => [id, key] as const)));
const iconKey = computed(() => {
  const id = props.nodeId ?? '';
  if (id === 'anatomy_root') return 'root';
  if (id.startsWith('anatomy_organ_')) return organIcons.get(id.slice('anatomy_organ_'.length)) ?? '';
  return id.replace(/^anatomy_system_/, '');
});
const paths = computed(() => icons[iconKey.value] ?? ['M4 7h16M4 12h16M4 17h16M8 4v6m8-1v6m-6-1v6']);

const palettes: Record<string, readonly [string, string, string]> = {
  root: ['#fff4da', '#8b5529', '#ad632b'],
  locomotor: ['#e9f1ff', '#315784', '#315784'],
  circulatory: ['#fbe7ed', '#a6375a', '#b03049'],
  respiratory: ['#e6f6fb', '#196781', '#227a96'],
  digestive: ['#fff0dd', '#8c521f', '#ab6426'],
  urinary: ['#f2eafa', '#714791', '#854e9e'],
  reproductive: ['#fcebf3', '#91436d', '#a14a79'],
  nervous: ['#eeecff', '#514b9e', '#6258a6'],
  endocrine: ['#f2eaff', '#784d97', '#784d97'],
  lymphatic: ['#e8f6ee', '#32735d', '#28785e']
};
const palette = computed(() => palettes[iconKey.value] ?? ['#edf3ff', '#345c91', '#345c91']);
</script>

<template>
  <svg viewBox="0 0 24 24" fill="none" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
    <ellipse v-if="!light" cx="12" cy="12" rx="11.75" ry="11.75" :fill="palette[0]" />
    <g :transform="light ? 'translate(1 1) scale(.9167)' : 'translate(3 3) scale(.75)'">
      <path v-for="(path, index) in paths" :key="path" :d="path" :stroke="light ? (index ? '#91e5ff' : '#e0f7ff') : (index ? palette[2] : palette[1])" />
    </g>
  </svg>
</template>
