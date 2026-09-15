<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import type { DigitalHumanMode, DigitalHumanState } from '../types';

const props = defineProps<{
  state: DigitalHumanState;
  mode: DigitalHumanMode;
  videoUrl?: string | null;
  poster: string;
  playing: boolean;
  muted: boolean;
  loading: boolean;
}>();

const emit = defineEmits<{ mediaError: [] }>();
const stateLabels: Record<DigitalHumanState, string> = {
  idle: '待机陪练',
  listening: '正在倾听',
  speaking: '正在讲解',
  warning: '风险提醒',
  scoring: '正在评分'
};
const videoRef = ref<HTMLVideoElement | null>(null);
const mediaFailed = ref(false);
const hasVideo = computed(() => Boolean(props.videoUrl) && !mediaFailed.value);

watch(
  () => props.videoUrl,
  () => {
    mediaFailed.value = false;
    window.setTimeout(() => videoRef.value?.load(), 0);
  }
);

watch(
  () => props.playing,
  async (playing) => {
    if (!videoRef.value) return;
    if (!playing) {
      videoRef.value.pause();
      return;
    }
    try {
      await videoRef.value.play();
    } catch {
      mediaFailed.value = true;
      emit('mediaError');
    }
  }
);

function handleMediaError() {
  mediaFailed.value = true;
  emit('mediaError');
}
</script>

<template>
  <div class="dh-player" :class="[`state-${state}`, { 'is-playing': playing, 'is-loading': loading }]">
    <video
      v-if="hasVideo"
      ref="videoRef"
      class="dh-media"
      :src="videoUrl ?? undefined"
      :poster="poster"
      :muted="muted"
      :autoplay="playing"
      playsinline
      loop
      @error="handleMediaError"
    />
    <div v-else class="dh-mock-media" role="img" aria-label="人工智能医学导师动态占位画面">
      <img :src="poster" alt="" />
      <div class="dh-depth-layer"></div>
      <div class="dh-scan-line"></div>
      <div class="dh-speaking-bars" aria-hidden="true"><span></span><span></span><span></span><span></span><span></span></div>
    </div>
    <div class="dh-player-topline"><span>{{ mode === 'liveact' ? '真实嘴型与语音' : '本地动态演示' }}</span><b>{{ stateLabels[state] }}</b></div>
    <div v-if="loading" class="dh-generating"><span></span><strong>正在生成嘴型与语音，请稍候</strong><small>首次约需 30–60 秒</small></div>
  </div>
</template>

<style scoped>
.dh-player{position:relative;aspect-ratio:16/11;overflow:hidden;background:#0b2830;isolation:isolate}
.dh-media,.dh-mock-media,.dh-mock-media img{width:100%;height:100%;display:block;object-fit:cover}
.dh-media,.dh-mock-media img{object-position:center 18%}
.dh-mock-media{position:relative}
.dh-mock-media img{transition:transform 1.2s cubic-bezier(.16,1,.3,1),filter .35s ease}
.dh-mock-media:after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(5,28,35,.02) 45%,rgba(5,28,35,.76) 100%)}
.dh-depth-layer{position:absolute;inset:0;box-shadow:inset 0 0 70px rgba(6,49,57,.24);pointer-events:none}
.dh-scan-line{position:absolute;left:0;right:0;top:18%;height:1px;background:rgba(141,241,230,.76);box-shadow:0 0 12px rgba(97,222,210,.65);opacity:0}
.dh-player-topline{position:absolute;left:12px;right:12px;top:12px;z-index:3;display:flex;justify-content:space-between;align-items:center;gap:8px;color:#f3fffd;font-size: 14px;font-weight:800;text-shadow:0 1px 6px rgba(3,28,34,.6)}
.dh-player-topline span,.dh-player-topline b{padding:6px 8px;border-radius:8px;background:rgba(6,36,43,.66);backdrop-filter:blur(10px)}
.dh-player-topline b{text-transform:capitalize}
.dh-speaking-bars{position:absolute;right:16px;bottom:16px;z-index:4;display:flex;align-items:flex-end;gap:3px;height:30px;opacity:0}
.dh-speaking-bars span{width:3px;height:8px;border-radius:3px;background:#a8f4eb}
.state-speaking.is-playing .dh-speaking-bars,.state-warning .dh-speaking-bars{opacity:1}
.state-speaking.is-playing .dh-speaking-bars span:nth-child(1){animation:dh-wave .72s ease-in-out infinite}
.state-speaking.is-playing .dh-speaking-bars span:nth-child(2){animation:dh-wave .72s .08s ease-in-out infinite}
.state-speaking.is-playing .dh-speaking-bars span:nth-child(3){animation:dh-wave .72s .16s ease-in-out infinite}
.state-speaking.is-playing .dh-speaking-bars span:nth-child(4){animation:dh-wave .72s .24s ease-in-out infinite}
.state-speaking.is-playing .dh-speaking-bars span:nth-child(5){animation:dh-wave .72s .32s ease-in-out infinite}
.state-speaking.is-playing .dh-mock-media img{transform:scale(1.025)}
.state-listening .dh-scan-line,.state-scoring .dh-scan-line{opacity:1;animation:dh-scan 1.8s ease-in-out infinite}
.state-warning .dh-mock-media img{filter:saturate(.82) contrast(1.04)}
.state-warning .dh-depth-layer{box-shadow:inset 0 0 0 2px rgba(225,147,54,.7),inset 0 0 80px rgba(173,88,20,.2)}
.dh-generating{position:absolute;inset:0;z-index:6;display:grid;place-content:center;justify-items:center;gap:12px;background:rgba(235,247,245,.64);color:#0a5e59;backdrop-filter:blur(5px)}
.dh-generating span{width:120px;height:7px;border-radius:8px;background:linear-gradient(90deg,#0c7c74 0 35%,rgba(12,124,116,.18) 35% 100%);animation:dh-loading 1.1s ease-in-out infinite}
.dh-generating strong{font-size: 15px}
.dh-generating small{color:#557579;font-size: 14px}
@keyframes dh-wave{0%,100%{height:7px}50%{height:28px}}
@keyframes dh-scan{0%,100%{transform:translateY(0);opacity:.2}50%{transform:translateY(180px);opacity:.9}}
@keyframes dh-loading{0%,100%{background-size:100% 100%}50%{background-size:180% 100%}}
@media (prefers-reduced-motion:reduce){.dh-mock-media img,.dh-scan-line,.dh-speaking-bars span,.dh-generating span{animation:none!important;transition:none!important}}
</style>




