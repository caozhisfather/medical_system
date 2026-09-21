import type { WorkspaceRole } from '../stores/training';

const version = 'v4-role-workflow';

export type TourPlacement = 'auto' | 'top' | 'bottom' | 'left' | 'right';

export interface TourStepConfig {
  id: string;
  route: string;
  target: string;
  eyebrow: string;
  title: string;
  body: string;
  placement?: TourPlacement;
}

export const tourSteps: Record<WorkspaceRole, TourStepConfig[]> = {
  student: [
    {
      id: 'dashboard',
      route: '/student/dashboard',
      target: '[data-tour="today-task"]',
      eyebrow: '学习总览',
      title: '从今日任务开始',
      body: '这里汇总八大系统入口、今日推荐任务与学习进度。第一次使用可以先按推荐路径进入虚拟解剖室。',
      placement: 'bottom'
    },
    {
      id: 'anatomy-modes',
      route: '/student/anatomy',
      target: '[data-tour="anatomy-mode-switch"]',
      eyebrow: '虚拟解剖室',
      title: '三种模式对应三种学习方式',
      body: '三维人体用于探索结构和教材依据；图谱分层用于系统、器官、精细结构逐层浏览；空间定位用于检验定位能力。',
      placement: 'bottom'
    },
    {
      id: 'textbook-study',
      route: '/student/anatomy',
      target: '[data-tour="anatomy-workspace"]',
      eyebrow: '教材阅读',
      title: '教材可以放大、勾画和做笔记',
      body: '选中结构后点击“教材详解”。学生可以放大教材页、使用画笔或荧光笔勾画，并在旁边记录笔记；标注会按账号自动保存。',
      placement: 'left'
    },
    {
      id: 'practice',
      route: '/student/anatomy?mode=practice',
      target: '[data-tour="anatomy-practice-workspace"]',
      eyebrow: '空间定位测验',
      title: '在二维图上完成定位',
      body: '题目会显示器官或精细结构图。点击你认为正确的位置，提交后立即得到评分和标准区域。',
      placement: 'left'
    },
    {
      id: 'archive',
      route: '/student/archive',
      target: '[data-tour="archive-tabs"]',
      eyebrow: '学习档案',
      title: '每次得分和错题都会留存',
      body: '测验记录显示每次作答、得分和正确率；错题本按结构聚合错误次数，方便安排下一次复习。',
      placement: 'bottom'
    },
    {
      id: 'graph',
      route: '/knowledge-graph',
      target: '[data-tour="graph-stage"]',
      eyebrow: '知识图谱',
      title: '把结构与临床联系起来',
      body: '从解剖结构继续查看功能、疾病、检查和病例关系。图谱用于理解知识之间的连接，不替代教材原文。',
      placement: 'right'
    }
  ],
  teacher: [
    {
      id: 'teacher-dashboard',
      route: '/teacher/dashboard',
      target: '[data-tour="teacher-dashboard-hero"]',
      eyebrow: '教学总览',
      title: '先看当前教学状态',
      body: '这里汇总知识库规模、资料处理状态、题型配置与系统提示词摘要，帮助教师确定下一步维护重点。',
      placement: 'bottom'
    },
    {
      id: 'knowledge-library',
      route: '/teacher/knowledge',
      target: '[data-tour="knowledge-library-toolbar"]',
      eyebrow: '教学知识库',
      title: '维护教材与医学依据',
      body: '上传教材、指南和病例资料，按资料类型筛选与检查入库状态。教材会优先用于学生讲解和引用。',
      placement: 'bottom'
    },
    {
      id: 'exam-types',
      route: '/teacher/exam-settings',
      target: '[data-tour="exam-question-types"]',
      eyebrow: '测验配置',
      title: '配置题型、选项和权重',
      body: '教师可以决定启用选择题、判断题或简答题，并设置选项数量和各类题型权重。',
      placement: 'bottom'
    },
    {
      id: 'exam-prompt',
      route: '/teacher/exam-settings',
      target: '[data-tour="exam-prompt"]',
      eyebrow: '命题策略',
      title: '统一出题提示词',
      body: '系统提示词约束题干风格、难度和证据范围。修改并保存后即时影响后续生成。',
      placement: 'top'
    },
    {
      id: 'teacher-graph',
      route: '/knowledge-graph',
      target: '[data-tour="graph-stage"]',
      eyebrow: '知识图谱',
      title: '检查结构与关系完整性',
      body: '通过图谱检查解剖结构、功能、疾病和检查之间是否存在缺失连接，为后续资料补录提供依据。',
      placement: 'right'
    }
  ],
  admin: [
    {
      id: 'admin-console',
      route: '/admin/dashboard',
      target: '[data-tour="admin-console"]',
      eyebrow: '管理控制台',
      title: '从系统运行状态开始',
      body: '先确认服务状态、用户审核和关键配置，再进入数据源、知识与图谱维护。',
      placement: 'bottom'
    },
    {
      id: 'admin-knowledge',
      route: '/admin/dashboard',
      target: '[data-tour="admin-knowledge"]',
      eyebrow: '知识库状态',
      title: '检查索引与向量状态',
      body: '查看知识条目、已经完成向量化的数量，以及教学资料是否可以正常参与检索。',
      placement: 'bottom'
    },
    {
      id: 'admin-sources',
      route: '/admin/dashboard',
      target: '[data-tour="admin-data-source"]',
      eyebrow: '数据源管理',
      title: '确认外部与本地数据源',
      body: '检查数据源连接、同步和处理状态。资料入库质量会直接影响教材证据和模型讲解。',
      placement: 'top'
    },
    {
      id: 'admin-graph',
      route: '/admin/dashboard',
      target: '[data-tour="admin-graph"]',
      eyebrow: '图谱管理',
      title: '检查节点与关系规模',
      body: '关注节点、关系和中英翻译完整度，发现缺失时再安排知识库补录。',
      placement: 'bottom'
    },
    {
      id: 'admin-policy',
      route: '/admin/dashboard',
      target: '[data-tour="admin-review-policy"]',
      eyebrow: '复盘策略',
      title: '配置每日复盘生成规则',
      body: '设置推荐数量、评分权重、数字人复盘和教师关注提醒。策略修改影响后续自动生成结果。',
      placement: 'top'
    },
    {
      id: 'admin-debug',
      route: '/admin/dashboard',
      target: '[data-tour="admin-debug"]',
      eyebrow: '系统调试',
      title: '检查 Agent 与接口状态',
      body: '查看工作流执行情况、接口响应和故障信息，用于定位外部模型或本地服务问题。',
      placement: 'top'
    }
  ]
};

export function onboardingKey(role: WorkspaceRole) {
  return `medical_onboarding_${version}_${role}`;
}

export function shouldShowOnboarding(role: WorkspaceRole) {
  return localStorage.getItem(onboardingKey(role)) !== 'done';
}

export function completeOnboarding(role: WorkspaceRole) {
  localStorage.setItem(onboardingKey(role), 'done');
}

export function resetOnboarding(role: WorkspaceRole) {
  localStorage.removeItem(onboardingKey(role));
}
