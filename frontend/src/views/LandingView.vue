<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import {
  Activity,
  ArrowRight,
  BookOpenCheck,
  Crosshair,
  FileCheck2,
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
import teacherMentorImage from '../assets/medical/teacher-mentor-hero.png';
import dashboardImage from '../assets/showcase/student-dashboard-hd.png';
import teacherDashboardImage from '../assets/medical/teacher-dashboard.png';
import type { WorkspaceRole } from '../stores/training';

const router = useRouter();
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
    action: '进入虚拟解剖室',
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
  <main class="landing-screen landing-v2">
    <header class="landing-header landing-nav">
      <a class="brand-lockup" href="#top" aria-label="返回页面顶部">
        <BrandLogo variant="compact" subtitle="可追溯的虚拟解剖实验室" />
      </a>
      <nav aria-label="落地页导航">
        <a href="#showcase">产品实景</a>
        <a href="#workflow">学习路径</a>
        <a href="#entry">进入平台</a>
      </nav>
      <button class="landing-nav-action" type="button" @click="scrollToEntry">
        开始学习 <ArrowRight :size="16" />
      </button>
    </header>

    <section id="top" class="landing-hero">
      <div class="landing-hero-copy">
        <span class="landing-hero-eyebrow">AI + 医学教育</span>
        <h1>虚拟解剖实验室</h1>
        <p>三维模型、教材依据与空间定位测验连成一条可验证的学习链路。</p>
        <div class="landing-hero-actions">
          <button class="landing-primary" type="button" @click="scrollToEntry">
            开始学习 <ArrowRight :size="19" />
          </button>
          <a class="landing-secondary" href="#showcase">查看产品实景</a>
        </div>
        <p class="landing-hero-source">数据来源：<strong>BodyParts3D 4.0</strong> · <strong>人民卫生出版社教材体系</strong></p>
      </div>

      <figure class="landing-hero-media" aria-label="虚拟解剖实验室界面">
        <img :src="teacherMentorImage" alt="虚拟解剖实验室中的三维人体与结构讲解界面" />
        <figcaption>
          <span class="live-state"><Activity :size="16" /> AnatomyAgent 已就绪</span>
          <strong>从整体人体走到具体结构</strong>
          <small>所有内容用于医学教育，不作为临床诊断依据。</small>
        </figcaption>
      </figure>
    </section>

    <section class="capability-rail" aria-label="平台核心能力">
      <article><ScanLine :size="21" /><span><strong>三维结构探索</strong><small>真实解剖模型</small></span></article>
      <article><Layers3 :size="21" /><span><strong>四级分层下钻</strong><small>整体到精细结构</small></span></article>
      <article><BookOpenCheck :size="21" /><span><strong>教材依据可追溯</strong><small>章节与页码定位</small></span></article>
      <article><SlidersHorizontal :size="21" /><span><strong>教师决定怎么考</strong><small>题型与提示词可控</small></span></article>
    </section>

    <section id="showcase" class="landing-showcase reveal">
      <header class="landing-section-head">
        <span class="landing-section-kicker">产品实景</span>
        <h2>不是概念片，是一套能上手操作的解剖教学产品。</h2>
        <p class="landing-section-lede">学生探索三维结构，教师维护可追溯的教学依据，管理员治理数据与索引，三个角色共用同一份知识底稿。</p>
      </header>

      <div class="showcase-grid">
        <article class="showcase-main">
          <div class="showcase-frame">
            <img :src="dashboardImage" alt="学生工作台实景" loading="lazy" />
          </div>
          <footer><span>学生工作台</span><strong>从系统入口直接进入三维解剖室</strong></footer>
        </article>

        <article class="showcase-report">
          <div class="showcase-frame">
            <img :src="teacherDashboardImage" alt="教师工作台实景" loading="lazy" />
          </div>
          <footer><span>教师工作台</span><strong>维护教学依据，配置题型与提示词</strong></footer>
        </article>

        <aside class="showcase-evidence" aria-label="可追溯证据链">
          <div class="evidence-statement">
            <Network :size="28" />
            <p>每个结构都连接三维模型、规范解剖名、教材依据与知识图谱。</p>
          </div>
          <div class="evidence-chain" aria-label="证据链组成">
            <span><i aria-hidden="true"></i><strong>三维模型</strong><small>可点击的结构</small></span>
            <span><i aria-hidden="true"></i><strong>规范术语</strong><small>中英解剖名对照</small></span>
            <span><i aria-hidden="true"></i><strong>教材依据</strong><small>章节与页码</small></span>
            <span><i aria-hidden="true"></i><strong>知识图谱</strong><small>连接临床联系</small></span>
          </div>
        </aside>
      </div>
    </section>

    <section id="workflow" class="landing-workflow reveal">
      <div class="workflow-intro landing-section-head">
        <span class="landing-section-kicker">学习路径</span>
        <h2>一次学习，从整体人体走到一个具体结构。</h2>
        <p class="landing-section-lede">从选择系统到精细结构，每一步都保留教材依据与可回看的训练记录。</p>
      </div>
      <div class="workflow-track">
        <article>
          <Layers3 :size="24" />
          <strong>选择系统</strong>
          <p>从整体人体进入运动、循环、呼吸、消化等八大系统，镜头自动框到该系统。</p>
        </article>
        <article>
          <ScanLine :size="24" />
          <strong>下钻器官</strong>
          <p>在系统内继续选择器官，例如心脏、肺、肝、肾，放大成独立的三维标本。</p>
        </article>
        <article>
          <MousePointer2 :size="24" />
          <strong>点选精细结构</strong>
          <p>点选心腔、瓣膜等精细结构，查看规范中文解剖名、英文原名与功能讲解。</p>
        </article>
        <article>
          <Crosshair :size="24" />
          <strong>测验与溯源</strong>
          <p>完成选择、判断与简答，讲解命中教材时给出书名、章节与页码。</p>
        </article>
      </div>
    </section>

    <section id="entry" class="landing-entry reveal">
      <div class="entry-heading landing-section-head">
        <span class="landing-section-kicker">进入平台</span>
        <h2>选择身份，进入各自的工作空间。</h2>
        <p>学生探索三维结构并完成测验，教师维护教学依据并决定命题方式，管理员治理数据与索引。</p>
      </div>

      <div class="entry-stage">
        <div class="role-choice" aria-label="选择平台身份">
          <button type="button" :class="{ active: selectedRole === 'student' }" :aria-pressed="selectedRole === 'student'" @click="selectedRole = 'student'">
            <GraduationCap :size="22" />
            <span><strong>医学生</strong><small>结构与定位训练</small></span>
          </button>
          <button type="button" :class="{ active: selectedRole === 'teacher' }" :aria-pressed="selectedRole === 'teacher'" @click="selectedRole = 'teacher'">
            <Users :size="22" />
            <span><strong>医学教师</strong><small>知识库与命题</small></span>
          </button>
          <button type="button" :class="{ active: selectedRole === 'admin' }" :aria-pressed="selectedRole === 'admin'" @click="selectedRole = 'admin'">
            <ShieldCheck :size="22" />
            <span><strong>超级管理员</strong><small>数据源与索引</small></span>
          </button>
        </div>

        <aside class="entry-console">
          <span>{{ roleContent.title }}</span>
          <h3>{{ roleContent.description }}</h3>
          <ul>
            <li v-for="feature in roleContent.features" :key="feature"><FileCheck2 :size="16" /> {{ feature }}</li>
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

    <footer class="landing-footer">
      <div class="brand-lockup">
        <BrandLogo variant="compact" subtitle="可追溯的虚拟解剖实验室" />
      </div>
      <p><ShieldCheck :size="16" /> 三维模型与讲解仅用于医学教育，不作为临床诊断依据。</p>
    </footer>
  </main>
</template>
