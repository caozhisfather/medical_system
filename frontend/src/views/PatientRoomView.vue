<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  AlertTriangle,
  ArrowLeft,
  BookOpenCheck,
  Check,
  ChevronRight,
  ClipboardPlus,
  FileCheck2,
  HeartPulse,
  LoaderCircle,
  LockKeyhole,
  MessageSquareText,
  Mic,
  Pill,
  Send,
  ShieldCheck,
  Stethoscope,
  Unlock
} from '@lucide/vue';
import DigitalHumanWorkspace from '../components/DigitalHumanWorkspace.vue';
import SafetyNotice from '../components/SafetyNotice.vue';
import { trainingStore } from '../stores/training';

const route = useRoute();
const router = useRouter();
const question = ref('');
const loading = ref(false);
const submitting = ref(false);
const activeWorkPanel = ref<'draft' | 'mentor'>('draft');
const chatWindow = ref<HTMLElement | null>(null);
const caseId = computed(() => String(route.params.caseId || 'emergency_chest_pain'));
const session = computed(() => trainingStore.state.session);
const caseData = computed(() => trainingStore.activeCase.value);
const mentorSubtitle = computed(() => [...(session.value?.messages ?? [])].reverse().find((message) => message.role === 'tutor')?.content ?? '我会关注你的问诊结构、风险遗漏和证据链。');
const mentorState = computed(() => loading.value ? 'listening' : session.value?.missingPoints.some((item) => item.level === 'danger') ? 'warning' : 'speaking');
const scoreAverage = computed(() => {
  const items = session.value?.scores ?? [];
  return items.length ? Math.round(items.reduce((sum, item) => sum + item.score, 0) / items.length) : 0;
});
const patientStageLabels: Record<string, string> = { chief_complaint: '主诉', present_illness: '现病史', past_history: '既往史', medication_history: '用药史', allergy_history: '过敏史', physical_exam: '查体', tests: '检查', clinical_decision: '临床决策' };
const patientStage = computed(() => patientStageLabels[session.value?.patientState.stage ?? 'chief_complaint'] ?? '问诊');
const vitalSigns = computed(() => (caseData.value.physical_exam ?? []).slice(0, 4).map((item, index) => {
  const match = item.match(/^([^0-9]*)(.*)$/);
  const label = match?.[1]?.replace(/[：:，,。]/g, '').trim() || `查体 ${index + 1}`;
  const value = match?.[2]?.trim() || '已记录';
  return [label.slice(0, 7), value];
}));
const quickQuestions = computed(() => {
  const symptoms = caseData.value.symptom_tags ?? [caseData.value.chief_complaint];
  return [
    `${symptoms[0]}是什么时候开始的，怎么变化的？`,
    symptoms[1] ? `有没有${symptoms[1]}，具体是什么情况？` : `还有哪些伴随不舒服？`,
    `以前有${caseData.value.specialty ?? caseData.value.department}相关疾病或用药吗？`
  ];
});
onMounted(async () => {
  await trainingStore.loadCases();
  trainingStore.ensureSession(caseId.value);
});

async function sendQuestion(text = question.value) {
  const content = text.trim();
  if (!content || loading.value) return;
  question.value = '';
  loading.value = true;
  await trainingStore.askPatient(content);
  loading.value = false;
  await nextTick();
  chatWindow.value?.scrollTo({ top: chatWindow.value.scrollHeight, behavior: 'smooth' });
}

function addHypothesis(value: string) {
  if (!session.value || session.value.draft.hypotheses.includes(value)) return;
  session.value.draft.hypotheses.push(value);
}

function removeHypothesis(value: string) {
  if (!session.value) return;
  session.value.draft.hypotheses = session.value.draft.hypotheses.filter((item) => item !== value);
}

async function finishTraining() {
  if (submitting.value) return;
  submitting.value = true;
  const report = await trainingStore.submitSession();
  submitting.value = false;
  if (report) router.push(`/training-report/${report.id}`);
}
</script>

<template>
  <main v-if="session" class="patient-room">
    <header class="room-header">
      <button class="icon-button" type="button" title="退出问诊室" @click="router.push('/student/cases')"><ArrowLeft :size="19" /></button>
      <div class="room-case-title"><span class="case-status-dot"></span><div><strong>{{ caseData.title }}</strong><small>变体 {{ session.variantId }} · {{ session.difficulty }} · {{ session.mode }} · 虚拟教学病例</small></div></div>
      <SafetyNotice compact />
      <div class="room-progress"><span>训练进度</span><strong>{{ scoreAverage }}%</strong></div>
      <button class="button-secondary" type="button" :disabled="submitting" @click="finishTraining">{{ submitting ? '后台评估中' : '结束并生成报告' }} <LoaderCircle v-if="submitting" class="spin" :size="17" /><FileCheck2 v-else :size="17" /></button>
    </header>

    <div class="room-layout">
      <aside class="case-rail">
        <section>
          <span class="rail-section-label"><Stethoscope :size="15" /> 病例概览</span>
          <h1>{{ caseData.chief_complaint }}</h1>
          <p>{{ caseData.patient_profile_text }}</p>
          <div class="case-identity"><ShieldCheck :size="16" /><span>虚拟标准化病人<br><small>脚本约束回答</small></span></div>
        </section>
        <section>
          <span class="rail-section-label"><HeartPulse :size="15" /> 生命体征</span>
          <div class="vitals-grid"><div v-for="item in vitalSigns" :key="item[0]"><small>{{ item[0] }}</small><strong>{{ item[1] }}</strong></div></div>
        </section>
        <section class="exam-locker">
          <span class="rail-section-label"><ClipboardPlus :size="15" /> 检查资料</span>
          <button
            v-for="exam in (caseData.available_exams ?? []).slice(0, 5)"
            :key="exam"
            type="button"
            :class="{ unlocked: session.unlockedExams.includes(exam) }"
            @click="trainingStore.unlockExam(exam)"
          >
            <component :is="session.unlockedExams.includes(exam) ? Unlock : LockKeyhole" :size="14" />
            <span><strong>{{ exam }}</strong><small>{{ session.unlockedExams.includes(exam) ? caseData.exam_results?.[exam] ?? '已申请，等待结果' : '点击申请并解锁' }}</small></span>
          </button>
        </section>
        <section>
          <span class="rail-section-label"><Check :size="15" /> 当前训练目标</span>
          <ul class="objective-list"><li v-for="item in (caseData.key_scoring_points ?? [])" :key="item">{{ item }}</li></ul>
        </section>
      </aside>

      <section class="patient-dialogue">
        <div class="dialogue-heading">
          <div><span class="section-kicker">标准化病人问诊</span><h2>请像真实接诊一样逐步提问</h2></div>
          <span class="patient-state"><i></i> 病人在线 · {{ patientStage }} {{ session.patientState.progress }}%</span>
        </div>
        <SafetyNotice compact class="room-mobile-boundary" />
        <div ref="chatWindow" class="clinical-chat">
          <article v-for="(message, index) in session.messages" :key="index" :class="`chat-${message.role}`">
            <div class="message-author">
              <span>{{ message.role === 'student' ? '你' : message.role === 'patient' ? '标准化病人' : '临床思维导师' }}</span>
              <small>{{ message.role === 'patient' ? caseData.speaking_style : message.role === 'tutor' ? '过程提示，不直接给出诊断' : '医学生' }}</small>
            </div>
            <p>{{ message.content }}</p>
            <div v-if="message.citations?.length" class="message-citations"><BookOpenCheck :size="14" /> {{ message.citations[0].title }}</div>
          </article>
          <div v-if="loading" class="patient-typing"><span></span><span></span><span></span><b>标准化病人正在回答</b></div>
        </div>
        <div class="quick-questions">
          <button v-for="item in quickQuestions" :key="item" type="button" @click="sendQuestion(item)">{{ item }}</button>
        </div>
        <div class="clinical-input">
          <button class="icon-button" type="button" title="语音输入演示"><Mic :size="19" /></button>
          <textarea v-model="question" rows="2" placeholder="输入问诊问题。请避免一次询问多个无关问题。" @keydown.enter.exact.prevent="sendQuestion()" />
          <button class="send-button" type="button" :disabled="loading || !question.trim()" title="发送问题" @click="sendQuestion()">
            <LoaderCircle v-if="loading" class="spin" :size="20" /><Send v-else :size="20" />
          </button>
        </div>
      </section>

      <aside class="reasoning-rail">
        <nav class="room-work-tabs" aria-label="临床工作区">
          <button type="button" :class="{ active: activeWorkPanel === 'draft' }" @click="activeWorkPanel = 'draft'"><MessageSquareText :size="16" />临床草稿</button>
          <button type="button" :class="{ active: activeWorkPanel === 'mentor' }" @click="activeWorkPanel = 'mentor'"><Stethoscope :size="16" />AI 导师</button>
        </nav>
        <template v-if="activeWorkPanel === 'mentor'">
          <DigitalHumanWorkspace
            class="room-digital-human"
            compact
            name="智能临床导师"
            description="根据问诊过程提示风险遗漏，不直接给出诊断"
            :subtitle="mentorSubtitle"
            :state="mentorState"
            :speak-key="session.messages.length"
          />
          <section class="mentor-boundary-card"><ShieldCheck :size="17" /><div><strong>导师边界</strong><p>仅提示问诊结构、风险遗漏和证据链，不直接给出最终诊断。</p></div></section>
        </template>
        <template v-else>
        <div class="reasoning-heading"><span><MessageSquareText :size="16" /> 临床思维草稿</span><small>自动保存</small></div>
        <section>
          <label>诊断假设</label>
          <div class="hypothesis-list">
            <button v-for="item in session.draft.hypotheses" :key="item" type="button" title="移除假设" @click="removeHypothesis(item)">{{ item }} ×</button>
          </div>
          <div class="hypothesis-options"><button v-for="item in (caseData.differential_diagnoses ?? []).slice(0, 5)" :key="item" type="button" @click="addHypothesis(item)">+ {{ item }}</button></div>
        </section>
        <section><label>最终初步诊断</label><textarea v-model="session.draft.finalDiagnosis" rows="2" placeholder="综合对话与检查结果，提交你的初步诊断" /></section>
        <section><label>鉴别诊断与理由</label><textarea v-model="session.draft.differentials" rows="4" placeholder="按危险程度或可能性排序，并写明支持/反对证据" /></section>
        <section><label>下一步检查</label><textarea v-model="session.draft.examinations" rows="3" placeholder="说明检查优先级及目的" /></section>
        <section><label>处理方案草稿</label><textarea v-model="session.draft.plan" rows="3" placeholder="仅填写教学训练中的处理原则，不开具真实处方" /></section>
        <section class="medication-draft"><label><Pill :size="15" />教学用药方案</label><textarea v-model="session.draft.medicationPlan" rows="4" placeholder="写明药物、剂量、途径、频次及禁忌证/监测要点；仅用于虚拟病例训练" /><small>非真实处方，不可用于现实诊疗。</small></section>
        <section><label>指南证据</label><textarea v-model="session.draft.evidence" rows="3" placeholder="写明依据来源及其与判断的关系" /></section>
        <section class="risk-monitor">
          <div><AlertTriangle :size="16" /><strong>风险遗漏监测</strong><span>{{ session.missingPoints.length }}</span></div>
          <p v-for="item in session.missingPoints.slice(0, 3)" :key="item.id">{{ item.text }}</p>
        </section>
        <button class="button-primary submit-thinking" type="button" :disabled="submitting" @click="finishTraining"><LoaderCircle v-if="submitting" class="spin" :size="18" />{{ submitting ? '后台 AI 正在评估' : '提交诊疗决策并评估' }}<ChevronRight v-if="!submitting" :size="18" /></button>
        </template>
      </aside>
    </div>
  </main>
</template>

