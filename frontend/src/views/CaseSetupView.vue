<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ArrowLeft, ArrowRight, BookOpenCheck, Check, Clock3, Gauge, ShieldCheck, Stethoscope } from '@lucide/vue';
import SafetyNotice from '../components/SafetyNotice.vue';
import { trainingStore } from '../stores/training';

const route = useRoute();
const router = useRouter();
const selectedCaseId = ref(String(route.query.case || 'emergency_chest_pain'));
const selectedVariant = ref(String(route.query.variant || 'A'));
const selectedDifficulty = ref('标准');
const selectedMode = ref('完整训练');
onMounted(() => trainingStore.loadCases());
watch(() => route.query.case, (value) => { if (value) selectedCaseId.value = String(value); });
const selectedCase = computed(() => trainingStore.state.cases.find((item) => item.id === selectedCaseId.value) ?? trainingStore.state.cases[0]);
const variants = computed(() => selectedCase.value.case_variants ?? []);
const selectedVariantData = computed(() => variants.value.find((item) => item.variant_id === selectedVariant.value) ?? variants.value[0]);
const profilePreview = computed(() => selectedVariantData.value
  ? `${selectedVariantData.value.age}岁${selectedVariantData.value.gender}，${selectedCase.value.patient_profile.occupation}，虚拟教学病例`
  : selectedCase.value.patient_profile_text);
const setupCases = computed(() => {
  const first = trainingStore.state.cases.slice(0, 6);
  return first.some((item) => item.id === selectedCaseId.value) ? first : [selectedCase.value, ...first.slice(0, 5)];
});

async function start() {
  trainingStore.startSession(selectedCaseId.value, selectedDifficulty.value, selectedMode.value, selectedVariant.value);
  await router.push(`/patient-room/${selectedCaseId.value}`);
}
</script>

<template>
  <div class="workspace-page setup-page">
    <button class="back-link" type="button" @click="router.push('/student/cases')"><ArrowLeft :size="17" /> 返回病例库</button>
    <section class="page-title-row">
      <div><span class="section-kicker">新建训练</span><h1>配置病例训练</h1><p>选择病例、难度和训练方式，进入标准化病人问诊室。</p></div>
      <div class="step-marker"><span class="active">1 配置</span><i></i><span>2 问诊</span><i></i><span>3 报告</span></div>
    </section>

    <div class="setup-layout">
      <section class="setup-main">
        <div class="setup-section">
          <div class="setup-section-title"><span>01</span><div><h2>选择病例</h2><p>病例脚本互相独立，患者只回答脚本内信息。</p></div></div>
          <div class="setup-case-list">
            <button v-for="item in setupCases" :key="item.id" type="button" :class="{ active: selectedCaseId === item.id }" @click="selectedCaseId = item.id">
              <Stethoscope :size="18" /><span><strong>{{ item.title }}</strong><small>{{ item.department }} · {{ item.chief_complaint }}</small></span><Check v-if="selectedCaseId === item.id" :size="17" />
            </button>
          </div>
        </div>
        <div class="setup-section">
          <div class="setup-section-title"><span>02</span><div><h2>病例变体</h2><p>变体改变患者年龄、表达方式与干扰信息，但不改变核心诊断逻辑。</p></div></div>
          <div class="variant-choice">
            <button v-for="item in variants" :key="item.variant_id" type="button" :class="{ active: selectedVariant === item.variant_id }" @click="selectedVariant = item.variant_id">
              <strong>{{ item.label }}</strong><small>{{ item.age }}岁{{ item.gender }} · {{ item.communication_style }}</small>
            </button>
          </div>
        </div>
        <div class="setup-section">
          <div class="setup-section-title"><span>03</span><div><h2>训练难度</h2><p>难度影响导师提示频率与可见病例信息。</p></div></div>
          <div class="segmented-choice">
            <button v-for="item in ['引导', '标准', '挑战']" :key="item" type="button" :class="{ active: selectedDifficulty === item }" @click="selectedDifficulty = item">
              <Gauge :size="17" /><strong>{{ item }}</strong><small>{{ item === '引导' ? '更多提示' : item === '标准' ? '适度提示' : '仅风险提示' }}</small>
            </button>
          </div>
        </div>
        <div class="setup-section">
          <div class="setup-section-title"><span>04</span><div><h2>训练模式</h2><p>完整训练适合形成报告，专项训练聚焦单项能力。</p></div></div>
          <div class="mode-choice">
            <button v-for="item in ['完整训练', '问诊专项', '鉴别诊断专项']" :key="item" type="button" :class="{ active: selectedMode === item }" @click="selectedMode = item">
              <BookOpenCheck :size="18" /><span><strong>{{ item }}</strong><small>{{ item === '完整训练' ? '问诊、推理、检查、证据全流程' : '15 分钟目标训练' }}</small></span>
            </button>
          </div>
        </div>
      </section>

      <aside class="setup-summary">
        <span class="section-kicker">训练预览</span>
        <h2>{{ selectedCase.title }}</h2>
        <p>{{ profilePreview }}</p>
        <dl>
          <dt>主诉</dt><dd>{{ selectedCase.chief_complaint }}</dd>
          <dt>病例变体</dt><dd>{{ selectedVariant }}</dd>
          <dt>难度</dt><dd>{{ selectedDifficulty }}</dd>
          <dt>模式</dt><dd>{{ selectedMode }}</dd>
          <dt>预计时长</dt><dd><Clock3 :size="15" /> 20 分钟</dd>
        </dl>
        <div class="training-objectives"><strong>训练目标</strong><span v-for="item in (selectedCase.key_scoring_points ?? []).slice(0, 3)" :key="item"><Check :size="14" /> {{ item }}</span></div>
        <div class="privacy-note"><ShieldCheck :size="17" /><span>虚拟教学病例<br><small>不包含真实患者信息</small></span></div>
        <button class="button-primary" type="button" @click="start">进入问诊室 <ArrowRight :size="18" /></button>
        <SafetyNotice compact />
      </aside>
    </div>
  </div>
</template>



