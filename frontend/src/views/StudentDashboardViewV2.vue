<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watchEffect } from 'vue';
import type { RouteLocationRaw } from 'vue-router';
import {
  Activity, ArrowRight, BarChart3, BookOpen, Bot, Box, CalendarDays, Check, ChevronLeft, ChevronRight,
  CirclePlay, ClipboardCheck, Crosshair, Flame, Heart, Layers3, Network, NotebookPen, PersonStanding
} from '@lucide/vue';
import { getAnatomyGlossary, getAnatomyRecords, getCurrentUser, getQuizRecords } from '../api';
import { ANATOMY_SYSTEMS_3D, ATLAS_3D_URL, ATLAS_ORGAN_URL, type AnatomyOrganPayload } from '../data/anatomy3d';
import heroArt from '../assets/medical/dashboard-anatomy-hero.png';
import graphArt from '../assets/medical/dashboard-knowledge-hero.webp';
import practiceArt from '../assets/medical/dashboard-practice-hero.webp';
import heartArt from '../assets/medical/anatomy/heart-blood-flow-blausen.webp';

const anatomy = '/student/anatomy';
const archive = '/student/archive';
const practice = { path: anatomy, query: { mode: 'practice' } };
const atlas = { path: anatomy, query: { mode: 'atlas' } };
const circulation = { path: anatomy, query: { system: 'circulatory' } };
const mistakes = { path: archive, query: { tab: 'mistakes' } };
const graph = '/knowledge-graph';
const weekdays = ['一', '二', '三', '四', '五', '六', '日'];

const heroSlides = [
  {
    title: '在三维结构中学习人体',
    description: '从整体人体逐层深入系统、器官和精细结构。结合三维模型、知识图谱和定位练习掌握解剖知识。',
    art: heroArt,
    primary: { label: '进入虚拟解剖室', to: anatomy, icon: Box, tour: 'anatomy-lab' },
    secondary: { label: '空间定位测验', to: practice, icon: Crosshair, tour: 'evidence' }
  },
  {
    title: '沿着图谱理解解剖',
    description: '从一个解剖结构出发，查看它所属的系统、相邻的器官，以及相关的功能与临床知识。',
    art: graphArt,
    primary: { label: '打开知识图谱', to: graph, icon: Network },
    secondary: { label: '浏览解剖分层', to: atlas, icon: Layers3 }
  },
  {
    title: '练习解剖空间定位',
    description: '在器官和精细结构图上标出目标位置，查看判分和标准区域，再回顾错题巩固记忆。',
    art: practiceArt,
    primary: { label: '开始定位测验', to: practice, icon: Crosshair },
    secondary: { label: '查看错题本', to: mistakes, icon: ClipboardCheck }
  }
];

const slideIndex = ref(0);
const currentSlide = computed(() => heroSlides[slideIndex.value]);
const actionsHovered = ref(false);
const actionsFocused = ref(false);
const pageVisible = ref(false);
const canRotate = computed(() => pageVisible.value && !actionsHovered.value && !actionsFocused.value);

function selectSlide(index: number) {
  slideIndex.value = (index + heroSlides.length) % heroSlides.length;
}

function syncPageVisibility() {
  pageVisible.value = !document.hidden;
}

watchEffect(onCleanup => {
  if (!canRotate.value) return;
  const next = slideIndex.value + 1;
  const timer = window.setTimeout(() => selectSlide(next), 5000);
  onCleanup(() => window.clearTimeout(timer));
});

const tasks = [
  { id: 'circulation', title: '学习循环系统与心脏结构', to: circulation, icon: CirclePlay },
  { id: 'practice', title: '完成一次空间定位测验', to: practice, icon: Crosshair },
  { id: 'atlas', title: '复习器官与精细结构', to: atlas, icon: Layers3 },
  { id: 'graph', title: '查看结构在知识图谱中的关系', to: graph, icon: Network },
  { id: 'review', title: '回顾学习记录与错题', to: mistakes, icon: NotebookPen }
];
const learningPath = [
  { title: '整体人体', description: '总览与分区', to: anatomy, icon: PersonStanding },
  { title: '系统', description: '按教学系统探索', to: null, icon: Layers3 },
  { title: '器官', description: '结构与功能', to: atlas, icon: Heart },
  { title: '精细结构', description: '二维定位与训练', to: practice, icon: Network }
];
const shortcuts = [
  { title: '三维模型库', description: '交互式解剖浏览', to: anatomy, icon: Box },
  { title: '知识图谱', description: '结构与关联', to: graph, icon: BookOpen },
  { title: '错题复习', description: '归纳错因 · 针对复习', to: mistakes, icon: ClipboardCheck },
  { title: '学习分析', description: '作答记录与成绩', to: archive, icon: BarChart3 }
];
const weeklyPlan = [
  { day: '周一', title: '复习循环系统', to: circulation },
  { day: '周三', title: '完成虚拟解剖实训', to: practice },
  { day: '周五', title: '整理错题与复习笔记', to: mistakes }
];

const today = new Date();
const dayFormatter = new Intl.DateTimeFormat('sv-SE');
const monthFormatter = new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: 'long' });
const dateFormatter = new Intl.DateTimeFormat('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });

function shiftDay(date: Date, offset: number) {
  const next = new Date(date);
  next.setDate(next.getDate() + offset);
  return next;
}

function dateKey(date: Date) {
  return dayFormatter.format(date);
}

const totalStructures = ref<number>();
const termCount = ref<number>();
const organCount = ref<number>();
const attemptCount = ref<number>();
const checkedTasks = ref<string[]>([]);
const taskStorageKey = ref('');
const tasksLoading = ref(true);
const weekOffset = ref(0);

interface ActivityEntry {
  timestamp: string;
  title: string;
  score: number;
  to: RouteLocationRaw;
}

const history = ref<ActivityEntry[]>();
const historyError = ref(false);
const latestActivity = computed(() => history.value?.[0]);
const attemptsByDay = computed(() => {
  const counts = new Map<string, number>();
  for (const entry of history.value ?? []) {
    const date = new Date(entry.timestamp);
    if (Number.isNaN(date.getTime())) continue;
    const key = dateKey(date);
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return counts;
});
const lastSevenDays = computed(() => Array.from({ length: 7 }, (_, i) => {
  const date = shiftDay(today, i - 6);
  return { date, count: attemptsByDay.value.get(dateKey(date)) ?? 0 };
}));
const maxDailyCount = computed(() => Math.max(1, ...lastSevenDays.value.map(day => day.count)));
const currentStreak = computed(() => {
  if (!history.value) return '—';
  let date = attemptsByDay.value.has(dateKey(today)) ? today : shiftDay(today, -1);
  let count = 0;
  while (attemptsByDay.value.has(dateKey(date))) {
    count += 1;
    date = shiftDay(date, -1);
  }
  return count;
});
function daysInWeek(date: Date) {
  const monday = shiftDay(date, -((date.getDay() + 6) % 7));
  return Array.from({ length: 7 }, (_, i) => {
    const date = shiftDay(monday, i);
    const key = dateKey(date);
    return { key, day: date.getDate(), today: key === dateKey(today), active: attemptsByDay.value.has(key) };
  });
}
const selectedWeek = computed(() => shiftDay(today, weekOffset.value * 7));
const calendarDays = computed(() => daysInWeek(selectedWeek.value));
const currentWeekDays = computed(() => daysInWeek(today));
const metrics = computed(() => [
  { label: '教学系统', value: ANATOMY_SYSTEMS_3D.length, unit: '个', icon: Layers3 },
  { label: '可探索结构', value: totalStructures.value, icon: Box },
  { label: '规范术语', value: termCount.value, icon: BookOpen },
  { label: '器官分组', value: organCount.value, icon: Heart },
  { label: '测验题型', value: 3, unit: '种', icon: Network },
  { label: '作答记录', value: attemptCount.value, unit: '条', icon: BarChart3 }
]);

async function readAsset<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) throw new Error('无法读取解剖资源');
  return response.json();
}

async function loadCatalog() {
  const [atlasResult, glossaryResult, organResult] = await Promise.allSettled([
    readAsset<{ parts: unknown[] }>(ATLAS_3D_URL),
    getAnatomyGlossary(),
    readAsset<AnatomyOrganPayload>(ATLAS_ORGAN_URL)
  ]);
  if (atlasResult.status === 'fulfilled') totalStructures.value = atlasResult.value.parts.length;
  if (glossaryResult.status === 'fulfilled') termCount.value = glossaryResult.value.count;
  if (organResult.status === 'fulfilled') {
    organCount.value = organResult.value.systems.reduce((count, system) => count + system.organs.length, 0);
  }
}

async function loadHistory() {
  try {
    const [location, quiz] = await Promise.all([getAnatomyRecords(200), getQuizRecords(200)]);
    attemptCount.value = location.summary.total + quiz.summary.total;
    const locations: ActivityEntry[] = location.items.map(item => ({
      timestamp: item.created_at, title: item.title, score: item.score,
      to: { path: anatomy, query: { mode: 'practice', exercise: item.exercise_id } }
    }));
    const quizzes: ActivityEntry[] = quiz.items.map(item => ({
      timestamp: item.updated_at, title: item.structure_label, score: item.score, to: anatomy
    }));
    history.value = [...locations, ...quizzes]
      .filter(item => Number.isFinite(Date.parse(item.timestamp)))
      .sort((a, b) => Date.parse(b.timestamp) - Date.parse(a.timestamp));
  } catch {
    historyError.value = true;
  }
}

async function loadTasks() {
  try {
    const user = await getCurrentUser();
    taskStorageKey.value = 'medical_dashboard_tasks:' + user.id;
    const saved = JSON.parse(localStorage.getItem(taskStorageKey.value) ?? 'null');
    if (saved?.date === dateKey(today) && Array.isArray(saved.tasks)) {
      checkedTasks.value = tasks.filter(task => saved.tasks.includes(task.id)).map(task => task.id);
    }
  } catch {
    // The checklist still works for the current page if browser storage is unavailable.
  } finally {
    tasksLoading.value = false;
  }
}

function toggleTask(id: string) {
  checkedTasks.value = checkedTasks.value.includes(id)
    ? checkedTasks.value.filter(task => task !== id)
    : [...checkedTasks.value, id];
  if (taskStorageKey.value) {
    try {
      localStorage.setItem(taskStorageKey.value, JSON.stringify({ date: dateKey(today), tasks: checkedTasks.value }));
    } catch {
      // Keep the current selection when browser storage is unavailable.
    }
  }
}

onMounted(() => {
  syncPageVisibility();
  document.addEventListener('visibilitychange', syncPageVisibility);
  void loadCatalog();
  void loadHistory();
  void loadTasks();
});

onBeforeUnmount(() => {
  document.removeEventListener('visibilitychange', syncPageVisibility);
});
</script>

<template>
  <div class="learning-dashboard">
    <div class="dashboard-main">
      <section class="learning-hero" aria-label="学习主题" aria-roledescription="轮播图"
        @keydown.left.prevent="selectSlide(slideIndex - 1)" @keydown.right.prevent="selectSlide(slideIndex + 1)">
        <img v-for="(slide, index) in heroSlides" :key="slide.art" class="hero-illustration"
          :class="{ 'is-active': index === slideIndex }" :src="slide.art" alt="" :fetchpriority="index === 0 ? 'high' : 'low'" />
        <div class="hero-copy" :aria-live="canRotate ? 'off' : 'polite'">
          <p class="hero-eyebrow">临思智训 <span>·</span> 个性化智能学习平台</p>
          <h1>{{ currentSlide.title }}</h1>
          <p class="hero-description">{{ currentSlide.description }}</p>
          <div class="dashboard-actions" @mouseenter="actionsHovered = true" @mouseleave="actionsHovered = false"
            @focusin="actionsFocused = true" @focusout="actionsFocused = false">
            <RouterLink class="dashboard-button primary" :to="currentSlide.primary.to" :data-tour="currentSlide.primary.tour">
              <component :is="currentSlide.primary.icon" :size="19" /> {{ currentSlide.primary.label }} <ArrowRight :size="16" />
            </RouterLink>
            <RouterLink class="dashboard-button secondary" :to="currentSlide.secondary.to" :data-tour="currentSlide.secondary.tour">
              <component :is="currentSlide.secondary.icon" :size="19" /> {{ currentSlide.secondary.label }}
            </RouterLink>
          </div>
        </div>
        <div class="hero-controls" role="group" aria-label="轮播控制">
          <button type="button" aria-label="上一张" @click="selectSlide(slideIndex - 1)"><ChevronLeft :size="17" /></button>
          <button v-for="(slide, index) in heroSlides" :key="slide.title" type="button" class="hero-dot"
            :aria-label="'切换到：' + slide.title" :aria-pressed="index === slideIndex" @click="selectSlide(index)"></button>
          <button type="button" aria-label="下一张" @click="selectSlide(slideIndex + 1)"><ChevronRight :size="17" /></button>
        </div>
      </section>

      <section class="dashboard-panel dashboard-metrics" aria-label="平台资源与作答">
        <div v-for="metric in metrics" :key="metric.label" class="dashboard-metric">
          <span class="metric-icon"><component :is="metric.icon" :size="23" /></span>
          <span><small>{{ metric.label }}</small><strong>{{ metric.value ?? '—' }} <small v-if="metric.unit && metric.value !== undefined">{{ metric.unit }}</small></strong></span>
        </div>
      </section>

      <div class="dashboard-middle">
        <section id="today-tasks" class="dashboard-panel task-panel" data-tour="today-task">
          <header class="panel-heading">
            <h2><CalendarDays /> 今日任务</h2>
            <span class="task-count"><strong>{{ checkedTasks.length }}</strong> / {{ tasks.length }}</span>
          </header>
          <progress class="dashboard-progress" :value="checkedTasks.length" :max="tasks.length" aria-label="今日任务完成进度"></progress>
          <ul class="task-list">
            <li v-for="task in tasks" :key="task.id">
              <label>
                <input type="checkbox" :checked="checkedTasks.includes(task.id)" :disabled="tasksLoading" @change="toggleTask(task.id)" />
                <span>{{ task.title }}</span>
              </label>
              <RouterLink class="task-link" :to="task.to" :aria-label="'打开任务：' + task.title"><component :is="task.icon" :size="17" /></RouterLink>
            </li>
          </ul>
        </section>

        <div class="dashboard-learning">
          <section id="learning-path" class="dashboard-panel path-panel">
            <header class="panel-heading">
              <h2><Layers3 /> 学习路径</h2>
              <RouterLink class="panel-link" :to="atlas">浏览图谱 <ChevronRight :size="15" /></RouterLink>
            </header>
            <ol class="path-grid">
              <li v-for="step in learningPath" :key="step.title">
                <RouterLink v-if="step.to" :to="step.to" class="path-tile">
                  <component :is="step.icon" :size="27" />
                  <strong>{{ step.title }}</strong>
                  <small>{{ step.description }}</small>
                </RouterLink>
                <details v-else class="system-menu">
                  <summary class="path-tile">
                    <component :is="step.icon" :size="27" />
                    <strong>{{ step.title }}</strong>
                    <small>{{ step.description }}</small>
                  </summary>
                  <div class="system-links" aria-label="教学系统">
                    <RouterLink v-for="system in ANATOMY_SYSTEMS_3D" :key="system.id" :to="{ path: anatomy, query: { system: system.id } }">
                      {{ system.name }} <ChevronRight :size="13" />
                    </RouterLink>
                  </div>
                </details>
              </li>
            </ol>
          </section>

          <section class="dashboard-panel resume-panel">
            <header class="panel-heading"><h2><CirclePlay /> 继续学习</h2></header>
            <div class="resume-content">
              <span class="resume-art" aria-hidden="true"><img :src="heartArt" alt="" /><CirclePlay :size="26" /></span>
              <div class="resume-copy">
                <strong>{{ latestActivity?.title || '循环系统：心脏与血管' }}</strong>
                <small v-if="latestActivity">最近得分 {{ latestActivity.score }} · {{ dateFormatter.format(new Date(latestActivity.timestamp)) }}</small>
                <small v-else>从心脏结构和血液循环开始探索</small>
              </div>
              <RouterLink class="dashboard-button primary" :to="latestActivity?.to ?? circulation">{{ latestActivity ? '继续学习' : '开始学习' }}</RouterLink>
            </div>
          </section>
        </div>
      </div>

      <section class="dashboard-panel shortcut-panel">
        <header class="panel-heading"><h2><Layers3 /> 高频功能</h2></header>
        <div class="shortcut-grid">
          <RouterLink v-for="shortcut in shortcuts" :key="shortcut.title" :to="shortcut.to" class="shortcut-tile">
            <span class="shortcut-icon"><component :is="shortcut.icon" :size="22" /></span>
            <span class="shortcut-copy"><strong>{{ shortcut.title }}</strong><small>{{ shortcut.description }}</small></span>
            <ChevronRight class="shortcut-arrow" :size="16" />
          </RouterLink>
        </div>
      </section>
    </div>

    <aside class="dashboard-side" aria-label="学习摘要">
      <section class="dashboard-panel overview-panel">
        <header class="panel-heading">
          <h2><BarChart3 /> 学习概览</h2>
          <RouterLink class="panel-link" :to="archive">近 7 天 <ChevronRight :size="15" /></RouterLink>
        </header>
        <div class="overview-content">
          <div><strong>{{ totalStructures ?? '—' }}</strong><small>可探索结构</small></div>
          <div v-if="history" class="activity-chart" role="img" :aria-label="'近七日每日作答次数 ' + lastSevenDays.map(day => day.count).join('、')">
            <span v-for="day in lastSevenDays" :key="dateKey(day.date)" class="activity-bar" :class="{ empty: !day.count }"
              :title="dateKey(day.date) + ' · ' + day.count + ' 次作答'" :style="{ height: Math.max(9, day.count / maxDailyCount * 100) + '%' }"></span>
          </div>
        </div>
        <p v-if="historyError" class="overview-note">暂时无法读取作答记录</p>
      </section>

      <section class="dashboard-panel streak-panel">
        <header class="panel-heading"><h2><Flame class="flame-icon" /> 连续学习 <strong>{{ currentStreak }}</strong> 天</h2></header>
        <ol class="week-grid streak-grid" aria-label="本周学习记录">
          <li v-for="(day, i) in currentWeekDays" :key="day.key">
            <span class="streak-mark" :class="{ active: day.active }"><Check v-if="day.active" :size="14" /></span><small>{{ weekdays[i] }}</small>
          </li>
        </ol>
      </section>

      <section id="weekly-plan" class="dashboard-panel plan-panel">
        <header class="panel-heading"><h2><ClipboardCheck /> 本周计划</h2><span class="panel-note">学习建议</span></header>
        <ul class="plan-list">
          <li v-for="entry in weeklyPlan" :key="entry.day">
            <RouterLink :to="entry.to"><span class="plan-dot"></span><span>{{ entry.day }}</span><strong>{{ entry.title }}</strong><ChevronRight :size="15" /></RouterLink>
          </li>
        </ul>
      </section>

      <section class="dashboard-panel calendar-panel">
        <header class="panel-heading">
          <h2><CalendarDays /> 学习日历</h2>
          <div class="calendar-controls">
            <button type="button" aria-label="上一周" @click="weekOffset--"><ChevronLeft :size="16" /></button>
            <time>{{ monthFormatter.format(selectedWeek) }}</time>
            <button type="button" aria-label="下一周" :disabled="weekOffset >= 0" @click="weekOffset++"><ChevronRight :size="16" /></button>
          </div>
        </header>
        <ol class="week-grid calendar-grid">
          <li v-for="(day, i) in calendarDays" :key="day.key">
            <small>{{ weekdays[i] }}</small>
            <time :datetime="day.key" :class="{ today: day.today, studied: day.active }" :aria-current="day.today ? 'date' : undefined">{{ day.day }}</time>
          </li>
        </ol>
      </section>

      <section class="dashboard-panel assistant-panel">
        <div class="assistant-art" aria-hidden="true">
          <svg width="59" height="59" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="1.45" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 8V4H8M2 14h2m16 0h2" />
            <rect x="4" y="8" width="16" height="12" rx="3" fill="#edf4ff" fill-opacity=".72" />
            <g class="assistant-eyes" fill="currentColor" stroke="none">
              <ellipse cx="9" cy="13.5" rx="1" ry="1.4" />
              <ellipse cx="15" cy="13.5" rx="1" ry="1.4" />
            </g>
            <path class="assistant-closed-eyes" d="M7.6 13.5q1.4 1.4 2.8 0m3.2 0q1.4 1.4 2.8 0" stroke-width="1.3" />
            <path d="M10.5 16.5q1.5 1.4 3 0" stroke-width="1.05" />
          </svg>
        </div>
        <header class="panel-heading"><h2><Bot /> AI 助教</h2></header>
        <p>选择解剖结构，查看教材依据与 AI 讲解。</p>
        <RouterLink class="dashboard-button secondary" :to="atlas">打开助教 <ArrowRight :size="16" /></RouterLink>
      </section>
    </aside>
  </div>
</template>

<style scoped src="../student-dashboard-cards.css"></style>
