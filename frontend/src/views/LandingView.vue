<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import {
  Box,
  BookOpen,
  ChevronRight,
  ChevronLeft,
  Pause,
  Play,
  ChartNoAxesColumnIncreasing,
  PlayCircle,
  ArrowRight,
  BookOpenCheck,
  Crosshair,
  GraduationCap,
  Layers3,
  MousePointer2,
  Network,
  ScanLine,
  ShieldCheck,
  SlidersHorizontal,
  UserRoundCheck,
  Users
} from '@lucide/vue';
import AgentCommand from '../components/AgentCommand.vue';
import BrandLogo from '../components/BrandLogo.vue';
import workflowBody from '../assets/medical/workflow-body.webp';
import workflowHeart from '../assets/medical/workflow-heart.webp';
import workflowValve from '../assets/medical/workflow-valve.webp';
import workflowTest from '../assets/medical/workflow-test.webp';
import footerBackground from '../assets/medical/landing-footer-dna.webp';
import entryLab from '../assets/medical/landing-entry-lab.webp';
import studentRoleArt from '../assets/medical/landing-resource-heart.webp';
import teacherRoleArt from '../assets/medical/teacher-overview-banner.webp';
import adminRoleArt from '../assets/medical/admin-console-banner.webp';
import labHero from '../assets/medical/landing-lab-reference.webp';
import heartResource from '../assets/medical/landing-resource-heart.webp';
import skeletonResource from '../assets/medical/landing-resource-skeleton.webp';
import headResource from '../assets/medical/landing-resource-head.webp';
import lungsResource from '../assets/medical/landing-resource-lungs.webp';
import type { WorkspaceRole } from '../stores/training';

const router = useRouter();
const workflowSteps = [
 {title:'选择系统',icon:Layers3,image:workflowBody,description:'从整体人体进入运动、循环、呼吸、消化等人体系统，镜头自动框到该系统。'},
 {title:'下钻器官',icon:ScanLine,image:workflowHeart,description:'在系统内继续选择器官，例如心脏、肺、肝、肾，放大成独立的三维标本。'},
 {title:'点选精细结构',icon:MousePointer2,image:workflowValve,description:'点选心腔、瓣膜等精细结构，查看规范中文解剖名、英文原名与功能讲解。'},
 {title:'测验与溯源',icon:Crosshair,image:workflowTest,description:'完成选择、判断与简答，讲解命中教材时给出书名、章节与页码。'}
];
const activeStep = ref(0);
const workflowPaused = ref(false);
const workflowHover = ref(false);
const workflowFocus = ref(false);
const workflowGrid = ref<HTMLElement|null>(null);
const workflowFrame = ref<Record<string,string>>({opacity:'0'});
let workflowTimer: ReturnType<typeof setInterval>|undefined;
let workflowObserver: IntersectionObserver|null = null;
let workflowResize: ResizeObserver|null = null;
let workflowVisible = false;
function measureWorkflow() {
 const card=workflowGrid.value?.querySelectorAll<HTMLElement>('.lp-workflow-card')[activeStep.value];
 if(card) workflowFrame.value={width:`${card.offsetWidth}px`,height:`${card.offsetHeight}px`,transform:`translate(${card.offsetLeft}px,${card.offsetTop}px)`,opacity:'1'};
}
function selectStep(index:number) { activeStep.value=(index+workflowSteps.length)%workflowSteps.length; }
watch(activeStep,()=>nextTick(measureWorkflow));
onMounted(()=>{
 workflowPaused.value=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
 if(workflowGrid.value){
  workflowObserver=new IntersectionObserver(entries=>{workflowVisible=entries[0]?.isIntersecting??false;},{threshold:0.2});
  workflowObserver.observe(workflowGrid.value);
  workflowResize=new ResizeObserver(measureWorkflow);workflowResize.observe(workflowGrid.value);
 }
 nextTick(measureWorkflow);
 workflowTimer=setInterval(()=>{if(workflowVisible&&!workflowPaused.value&&!workflowHover.value&&!workflowFocus.value&&!document.hidden)selectStep(activeStep.value+1);},3500);
});
onBeforeUnmount(()=>{clearInterval(workflowTimer);workflowObserver?.disconnect();workflowResize?.disconnect();});
const resources = [
  {title:'系统解剖实验',description:'心血管、呼吸、消化等系统的结构认知与空间关系',image:heartResource,system:'circulatory'},
  {title:'骨骼与关节实验',description:'全身骨骼结构、关节组成与运动相关解剖',image:skeletonResource,system:'locomotor'},
  {title:'局部解剖实验',description:'头颈、胸部、腹部等区域的分层解剖与结构辨识',image:headResource,system:'nervous'},
  {title:'临床病例与测验',description:'基于真实临床情境的结构识别与综合应用训练',image:lungsResource,system:'respiratory'}
];
function openResource(system:string) { router.push({path:'/login',query:{role:'student',redirect:`/student/anatomy?system=${system}`}}); }
const selectedRole = ref<WorkspaceRole>('student');
let revealObserver: IntersectionObserver | null = null;

const roleContent = computed(() => {
  if (selectedRole.value === 'teacher') {
    return {
      title: '教师教学空间',
      description: '维护可追溯的教学知识库，决定考什么题型、用什么提示词命题。',
      action: '进入教师工作台',
      features: ['教学知识库', '题型与提示词', '知识图谱']
    };
  }
  if (selectedRole.value === 'admin') {
    return {
      title: '系统控制台',
      description: '管理数据源、知识库索引与图谱状态，保持教学依据可追溯。',
      action: '进入管理员工作台',
      features: ['数据源管理', '知识库状态', '图谱治理']
    };
  }
  return {
    title: '虚拟解剖实验室',
    description: '在三维人体中按“整体 → 系统 → 器官 → 精细结构”逐层探索，完成空间定位测验。',
    action: '进入虚拟解剖实验室',
    features: ['三维结构探索', '教材依据讲解', '空间定位测验']
  };
});

function scrollToEntry() {
  document.querySelector('#entry')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function enter() {
  await router.push({ path: '/login', query: { role: selectedRole.value } });
}

onMounted(() => {
  revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        revealObserver?.unobserve(entry.target);
      }
    });
  }, { threshold: 0.14 });

  document.querySelectorAll('.landing-v2 .reveal').forEach((element) => revealObserver?.observe(element));
});

onBeforeUnmount(() => revealObserver?.disconnect());
</script>

<template>
  <main class="landing-screen landing-v2 landing-reference">
    <header class="landing-header landing-nav">
      <a class="brand-lockup" href="#top" aria-label="返回页面顶部">
        <BrandLogo variant="compact" subtitle="可追溯的虚拟解剖实验室" />
      </a>
      <nav aria-label="落地页导航">
        <a href="#resources">实验资源</a>
        <a href="#workflow">学习路径</a>
        <a href="#entry">进入平台</a>
      </nav>
      <button class="landing-nav-action" type="button" @click="scrollToEntry">
        开始学习 <ArrowRight :size="16" />
      </button>
    </header>

    <section id="top" class="lp-hero" :style="{'--lab-hero': `url(${labHero})`}">
      <div class="lp-hero-copy">
        <span class="lp-eyebrow">AI + 医学教育</span>
        <h1>虚拟解剖实验室</h1>
        <p>基于真实解剖数据与教学标准，提供可交互、<br class="lp-desktop-break"/>可训练、可评估的医学实验学习环境。</p>
        <div class="lp-benefits"><span><Box :size="24"/>三维结构交互</span><span><Layers3 :size="24"/>教材依据明确</span><span><ChartNoAxesColumnIncreasing :size="24"/>教学评价支持</span></div>
        <div class="lp-actions"><button class="lp-primary" @click="scrollToEntry">开始学习 <ArrowRight :size="23"/></button><a href="#resources"><PlayCircle :size="24"/>浏览实验资源</a></div>
        <small class="lp-source">数据来源：BodyParts3D 4.0 · 人民卫生出版社教材体系</small>
      </div>
    </section>
    <section class="lp-capabilities" aria-label="平台核心能力">
      <article><i><Box :size="38"/></i><span><strong>三维结构探索</strong><small>真实解剖模型，多层级交互</small></span></article>
      <article><i><Layers3 :size="38"/></i><span><strong>四级分层下钻</strong><small>从系统到精细结构逐层查看</small></span></article>
      <article><i><BookOpenCheck :size="38"/></i><span><strong>教材依据可追溯</strong><small>对接权威教材与课程标准</small></span></article>
      <article><i><SlidersHorizontal :size="38"/></i><span><strong>教师决策与考核</strong><small>题型与提示词灵活配置</small></span></article>
    </section>
    <section id="resources" class="lp-resources" aria-labelledby="resource-title">
      <header><h2 id="resource-title">核心实验资源</h2><button @click="scrollToEntry">查看全部资源 <ArrowRight :size="23"/></button></header>
      <div class="lp-resource-grid"><button v-for="r in resources" :key="r.title" class="lp-resource-card" @click="openResource(r.system)"><img :src="r.image" :alt="r.title+'教学模型'"/><div><h3>{{r.title}}</h3><p>{{r.description}}</p><span class="lp-resource-arrow"><ArrowRight :size="22"/></span></div></button></div>
    </section>

    <section id="workflow" class="lp-workflow reveal" :style="{'--workflow-bg':`url(${footerBackground})`}">
      <header class="lp-workflow-heading"><span>学习路径</span><h2>一次学习，从整体人体走到一个具体结构<span>。</span></h2><i aria-hidden="true"></i><p>从选择系统到精细结构，每一步都保留教材依据与可回看的训练记录。</p></header>
      <div ref="workflowGrid" class="lp-workflow-grid" @mouseenter="workflowHover=true" @mouseleave="workflowHover=false" @focusin="workflowFocus=true" @focusout="workflowFocus=false"><span class="lp-workflow-frame" :style="workflowFrame" aria-hidden="true"></span><article v-for="(step,index) in workflowSteps" :key="step.title" :class="{featured:index===activeStep}" class="lp-workflow-card" role="button" tabindex="0" :aria-pressed="activeStep===index" :aria-label="`第${index+1}步：${step.title}`" @click="selectStep(index)" @keydown.enter.prevent="selectStep(index)" @keydown.space.prevent="selectStep(index)" @keydown.right.prevent="selectStep(activeStep+1)" @keydown.left.prevent="selectStep(activeStep-1)"><div class="lp-step-top"><span>{{String(index+1).padStart(2,'0')}}</span><component :is="step.icon" :size="34"/></div><img :src="step.image" :alt="step.title+'示意图'" loading="lazy"/><h3>{{step.title}}</h3><p>{{step.description}}</p><span v-if="index<workflowSteps.length-1" class="lp-step-arrow" aria-hidden="true"><ChevronRight :size="25"/></span></article></div>
      <div class="lp-workflow-controls" aria-label="学习路径轮播控制"><button aria-label="上一步" @click="selectStep(activeStep-1)"><ChevronLeft :size="18"/></button><button v-for="(step,index) in workflowSteps" :key="step.title" class="lp-step-dot" :class="{active:activeStep===index}" :aria-label="`切换到第${index+1}步`" :aria-pressed="activeStep===index" @click="selectStep(index)">{{String(index+1).padStart(2,'0')}}</button><button aria-label="下一步" @click="selectStep(activeStep+1)"><ChevronRight :size="18"/></button><button class="lp-play-toggle" :aria-label="workflowPaused?'播放轮播':'暂停轮播'" @click="workflowPaused=!workflowPaused"><Play v-if="workflowPaused" :size="16"/><Pause v-else :size="16"/>{{workflowPaused?'播放':'暂停'}}</button></div>
    </section>

    <section id="entry" class="landing-entry lp-entry reveal">
      <div class="entry-heading landing-section-head">

        <h2>选择身份，进入各<br/>自的工作空间。</h2>
        <p>学生探索三维结构并完成测验，教师维护教学依据并决定命题方式，管理员治理数据与索引。</p>
      </div>

      <div class="entry-stage lp-entry-stage">
        <div class="role-choice" aria-label="选择平台身份">
          <button type="button" :style="{'--role-art':`url(${studentRoleArt})`}" :class="{ active: selectedRole === 'student' }" :aria-pressed="selectedRole === 'student'" @click="selectedRole = 'student'">
            <GraduationCap :size="22" />
            <span><strong>医学生</strong><small>结构探索 · 虚拟实验 · 定位训练</small></span>
          </button>
          <button type="button" :style="{'--role-art':`url(${teacherRoleArt})`}" :class="{ active: selectedRole === 'teacher' }" :aria-pressed="selectedRole === 'teacher'" @click="selectedRole = 'teacher'">
            <Users :size="22" />
            <span><strong>医学教师</strong><small>知识库管理 · 题目命制 · 教学评价</small></span>
          </button>
          <button type="button" :style="{'--role-art':`url(${adminRoleArt})`}" :class="{ active: selectedRole === 'admin' }" :aria-pressed="selectedRole === 'admin'" @click="selectedRole = 'admin'">
            <ShieldCheck :size="22" />
            <span><strong>超级管理员</strong><small>数据治理 · 权限配置 · 系统维护</small></span>
          </button>
        </div>

        <aside class="entry-console lp-entry-console" :style="{'--entry-lab':`url(${entryLab})`}">
          <span>{{ roleContent.title }}</span>
          <h3>{{ roleContent.description }}</h3>
          <ul>
            <li v-for="(feature,index) in roleContent.features" :key="feature"><i><component :is="[Box,BookOpenCheck,Crosshair][index]" :size="39"/></i><strong>{{ feature }}</strong></li>
          </ul>
          <button class="landing-primary" type="button" @click="enter">
            {{ roleContent.action }} <ArrowRight :size="19" />
          </button>
        </aside>
      </div>

      <div class="landing-command">
        <span><strong>也可以直接告诉智能体</strong><small>例如：“打开循环系统三维模型”</small></span>
        <AgentCommand />
      </div>
    </section>

    <footer class="landing-footer lp-reference-footer" :style="{'--footer-background':`url(${footerBackground})`}">
      <div class="lp-footer-brand"><BookOpen :size="62" :stroke-width="1.5"/><span><strong>虚拟解剖实验室</strong><small>医学三维结构与空间定位训练平台</small></span></div>
      <p><ShieldCheck :size="28"/> <span>三维模型与讲解仅用于医学教育，不作为临床诊断依据。</span></p>
    </footer>
  </main>
</template>

<style scoped src="./landing-reference.css"></style>
