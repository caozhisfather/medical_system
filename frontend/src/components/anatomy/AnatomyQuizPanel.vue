<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { ArrowRight, BookOpenCheck, Check, CircleAlert, Crosshair, LoaderCircle, RotateCcw, Sparkles, X } from '@lucide/vue';
import { generateQuiz, gradeQuiz } from '../../api';
import type { QuizGrade, QuizQuestion, QuizSet } from '../../types';

const props = defineProps<{
  structureEn: string;
  structureCn?: string;
  system?: string;
}>();

const quiz = ref<QuizSet | null>(null);
const loading = ref(false);
const error = ref('');
const index = ref(0);
const picked = ref<number | null>(null);
const judge = ref<boolean | null>(null);
const draft = ref('');
const grading = ref(false);
const grade = ref<QuizGrade | null>(null);
const results = ref<Array<{ question: QuizQuestion; score: number; correct: boolean }>>([]);

const current = computed<QuizQuestion | null>(() => quiz.value?.questions[index.value] ?? null);
const finished = computed(() => Boolean(quiz.value) && index.value >= (quiz.value?.questions.length ?? 0));
const canSubmit = computed(() => {
  const question = current.value;
  if (!question || grade.value || grading.value) return false;
  if (question.type === 'single_choice') return picked.value !== null;
  if (question.type === 'true_false') return judge.value !== null;
  return draft.value.trim().length > 0;
});
const average = computed(() => {
  if (!results.value.length) return 0;
  return Math.round(results.value.reduce((total, item) => total + item.score, 0) / results.value.length);
});

const TYPE_LABEL: Record<string, string> = {
  single_choice: '选择题',
  true_false: '判断题',
  short_answer: '简答题'
};

function resetAnswerState() {
  picked.value = null;
  judge.value = null;
  draft.value = '';
  grade.value = null;
}

async function load(force = false) {
  if (!props.structureEn) return;
  loading.value = true;
  error.value = '';
  quiz.value = null;
  results.value = [];
  index.value = 0;
  resetAnswerState();
  try {
    quiz.value = await generateQuiz({
      structure_en: props.structureEn,
      structure_cn: props.structureCn,
      system: props.system,
      force
    });
  } catch (fetchError) {
    error.value = fetchError instanceof Error ? fetchError.message : '题目生成失败';
  } finally {
    loading.value = false;
  }
}

async function submit() {
  const question = current.value;
  if (!question || !canSubmit.value) return;
  const answer =
    question.type === 'single_choice' ? picked.value : question.type === 'true_false' ? judge.value : draft.value.trim();
  grading.value = true;
  try {
    const result = await gradeQuiz({ question_id: question.id, answer });
    grade.value = result;
    results.value = [...results.value, { question, score: result.score, correct: result.correct }];
  } catch (gradeError) {
    error.value = gradeError instanceof Error ? gradeError.message : '评分失败';
  } finally {
    grading.value = false;
  }
}

function next() {
  index.value += 1;
  resetAnswerState();
}

function restart() {
  void load(true);
}

watch(() => props.structureEn, () => { void load(); }, { immediate: true });
</script>

<template>
  <section class="quiz-panel">
    <header class="quiz-panel-head">
      <div>
        <span class="section-kicker">空间定位测验</span>
        <h3>{{ quiz?.structure_label || structureCn || structureEn }}</h3>
      </div>
      <button v-if="quiz" class="text-button" type="button" :disabled="loading" @click="restart"><RotateCcw :size="15" />重新出题</button>
    </header>

    <div v-if="loading" class="quiz-state"><LoaderCircle class="spin" :size="22" />正在按教师的题型设置生成题目</div>

    <div v-else-if="error" class="quiz-state is-error"><CircleAlert :size="20" />{{ error }}</div>

    <div v-else-if="quiz && !quiz.enabled" class="quiz-state"><CircleAlert :size="20" />{{ quiz.message || '教师尚未启用任何题型。' }}</div>

    <div v-else-if="quiz && !quiz.questions.length" class="quiz-state"><CircleAlert :size="20" />{{ quiz.message || '本题型组合暂时没有生成出题目，请稍后重试。' }}</div>

    <template v-else-if="current">
      <div class="quiz-progress">
        <span>第 {{ index + 1 }} / {{ quiz?.questions.length }} 题</span>
        <b>{{ TYPE_LABEL[current.type] }}</b>
      </div>

      <p class="quiz-stem">{{ current.stem }}</p>

      <div v-if="current.type === 'single_choice'" class="quiz-options">
        <button
          v-for="(option, optionIndex) in current.options"
          :key="optionIndex"
          type="button"
          :disabled="Boolean(grade)"
          :class="{ picked: picked === optionIndex, right: grade && optionIndex === grade.correct_answer, wrong: grade && picked === optionIndex && optionIndex !== grade.correct_answer }"
          @click="picked = optionIndex"
        >
          <span>{{ String.fromCharCode(65 + optionIndex) }}</span>{{ option }}
        </button>
      </div>

      <div v-else-if="current.type === 'true_false'" class="quiz-judge">
        <button type="button" :disabled="Boolean(grade)" :class="{ picked: judge === true, right: grade && grade.correct_answer === true, wrong: grade && judge === true && grade.correct_answer !== true }" @click="judge = true"><Check :size="17" />正确</button>
        <button type="button" :disabled="Boolean(grade)" :class="{ picked: judge === false, right: grade && grade.correct_answer === false, wrong: grade && judge === false && grade.correct_answer !== false }" @click="judge = false"><X :size="17" />错误</button>
      </div>

      <textarea v-else v-model="draft" :disabled="Boolean(grade)" rows="5" placeholder="说出这是什么结构、有什么功能、可能发生什么病变" />

      <div v-if="grade" class="quiz-feedback" :class="grade.correct ? 'is-correct' : 'is-wrong'">
        <header><span>{{ grade.score }} 分</span><strong>{{ grade.correct ? '回答正确' : '需要复习' }}</strong></header>
        <p>{{ grade.feedback }}</p>
        <p v-if="grade.expected" class="quiz-expected">参考答案：{{ grade.expected }}</p>
        <div v-if="grade.hit_points?.length" class="quiz-points">
          <small>答对要点</small>
          <span v-for="point in grade.hit_points" :key="point">{{ point }}</span>
        </div>
        <div v-if="grade.missed_points?.length" class="quiz-points is-missed">
          <small>遗漏要点</small>
          <span v-for="point in grade.missed_points" :key="point">{{ point }}</span>
        </div>
        <p v-if="current.citation" class="quiz-citation"><BookOpenCheck :size="14" />{{ current.citation }}</p>
      </div>

      <div class="quiz-actions">
        <button v-if="!grade" class="button-primary" type="button" :disabled="!canSubmit || grading" @click="submit">
          <LoaderCircle v-if="grading" class="spin" :size="16" /><Crosshair v-else :size="16" />{{ grading ? '评分中' : '提交作答' }}
        </button>
        <button v-else class="button-primary" type="button" @click="next">{{ index + 1 >= (quiz?.questions.length ?? 0) ? '查看结果' : '下一题' }}<ArrowRight :size="16" /></button>
      </div>
    </template>

    <div v-else-if="finished" class="quiz-summary">
      <Sparkles :size="26" />
      <strong>本次得分 {{ average }}</strong>
      <p>共 {{ results.length }} 题，答对 {{ results.filter((item) => item.correct).length }} 题。</p>
      <ul>
        <li v-for="(item, itemIndex) in results" :key="itemIndex" :class="{ missed: !item.correct }">
          <span>{{ itemIndex + 1 }}</span><b>{{ TYPE_LABEL[item.question.type] }}</b><i>{{ item.score }} 分</i>
        </li>
      </ul>
      <button class="button-secondary" type="button" @click="restart"><RotateCcw :size="16" />再练一次</button>
    </div>
  </section>
</template>

<style scoped>
.quiz-panel { display: grid; gap: 10px; padding: 14px; border-radius: 8px; background: #fff; }
.quiz-panel-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }
.quiz-panel-head h3 { margin: 3px 0 0; color: #214b51; font-size: 16px; }
.quiz-state { display: flex; align-items: center; gap: 8px; padding: 22px 12px; color: #5d757a; font-size: 13px; }
.quiz-state.is-error { color: #a4342a; }
.quiz-progress { display: flex; align-items: center; justify-content: space-between; color: #6d8a8d; font-size: 11px; }
.quiz-progress b { padding: 2px 8px; border-radius: 999px; background: #e4f1ee; color: var(--teal-dark, #075b57); font-size: 11px; }
.quiz-stem { margin: 0; color: #23484f; font-size: 14px; line-height: 1.65; }
.quiz-options { display: grid; gap: 6px; }
.quiz-options button { display: grid; grid-template-columns: 24px minmax(0,1fr); align-items: center; gap: 8px; padding: 9px 11px; border: 1px solid var(--line, #e1e9ea); border-radius: 7px; background: #fbfdfd; color: #35535a; font-size: 13px; text-align: left; cursor: pointer; }
.quiz-options button > span { display: grid; place-items: center; width: 22px; height: 22px; border-radius: 50%; background: #e7f0ef; color: var(--teal-dark, #075b57); font-size: 11px; font-weight: 700; }
.quiz-options button.picked { border-color: rgba(15,118,110,.5); background: #e9f4f1; }
.quiz-options button.right { border-color: #3f9c6d; background: #e8f6ee; }
.quiz-options button.wrong { border-color: #c0564a; background: #fdeeec; }
.quiz-options button:disabled { cursor: default; }
.quiz-judge { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.quiz-judge button { display: inline-flex; align-items: center; justify-content: center; gap: 6px; min-height: 42px; border: 1px solid var(--line, #e1e9ea); border-radius: 7px; background: #fbfdfd; color: #35535a; font-size: 13px; cursor: pointer; }
.quiz-judge button.picked { border-color: rgba(15,118,110,.5); background: #e9f4f1; }
.quiz-judge button.right { border-color: #3f9c6d; background: #e8f6ee; }
.quiz-judge button.wrong { border-color: #c0564a; background: #fdeeec; }
.quiz-panel textarea { width: 100%; padding: 10px; border: 1px solid var(--line, #e1e9ea); border-radius: 7px; background: #fbfdfd; color: #2f4f56; font-size: 13px; line-height: 1.65; resize: vertical; }
.quiz-feedback { display: grid; gap: 6px; padding: 11px; border-radius: 7px; }
.quiz-feedback.is-correct { background: #e8f6ee; }
.quiz-feedback.is-wrong { background: #fdeeec; }
.quiz-feedback header { display: flex; align-items: baseline; gap: 8px; }
.quiz-feedback header span { color: #21484e; font-size: 20px; font-weight: 800; }
.quiz-feedback header strong { color: #35535a; font-size: 12px; }
.quiz-feedback p { margin: 0; color: #456066; font-size: 12px; line-height: 1.6; }
.quiz-expected { font-weight: 700; }
.quiz-points { display: grid; gap: 3px; }
.quiz-points small { color: #4d7d78; font-size: 11px; font-weight: 800; }
.quiz-points span { color: #3d5a60; font-size: 12px; }
.quiz-points.is-missed small { color: #a4681c; }
.quiz-citation { display: inline-flex; align-items: center; gap: 4px; color: #6d8a8d; font-size: 11px; }
.quiz-actions { display: flex; gap: 8px; }
.quiz-summary { display: grid; justify-items: center; gap: 8px; padding: 16px 8px; text-align: center; color: #5d757a; }
.quiz-summary strong { color: #16414a; font-size: 20px; }
.quiz-summary p { margin: 0; font-size: 12px; }
.quiz-summary ul { display: grid; gap: 4px; width: 100%; margin: 6px 0; padding: 0; list-style: none; }
.quiz-summary li { display: grid; grid-template-columns: 22px 1fr auto; align-items: center; gap: 8px; padding: 6px 9px; border-radius: 6px; background: #eef6f4; font-size: 12px; }
.quiz-summary li.missed { background: #fdf1ef; }
.quiz-summary li span { display: grid; place-items: center; width: 20px; height: 20px; border-radius: 50%; background: #fff; font-size: 11px; font-weight: 700; }
.quiz-summary li b { color: #35535a; font-weight: 700; }
.quiz-summary li i { color: #4d7d78; font-style: normal; font-weight: 700; }
</style>
