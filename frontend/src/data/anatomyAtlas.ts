import heartOverview from '../assets/medical/anatomy/heart-chambers-valves.svg';
import heartDetail from '../assets/medical/anatomy/heart-chambers-detail.svg';
import digestiveOverview from '../assets/medical/anatomy/digestive-system-overview.svg';
import duodenumDetail from '../assets/medical/anatomy/duodenum-detail.jpg';
import largeIntestineDetail from '../assets/medical/anatomy/large-intestine-detail.png';
import rectumDetail from '../assets/medical/anatomy/rectum-detail.svg';
import skeletalOverview from '../assets/medical/anatomy/skeletal-system-overview.webp';
import respiratoryOverview from '../assets/medical/anatomy/respiratory-system-overview.webp';
import kidneyOverview from '../assets/medical/anatomy/kidney-overview.webp';
import maleReproductiveOverview from '../assets/medical/anatomy/male-reproductive-overview.webp';
import femaleReproductiveOverview from '../assets/medical/anatomy/female-reproductive-overview.webp';
import nervousOverview from '../assets/medical/anatomy/nervous-system-overview.webp';
import endocrineOverview from '../assets/medical/anatomy/endocrine-system-overview.webp';
import type { AnatomySystemName } from './anatomyResources';

export interface AnatomyAtlasHotspot {
  id: string;
  label: string;
  x: number;
  y: number;
  width: number;
  height: number;
  target_id?: string;
  structure_id?: string;
}

export interface AnatomyAtlasStructure {
  id: string;
  name: string;
  category: string;
  description: string;
  clinical_note: string;
}

export interface AnatomyAtlasNode {
  id: string;
  system: AnatomySystemName;
  title: string;
  subtitle: string;
  level: 'system' | 'organ';
  parent_id?: string;
  image: string;
  image_aspect: string;
  description: string;
  instruction: string;
  hotspots: AnatomyAtlasHotspot[];
  structures: AnatomyAtlasStructure[];
  source_label: string;
}

export const anatomyAtlasNodes: AnatomyAtlasNode[] = [
  {
    id: 'skeletal_overview',
    system: '运动系统',
    title: '全身骨骼系统总览',
    subtitle: '从中轴骨与附肢骨进入主要骨骼区域',
    level: 'system',
    image: skeletalOverview,
    image_aspect: '1600 / 1600',
    description: '骨骼系统由中轴骨和附肢骨组成，为身体提供支撑、保护和运动杠杆。点击热点认识主要骨骼区域。',
    instruction: '点击颅骨、胸廓、脊柱、骨盆或四肢区域',
    hotspots: [
      { id: 'bone_skull_hs', label: '颅骨', x: 25, y: 8, width: 13, height: 12, structure_id: 'bone_skull' },
      { id: 'bone_thorax_hs', label: '胸廓', x: 25, y: 27, width: 22, height: 22, structure_id: 'bone_thorax' },
      { id: 'bone_spine_hs', label: '脊柱', x: 74, y: 34, width: 12, height: 37, structure_id: 'bone_spine' },
      { id: 'bone_pelvis_hs', label: '骨盆', x: 25, y: 47, width: 22, height: 16, structure_id: 'bone_pelvis' },
      { id: 'bone_upper_limb_hs', label: '上肢骨', x: 10, y: 37, width: 15, height: 40, structure_id: 'bone_upper_limb' },
      { id: 'bone_lower_limb_hs', label: '下肢骨', x: 25, y: 75, width: 23, height: 45, structure_id: 'bone_lower_limb' }
    ],
    structures: [
      { id: 'bone_skull', name: '颅骨', category: '中轴骨', description: '包括脑颅骨和面颅骨，构成颅腔并支撑面部结构。', clinical_note: '颅骨骨折需要结合骨缝、颅底孔裂及神经血管走行判断风险。' },
      { id: 'bone_thorax', name: '胸廓', category: '中轴骨', description: '由胸椎、肋骨和胸骨共同组成，保护心肺。', clinical_note: '肋骨骨折可能影响通气并损伤胸膜或肺。' },
      { id: 'bone_spine', name: '脊柱', category: '中轴骨', description: '由颈、胸、腰椎以及骶骨和尾骨组成。', clinical_note: '脊柱损伤评估需关注稳定性和脊髓受压。' },
      { id: 'bone_pelvis', name: '骨盆', category: '附肢骨', description: '由髋骨、骶骨和尾骨构成，连接躯干与下肢。', clinical_note: '骨盆骨折可能伴随大量出血和盆腔脏器损伤。' },
      { id: 'bone_upper_limb', name: '上肢骨', category: '附肢骨', description: '包括肩带、肱骨、尺桡骨和手骨。', clinical_note: '关节周围骨性标志是体格检查和影像定位的重要依据。' },
      { id: 'bone_lower_limb', name: '下肢骨', category: '附肢骨', description: '包括骨盆带、股骨、髌骨、胫腓骨和足骨。', clinical_note: '股骨颈和踝部骨折需要评估血供、负重与关节稳定性。' }
    ],
    source_label: 'OpenStax · Figure 7.2 · CC BY-NC-SA 4.0'
  },
  {
    id: 'respiratory_overview',
    system: '呼吸系统',
    title: '呼吸系统分层总览',
    subtitle: '从上气道进入气管、支气管、肺与膈',
    level: 'system',
    image: respiratoryOverview,
    image_aspect: '1680 / 1416',
    description: '呼吸系统由上呼吸道和下呼吸道组成，空气经鼻腔、咽、喉、气管和支气管到达肺泡。',
    instruction: '点击气道、肺或膈肌区域查看说明',
    hotspots: [
      { id: 'resp_nose_hs', label: '鼻腔与咽', x: 39, y: 24, width: 24, height: 20, structure_id: 'resp_upper_airway' },
      { id: 'resp_larynx_hs', label: '喉', x: 45, y: 40, width: 13, height: 12, structure_id: 'resp_larynx' },
      { id: 'resp_trachea_hs', label: '气管', x: 48, y: 54, width: 12, height: 25, structure_id: 'resp_trachea' },
      { id: 'resp_lungs_hs', label: '左右肺', x: 50, y: 72, width: 43, height: 36, structure_id: 'resp_lungs' },
      { id: 'resp_diaphragm_hs', label: '膈肌', x: 56, y: 91, width: 45, height: 10, structure_id: 'resp_diaphragm' }
    ],
    structures: [
      { id: 'resp_upper_airway', name: '鼻腔、咽', category: '上呼吸道', description: '对吸入气体进行过滤、加温和湿化，并作为空气通道。', clinical_note: '上气道阻塞可迅速影响通气，需要优先评估气道通畅。' },
      { id: 'resp_larynx', name: '喉', category: '上呼吸道', description: '连接咽与气管，参与发声并保护下呼吸道。', clinical_note: '会厌和声门区域水肿可能造成危及生命的气道梗阻。' },
      { id: 'resp_trachea', name: '气管与主支气管', category: '下呼吸道', description: '气管在隆嵴处分为左右主支气管。', clinical_note: '右主支气管更短、粗、直，异物更容易进入右侧。' },
      { id: 'resp_lungs', name: '左右肺', category: '呼吸器官', description: '右肺通常分三叶，左肺分两叶，肺泡完成气体交换。', clinical_note: '肺叶和肺段解剖是影像定位及手术切除范围判断的基础。' },
      { id: 'resp_diaphragm', name: '膈肌', category: '呼吸肌', description: '膈肌收缩使胸腔容积增大，是平静呼吸的主要动力。', clinical_note: '膈神经损伤可能造成同侧膈肌运动减弱或矛盾运动。' }
    ],
    source_label: 'OpenStax · Figure 22.2 · CC BY-NC-SA 4.0'
  },
  {
    id: 'urinary_overview',
    system: '泌尿系统',
    title: '肾脏剖面精细图',
    subtitle: '从肾皮质、髓质到肾盂和输尿管',
    level: 'system',
    image: kidneyOverview,
    image_aspect: '1976 / 1123',
    description: '肾脏通过肾单位滤过血液并形成尿液，尿液经肾盏、肾盂和输尿管排出。',
    instruction: '点击肾实质、肾门或集合系统',
    hotspots: [
      { id: 'kidney_cortex_hs', label: '肾皮质', x: 72, y: 76, width: 28, height: 20, structure_id: 'kidney_cortex' },
      { id: 'kidney_medulla_hs', label: '肾髓质', x: 65, y: 54, width: 32, height: 42, structure_id: 'kidney_medulla' },
      { id: 'kidney_pelvis_hs', label: '肾盂肾盏', x: 63, y: 41, width: 25, height: 28, structure_id: 'kidney_pelvis' },
      { id: 'kidney_hilum_hs', label: '肾门', x: 46, y: 51, width: 18, height: 34, structure_id: 'kidney_hilum' },
      { id: 'kidney_ureter_hs', label: '输尿管', x: 45, y: 78, width: 11, height: 36, structure_id: 'kidney_ureter' }
    ],
    structures: [
      { id: 'kidney_cortex', name: '肾皮质', category: '肾实质', description: '位于肾脏外层，包含肾小体和部分肾小管。', clinical_note: '皮质灌注改变可反映肾血流和急性肾损伤风险。' },
      { id: 'kidney_medulla', name: '肾髓质与肾锥体', category: '肾实质', description: '肾锥体由集合管和髓袢等结构组成，尖端形成肾乳头。', clinical_note: '髓质高渗环境对于尿液浓缩至关重要。' },
      { id: 'kidney_pelvis', name: '肾盏与肾盂', category: '集合系统', description: '尿液由肾乳头进入小肾盏、大肾盏，汇入肾盂。', clinical_note: '结石或梗阻可引起肾盂积水。' },
      { id: 'kidney_hilum', name: '肾门', category: '血管神经门户', description: '肾动脉、肾静脉、淋巴管、神经和肾盂由此进出。', clinical_note: '肾门结构层次是手术和影像识别的重要基础。' },
      { id: 'kidney_ureter', name: '输尿管', category: '尿液通道', description: '输尿管由肾盂向下进入膀胱，通过蠕动运输尿液。', clinical_note: '输尿管生理性狭窄是结石常见嵌顿部位。' }
    ],
    source_label: 'OpenStax · Figure 25.8 · CC BY-NC-SA 4.0'
  },
  {
    id: 'male_reproductive_overview',
    system: '生殖系统',
    title: '男性生殖系统总览',
    subtitle: '睾丸、附睾、输精管、前列腺与尿道',
    level: 'system',
    image: maleReproductiveOverview,
    image_aspect: '1445 / 1584',
    description: '男性生殖系统包括生殖腺、生殖管道、附属腺体和外生殖器。可在左侧切换女性生殖系统。',
    instruction: '点击睾丸、输精管、前列腺或外生殖器',
    hotspots: [
      { id: 'male_testis_hs', label: '睾丸与附睾', x: 42, y: 82, width: 23, height: 24, structure_id: 'male_testis' },
      { id: 'male_vas_hs', label: '输精管', x: 40, y: 57, width: 28, height: 14, structure_id: 'male_vas' },
      { id: 'male_prostate_hs', label: '前列腺', x: 53, y: 62, width: 17, height: 14, structure_id: 'male_prostate' },
      { id: 'male_seminal_hs', label: '精囊', x: 62, y: 58, width: 14, height: 15, structure_id: 'male_seminal' },
      { id: 'male_penis_hs', label: '阴茎与尿道', x: 24, y: 78, width: 19, height: 34, structure_id: 'male_penis' }
    ],
    structures: [
      { id: 'male_testis', name: '睾丸与附睾', category: '生殖腺与储精结构', description: '睾丸产生精子和雄激素，精子进入附睾成熟和储存。', clinical_note: '睾丸扭转属于时间敏感性急症。' },
      { id: 'male_vas', name: '输精管', category: '生殖管道', description: '输精管由附睾延续，经腹股沟管进入盆腔。', clinical_note: '输精管走行是男性绝育术和疝修补术的重要解剖依据。' },
      { id: 'male_prostate', name: '前列腺', category: '附属腺', description: '位于膀胱下方，包绕前列腺部尿道。', clinical_note: '前列腺增生可压迫尿道并造成排尿困难。' },
      { id: 'male_seminal', name: '精囊', category: '附属腺', description: '位于膀胱后方，分泌液体参与构成精液。', clinical_note: '精囊与直肠、膀胱的位置关系可在盆腔影像中识别。' },
      { id: 'male_penis', name: '阴茎与海绵体尿道', category: '外生殖器', description: '阴茎含海绵体组织，尿道海绵体内走行海绵体部尿道。', clinical_note: '尿道损伤部位与骨盆或会阴外伤机制相关。' }
    ],
    source_label: 'OpenStax · Figure 27.2 · CC BY-NC-SA 4.0'
  },
  {
    id: 'female_reproductive_overview',
    system: '生殖系统',
    title: '女性生殖系统精细图',
    subtitle: '卵巢、输卵管、子宫、宫颈与阴道',
    level: 'organ',
    parent_id: 'male_reproductive_overview',
    image: femaleReproductiveOverview,
    image_aspect: '1290 / 1792',
    description: '女性生殖系统包括卵巢、输卵管、子宫、阴道和外生殖器，图中展示矢状面与前面观。',
    instruction: '点击子宫、卵巢、输卵管、宫颈或阴道',
    hotspots: [
      { id: 'female_uterus_hs', label: '子宫', x: 45, y: 19, width: 22, height: 20, structure_id: 'female_uterus' },
      { id: 'female_ovary_hs', label: '卵巢', x: 52, y: 24, width: 14, height: 14, structure_id: 'female_ovary' },
      { id: 'female_cervix_hs', label: '宫颈', x: 48, y: 35, width: 14, height: 12, structure_id: 'female_cervix' },
      { id: 'female_vagina_hs', label: '阴道', x: 48, y: 42, width: 15, height: 18, structure_id: 'female_vagina' },
      { id: 'female_tube_hs', label: '输卵管', x: 39, y: 75, width: 33, height: 15, structure_id: 'female_tube' }
    ],
    structures: [
      { id: 'female_uterus', name: '子宫', category: '生殖器官', description: '子宫分为底、体、峡和颈部，肌层参与分娩收缩。', clinical_note: '子宫位置、肌层和内膜是超声及妇科检查的重要观察内容。' },
      { id: 'female_ovary', name: '卵巢', category: '生殖腺', description: '卵巢产生卵母细胞并分泌雌激素、孕激素。', clinical_note: '卵巢扭转可影响血供，需要及时识别。' },
      { id: 'female_tube', name: '输卵管', category: '生殖管道', description: '分为漏斗部、壶腹部、峡部和子宫部。', clinical_note: '异位妊娠最常发生于输卵管。' },
      { id: 'female_cervix', name: '宫颈', category: '子宫下部', description: '连接子宫体和阴道，包含宫颈管和内、外口。', clinical_note: '宫颈转化区是筛查与病变评估的重要区域。' },
      { id: 'female_vagina', name: '阴道', category: '生殖管道', description: '连接宫颈与外生殖器，是肌性管道。', clinical_note: '盆底支持结构受损可能影响阴道和盆腔器官位置。' }
    ],
    source_label: 'OpenStax · Figure 27.9 · CC BY-NC-SA 4.0'
  },
  {
    id: 'nervous_overview',
    system: '神经系统',
    title: '大脑结构总览',
    subtitle: '外侧面与前面观的主要大脑结构',
    level: 'system',
    image: nervousOverview,
    image_aspect: '1081 / 521',
    description: '大脑由左右半球组成，表面为大脑皮质，胼胝体连接两侧半球。',
    instruction: '点击皮质、半球、胼胝体或纵裂区域',
    hotspots: [
      { id: 'brain_cerebrum_hs', label: '大脑', x: 31, y: 43, width: 38, height: 63, structure_id: 'brain_cerebrum' },
      { id: 'brain_cortex_hs', label: '大脑皮质', x: 14, y: 62, width: 20, height: 25, structure_id: 'brain_cortex' },
      { id: 'brain_callosum_hs', label: '胼胝体', x: 25, y: 35, width: 20, height: 20, structure_id: 'brain_callosum' },
      { id: 'brain_hemisphere_hs', label: '左右半球', x: 77, y: 49, width: 36, height: 65, structure_id: 'brain_hemispheres' },
      { id: 'brain_fissure_hs', label: '大脑纵裂', x: 77, y: 19, width: 15, height: 19, structure_id: 'brain_fissure' }
    ],
    structures: [
      { id: 'brain_cerebrum', name: '大脑', category: '中枢神经系统', description: '大脑是高级神经活动的主要结构，包括皮质、白质和皮质下核团。', clinical_note: '局灶性脑损伤可根据功能定位出现运动、感觉、语言或认知障碍。' },
      { id: 'brain_cortex', name: '大脑皮质', category: '灰质', description: '覆盖大脑表面的灰质层，包含多种功能区。', clinical_note: '皮质功能区定位用于解释卒中和癫痫的临床表现。' },
      { id: 'brain_callosum', name: '胼胝体', category: '连合纤维', description: '连接左右大脑半球的主要白质纤维束。', clinical_note: '胼胝体病变可能造成半球间信息传递障碍。' },
      { id: 'brain_hemispheres', name: '左右大脑半球', category: '大脑分区', description: '两侧半球在结构上近似对称，但部分高级功能存在优势侧。', clinical_note: '语言优势半球通常位于左侧，但存在个体差异。' },
      { id: 'brain_fissure', name: '大脑纵裂', category: '表面标志', description: '位于两侧大脑半球之间，内有大脑镰。', clinical_note: '纵裂和主要脑沟是神经影像定位的重要标志。' }
    ],
    source_label: 'OpenStax · The Cerebrum · CC BY-NC-SA 4.0'
  },
  {
    id: 'endocrine_overview',
    system: '内分泌系统',
    title: '内分泌腺体全身分布',
    subtitle: '从下丘脑—垂体到甲状腺、肾上腺、胰腺与性腺',
    level: 'system',
    image: endocrineOverview,
    image_aspect: '1336 / 1488',
    description: '内分泌系统通过激素调节生长、代谢、应激、生殖和内环境稳定。',
    instruction: '点击主要内分泌腺体查看结构与功能',
    hotspots: [
      { id: 'endo_pituitary_hs', label: '下丘脑与垂体', x: 64, y: 12, width: 24, height: 17, structure_id: 'endo_pituitary' },
      { id: 'endo_thyroid_hs', label: '甲状腺/甲状旁腺', x: 64, y: 34, width: 28, height: 20, structure_id: 'endo_thyroid' },
      { id: 'endo_thymus_hs', label: '胸腺', x: 37, y: 42, width: 16, height: 18, structure_id: 'endo_thymus' },
      { id: 'endo_adrenal_hs', label: '肾上腺', x: 36, y: 65, width: 23, height: 14, structure_id: 'endo_adrenal' },
      { id: 'endo_pancreas_hs', label: '胰腺', x: 46, y: 70, width: 27, height: 13, structure_id: 'endo_pancreas' },
      { id: 'endo_gonad_hs', label: '性腺', x: 48, y: 88, width: 29, height: 20, structure_id: 'endo_gonads' }
    ],
    structures: [
      { id: 'endo_pituitary', name: '下丘脑与垂体', category: '中枢内分泌调控', description: '下丘脑通过释放激素和神经联系调节垂体功能。', clinical_note: '垂体占位可能同时造成激素异常和视野缺损。' },
      { id: 'endo_thyroid', name: '甲状腺与甲状旁腺', category: '颈部腺体', description: '甲状腺调节代谢，甲状旁腺主要参与钙磷稳态。', clinical_note: '颈部手术需关注喉返神经及甲状旁腺保护。' },
      { id: 'endo_thymus', name: '胸腺', category: '免疫相关腺体', description: '位于前上纵隔，儿童期较发达，参与T细胞成熟。', clinical_note: '胸腺病变与部分自身免疫疾病存在关联。' },
      { id: 'endo_adrenal', name: '肾上腺', category: '腹膜后腺体', description: '皮质分泌糖皮质激素、盐皮质激素和雄激素，髓质分泌儿茶酚胺。', clinical_note: '肾上腺病变需结合激素水平和影像特征评估。' },
      { id: 'endo_pancreas', name: '胰岛', category: '胰腺内分泌部', description: '胰岛细胞分泌胰岛素、胰高血糖素等激素。', clinical_note: '胰岛素与胰高血糖素共同维持血糖稳态。' },
      { id: 'endo_gonads', name: '卵巢与睾丸', category: '性腺', description: '性腺兼具生殖和内分泌功能，分泌性激素。', clinical_note: '下丘脑—垂体—性腺轴异常可影响青春发育和生殖功能。' }
    ],
    source_label: 'OpenStax · Figure 17.2 · CC BY-NC-SA 4.0'
  },
  {
    id: 'heart_overview',
    system: '循环系统',
    title: '心脏内部结构总览',
    subtitle: '从心腔、瓣膜和血流方向进入精细学习',
    level: 'system',
    image: heartOverview,
    image_aspect: '458 / 481',
    description: '心脏由左右心房、左右心室以及房室瓣和半月瓣组成。点击图中区域进入心腔与瓣膜的精细图。',
    instruction: '点击心房、心室或瓣膜区域进入下一层',
    hotspots: [
      { id: 'heart_atria', label: '左右心房', x: 50, y: 31, width: 58, height: 25, target_id: 'heart_chambers' },
      { id: 'heart_ventricles', label: '左右心室', x: 51, y: 67, width: 61, height: 35, target_id: 'heart_chambers' },
      { id: 'heart_valves', label: '四组瓣膜', x: 50, y: 49, width: 42, height: 24, target_id: 'heart_chambers', structure_id: 'mitral_valve' }
    ],
    structures: [],
    source_label: 'Wikimedia Commons · CC BY-SA 3.0'
  },
  {
    id: 'heart_chambers',
    system: '循环系统',
    title: '心腔与瓣膜精细图',
    subtitle: '第二层：点击单个心腔或瓣膜查看结构说明',
    level: 'organ',
    parent_id: 'heart_overview',
    image: heartDetail,
    image_aspect: '17600 / 14068',
    description: '四个心腔形成串联的肺循环和体循环，四组瓣膜维持单向血流。',
    instruction: '点击带编号的热点查看结构与临床关联',
    hotspots: [
      { id: 'hs_ra', label: '右心房', x: 22, y: 32, width: 22, height: 23, structure_id: 'right_atrium' },
      { id: 'hs_rv', label: '右心室', x: 31, y: 66, width: 27, height: 31, structure_id: 'right_ventricle' },
      { id: 'hs_la', label: '左心房', x: 77, y: 31, width: 23, height: 22, structure_id: 'left_atrium' },
      { id: 'hs_lv', label: '左心室', x: 69, y: 67, width: 28, height: 33, structure_id: 'left_ventricle' },
      { id: 'hs_mv', label: '二尖瓣', x: 62, y: 47, width: 19, height: 14, structure_id: 'mitral_valve' },
      { id: 'hs_tv', label: '三尖瓣', x: 39, y: 47, width: 19, height: 14, structure_id: 'tricuspid_valve' },
      { id: 'hs_semilunar', label: '半月瓣', x: 51, y: 30, width: 22, height: 14, structure_id: 'semilunar_valves' }
    ],
    structures: [
      { id: 'right_atrium', name: '右心房', category: '心腔', description: '接收上、下腔静脉和冠状窦回流的静脉血，并经三尖瓣进入右心室。', clinical_note: '右心房压力升高可表现为颈静脉充盈。' },
      { id: 'right_ventricle', name: '右心室', category: '心腔', description: '经肺动脉瓣将静脉血泵入肺动脉和肺循环。', clinical_note: '肺动脉高压会增加右心室后负荷。' },
      { id: 'left_atrium', name: '左心房', category: '心腔', description: '接收肺静脉回流的含氧血，并经二尖瓣进入左心室。', clinical_note: '房颤患者的血栓形成常与左心耳有关。' },
      { id: 'left_ventricle', name: '左心室', category: '心腔', description: '心肌壁最厚，经主动脉瓣将血液泵入体循环。', clinical_note: '左室射血分数用于评价收缩功能。' },
      { id: 'mitral_valve', name: '二尖瓣', category: '房室瓣', description: '位于左心房和左心室之间，由前、后瓣叶组成。', clinical_note: '二尖瓣狭窄或关闭不全会改变左心房和肺循环压力。' },
      { id: 'tricuspid_valve', name: '三尖瓣', category: '房室瓣', description: '位于右心房和右心室之间，防止心室收缩时血液反流。', clinical_note: '三尖瓣反流可伴右心容量负荷增加。' },
      { id: 'semilunar_valves', name: '主动脉瓣与肺动脉瓣', category: '半月瓣', description: '分别位于左、右心室流出道，防止舒张期大动脉血液回流。', clinical_note: '瓣膜听诊区与瓣膜实际解剖投影并不完全重合。' }
    ],
    source_label: 'Wikimedia Commons · CC BY-SA 4.0'
  },
  {
    id: 'digestive_overview',
    system: '消化系统',
    title: '消化系统分层总览',
    subtitle: '从完整消化道进入十二指肠、大肠与直肠',
    level: 'system',
    image: digestiveOverview,
    image_aspect: '370 / 810',
    description: '消化道自口腔延续至肛管。点击十二指肠、大肠或直肠区域进入器官级精细图。',
    instruction: '点击蓝色热点进入对应器官细节',
    hotspots: [
      { id: 'digestive_duodenum', label: '十二指肠', x: 51, y: 43, width: 25, height: 12, target_id: 'duodenum_detail' },
      { id: 'digestive_colon', label: '大肠', x: 50, y: 61, width: 54, height: 30, target_id: 'large_intestine_detail' },
      { id: 'digestive_rectum', label: '直肠', x: 50, y: 79, width: 20, height: 13, target_id: 'rectum_detail' }
    ],
    structures: [],
    source_label: 'Wikimedia Commons · Public domain'
  },
  {
    id: 'duodenum_detail',
    system: '消化系统',
    title: '十二指肠精细图',
    subtitle: '第二层：辨认上部、降部、水平部与升部',
    level: 'organ',
    parent_id: 'digestive_overview',
    image: duodenumDetail,
    image_aspect: '1400 / 1000',
    description: '十二指肠呈C形包绕胰头，是胆汁和胰液进入消化道的重要区域。',
    instruction: '点击各段查看毗邻和临床意义',
    hotspots: [
      { id: 'duo_1', label: '上部', x: 44, y: 16, width: 28, height: 16, structure_id: 'duodenum_superior' },
      { id: 'duo_2', label: '降部', x: 29, y: 45, width: 20, height: 35, structure_id: 'duodenum_descending' },
      { id: 'duo_3', label: '水平部', x: 50, y: 73, width: 34, height: 18, structure_id: 'duodenum_horizontal' },
      { id: 'duo_4', label: '升部', x: 73, y: 65, width: 22, height: 25, structure_id: 'duodenum_ascending' }
    ],
    structures: [
      { id: 'duodenum_superior', name: '十二指肠上部', category: '第一部', description: '自幽门向右后方走行，起始段又称十二指肠球部。', clinical_note: '十二指肠溃疡常发生于球部。' },
      { id: 'duodenum_descending', name: '十二指肠降部', category: '第二部', description: '沿胰头右侧下降，内侧壁可见十二指肠大乳头。', clinical_note: '胆总管和主胰管通常在大乳头区域开口。' },
      { id: 'duodenum_horizontal', name: '十二指肠水平部', category: '第三部', description: '横过下腔静脉和腹主动脉前方，上方有肠系膜上血管。', clinical_note: '肠系膜上动脉综合征可压迫此段。' },
      { id: 'duodenum_ascending', name: '十二指肠升部', category: '第四部', description: '向左上方走行，在十二指肠空肠曲移行为空肠。', clinical_note: 'Treitz韧带是上、下消化道出血划分的重要解剖标志。' }
    ],
    source_label: 'Wikimedia Commons · CC BY-SA 3.0'
  },
  {
    id: 'large_intestine_detail',
    system: '消化系统',
    title: '大肠精细图',
    subtitle: '第二层：从盲肠沿结肠框架到乙状结肠',
    level: 'organ',
    parent_id: 'digestive_overview',
    image: largeIntestineDetail,
    image_aspect: '900 / 1200',
    description: '大肠包括盲肠、结肠和直肠，结肠形成围绕小肠的框架。',
    instruction: '点击结肠分段查看解剖走行',
    hotspots: [
      { id: 'colon_cecum', label: '盲肠', x: 27, y: 31, width: 20, height: 18, structure_id: 'cecum' },
      { id: 'colon_ascending', label: '升结肠', x: 23, y: 20, width: 17, height: 25, structure_id: 'ascending_colon' },
      { id: 'colon_transverse', label: '横结肠', x: 48, y: 9, width: 48, height: 15, structure_id: 'transverse_colon' },
      { id: 'colon_descending', label: '降结肠', x: 71, y: 22, width: 18, height: 27, structure_id: 'descending_colon' },
      { id: 'colon_sigmoid', label: '乙状结肠', x: 55, y: 38, width: 30, height: 17, structure_id: 'sigmoid_colon' }
    ],
    structures: [
      { id: 'cecum', name: '盲肠与阑尾', category: '大肠起始部', description: '位于右髂窝，回肠在回盲瓣处汇入，阑尾起自盲肠后内侧。', clinical_note: '阑尾根部体表投影常用于急性阑尾炎定位。' },
      { id: 'ascending_colon', name: '升结肠', category: '结肠', description: '自盲肠向上走行至肝曲，多数位于腹膜后。', clinical_note: '右半结肠病变可表现为慢性失血和贫血。' },
      { id: 'transverse_colon', name: '横结肠', category: '结肠', description: '自肝曲横行至脾曲，由横结肠系膜悬吊。', clinical_note: '脾曲位置较高，邻近脾脏。' },
      { id: 'descending_colon', name: '降结肠', category: '结肠', description: '自脾曲沿左侧腹部下降至左髂窝。', clinical_note: '降结肠和乙状结肠病变常与左下腹症状相关。' },
      { id: 'sigmoid_colon', name: '乙状结肠', category: '结肠', description: '呈S形，由乙状结肠系膜悬吊并移行为直肠。', clinical_note: '乙状结肠是憩室病和扭转的常见部位。' }
    ],
    source_label: 'Wikimedia Commons · Public domain'
  },
  {
    id: 'rectum_detail',
    system: '消化系统',
    title: '直肠与肛管精细图',
    subtitle: '第二层：观察直肠壶腹、肛管与周围盆底结构',
    level: 'organ',
    parent_id: 'digestive_overview',
    image: rectumDetail,
    image_aspect: '612 / 700',
    description: '直肠自第3骶椎平面续于乙状结肠，下端穿过盆膈移行为肛管。',
    instruction: '点击直肠和肛管区域查看结构说明',
    hotspots: [
      { id: 'rectum_ampulla_hs', label: '直肠壶腹', x: 54, y: 54, width: 23, height: 32, structure_id: 'rectal_ampulla' },
      { id: 'anal_canal_hs', label: '肛管', x: 54, y: 78, width: 18, height: 20, structure_id: 'anal_canal' },
      { id: 'pelvic_floor_hs', label: '盆底', x: 53, y: 69, width: 44, height: 15, structure_id: 'pelvic_floor' }
    ],
    structures: [
      { id: 'rectal_ampulla', name: '直肠壶腹', category: '直肠', description: '直肠下段扩张形成的储存区域，与排便反射相关。', clinical_note: '直肠指检可评估低位直肠和邻近结构。' },
      { id: 'anal_canal', name: '肛管', category: '消化道末端', description: '自盆膈至肛门，包含重要的齿状线和括约肌结构。', clinical_note: '齿状线上下在血供、淋巴和神经支配方面存在差异。' },
      { id: 'pelvic_floor', name: '盆底与括约肌', category: '支持结构', description: '肛提肌与内、外括约肌共同维持排便控制。', clinical_note: '盆底功能障碍可能导致排便困难或失禁。' }
    ],
    source_label: 'Wikimedia Commons · CC BY 3.0'
  }
];

export const anatomyAtlasSystems = ['运动系统', '循环系统', '呼吸系统', '消化系统', '泌尿系统', '生殖系统', '神经系统', '内分泌系统'] as const;
