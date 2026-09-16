// Geometry source: BodyParts3D 4.0 (CC BY 4.0), packed by the MIT-licensed
// `ashemag/human-atlas` project and re-chunked by
// `backend/scripts/prepare_anatomy_models.py`.

export interface AtlasPart {
  id: string;
  name: string;
  conceptId: string;
  system: string;
  chunk: number;
  positions: number;
  normals: number;
  indices: number;
  vertexCount: number;
  indexCount: number;
  bounds: [number[], number[]];
}

export interface AtlasConcept {
  id: string;
  name: string;
  elements: string[];
}

export interface AtlasChunk {
  url: string;
  bytes: number;
  system: string;
}

export interface Atlas3D {
  version: string;
  sex?: string;
  source?: string;
  scope?: string;
  parts: AtlasPart[];
  concepts: AtlasConcept[];
  chunks: AtlasChunk[];
  triangles: number;
}

export interface AnatomySystem3D {
  id: string;
  name: string;
  color: string;
  summary: string;
  /** Data-system ids merged into this teaching system. */
  members: string[];
}

export const ATLAS_3D_URL = '/anatomy/atlas.json';
export const ATLAS_ORGAN_URL = '/anatomy/organs.json';

export interface AnatomyOrgan {
  id: string;
  name: string;
  nameEn: string;
  system: string;
  partIds: string[];
}

export interface AnatomyOrganGroup {
  system: string;
  organs: AnatomyOrgan[];
}

export interface AnatomyOrganPayload {
  source: string;
  systems: AnatomyOrganGroup[];
}

/** Render colours keyed by the atlas data systems. */
export const ANATOMY_DATA_SYSTEM_COLORS: Record<string, string> = {
  skeletal: '#ded4b4',
  cardiac: '#c2564e',
  arterial: '#cf5a4a',
  venous: '#5b83a8',
  respiratory: '#c98a96',
  digestive: '#b98a5e',
  urinary: '#b5795f',
  reproductive: '#b08ea6',
  nervous: '#d3ab4f',
  endocrine: '#bd8fa0',
  lymphatic: '#7f9c72'
};

/** The systems a systematic anatomy course is organised around. */
export const ANATOMY_SYSTEMS_3D: AnatomySystem3D[] = [
  { id: 'locomotor', name: '运动系统', color: '#ded4b4', members: ['skeletal'], summary: '骨构成人体支架，保护器官并提供肌肉附着点，是定位其他结构的参照。' },
  { id: 'circulatory', name: '循环系统', color: '#c2564e', members: ['cardiac', 'arterial', 'venous'], summary: '心脏为动力泵，动脉将血液输送到组织，静脉把血液送回心房。' },
  { id: 'respiratory', name: '呼吸系统', color: '#c98a96', members: ['respiratory'], summary: '气道将空气送达肺泡，在此完成氧气与二氧化碳的交换。' },
  { id: 'digestive', name: '消化系统', color: '#b98a5e', members: ['digestive'], summary: '消化管分解食物并吸收营养，附属器官分泌胆汁与消化酶。' },
  { id: 'urinary', name: '泌尿系统', color: '#b5795f', members: ['urinary'], summary: '肾脏滤过血液并调节水电解质平衡，尿液经输尿管、膀胱排出。' },
  { id: 'reproductive', name: '生殖系统', color: '#b08ea6', members: ['reproductive'], summary: '本例为男性参考解剖，显示生殖腺与输送管道的位置关系。' },
  { id: 'nervous', name: '神经系统', color: '#d3ab4f', members: ['nervous'], summary: '脑与脑神经传导并处理信号，身体的感受与运动由神经系统协调。' },
  { id: 'endocrine', name: '内分泌系统', color: '#bd8fa0', members: ['endocrine'], summary: '内分泌器官分泌激素入血，调控代谢、生长与应激反应。' },
  { id: 'lymphatic', name: '淋巴系统', color: '#7f9c72', members: ['lymphatic'], summary: '淋巴管回收组织液，淋巴器官参与免疫监视与应答。' }
];

export const ANATOMY_SYSTEM_3D_BY_ID: Record<string, AnatomySystem3D> = Object.fromEntries(
  ANATOMY_SYSTEMS_3D.map((system) => [system.id, system])
);

/** Resolve the teaching system that owns a raw atlas data system. */
export function displaySystemOf(dataSystem: string): AnatomySystem3D | undefined {
  return ANATOMY_SYSTEMS_3D.find((system) => system.members.includes(dataSystem));
}

export function system3DName(dataSystem: string): string {
  return displaySystemOf(dataSystem)?.name ?? dataSystem;
}

export function system3DColor(dataSystem: string): string {
  return ANATOMY_DATA_SYSTEM_COLORS[dataSystem] ?? '#b9c4c6';
}
