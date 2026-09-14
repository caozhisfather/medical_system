<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { ArrowRight, BarChart3, BookOpen, BookOpenCheck, Bot, CircleHelp, ClipboardCheck, Database, GraduationCap, Network, ScanLine, Settings2, ShieldCheck, Stethoscope, Users } from '@lucide/vue';
import { resetOnboarding } from '../services/onboarding';
import { trainingStore } from '../stores/training';

const router = useRouter();
const activeRole = ref<'student' | 'teacher' | 'admin'>('student');

const studentSteps = [
  { icon: Stethoscope, title: '进入学习总览', text: '从首页查看六维能力画像、待办训练和系统推荐病例，先看弱项再开始。', path: '/student/dashboard' },
  { icon: BookOpen, title: '选择病例开始训练', text: '在病例训练库按科室、症状和难度筛选，选择病例与教学变体后进入问诊室。', path: '/student/cases' },
  { icon: Bot, title: '与 AI 标准化病人问诊', text: '围绕主诉追问起病、性质、诱因、伴随症状和既往史，按需申请检查，不要直接问最终诊断。', path: '/student/cases' },
  { icon: ClipboardCheck, title: '提交临床决策', text: '完成问诊后给出初步诊断、鉴别诊断、检查选择、治疗原则和指南依据，系统会逐项评分。', path: '/student/cases' },
  { icon: Network, title: '查看训练报告与知识图谱', text: '训练报告展示得分、错因、遗漏点和风险项；再用知识图谱沿症状到疾病、检查、指南查证。', path: '/knowledge-graph' },
  { icon: ScanLine, title: '虚拟解剖室·三维人体', text: '拖动旋转三维人体、滚轮缩放、点击任意结构。选中后可查看中文解剖名、英文原名、AI 讲解，并溯源到教材章节与页码。', path: '/student/anatomy' },
  { icon: ScanLine, title: '虚拟解剖室·图谱分层', text: '按系统总览、器官精细图、精细结构图逐层点击编号热点，学习结构与临床关联。', path: '/student/anatomy' },
  { icon: BookOpenCheck, title: '每日复盘并订制明日计划', text: '训练结束后进入学习档案，查看每日复盘、薄弱点和明日推荐练习。', path: '/student/archive' }
];

const teacherSteps = [
  { icon: Users, title: '教学总览', text: '查看班级均分、完成率、需干预学生和共性薄弱点，优先处理风险名单。', path: '/teacher/dashboard' },
  { icon: Database, title: '教学知识库', text: '先维护病例、教材和权威医学依据，再进入训练病例审核；资料支持脱敏、编辑和 AI 整合。', path: '/teacher/cases?tab=knowledge' },
  { icon: ClipboardCheck, title: '训练病例审核', text: '审核 AI Agent 根据知识库生成的训练病例，教师可以编辑、批准、退回或拒绝。', path: '/teacher/cases?tab=assets' },
  { icon: BarChart3, title: '学情推荐', text: '查看 AI 根据学生训练结果生成的病例建议，教师确认后再布置训练。', path: '/teacher/cases?tab=recommendations' },
  { icon: BookOpenCheck, title: '教学复盘', text: '阅读 AI 汇总的班级复盘、报告复核和教学建议，定位知识断点与高危遗漏。', path: '/teacher/class-review' },
  { icon: ClipboardCheck, title: '报告复核', text: '在教学复盘页切换到报告复核，查看学生训练报告和班级聚合分析。', path: '/teacher/class-review?tab=reports' }
];
const adminSteps = [
  { icon: Settings2, title: '进入系统控制台', text: '查看数据源、知识条目、向量索引、图谱规模和审计状态。', path: '/admin/dashboard' },
  { icon: Database, title: '维护教学知识库', text: '统一管理病例、教材和权威资料，负责新增、编辑、删除及导入审核。', path: '/admin/knowledge' },
  { icon: ShieldCheck, title: '执行脱敏与来源审核', text: '确认姓名、联系方式、病历号等敏感信息已脱敏，并补齐版本、机构、页码和版权字段。', path: '/admin/knowledge' },
  { icon: Network, title: '检查索引与知识图谱', text: '资料修改后关注 OCR、embedding 和图谱状态，发现目录或章节错配时退回清洗。', path: '/knowledge-graph' },
  { icon: ClipboardCheck, title: '查看操作审计', text: '追踪教师审核、管理员导入、删除、索引和推荐决策，确保教学数据可追溯。', path: '/admin/dashboard' }
];

function replayTour() {
  resetOnboarding(trainingStore.state.profile.role);
  window.dispatchEvent(new CustomEvent('medical-tour-reset'));
}
</script>

<template>
  <div class="workspace-page help-page">
    <section class="page-title-row">
      <div>
        <span class="section-kicker">帮助中心 · 新手引导</span>
        <h1>按身份快速上手</h1>
        <p>学生围绕“问诊 → 决策 → 复盘”完成训练闭环；教师围绕“看板 → 病例工作流 → 复核”组织教学。</p>
      </div>
      <button class="button-primary" type="button" @click="replayTour"><CircleHelp :size="18" /> 重新打开新手引导</button>
    </section>

    <div class="help-role-switch" role="tablist" aria-label="选择身份指南">
      <button type="button" role="tab" :aria-selected="activeRole === 'student'" :class="{ active: activeRole === 'student' }" @click="activeRole = 'student'"><GraduationCap :size="17" />学生使用指南</button>
      <button type="button" role="tab" :aria-selected="activeRole === 'teacher'" :class="{ active: activeRole === 'teacher' }" @click="activeRole = 'teacher'"><Users :size="17" />教师使用指南</button>
      <button type="button" role="tab" :aria-selected="activeRole === 'admin'" :class="{ active: activeRole === 'admin' }" @click="activeRole = 'admin'"><Settings2 :size="17" />管理员使用指南</button>
    </div>

    <section v-if="activeRole === 'student'" class="help-guide help-guide-student">
      <header><span><Stethoscope :size="20" /></span><div><strong>学生：一次完整训练怎么走</strong><small>建议按顺序完成，训练报告与每日复盘会自动累积到学习档案。</small></div></header>
      <ol class="help-steps">
        <li v-for="(step, index) in studentSteps" :key="step.title">
          <b>{{ index + 1 }}</b>
          <component :is="step.icon" :size="18" />
          <div><strong>{{ step.title }}</strong><p>{{ step.text }}</p></div>
          <button type="button" @click="router.push(step.path)">前往 <ArrowRight :size="14" /></button>
        </li>
      </ol>
    </section>

    <section v-else-if="activeRole === 'teacher'" class="help-guide help-guide-teacher">
      <header><span><Users :size="20" /></span><div><strong>教师：如何组织一次教学干预</strong><small>先看数据，再用 AI 病例工作流补齐短板，最后由教师本人决策发布。</small></div></header>
      <ol class="help-steps">
        <li v-for="(step, index) in teacherSteps" :key="step.title">
          <b>{{ index + 1 }}</b>
          <component :is="step.icon" :size="18" />
          <div><strong>{{ step.title }}</strong><p>{{ step.text }}</p></div>
          <button type="button" @click="router.push(step.path)">前往 <ArrowRight :size="14" /></button>
        </li>
      </ol>
    </section>

    <section v-else class="help-guide help-guide-admin">
      <header><span><Settings2 :size="20" /></span><div><strong>管理员：维护可信教学数据</strong><small>管理员负责资料生命周期与审计，教师负责病例教学编排和发布决策。</small></div></header>
      <ol class="help-steps">
        <li v-for="(step, index) in adminSteps" :key="step.title">
          <b>{{ index + 1 }}</b><component :is="step.icon" :size="18" /><div><strong>{{ step.title }}</strong><p>{{ step.text }}</p></div><button type="button" @click="router.push(step.path)">前往 <ArrowRight :size="14" /></button>
        </li>
      </ol>
    </section>

    <section class="help-tips">
      <article><Bot :size="19" /><div><strong>怎么问 AI 病人</strong><p>围绕主诉一次问清起病、性质、诱因、伴随症状和既往史；先问开放性症状，再追问关键细节，不要直接问“诊断是什么”。</p></div></article>
      <article><ShieldCheck :size="19" /><div><strong>病例脱敏规则</strong><p>病例知识库保存前会自动脱敏姓名、证件号、电话、住址、出生日期和病历号，可先预览再入库；原始真实病历不要直接粘贴。</p></div></article>
      <article><CircleHelp :size="19" /><div><strong>演示账号</strong><p>学生 student / student123，教师 teacher / teacher123，管理员 admin / admin123。</p></div></article>
    </section>

    <section class="surface-panel help-safety">
      <ShieldCheck :size="22" />
      <div>
        <strong>医学安全声明</strong>
        <p>本平台仅用于医学教学训练，所有病例均为虚拟或脱敏教学数据，不用于真实临床诊断、治疗决策或急救处置。</p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.help-role-switch { display: inline-flex; gap: 4px; margin: 18px 0 0; padding: 4px; border-radius: 8px; background: #e8f0ef; }
.help-role-switch button { display: inline-flex; align-items: center; gap: 7px; min-height: 36px; padding: 0 14px; border: 0; border-radius: 6px; background: transparent; color: #617b80; font-weight: 800; }
.help-role-switch button.active { background: #fff; color: var(--teal-dark); box-shadow: 0 5px 14px rgba(24,64,72,.1); }
.help-guide { margin-top: 14px; overflow: hidden; border-radius: 8px; background: #fbfdfd; box-shadow: 0 10px 30px rgba(23,63,72,.06); }
.help-guide > header { display: flex; align-items: center; gap: 12px; padding: 16px 18px; border-bottom: 1px solid var(--line); }
.help-guide > header > span { display: grid; width: 38px; height: 38px; place-items: center; border-radius: 8px; background: #e3f1ee; color: var(--teal); }
.help-guide > header strong { display: block; color: #183b43; font-size: 17px; }
.help-guide > header small { color: #5d767b; font-size: 12px; }
.help-steps { display: grid; margin: 0; padding: 18px; list-style: none; }
.help-steps li { display: grid; grid-template-columns: 28px 20px minmax(0,1fr) auto; align-items: start; gap: 10px; padding: 12px 0; border-bottom: 1px solid #edf2f1; }
.help-steps li:last-child { border-bottom: 0; }
.help-steps li > b { display: grid; width: 24px; height: 24px; place-items: center; border-radius: 50%; background: #dcefea; color: var(--teal-dark); font-size: 12px; }
.help-steps li > svg { margin-top: 3px; color: #4f8f8c; }
.help-steps li strong { color: #26494f; font-size: 14px; }
.help-steps li p { margin: 2px 0 0; color: #5d767b; font-size: 12px; line-height: 1.6; }
.help-steps li button { display: inline-flex; align-items: center; gap: 4px; margin-top: 2px; padding: 5px 8px; border: 0; border-radius: 6px; background: #eef4f3; color: var(--teal-dark); font-size: 11px; font-weight: 900; white-space: nowrap; }
.help-steps li button:hover { background: #dfeeea; }
.help-tips { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 12px; margin-top: 16px; }
.help-tips article { display: flex; gap: 10px; padding: 14px; border-radius: 8px; background: #eef6f4; color: var(--teal-dark); }
.help-tips article strong { display: block; color: #21484e; font-size: 13px; }
.help-tips article p { margin: 3px 0 0; color: #55747a; font-size: 12px; line-height: 1.55; }
@media (max-width: 760px) {
  .help-tips { grid-template-columns: 1fr; }
  .help-steps li { grid-template-columns: 28px minmax(0,1fr); }
  .help-steps li > svg { display: none; }
  .help-steps li button { grid-column: 2; }
}
</style>
