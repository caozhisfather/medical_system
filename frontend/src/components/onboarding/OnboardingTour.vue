<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { completeOnboarding, shouldShowOnboarding, tourSteps, type TourPlacement } from '../../services/onboarding';
import type { WorkspaceRole } from '../../stores/training';
import TourStep from './TourStep.vue';

const props = defineProps<{ role: WorkspaceRole }>();
const router = useRouter();
const active = ref(false);
const index = ref(0);
const moving = ref(false);
const targetMissing = ref(false);
const spotlight = ref({ top: 90, left: 240, width: 360, height: 120 });
const popoverStyle = ref<Record<string, string>>({});
const steps = computed(() => tourSteps[props.role]);
const step = computed(() => steps.value[index.value] ?? steps.value[0]);

let positionFrame = 0;

function clamp(value: number, minimum: number, maximum: number) {
  return Math.min(Math.max(value, minimum), maximum);
}

async function waitForTarget(selector: string, timeout = 6000) {
  const deadline = performance.now() + timeout;
  while (performance.now() < deadline) {
    await nextTick();
    const target = document.querySelector(selector) as HTMLElement | null;
    if (target) return target;
    await new Promise((resolve) => window.setTimeout(resolve, 60));
  }
  return null;
}

function placePopover(rect: DOMRect) {
  const width = Math.min(368, window.innerWidth - 32);
  const estimatedHeight = 252;
  const gap = 18;
  const mobile = window.innerWidth <= 760;
  if (mobile) {
    popoverStyle.value = {
      left: '16px',
      top: `${Math.max(16, window.innerHeight - estimatedHeight - 16)}px`,
      width: `${window.innerWidth - 32}px`
    };
    return;
  }

  const spaceRight = window.innerWidth - rect.right;
  const spaceLeft = rect.left;
  const spaceBottom = window.innerHeight - rect.bottom;
  const spaceTop = rect.top;
  const requested = step.value.placement ?? 'auto';
  const candidates: TourPlacement[] = requested === 'auto'
    ? ['right', 'bottom', 'left', 'top']
    : [requested, 'right', 'bottom', 'left', 'top'];
  const placement = candidates.find((candidate) => {
    if (candidate === 'right') return spaceRight >= width + gap;
    if (candidate === 'left') return spaceLeft >= width + gap;
    if (candidate === 'bottom') return spaceBottom >= estimatedHeight + gap;
    return spaceTop >= estimatedHeight + gap;
  }) ?? 'bottom';

  let left = rect.left;
  let top = rect.bottom + gap;
  if (placement === 'right') {
    left = rect.right + gap;
    top = rect.top + rect.height / 2 - estimatedHeight / 2;
  } else if (placement === 'left') {
    left = rect.left - width - gap;
    top = rect.top + rect.height / 2 - estimatedHeight / 2;
  } else if (placement === 'top') {
    left = rect.left + rect.width / 2 - width / 2;
    top = rect.top - estimatedHeight - gap;
  } else {
    left = rect.left + rect.width / 2 - width / 2;
    top = rect.bottom + gap;
  }
  popoverStyle.value = {
    left: `${clamp(left, 16, window.innerWidth - width - 16)}px`,
    top: `${clamp(top, 16, window.innerHeight - estimatedHeight - 16)}px`,
    width: `${width}px`
  };
}

async function positionSpotlight() {
  await nextTick();
  const target = await waitForTarget(step.value.target);
  targetMissing.value = !target;
  if (!target) {
    const fallback = {
      top: Math.max(72, window.innerHeight * .18),
      left: 240,
      width: Math.min(520, window.innerWidth - 48),
      height: 150
    };
    spotlight.value = fallback;
    placePopover(new DOMRect(fallback.left, fallback.top, fallback.width, fallback.height));
    return;
  }

  target.scrollIntoView({ block: 'center', inline: 'center', behavior: 'auto' });
  await new Promise((resolve) => window.setTimeout(resolve, 90));
  const rect = target.getBoundingClientRect();
  const safeRect = {
    top: Math.max(8, rect.top - 8),
    left: Math.max(8, rect.left - 8),
    width: Math.min(window.innerWidth - 16, rect.width + 16),
    height: Math.min(window.innerHeight - 16, rect.height + 16)
  };
  spotlight.value = safeRect;
  placePopover(new DOMRect(safeRect.left, safeRect.top, safeRect.width, safeRect.height));
}

function schedulePosition() {
  window.cancelAnimationFrame(positionFrame);
  positionFrame = window.requestAnimationFrame(() => {
    void positionSpotlight();
  });
}

async function show() {
  if (!shouldShowOnboarding(props.role)) return;
  active.value = true;
  const current = `${window.location.pathname}${window.location.search}`;
  const exact = steps.value.findIndex((item) => {
    const url = new URL(item.route, window.location.origin);
    return `${url.pathname}${url.search}` === current;
  });
  const samePath = steps.value.findIndex((item) => new URL(item.route, window.location.origin).pathname === window.location.pathname);
  index.value = exact >= 0 ? exact : samePath >= 0 ? samePath : 0;
  await positionSpotlight();
}

function finish() {
  completeOnboarding(props.role);
  active.value = false;
}

async function move(delta: number) {
  if (moving.value) return;
  const nextIndex = clamp(index.value + delta, 0, steps.value.length - 1);
  if (nextIndex === index.value) return;
  moving.value = true;
  index.value = nextIndex;
  await router.push(step.value.route);
  await positionSpotlight();
  moving.value = false;
}

function resetHandler() {
  active.value = true;
  index.value = 0;
  void router.push(step.value.route).then(positionSpotlight);
}

function keyHandler(event: KeyboardEvent) {
  if (!active.value) return;
  if (event.key === 'Escape') {
    finish();
  } else if (event.key === 'ArrowLeft') {
    void move(-1);
  } else if (event.key === 'ArrowRight' || event.key === 'Enter') {
    if (index.value < steps.value.length - 1) void move(1);
    else finish();
  }
}

onMounted(() => {
  void show();
  window.addEventListener('resize', schedulePosition);
  window.addEventListener('medical-tour-reset', resetHandler);
  window.addEventListener('keydown', keyHandler);
});

onBeforeUnmount(() => {
  window.cancelAnimationFrame(positionFrame);
  window.removeEventListener('resize', schedulePosition);
  window.removeEventListener('medical-tour-reset', resetHandler);
  window.removeEventListener('keydown', keyHandler);
});

watch(() => props.role, () => {
  active.value = false;
  void show();
});
</script>

<template>
  <Teleport to="body">
    <div v-if="active" class="tour-layer" :class="`role-${role}`">
      <div class="tour-scrim"></div>
      <div class="tour-spotlight" :class="{ 'is-fallback': targetMissing }" :style="{ top: `${spotlight.top}px`, left: `${spotlight.left}px`, width: `${spotlight.width}px`, height: `${spotlight.height}px` }"></div>
      <TourStep
        :style="popoverStyle"
        :eyebrow="step.eyebrow"
        :title="step.title"
        :body="step.body"
        :index="index"
        :total="steps.length"
        :busy="moving"
        @previous="move(-1)"
        @next="move(1)"
        @finish="finish"
        @skip="finish"
      />
    </div>
  </Teleport>
</template>
