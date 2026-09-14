<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import {
  Activity,
  ArrowRight,
  BookOpenCheck,
  BrainCircuit,
  ChartNoAxesColumnIncreasing,
  FileCheck2,
  GraduationCap,
  MousePointer2,
  Network,
  ShieldCheck,
  Stethoscope,
  UserRoundCheck,
  Users
} from '@lucide/vue';
import AgentCommand from '../components/AgentCommand.vue';
import teacherMentorImage from '../assets/medical/teacher-mentor-hero.png';
import dashboardImage from '../assets/showcase/student-dashboard-hd.png';
import reportImage from '../assets/showcase/training-report-hd.png';
import teacherReportsImage from '../assets/showcase/teacher-reports-hd.png';
import type { WorkspaceRole } from '../stores/training';

const router = useRouter();
const selectedRole = ref<WorkspaceRole>('student');
let revealObserver: IntersectionObserver | null = null;

const roleContent = computed(() => {
  if (selectedRole.value === 'teacher') {
    return {
      title: '教师教学空间',
      description: '复核训练报告，定位班级薄弱项，把 AI 评分转化为下一次教学行动。',
      action: '进入教师工作台',
      features: ['班级复盘', '报告复核', '教学建议']
    };
  }
  if (selectedRole.value === 'admin') {
    return {
      title: '系统控制台',
      description: '管理数据源、知识图谱与 Agent 策略，保持训练边界清晰且可追溯。',
      action: '进入管理员工作台',
      features: ['数据源管理', '图谱状态', '策略控制']
    };
  }
  return {
    title: '虚拟解剖实验室',
    description: '在三维人体结构中观察、定位和追溯教材依据，再进入病例训练检验临床联系。',
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
        <span class="brand-mark">临</span>
        <span><strong>临思智训</strong><small>AI标准化病人临床思维训练平台</small></span>
      </a>
      <nav aria-label="落地页导航">
        <a href="#showcase">产品实景</a>
        <a href="#workflow">训练闭环</a>
        <a href="#entry">进入平台</a>
      </nav>
      <button class="landing-nav-action" type="button" @click="scrollToEntry">
        开始训练 <ArrowRight :size="16" />
      </button>
    </header>

    <section id="top" class="landing-hero">
      <div class="landing-hero-copy">
        <h1>把人体结构<br /><em>变成可探索的空间</em></h1>
        <p>虚拟解剖实验室连接三维模型、教材证据、AI讲解和定位测验。</p>
        <div class="landing-hero-actions">
          <button class="landing-primary" type="button" @click="scrollToEntry">
            开始训练 <ArrowRight :size="19" />
          </button>
          <a class="landing-secondary" href="#showcase">查看产品实景</a>
        </div>
      </div>

      <figure class="landing-hero-media" aria-label="AI医学教学导师与临床训练界面">
        <img :src="teacherMentorImage" alt="AI医学教学导师在临床模拟界面中讲解病例" />
        <figcaption>
          <span class="live-state"><Activity :size="16" /> AnatomyAgent 已就绪</span>
          <strong>虚拟解剖实验室</strong>
          <small>所有内容用于医学教育训练，不用于真实临床诊断。</small>
        </figcaption>
      </figure>
    </section>

    <section class="capability-rail" aria-label="平台核心能力">
      <article><ScanLine :size="21" /><span><strong>三维结构探索</strong><small>系统到精细结构</small></span></article>
      <article><MousePointer2 :size="21" /><span><strong>热点交互定位</strong><small>点击即看结构说明</small></span></article>
      <article><BookOpenCheck :size="21" /><span><strong>教材依据可追溯</strong><small>章节与页码定位</small></span></article>
      <article><UserRoundCheck :size="21" /><span><strong>教师在环复核</strong><small>AI 不替代教学判断</small></span></article>
    </section>

    <section id="showcase" class="landing-showcase reveal">
      <header>
        <h2>不是概念片，是一套跑得通的训练产品。</h2>

      </header>

      <div class="showcase-grid">
        <article class="showcase-main">
          <div class="showcase-frame">
            <img :src="dashboardImage" alt="学生训练工作台实景" loading="lazy" />
          </div>
          <footer><span>学生工作台</span><strong>从今日任务直接进入病例训练</strong></footer>
        </article>

        <article class="showcase-report">
          <div class="showcase-frame">
            <img :src="reportImage" alt="临床思维训练报告实景" loading="lazy" />
          </div>
          <footer><span>训练报告</span><strong>把思维过程变成可复盘证据</strong></footer>
        </article>

        <article class="showcase-teacher">
          <div class="showcase-frame">
            <img :src="teacherReportsImage" alt="教师报告复核工作台实景" loading="lazy" />
          </div>
          <footer><span>教师复核</span><strong>定位班级薄弱项，形成教学行动</strong></footer>
        </article>

        <aside class="showcase-evidence" aria-label="病例训练证据链">
          <div class="evidence-statement">
            <Network :size="28" />
            <p>每个病例都连接患者脚本、评分量表、指南证据与知识图谱。</p>
          </div>
          <div class="evidence-chain" aria-label="证据链组成">
            <span><i aria-hidden="true"></i><strong>患者脚本</strong><small>约束患者表达</small></span>
            <span><i aria-hidden="true"></i><strong>评分量表</strong><small>记录推理过程</small></span>
            <span><i aria-hidden="true"></i><strong>指南证据</strong><small>支持反馈溯源</small></span>
            <span><i aria-hidden="true"></i><strong>知识图谱</strong><small>连接训练路径</small></span>
          </div>
        </aside>
      </div>
    </section>

    <section id="workflow" class="landing-workflow reveal">
      <div class="workflow-intro">
        <h2>一次训练，完成一次可解释的能力闭环。</h2>

      </div>
      <div class="workflow-track">
        <article>
          <Stethoscope :size="24" />
          <strong>进入病例</strong>
          <p>从胸痛、腹痛、发热与呼吸困难等虚拟教学病例开始。</p>
        </article>
        <article>
          <BrainCircuit :size="24" />
          <strong>展开推理</strong>
          <p>边问诊边记录鉴别诊断、检查选择与风险判断。</p>
        </article>
        <article>
          <FileCheck2 :size="24" />
          <strong>获得反馈</strong>
          <p>评分对应遗漏点与指南证据，教师可以继续复核。</p>
        </article>
        <article>
          <ChartNoAxesColumnIncreasing :size="24" />
          <strong>形成路径</strong>
          <p>训练报告进入每日复盘，并生成下一次学习建议。</p>
        </article>
      </div>
    </section>

    <section id="entry" class="landing-entry reveal">
      <div class="entry-heading">
        <h2>选择身份，进入真正不同的工作空间。</h2>
        <p>学生练习临床推理，教师完成教学复核，管理员维护可信数据与 Agent 边界。</p>
      </div>

      <div class="entry-stage">
        <div class="role-choice" aria-label="选择平台身份">
          <button type="button" :class="{ active: selectedRole === 'student' }" :aria-pressed="selectedRole === 'student'" @click="selectedRole = 'student'">
            <GraduationCap :size="22" />
            <span><strong>医学生</strong><small>训练与能力提升</small></span>
          </button>
          <button type="button" :class="{ active: selectedRole === 'teacher' }" :aria-pressed="selectedRole === 'teacher'" @click="selectedRole = 'teacher'">
            <Users :size="22" />
            <span><strong>医学教师</strong><small>复核与教学分析</small></span>
          </button>
          <button type="button" :class="{ active: selectedRole === 'admin' }" :aria-pressed="selectedRole === 'admin'" @click="selectedRole = 'admin'">
            <ShieldCheck :size="22" />
            <span><strong>超级管理员</strong><small>策略与系统控制</small></span>
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
        <span><strong>也可以直接告诉智能体</strong><small>例如：“带我去胸痛病例训练”</small></span>
        <AgentCommand />
      </div>
    </section>

    <footer class="landing-footer">
      <div class="brand-lockup">
        <span class="brand-mark">临</span>
        <span><strong>临思智训</strong><small>AI标准化病人临床思维训练平台</small></span>
      </div>
      <p><ShieldCheck :size="16" /> 虚拟教学病例，不含真实患者数据，不用于真实临床诊断。</p>
    </footer>
  </main>
</template>
