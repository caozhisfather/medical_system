import type { WorkspaceRole } from '../stores/training';

const version = 'v2-daily-review';

export interface TourStepConfig {
  target: string;
  title: string;
  body: string;
}

export const tourSteps: Record<WorkspaceRole, TourStepConfig[]> = {
  student: [
    { target: '[data-tour="today-task"]', title: '今日任务', body: '查看今天推荐病例和学习目标。' },
    { target: '[data-tour="case-training"]', title: '病例训练', body: '选择病例，与 AI 标准化病人问诊。' },
    { target: '[data-tour="evidence"]', title: '指南依据', body: '查看 AI 反馈引用的教材和指南。' },
    { target: '[data-tour="knowledge-graph"]', title: '知识图谱', body: '沿症状、疾病、检查和解剖结构建立学习路径。' },
    { target: '[data-tour="daily-review"]', title: '每日复盘', body: '训练结束后查看 AI 生成的复盘和明日计划。' },
    { target: '[data-tour="digital-human"]', title: '数字人导师', body: '让 AI 导师讲解薄弱点。' }
  ],
  teacher: [
    { target: '[data-tour="teacher-dashboard"]', title: '班级看板', body: '查看班级整体训练表现。' },
    { target: '[data-tour="student-alert"]', title: '学生预警', body: '定位需要干预的学生。' },
    { target: '[data-tour="common-weakness"]', title: '共性问题', body: '查看班级薄弱知识点。' },
    { target: '[data-tour="case-management"]', title: '病例管理', body: '维护病例脚本和评分点。' },
    { target: '[data-tour="class-review"]', title: '班级复盘', body: '查看 AI 生成的教学建议。' }
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
