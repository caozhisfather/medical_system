<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import DigitalHumanPanel from './DigitalHumanPanel.vue';
import medicalTutorPoster from '../assets/digital-human/medical-tutor.png';
import {
  createDigitalHumanSession,
  getDigitalHumanModes,
  speakDigitalHuman,
  sendSparkOsAudio
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
const sparkosAvailable = ref(false);
const playing = ref(true);
const muted = ref(false);
const generating = ref(false);
const videoUrl = ref<string | null>(null);
const provider = ref('数字人本地演示适配器');
const fallbackReason = ref<string | null>(null);
const recording = ref(false);
const audioUrl = ref<string | null>(null);
const mediaRecorder = ref<MediaRecorder | null>(null);
const recordedChunks: Blob[] = [];
const subtitleText = ref(props.subtitle);
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
    sparkosAvailable.value = Boolean(modes.sparkos_available);
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

watch(() => props.subtitle, (value) => { subtitleText.value = value; });

function normalizeVideoUrl(value?: string | null) {
  if (!value) return null;
  if (/^https?:\/\//.test(value)) return value;
  if (value.startsWith('/generated-videos')) return `${serviceBaseUrl.value}${value}`;
  return value;
}

async function generate() {
  const text = props.subtitle.trim();
  if (!text || generating.value || requestedMode.value === 'sparkos') return;
  generating.value = true;
  fallbackReason.value = null;
  try {
    const result = await speakDigitalHuman({
      session_id: sessionId.value,
      text,
      emotion: props.state === 'warning' ? 'warning' : 'teaching',
      action: props.state === 'scoring' ? 'score' : props.state === 'reviewing' ? 'review' : 'explain',
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
  if (mode !== 'sparkos') await generate();
}

function bytesToBase64(bytes: Uint8Array) {
  let binary = '';
  for (let index = 0; index < bytes.length; index += 0x8000) binary += String.fromCharCode(...bytes.subarray(index, index + 0x8000));
  return btoa(binary);
}

async function blobToPcmBase64(blob: Blob) {
  const context = new AudioContext();
  try {
    const decoded = await context.decodeAudioData(await blob.arrayBuffer());
    const channel = decoded.getChannelData(0);
    const pcm = new Int16Array(channel.length);
    for (let index = 0; index < channel.length; index += 1) pcm[index] = Math.max(-1, Math.min(1, channel[index])) * 0x7fff;
    return bytesToBase64(new Uint8Array(pcm.buffer));
  } finally {
    await context.close();
  }
}

function base64ToBlob(value: string, type: string) {
  const binary = atob(value);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
  return new Blob([bytes], { type });
}

async function toggleRecording() {
  if (recording.value && mediaRecorder.value) { mediaRecorder.value.stop(); return; }
  if (!sparkosAvailable.value || !navigator.mediaDevices?.getUserMedia) {
    fallbackReason.value = '当前浏览器不支持录音或讯飞服务未配置。';
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recordedChunks.length = 0;
    const recorder = new MediaRecorder(stream);
    mediaRecorder.value = recorder;
    recorder.ondataavailable = (event) => { if (event.data.size) recordedChunks.push(event.data); };
    recorder.onstop = async () => {
      stream.getTracks().forEach((track) => track.stop());
      recording.value = false;
      generating.value = true;
      try {
        const result = await sendSparkOsAudio(await blobToPcmBase64(new Blob(recordedChunks)), sessionId.value);
        actualMode.value = 'sparkos';
        provider.value = '讯飞 SparkOS 超拟人对话';
        fallbackReason.value = null;
        if (result.text) subtitleText.value = result.text;
        if (result.audio_base64) {
          if (audioUrl.value) URL.revokeObjectURL(audioUrl.value);
          audioUrl.value = URL.createObjectURL(base64ToBlob(result.audio_base64, 'audio/mpeg'));
        }
      } catch (error) {
        fallbackReason.value = error instanceof Error ? error.message : '讯飞语音调用失败';
      } finally {
        generating.value = false;
      }
    };
    recorder.start();
    recording.value = true;
  } catch (error) {
    fallbackReason.value = error instanceof Error ? error.message : '无法访问麦克风，请检查浏览器权限。';
  }
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
    :sparkos-available="sparkosAvailable"
    :recording="recording"
    :audio-url="audioUrl"
    :video-url="videoUrl"
    :poster="medicalTutorPoster"
    :subtitle="subtitleText"
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
    @toggle-recording="toggleRecording"
    @media-error="actualMode = 'mock'; videoUrl = null"
  />
</template>
