import type { WorkspaceRole } from '../stores/training';

const version = 'v3-anatomy-lab';

export interface TourStepConfig {
  target: string;
  title: string;
  body: string;
}

export const tourSteps: Record<WorkspaceRole, TourStepConfig[]> = {
  student: [
    { target: '[data-tour="today-task"]', title: '学习总览', body: '查看八大系统入口与今日推荐的学习路径。' },
    { target: '[data-tour="anatomy-lab"]', title: '虚拟解剖室', body: '按“整体人体 → 系统 → 器官 → 精细结构”逐层探索三维模型。' },
    { target: '[data-tour="evidence"]', title: '教材依据', body: '选中结构后查看讲解引用的教材章节与页码。' },
    { target: '[data-tour="knowledge-graph"]', title: '知识图谱', body: '沿结构与功能、临床联系建立学习路径。' },
    { target: '[data-tour="daily-review"]', title: '学习档案', body: '查看空间定位测验的作答记录与错题。' }
  ],
  teacher: [
    { target: '[data-tour="teacher-dashboard"]', title: '教学总览', body: '查看知识库规模、索引状态与练习概况。' },
    { target: '[data-tour="case-management"]', title: '教学知识库', body: '导入教材与权威依据，作为讲解与命题的来源。' },
    { target: '[data-tour="exam-settings"]', title: '题型与提示词', body: '决定启用哪些题型与选项数，并编辑出题的系统提示词。' },
    { target: '[data-tour="teacher-graph"]', title: '知识图谱', body: '检查结构节点与关系是否完整。' }
  ],
  admin: [
    { target: '[data-tour="admin-data-source"]', title: '数据源管理', body: '查看 ModelScope、知识库和指南数据源。' },
    { target: '[data-tour="admin-knowledge"]', title: '知识库状态', body: '查看 embedding 和索引情况。' },
    { target: '[data-tour="admin-graph"]', title: '图谱管理', body: '查看节点、关系和中英翻译完整率。' },
    { target: '[data-tour="admin-review-policy"]', title: '复盘策略', body: '配置每日复盘生成逻辑。' },
    { target: '[data-tour="admin-debug"]', title: '系统调试', body: '查看 Agent 工作流日志和接口状态。' }
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
