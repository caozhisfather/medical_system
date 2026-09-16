<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { ArrowRight, BookOpenCheck, ChartNetwork, CircleHelp, Crosshair, Database, GraduationCap, History, Layers3, ScanLine, Settings2, ShieldCheck, SlidersHorizontal, Sparkles, Users } from '@lucide/vue';
import { resetOnboarding } from '../services/onboarding';
import { trainingStore } from '../stores/training';

const router = useRouter();
const activeRole = ref<'student' | 'teacher' | 'admin'>('student');

const studentSteps = [
  { icon: Layers3, title: '进入学习总览', text: '首页列出八大系统的入口与可探索结构数量，从这里直接进入某一个系统。', path: '/student/dashboard' },
  { icon: ScanLine, title: '三维人体解剖', text: '拖动旋转、滚轮缩放，点击任意结构即选中。左侧可单独查看某个系统，右上角支持全屏。', path: '/student/anatomy' },
  { icon: Layers3, title: '按层级深入结构', text: '沿“整体人体 → 系统 → 器官 → 精细结构”逐层下钻，每一层都把镜头自动框到当前对象。', path: '/student/anatomy' },
  { icon: BookOpenCheck, title: '查看结构讲解与教材依据', text: '选中结构后显示规范中文解剖名与英文原名，由 AnatomyAgent 讲解，命中时给出教材章节与页码。', path: '/student/anatomy' },
  { icon: Crosshair, title: '完成空间定位测验', text: '围绕当前结构作答，题型包含选择、判断与简答，提交后即时判分并给出错因。', path: '/student/anatomy?mode=practice' },
  { icon: ChartNetwork, title: '沿知识图谱延伸', text: '从结构出发查看它在知识网络中的上下游关系，把解剖与功能、临床联系起来。', path: '/knowledge-graph' },
  { icon: History, title: '在学习档案中复习', text: '测验记录与错因汇总在学习档案，用于安排下一次复习。', path: '/student/archive' }
];

const teacherSteps = [
  { icon: Users, title: '查看教学总览', text: '了解当前知识库规模、索引状态与学生练习概况。', path: '/teacher/dashboard' },
  { icon: Database, title: '维护教学知识库', text: '导入教材与权威医学依据，支持编辑、删除与来源字段补全，内容会作为讲解与命题的依据。', path: '/teacher/knowledge' },
  { icon: SlidersHorizontal, title: '配置题型与提示词', text: '决定启用选择、判断、简答中的哪些题型，选择题支持 2/3/4/5 选一，并设置权重与难度。', path: '/teacher/exam-settings' },
  { icon: Sparkles, title: '编辑系统提示词', text: '这段提示词决定出题范围、干扰项风格与解析要求，修改保存后即时对学生生效。', path: '/teacher/exam-settings' },
  { icon: ChartNetwork, title: '检查知识图谱', text: '查看结构节点与关系是否完整，发现错配时回到知识库修正来源。', path: '/knowledge-graph' }
];

const adminSteps = [
  { icon: Settings2, title: '进入系统控制台', text: '查看数据源、知识条目、向量索引、图谱规模与审计状态。', path: '/admin/dashboard' },
  { icon: Database, title: '维护教学知识库', text: '统一管理教材与权威资料，负责上传、编辑、删除及导入审核。', path: '/admin/knowledge' },
  { icon: ShieldCheck, title: '补齐来源与版权字段', text: '确认版本、机构、页码与版权信息完整，来源不清的资料不要入库。', path: '/admin/knowledge' },
  { icon: ChartNetwork, title: '检查索引与知识图谱', text: '资料修改后关注 OCR、embedding 与图谱状态，发现目录或章节错配时退回清洗。', path: '/knowledge-graph' },
  { icon: History, title: '查看操作审计', text: '追踪导入、删除、索引与配置变更，确保教学数据可追溯。', path: '/admin/dashboard' }
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
        <p>学生沿“整体 → 系统 → 器官 → 精细结构”学习并完成定位测验；教师维护知识库并配置题型与提示词。</p>
      </div>
      <button class="button-primary" type="button" @click="replayTour"><CircleHelp :size="18" /> 重新打开新手引导</button>
    </section>

    <div class="help-role-switch" role="tablist" aria-label="选择身份指南">
      <button type="button" role="tab" :aria-selected="activeRole === 'student'" :class="{ active: activeRole === 'student' }" @click="activeRole = 'student'"><GraduationCap :size="17" />学生使用指南</button>
      <button type="button" role="tab" :aria-selected="activeRole === 'teacher'" :class="{ active: activeRole === 'teacher' }" @click="activeRole = 'teacher'"><Users :size="17" />教师使用指南</button>
      <button type="button" role="tab" :aria-selected="activeRole === 'admin'" :class="{ active: activeRole === 'admin' }" @click="activeRole = 'admin'"><Settings2 :size="17" />管理员使用指南</button>
    </div>

    <section v-if="activeRole === 'student'" class="help-guide help-guide-student">
      <header><span><ScanLine :size="20" /></span><div><strong>学生：一次完整学习怎么走</strong><small>建议按顺序完成，测验记录会自动累积到学习档案。</small></div></header>
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
      <header><span><Users :size="20" /></span><div><strong>教师：如何组织教学与命题</strong><small>先补齐可追溯的教学依据，再决定考什么、怎么考。</small></div></header>
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
      <header><span><Settings2 :size="20" /></span><div><strong>管理员：维护可信教学数据</strong><small>管理员负责资料生命周期与审计，教师负责题型与命题策略。</small></div></header>
      <ol class="help-steps">
        <li v-for="(step, index) in adminSteps" :key="step.title">
          <b>{{ index + 1 }}</b><component :is="step.icon" :size="18" /><div><strong>{{ step.title }}</strong><p>{{ step.text }}</p></div><button type="button" @click="router.push(step.path)">前往 <ArrowRight :size="14" /></button>
        </li>
      </ol>
    </section>

    <section class="help-tips">
      <article><ScanLine :size="19" /><div><strong>三维模型怎么操作</strong><p>拖动旋转、滚轮缩放、单击选中结构，右上角可全屏。左侧点系统名进入该系统单独视图，点眼睛图标显示或隐藏。</p></div></article>
      <article><BookOpenCheck :size="19" /><div><strong>教材依据从哪里来</strong><p>讲解会优先匹配已入库的《系统解剖学》章节与页码；没有命中时会明确提示待补充，不编造出处，可点「教材详解」进一步检索。</p></div></article>
      <article><CircleHelp :size="19" /><div><strong>演示账号</strong><p>学生 student / student123，教师 teacher / teacher123，管理员 admin / admin123。</p></div></article>
    </section>

    <section class="surface-panel help-safety">
      <ShieldCheck :size="22" />
      <div>
        <strong>医学安全声明</strong>
        <p>本平台仅用于医学教学训练，解剖模型与讲解不作为临床诊断、治疗决策或急救处置依据。</p>
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
