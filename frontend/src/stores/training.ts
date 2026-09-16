import { reactive } from 'vue';
import { login } from '../api';

export type WorkspaceRole = 'student' | 'teacher' | 'admin';

export interface UserProfile {
  role: WorkspaceRole;
  name: string;
  school: string;
  grade: string;
  specialty: string;
  className: string;
  direction: string;
  completed: boolean;
}

const defaultProfile: UserProfile = {
  role: 'student',
  name: '陈同学',
  school: '东部医科大学',
  grade: '临床医学四年级',
  specialty: '临床医学',
  className: '临床医学 2023-2 班',
  direction: '虚拟解剖与空间定位',
  completed: false
};

function readStored<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) as T : fallback;
  } catch {
    return fallback;
  }
}

function persist(key: string, value: unknown) {
  localStorage.setItem(key, JSON.stringify(value));
}

function hasStoredSession() {
  return Boolean(localStorage.getItem('medical_auth_token')) || readStored('medical_auth', false);
}

const state = reactive({
  authenticated: hasStoredSession(),
  profile: readStored<UserProfile>('medical_profile', defaultProfile)
});

export const trainingStore = {
  state,

  signIn(role: WorkspaceRole) {
    state.authenticated = true;
    state.profile = { ...state.profile, role };
    if (import.meta.env.DEV) {
      const demoTokens: Record<WorkspaceRole, string> = {
        student: 'mock-student-student01-token',
        teacher: 'mock-teacher-teacher01-token',
        admin: 'mock-super_admin-admin-token'
      };
      localStorage.setItem('medical_auth_token', demoTokens[role]);
    }
    persist('medical_auth', true);
    persist('medical_profile', state.profile);
  },

  async authenticate(account: string, password: string, role: WorkspaceRole, rememberAccount = true) {
    let response;
    try {
      response = await login(account, password, role);
    } catch (error) {
      if (error instanceof TypeError) throw new Error('登录服务暂时无法连接，请确认后端服务已启动。');
      throw error;
    }
    const responseRole: WorkspaceRole = response.user.role === 'super_admin' ? 'admin' : response.user.role as WorkspaceRole;
    if (responseRole !== role) throw new Error('该账号不属于当前选择的身份，请切换身份后重试。');
    const roleProfile = role === 'teacher'
      ? { grade: response.user.department || '解剖学教研室', specialty: '解剖学与临床技能', className: '临床医学 2023-2 班', direction: '解剖教学与命题' }
      : role === 'admin'
        ? { grade: response.user.department || '系统管理中心', specialty: '平台运维与知识工程', className: '全校医学教学空间', direction: '数据源与知识库治理' }
        : { grade: response.user.department || '临床医学四年级', specialty: '临床医学', className: '临床医学 2023-2 班', direction: '虚拟解剖与空间定位' };
    state.authenticated = true;
    state.profile = { ...state.profile, ...roleProfile, role, name: response.user.name, completed: true };
    localStorage.setItem('medical_auth_token', response.token);
    persist('medical_auth', true);
    persist('medical_profile', state.profile);
    if (rememberAccount) localStorage.setItem(`medical_login_account_${role}`, account);
    else localStorage.removeItem(`medical_login_account_${role}`);
    return response;
  },

  signOut() {
    state.authenticated = false;
    localStorage.removeItem('medical_auth_token');
    persist('medical_auth', false);
  },

  saveProfile(profile: Partial<UserProfile>) {
    state.profile = { ...state.profile, ...profile, completed: true };
    persist('medical_profile', state.profile);
  }
};
