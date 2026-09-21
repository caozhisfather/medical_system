<script setup lang="ts">
import { computed, ref } from 'vue';
import { Eraser, Highlighter, Maximize2, Minimize2, PenLine, RotateCcw, Scan } from '@lucide/vue';
import type { TextbookAnnotationStroke } from '../types';

type ViewerTool = 'browse' | 'pen' | 'highlight' | 'erase';

const props = withDefaults(defineProps<{
  imageUrl: string;
  alt?: string;
  annotations?: TextbookAnnotationStroke[];
}>(), {
  alt: '教材页',
  annotations: () => []
});

const emit = defineEmits<{
  (event: 'update:annotations', value: TextbookAnnotationStroke[]): void;
}>();

const svg = ref<SVGSVGElement | null>(null);
const tool = ref<ViewerTool>('browse');
const zoomed = ref(false);
const activeStroke = ref<TextbookAnnotationStroke | null>(null);
const strokes = computed(() => props.annotations ?? []);

function pointFromEvent(event: PointerEvent) {
  const rect = svg.value?.getBoundingClientRect();
  if (!rect || !rect.width || !rect.height) return null;
  return {
    x: Math.max(0, Math.min(1000, ((event.clientX - rect.left) / rect.width) * 1000)),
    y: Math.max(0, Math.min(1000, ((event.clientY - rect.top) / rect.height) * 1000))
  };
}

function pathFor(points: TextbookAnnotationStroke['points']) {
  if (!points.length) return '';
  return points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`).join(' ');
}

function startStroke(event: PointerEvent) {
  if (tool.value === 'browse') return;
  if (tool.value === 'erase') {
    const target = event.target as SVGElement;
    const strokeId = target.dataset.strokeId;
    if (strokeId) emit('update:annotations', strokes.value.filter((item) => item.id !== strokeId));
    return;
  }
  const point = pointFromEvent(event);
  if (!point) return;
  activeStroke.value = {
    id: `stroke-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    tool: tool.value,
    color: tool.value === 'highlight' ? '#f4c430' : '#d84b43',
    width: tool.value === 'highlight' ? 14 : 3,
    points: [point]
  };
  svg.value?.setPointerCapture(event.pointerId);
}

function moveStroke(event: PointerEvent) {
  if (!activeStroke.value) return;
  const point = pointFromEvent(event);
  if (!point) return;
  const points = activeStroke.value.points;
  const previous = points[points.length - 1];
  if (previous && Math.hypot(point.x - previous.x, point.y - previous.y) < 2) return;
  activeStroke.value.points = [...points, point];
}

function endStroke(event: PointerEvent) {
  if (svg.value?.hasPointerCapture(event.pointerId)) svg.value.releasePointerCapture(event.pointerId);
  if (!activeStroke.value) return;
  emit('update:annotations', [...strokes.value, activeStroke.value]);
  activeStroke.value = null;
}

function clearAnnotations() {
  emit('update:annotations', []);
}
</script>

<template>
  <div class="textbook-page-viewer" :class="{ 'is-zoomed': zoomed }">
    <div class="textbook-viewer-toolbar">
      <button type="button" :class="{ active: tool === 'browse' }" title="浏览与放大" @click="tool = 'browse'"><Scan :size="15" />浏览</button>
      <button type="button" :class="{ active: tool === 'pen' }" title="画笔标注" @click="tool = 'pen'"><PenLine :size="15" />画笔</button>
      <button type="button" :class="{ active: tool === 'highlight' }" title="荧光笔" @click="tool = 'highlight'"><Highlighter :size="15" />高亮</button>
      <button type="button" :class="{ active: tool === 'erase' }" title="点击笔画擦除" @click="tool = 'erase'"><Eraser :size="15" />擦除</button>
      <button type="button" title="清空本页标注" :disabled="!strokes.length" @click="clearAnnotations"><RotateCcw :size="15" />清空</button>
      <button type="button" class="zoom-button" :title="zoomed ? '恢复页面大小' : '放大教材页'" @click="zoomed = !zoomed">
        <Minimize2 v-if="zoomed" :size="15" /><Maximize2 v-else :size="15" />{{ zoomed ? '缩小' : '放大' }}
      </button>
    </div>
    <div class="textbook-viewer-scroll">
      <div class="textbook-viewer-paper">
        <img :src="imageUrl" :alt="alt" @click="tool === 'browse' && (zoomed = !zoomed)" />
        <svg
          ref="svg"
          class="textbook-annotation-layer"
          viewBox="0 0 1000 1000"
          preserveAspectRatio="none"
          :class="{ drawable: tool !== 'browse' }"
          @pointerdown="startStroke"
          @pointermove="moveStroke"
          @pointerup="endStroke"
          @pointercancel="endStroke"
        >
          <path
            v-for="stroke in strokes"
            :key="stroke.id"
            :d="pathFor(stroke.points)"
            :stroke="stroke.color"
            :stroke-width="stroke.width"
            :data-stroke-id="stroke.id"
            :class="{ highlight: stroke.tool === 'highlight', eraser: tool === 'erase' }"
            fill="none"
            stroke-linecap="round"
            stroke-linejoin="round"
            vector-effect="non-scaling-stroke"
          />
          <path
            v-if="activeStroke"
            :d="pathFor(activeStroke.points)"
            :stroke="activeStroke.color"
            :stroke-width="activeStroke.width"
            :class="{ highlight: activeStroke.tool === 'highlight' }"
            fill="none"
            stroke-linecap="round"
            stroke-linejoin="round"
            vector-effect="non-scaling-stroke"
          />
        </svg>
      </div>
    </div>
    <p>{{ tool === 'browse' ? '点击教材页可放大或缩小，切换到画笔后可勾画。' : tool === 'erase' ? '点击某条笔画即可单笔擦除。' : '直接在教材页上按住拖动即可标注。' }}</p>
  </div>
</template>

<style scoped>
.textbook-page-viewer { display: grid; gap: 8px; min-width: 0; }
.textbook-viewer-toolbar { display: flex; flex-wrap: wrap; gap: 5px; padding: 7px; border: 1px solid #d5e2e0; border-radius: 7px; background: #f3f8f7; }
.textbook-viewer-toolbar button { display: inline-flex; min-height: 30px; align-items: center; gap: 4px; padding: 0 8px; border: 1px solid transparent; border-radius: 5px; background: #fff; color: #4d6a6e; font-size: 11px; cursor: pointer; }
.textbook-viewer-toolbar button:hover:not(:disabled), .textbook-viewer-toolbar button.active { border-color: #6ab7ad; background: #e3f3ef; color: #075f59; }
.textbook-viewer-toolbar button:disabled { cursor: not-allowed; opacity: .42; }
.textbook-viewer-toolbar .zoom-button { margin-left: auto; }
.textbook-viewer-scroll { max-height: 520px; overflow: auto; border: 1px solid #d5e2e0; border-radius: 7px; background: #eef3f2; scrollbar-gutter: stable; }
.textbook-viewer-paper { position: relative; width: 100%; min-width: 0; transition: width .2s ease; }
.is-zoomed .textbook-viewer-paper { width: 170%; }
.textbook-viewer-paper > img { display: block; width: 100%; height: auto; cursor: zoom-in; }
.is-zoomed .textbook-viewer-paper > img { cursor: zoom-out; }
.textbook-annotation-layer { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; touch-action: none; }
.textbook-annotation-layer.drawable { pointer-events: auto; cursor: crosshair; }
.textbook-annotation-layer path { opacity: .94; }
.textbook-annotation-layer path.highlight { opacity: .38; }
.textbook-annotation-layer path.eraser { cursor: not-allowed; }
.textbook-page-viewer > p { margin: 0; color: #72878a; font-size: 10px; line-height: 1.5; }
</style>
