<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import DigitalHumanPanel from './DigitalHumanPanel.vue';
import medicalTutorPoster from '../assets/digital-human/medical-tutor.png';
import {
  createDigitalHumanSession,
  getDigitalHumanModes,
  speakDigitalHuman
} from '../services/digitalHumanApi';
import type { DigitalHumanMode, DigitalHumanState } from '../types';

const props = withDefaults(defineProps<{
  name?: string;
  description?: string;
  subtitle: string;
  state?: DigitalHumanState;
  speakKey?: string | number;
  compact?: boolean;
}>(), {
  name: '智能临床导师',
  description: '陪伴问诊、推理与训练复盘',
  state: 'idle',
  compact: false
});

const sessionId = ref('digital-human-demo');
const requestedMode = ref<DigitalHumanMode>('mock');
const actualMode = ref<DigitalHumanMode>('mock');
const liveactAvailable = ref(false);
const playing = ref(true);
const muted = ref(false);
const generating = ref(false);
const videoUrl = ref<string | null>(null);
const provider = ref('数字人本地演示适配器');
const fallbackReason = ref<string | null>(null);
const serviceBaseUrl = ref('http://127.0.0.1:8090');
const displayState = computed<DigitalHumanState>(() => generating.value ? 'speaking' : props.state);

onMounted(async () => {
  try {
    const [modes, session] = await Promise.all([
      getDigitalHumanModes(),
      createDigitalHumanSession('student')
    ]);
    requestedMode.value = modes.active_mode;
    actualMode.value = modes.active_mode;
    liveactAvailable.value = modes.liveact_available;
    serviceBaseUrl.value = modes.liveact_service_url.replace('localhost', '127.0.0.1');
    sessionId.value = session.session_id;
  } catch {
    provider.value = '数字人本地演示适配器';
  }
});

watch(() => props.speakKey, async (next, previous) => {
  if (next === undefined || next === previous) return;
  await generate();
});

function normalizeVideoUrl(value?: string | null) {
  if (!value) return null;
  if (/^https?:\/\//.test(value)) return value;
  if (value.startsWith('/generated-videos')) return `${serviceBaseUrl.value}${value}`;
  return value;
}

async function generate() {
  const text = props.subtitle.trim();
  if (!text || generating.value) return;
  generating.value = true;
  fallbackReason.value = null;
  try {
    const result = await speakDigitalHuman({
      session_id: sessionId.value,
      text,
      emotion: props.state === 'warning' ? 'warning' : 'teaching',
      action: props.state === 'scoring' ? 'score' : 'explain',
      avatar_id: 'medical_tutor_001',
      voice: 'zh_female_warm',
      mode: requestedMode.value
    });
    actualMode.value = result.mode;
    videoUrl.value = normalizeVideoUrl(result.video_url);
    provider.value = result.provider;
    fallbackReason.value = result.fallback_reason ?? null;
    playing.value = true;
  } catch (error) {
    actualMode.value = 'mock';
    videoUrl.value = null;
    provider.value = '数字人本地演示适配器';
    fallbackReason.value = error instanceof Error ? error.message : '数字人服务暂不可用';
  } finally {
    generating.value = false;
  }
}

async function changeMode(mode: DigitalHumanMode) {
  requestedMode.value = mode;
  await generate();
}
</script>

<template>
  <DigitalHumanPanel
    class="digital-human-workspace"
    :class="{ compact }"
    :name="name"
    :description="description"
    :state="displayState"
    :mode="actualMode"
    :requested-mode="requestedMode"
    :liveact-available="liveactAvailable"
    :video-url="videoUrl"
    :poster="medicalTutorPoster"
    :subtitle="subtitle"
    :provider="provider"
    :fallback-reason="fallbackReason"
    :playing="playing"
    :muted="muted"
    :loading="generating"
    @play="playing = true"
    @pause="playing = false"
    @toggle-mute="muted = !muted"
    @regenerate="generate"
    @change-mode="changeMode"
    @media-error="actualMode = 'mock'; videoUrl = null"
  />
</template>
