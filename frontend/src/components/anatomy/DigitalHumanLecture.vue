<script setup lang="ts">
import { computed } from 'vue';
import { LoaderCircle, Play, RotateCcw, Volume2, VolumeX } from '@lucide/vue';
import DigitalHumanPlayer from '../DigitalHumanPlayer.vue';
import AgentEvidence from './AgentEvidence.vue';
import MarkdownContent from '../MarkdownContent.vue';
import type { AgentAction, AgentResponse, DigitalHumanResponse, DigitalHumanState } from '../../types';

const props = defineProps<{
  agentLoading: boolean;
  agentReply: string;
  agentResponse: AgentResponse | null;
  agentPrompt: string;
  narration: DigitalHumanResponse | null;
  narrationLoading: boolean;
  narrationError: string;
  playing: boolean;
  muted: boolean;
  poster: string;
}>();

const emit = defineEmits<{
  action: [value: AgentAction];
  'update:playing': [value: boolean];
  'update:muted': [value: boolean];
  replay: [];
  mediaError: [];
  playBlocked: [];
}>();

const state = computed<DigitalHumanState>(() => {
  if (props.agentLoading || props.narrationLoading) return 'listening';
  return props.narration?.state ?? 'idle';
});
const mode = computed(() => props.narration?.mode ?? 'mock');
const videoUrl = computed(() => props.narration?.video_url || props.narration?.stream_url || null);
const statusText = computed(() => {
  if (props.agentLoading) return '正在调用教材、结构和图谱 Skill';
  if (props.narrationLoading) return '正在生成数字人语音与口型';
  if (props.narration?.status === 'fallback') return '真实数字人暂不可用，当前使用本地讲播回退';
  if (props.narrationError) return props.narrationError;
  if (props.narration) return props.narration.provider;
  return '选择一个主题开始讲播';
});
</script>

<template>
  <div class="digital-human-lecture">
    <div class="digital-human-lecture-heading"><strong>数字人讲播</strong><span>{{ statusText }}</span></div>
    <DigitalHumanPlayer
      :state="state"
      :mode="mode"
      :video-url="videoUrl"
      :poster="poster"
      :playing="playing"
      :muted="muted"
      :loading="agentLoading || narrationLoading"
      @media-error="emit('mediaError')"
      @play-blocked="emit('playBlocked')"
      @playback-change="emit('update:playing', $event)"
    />
    <div class="digital-human-lecture-controls">
      <button type="button" :disabled="agentLoading || narrationLoading || !agentReply" @click="emit('replay')">
        <LoaderCircle v-if="agentLoading || narrationLoading" class="spin" :size="15" />
        <RotateCcw v-else :size="15" />
        {{ agentLoading || narrationLoading ? '准备讲播' : '重新讲播' }}
      </button>
      <button type="button" :disabled="!narration" :title="muted ? '打开声音' : '静音'" :aria-label="muted ? '打开声音' : '静音'" @click="emit('update:muted', !muted)">
        <VolumeX v-if="muted" :size="15" />
        <Volume2 v-else :size="15" />
        {{ muted ? '已静音' : '声音开启' }}
      </button>
      <button v-if="narration && !playing && videoUrl" type="button" @click="emit('update:playing', true)"><Play :size="15" />播放</button>
    </div>
    <div v-if="agentLoading || narrationLoading" class="digital-human-lecture-state" role="status" aria-live="polite"><LoaderCircle class="spin" :size="16" />{{ statusText }}，请稍候</div>
    <details v-if="agentReply" class="digital-human-transcript" :open="Boolean(agentResponse)">
      <summary>查看讲解文字与依据</summary>
      <MarkdownContent class="agent-markdown" :content="agentReply" />
      <AgentEvidence v-if="agentResponse" :response="agentResponse" @action="emit('action', $event)" />
      <small v-if="agentPrompt">本次问题：{{ agentPrompt }}</small>
    </details>
    <slot name="prompts" />
  </div>
</template>
