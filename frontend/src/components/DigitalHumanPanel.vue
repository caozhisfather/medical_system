<script setup lang="ts">
import DigitalHumanPlayer from './DigitalHumanPlayer.vue';
import type { DigitalHumanMode, DigitalHumanState } from '../types';

defineProps<{
  name: string;
  description: string;
  role?: 'patient' | 'teacher';
  state: DigitalHumanState;
  mode: DigitalHumanMode;
  requestedMode: DigitalHumanMode;
  liveactAvailable: boolean;
  sparkosAvailable: boolean;
  recording: boolean;
  audioUrl?: string | null;
  videoUrl?: string | null;
  poster: string;
  subtitle: string;
  provider: string;
  fallbackReason?: string | null;
  playing: boolean;
  muted: boolean;
  loading: boolean;
}>();

const emit = defineEmits<{
  play: [];
  pause: [];
  toggleMute: [];
  regenerate: [];
  changeMode: [mode: DigitalHumanMode];
  toggleRecording: [];
  mediaError: [];
}>();

const stateLabels: Record<DigitalHumanState, string> = {
  idle: '待机陪练',
  listening: '正在倾听',
  speaking: '正在讲解',
  warning: '风险提醒',
  scoring: '正在评分',
  reviewing: '复盘讲解'
};
</script>

<template>
  <section class="digital-human-panel panel" :class="[`dh-${state}`]">
    <header class="dh-panel-head">
      <div><span>{{ role === 'teacher' ? '人工智能教学助手' : '人工智能标准化病人' }}</span><strong>{{ name }}</strong></div>
      <div class="dh-mode-switch" aria-label="数字人模式">
        <button type="button" :class="{ active: requestedMode === 'mock' }" @click="emit('changeMode', 'mock')">本地演示</button>
        <button type="button" :class="{ active: requestedMode === 'liveact' }" @click="emit('changeMode', 'liveact')">真实数字人</button>
      </div>
    </header>

    <DigitalHumanPlayer
      :state="state"
      :mode="mode"
      :video-url="videoUrl"
      :poster="poster"
      :playing="playing"
      :muted="muted"
      :loading="loading"
      @media-error="emit('mediaError')"
    />

    <div class="dh-status-row">
      <strong>{{ stateLabels[state] }}</strong>
      <span :class="{ unavailable: requestedMode === 'liveact' && !liveactAvailable }">
        {{ mode === 'liveact' ? 'GPU 生成视频' : mode === 'sparkos' ? '讯飞语音对话' : requestedMode === 'liveact' ? '已自动切换本地演示' : requestedMode === 'sparkos' ? '讯飞配置不可用' : '本地演示模式' }}
      </span>
    </div>

    <div class="dh-subtitle" aria-live="polite">
      <span>实时字幕</span>
      <p>{{ subtitle }}</p>
    </div>

    <p class="dh-description">{{ description }}</p>
    <p v-if="fallbackReason" class="dh-fallback">{{ fallbackReason }}</p>

    <div class="dh-controls">
      <button type="button" class="primary" :disabled="loading" @click="playing ? emit('pause') : emit('play')">{{ playing ? '暂停' : '播放讲解' }}</button>
      <button type="button" @click="emit('toggleMute')">{{ muted ? '开启声音' : '静音' }}</button>
      <button type="button" :disabled="loading" @click="emit('regenerate')">重新生成</button>
    </div>
    <div v-if="requestedMode === 'sparkos'" class="dh-sparkos-controls">
      <button type="button" class="primary" :disabled="loading || !sparkosAvailable" @click="emit('toggleRecording')">{{ recording ? '停止录音并发送' : '开始讯飞语音问答' }}</button>
      <audio v-if="audioUrl" :src="audioUrl" controls preload="metadata" />
    </div>
    <small>{{ provider }}</small>
  </section>
</template>

<style scoped>
.digital-human-panel{position:relative;padding:0;overflow:hidden;background:#f9fcfb}
.dh-panel-head{display:flex;justify-content:space-between;gap:12px;align-items:center;padding:15px 16px 13px}
.dh-panel-head>div:first-child span{display:block;margin-bottom:3px;color:#0a6c66;font-size: 14px;font-weight:900}
.dh-panel-head strong{display:block;color:#0b2931;font-size:1.05rem}
.dh-mode-switch{display:flex;padding:3px;border-radius:10px;background:#e9f3f1}
.dh-mode-switch button{min-height:30px;padding:0 8px;border:0;border-radius:8px;background:transparent;color:#4f696d;font-size: 14px;font-weight:900}
.dh-mode-switch button.active{background:#fff;color:#0a655f;box-shadow:0 4px 12px rgba(28,73,79,.1)}
.dh-status-row{display:flex;justify-content:space-between;gap:10px;align-items:center;padding:13px 16px 0}
.dh-status-row strong{color:#12363d}
.dh-status-row span{padding:5px 7px;border-radius:8px;background:#e6f4f1;color:#0a655f;font-size: 14px;font-weight:900}
.dh-status-row span.unavailable{background:#fff1df;color:#8a5511}
.dh-subtitle{margin:12px 16px 0;padding:12px;border-radius:12px;background:#0c2d35;color:#eefdfb;box-shadow:0 12px 28px rgba(10,46,54,.16)}
.dh-subtitle span{color:#83dbd1;font-size: 14px;font-weight:900}
.dh-subtitle p{display:-webkit-box;overflow:hidden;margin:6px 0 0;color:#f3fbfa;font-size: 15px;line-height:1.65;-webkit-box-orient:vertical;-webkit-line-clamp:3}
.dh-description{margin:11px 16px 0;color:#587175;font-size: 14px;line-height:1.55}
.dh-fallback{margin:9px 16px 0;padding:9px 10px;border-radius:9px;background:#fff5e8;color:#7b511c;font-size: 14px;line-height:1.5}
.dh-controls{display:grid;grid-template-columns:1fr .72fr 1fr;gap:7px;padding:12px 16px 8px}
.dh-controls button{min-width:0;min-height:38px;padding:0 8px;border:1px solid rgba(10,101,95,.15);border-radius:9px;background:#edf6f4;color:#0b5e59;font-size: 14px;font-weight:900;white-space:nowrap}
.dh-controls button.primary{border-color:#0a756d;background:#0a756d;color:#fff}
.dh-controls button:disabled{opacity:.58}
.dh-sparkos-controls{display:grid;gap:8px;padding:0 16px 10px}.dh-sparkos-controls button{min-height:38px;border:1px solid #0a756d;border-radius:9px;background:#0a756d;color:#fff;font-weight:900}.dh-sparkos-controls button:disabled{opacity:.58}.dh-sparkos-controls audio{width:100%;height:34px}
.digital-human-panel>small{display:block;padding:0 16px 14px;color:#6d8386;font-size: 13px}
.dh-warning .dh-status-row strong{color:#9a5b0b}
@media (max-width:420px){.dh-controls{grid-template-columns:1fr 1fr}.dh-controls button:last-child{grid-column:1/-1}}
</style>



