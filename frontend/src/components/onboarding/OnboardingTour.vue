<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { completeOnboarding, shouldShowOnboarding, tourSteps } from '../../services/onboarding';
import type { WorkspaceRole } from '../../stores/training';
import TourStep from './TourStep.vue';

const props = defineProps<{ role: WorkspaceRole }>();
const router = useRouter();
const active = ref(false);
const index = ref(0);
const spotlight = ref({ top: 90, left: 240, width: 360, height: 120 });
const steps = computed(() => tourSteps[props.role]);
const step = computed(() => steps.value[index.value]);

function routeFor(role: WorkspaceRole, target: string) {
  if (role === 'teacher') {
    if (target.includes('exam-settings')) return '/teacher/exam-settings';
    if (target.includes('case-management')) return '/teacher/knowledge';
    if (target.includes('teacher-graph')) return '/knowledge-graph';
    return '/teacher/dashboard';
  }
  if (role === 'admin') return '/admin/dashboard';
  if (target.includes('daily-review')) return '/student/archive';
  if (target.includes('knowledge-graph')) return '/knowledge-graph';
  if (target.includes('anatomy-lab')) return '/student/anatomy';
  return '/student/dashboard';
}

async function positionSpotlight() {
  await nextTick();
  const target = document.querySelector(step.value.target) as HTMLElement | null;
  if (!target) {
    spotlight.value = { top: 92, left: 240, width: Math.min(520, window.innerWidth - 40), height: 150 };
    return;
  }
  target.scrollIntoView({ block: 'center', behavior: 'smooth' });
  await new Promise((resolve) => window.setTimeout(resolve, 120));
  const rect = target.getBoundingClientRect();
  spotlight.value = {
    top: Math.max(12, rect.top - 8),
    left: Math.max(12, rect.left - 8),
    width: Math.min(window.innerWidth - 24, rect.width + 16),
    height: Math.min(window.innerHeight - 24, rect.height + 16)
  };
}

async function show() {
  if (!shouldShowOnboarding(props.role)) return;
  active.value = true;
  index.value = 0;
  // Auto-start must not hijack the URL: if the user opened a deep link, the
  // tour highlights whatever is on screen instead of bouncing them elsewhere.
  await positionSpotlight();
}

function finish() {
  completeOnboarding(props.role);
  active.value = false;
}

async function move(delta: number) {
  index.value = Math.min(steps.value.length - 1, Math.max(0, index.value + delta));
  await router.push(routeFor(props.role, step.value.target));
  await positionSpotlight();
}

function resetHandler() {
  active.value = true;
  index.value = 0;
  void move(0);
}

function keyHandler(event: KeyboardEvent) {
  if (event.key === 'Escape' && active.value) finish();
}

onMounted(() => {
  void show();
  window.addEventListener('resize', positionSpotlight);
  window.addEventListener('medical-tour-reset', resetHandler);
  window.addEventListener('keydown', keyHandler);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', positionSpotlight);
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
      <div class="tour-spotlight" :style="{ top: `${spotlight.top}px`, left: `${spotlight.left}px`, width: `${spotlight.width}px`, height: `${spotlight.height}px` }"></div>
      <TourStep
        :title="step.title"
        :body="step.body"
        :index="index"
        :total="steps.length"
        @previous="move(-1)"
        @next="move(1)"
        @finish="finish"
        @skip="finish"
      />
    </div>
  </Teleport>
</template>
