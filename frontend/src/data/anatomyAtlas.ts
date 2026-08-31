import heartOverview from '../assets/medical/anatomy/blausen20260812/NI056.webp';
import heartDetail from '../assets/medical/anatomy/blausen20260812/NI059.webp';
import digestiveOverview from '../assets/medical/anatomy/blausen20260812/NI015.webp';
import duodenumDetail from '../assets/medical/anatomy/blausen20260812/NI028.webp';
import largeIntestineDetail from '../assets/medical/anatomy/blausen20260812/NI021.webp';
import rectumDetail from '../assets/medical/anatomy/blausen20260812/NI022.webp';
import skeletalOverview from '../assets/medical/anatomy/blausen20260812/NI005.webp';
import respiratoryOverview from '../assets/medical/anatomy/blausen20260812/NI030.webp';
import kidneyOverview from '../assets/medical/anatomy/blausen20260812/NI041.webp';
import maleReproductiveOverview from '../assets/medical/anatomy/blausen20260812/NI046.webp';
import femaleReproductiveOverview from '../assets/medical/anatomy/blausen20260812/NI045.webp';
import nervousOverview from '../assets/medical/anatomy/blausen20260812/NI075.webp';
import endocrineOverview from '../assets/medical/anatomy/blausen20260812/NI091.webp';
import tracheaDetail from '../assets/medical/anatomy/blausen20260812/NI034.webp';
import nephronDetail from '../assets/medical/anatomy/blausen20260812/NI043.webp';
import heartBloodFlowDetail from '../assets/medical/anatomy/blausen20260812/NI057.webp';
import coronaryArteriesDetail from '../assets/medical/anatomy/blausen20260812/NI066.webp';
import cranialNervesDetail from '../assets/medical/anatomy/blausen20260812/NI078.webp';
import brainVentriclesDetail from '../assets/medical/anatomy/blausen20260812/NI079.webp';
import spinalCordSectionDetail from '../assets/medical/anatomy/blausen20260812/NI081.webp';
import skullBonesDetail from '../assets/medical/anatomy/blausen20260812/NI001.webp';
import vertebralColumnDetail from '../assets/medical/anatomy/blausen20260812/NI003.webp';
import shoulderJointDetail from '../assets/medical/anatomy/blausen20260812/NI009.webp';
import kneeAnatomyDetail from '../assets/medical/anatomy/blausen20260812/NI011.webp';
import smallIntestineDetail from '../assets/medical/anatomy/blausen20260812/NI020.webp';
import pancreasBiliaryDetail from '../assets/medical/anatomy/blausen20260812/NI028.webp';
import femalePelvicFloorDetail from '../assets/medical/anatomy/blausen20260812/NI050.webp';
import pancreaticIsletDetail from '../assets/medical/anatomy/blausen20260812/NI093.webp';
import upperRespiratoryDetail from '../assets/medical/anatomy/blausen20260812/NI032.webp';
import respiratoryEpitheliumDetail from '../assets/medical/anatomy/blausen20260812/NI035.webp';
import urinarySystemFemaleDetail from '../assets/medical/anatomy/blausen20260812/NI037.webp';
import urinarySphincterDetail from '../assets/medical/anatomy/blausen20260812/NI044.webp';
import malePelvicFloorDetail from '../assets/medical/anatomy/blausen20260812/NI052.webp';
import arteryWallDetail from '../assets/medical/anatomy/blausen20260812/NI068.webp';
import brainLobesDetail from '../assets/medical/anatomy/blausen20260812/NI075.webp';
import brainstemDetail from '../assets/medical/anatomy/blausen20260812/NI076.webp';
import csfSystemDetail from '../assets/medical/anatomy/blausen20260812/NI080.webp';
import hipJointDetail from '../assets/medical/anatomy/blausen20260812/NI010.webp';
import skeletalMuscleDetail from '../assets/medical/anatomy/blausen20260812/NI013.webp';
import oralCavityDetail from '../assets/medical/anatomy/blausen20260812/NI018.webp';
import liverOrganDetail from '../assets/medical/anatomy/blausen20260812/NI024.webp';
import gallbladderOrganDetail from '../assets/medical/anatomy/blausen20260812/NI025.webp';
import legVeinsDetail from '../assets/medical/anatomy/blausen20260812/NI069.webp';
import brainLayersDetail from '../assets/medical/anatomy/blausen20260812/NI074.webp';
import spinalSensoryPathwaysDetail from '../assets/medical/anatomy/blausen20260812/NI082.webp';
import spinalMotorPathwaysDetail from '../assets/medical/anatomy/blausen20260812/NI083.webp';
import multipolarNeuronDetail from '../assets/medical/anatomy/blausen20260812/NI086.webp';
import sympatheticInnervationDetail from '../assets/medical/anatomy/blausen20260812/NI087.webp';
import parasympatheticInnervationDetail from '../assets/medical/anatomy/blausen20260812/NI088.webp';
import type { AnatomySystemName } from './anatomyResources';
import { blausenAtlasAssets } from './blausenAtlasAssets';

const blausenImageModules = import.meta.glob('../assets/medical/anatomy/blausen20260812/*.webp', { eager: true, query: '?url', import: 'default' }) as Record<string, string>;
const blausenImage = (id: string) => blausenImageModules[`../assets/medical/anatomy/blausen20260812/${id}.webp`];

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
  level: 'system' | 'organ' | 'detail';
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
      { id: 'bone_skull_hs', label: '颅骨', x: 25, y: 8, width: 13, height: 12, target_id: 'skull_bones_detail', structure_id: 'cranial_bones' },
      { id: 'bone_thorax_hs', label: '胸廓', x: 25, y: 27, width: 22, height: 22, structure_id: 'bone_thorax' },
      { id: 'bone_spine_hs', label: '脊柱', x: 74, y: 34, width: 12, height: 37, target_id: 'vertebral_column_detail', structure_id: 'vertebral_regions' },
      { id: 'bone_pelvis_hs', label: '骨盆与髋关节', x: 25, y: 47, width: 22, height: 16, target_id: 'hip_joint_detail', structure_id: 'bone_pelvis' },
      { id: 'bone_upper_limb_hs', label: '肩关节', x: 10, y: 37, width: 15, height: 40, target_id: 'shoulder_joint_detail', structure_id: 'glenohumeral_joint' },
      { id: 'bone_lower_limb_hs', label: '膝关节', x: 25, y: 75, width: 23, height: 45, target_id: 'knee_anatomy_detail', structure_id: 'patella' },
      { id: 'skeletal_muscle_entry_hs', label: '骨骼肌纤维', x: 75, y: 72, width: 24, height: 32, target_id: 'skeletal_muscle_detail' }
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
    id: 'skull_bones_detail', system: '运动系统', title: '颅骨精细图', subtitle: '第二层：区分脑颅骨与面颅骨', level: 'organ', parent_id: 'skeletal_overview',
    image: skullBonesDetail, image_aspect: '2000 / 2000', description: '颅骨由脑颅骨和面颅骨组成，骨缝连接多数颅骨并共同围成颅腔、眶和鼻腔。', instruction: '点击主要颅骨分区查看说明',
    hotspots: [
      { id: 'cranial_bones_hs', label: '脑颅骨', x: 43, y: 23, width: 46, height: 35, structure_id: 'cranial_bones' },
      { id: 'facial_bones_hs', label: '面颅骨', x: 76, y: 66, width: 31, height: 31, structure_id: 'facial_bones' },
      { id: 'temporal_bone_hs', label: '颞骨', x: 40, y: 38, width: 22, height: 21, structure_id: 'temporal_bone' },
      { id: 'mandible_hs', label: '下颌骨', x: 73, y: 78, width: 24, height: 19, structure_id: 'mandible' }
    ],
    structures: [
      { id: 'cranial_bones', name: '脑颅骨', category: '颅骨', description: '额骨、顶骨、枕骨、颞骨、蝶骨和筛骨共同围成颅腔。', clinical_note: '颅底骨折可能累及脑神经及重要血管。' },
      { id: 'facial_bones', name: '面颅骨', category: '颅骨', description: '构成面部支架、眶和鼻腔等结构。', clinical_note: '面中部骨折需评估眶、鼻腔和咬合关系。' },
      { id: 'temporal_bone', name: '颞骨', category: '脑颅骨', description: '参与颅底和颅侧壁构成，容纳中耳和内耳结构。', clinical_note: '颞骨骨折可伴听力、面神经或脑脊液漏问题。' },
      { id: 'mandible', name: '下颌骨', category: '面颅骨', description: '唯一可大幅活动的颅骨，通过颞下颌关节与颞骨相连。', clinical_note: '下颌骨骨折常影响咬合和张口活动。' }
    ], source_label: 'Blausen Medical · NI001 · CC BY-SA 4.0'
  },
  {
    id: 'vertebral_column_detail', system: '运动系统', title: '脊柱分段图', subtitle: '第二层：颈、胸、腰、骶尾椎与生理曲度', level: 'organ', parent_id: 'skeletal_overview',
    image: vertebralColumnDetail, image_aspect: '750 / 1441', description: '脊柱构成躯干中轴并保护脊髓，不同区域的椎骨形态和活动度不同。', instruction: '点击脊柱各段查看解剖与临床特点',
    hotspots: [
      { id: 'cervical_hs', label: '颈椎', x: 50, y: 19, width: 19, height: 18, structure_id: 'cervical_spine' },
      { id: 'thoracic_hs', label: '胸椎', x: 50, y: 39, width: 18, height: 30, structure_id: 'thoracic_spine' },
      { id: 'lumbar_hs', label: '腰椎', x: 50, y: 63, width: 20, height: 23, structure_id: 'lumbar_spine' },
      { id: 'sacrum_hs', label: '骶尾骨', x: 50, y: 80, width: 25, height: 19, structure_id: 'sacrum' }
    ],
    structures: [
      { id: 'cervical_spine', name: '颈椎', category: '脊柱分段', description: '通常为7块，活动度较大，横突孔内有椎动脉走行。', clinical_note: '颈椎损伤可能同时危及脊髓、神经根和椎动脉。' },
      { id: 'thoracic_spine', name: '胸椎', category: '脊柱分段', description: '通常为12块，与肋骨构成胸廓。', clinical_note: '胸椎活动受胸廓限制，压缩性骨折较常见。' },
      { id: 'lumbar_spine', name: '腰椎', category: '脊柱分段', description: '通常为5块，椎体粗大并承受较大负荷。', clinical_note: '腰椎间盘突出可压迫相应神经根。' },
      { id: 'sacrum', name: '骶骨与尾骨', category: '脊柱分段', description: '骶骨与骨盆相连，将躯干重量传向下肢。', clinical_note: '骶髂关节及骶神经受累可造成腰骶部和下肢症状。' }
    ], source_label: 'Blausen Medical · NI003 · CC BY 3.0'
  },
  {
    id: 'shoulder_joint_detail', system: '运动系统', title: '肩关节精细图', subtitle: '第二层：肱骨头、关节盂、关节囊与滑膜', level: 'organ', parent_id: 'skeletal_overview',
    image: shoulderJointDetail, image_aspect: '2000 / 2000', description: '盂肱关节以较浅的关节盂容纳较大的肱骨头，活动度大但稳定性较依赖软组织。', instruction: '点击关节面和关节囊结构查看说明',
    hotspots: [
      { id: 'humeral_head_hs', label: '肱骨头', x: 55, y: 44, width: 26, height: 30, structure_id: 'humeral_head' },
      { id: 'glenoid_hs', label: '关节盂', x: 70, y: 44, width: 17, height: 24, structure_id: 'glenoid' },
      { id: 'capsule_hs', label: '关节囊', x: 66, y: 40, width: 28, height: 30, structure_id: 'joint_capsule' },
      { id: 'cartilage_hs', label: '关节软骨', x: 64, y: 50, width: 18, height: 22, structure_id: 'articular_cartilage' }
    ],
    structures: [
      { id: 'humeral_head', name: '肱骨头', category: '关节面', description: '近似球形，与肩胛骨关节盂构成盂肱关节。', clinical_note: '肩关节前脱位时肱骨头常移向前下方。' },
      { id: 'glenoid', name: '关节盂', category: '关节面', description: '肩胛骨外侧的浅凹，盂唇可加深关节窝。', clinical_note: '盂唇损伤可能导致疼痛和关节不稳。' },
      { id: 'joint_capsule', name: '关节囊与滑膜', category: '软组织', description: '关节囊包绕关节，内层滑膜分泌滑液。', clinical_note: '粘连性关节囊炎可明显限制肩关节活动。' },
      { id: 'articular_cartilage', name: '关节软骨', category: '软骨', description: '覆盖相对关节面，减少摩擦并分散负荷。', clinical_note: '软骨损伤会影响关节顺滑运动并促进退变。' }
    ], source_label: 'Blausen Medical · NI009 · CC BY 3.0'
  },
  {
    id: 'knee_anatomy_detail', system: '运动系统', title: '膝关节前面观', subtitle: '第二层：髌骨、股骨、胫腓骨与髌腱', level: 'organ', parent_id: 'skeletal_overview',
    image: kneeAnatomyDetail, image_aspect: '1500 / 1500', description: '膝关节由股骨、胫骨和髌骨参与构成，依靠韧带、半月板和周围肌腱维持稳定。', instruction: '点击主要骨性与伸膝装置结构',
    hotspots: [
      { id: 'patella_hs', label: '髌骨', x: 50, y: 43, width: 23, height: 22, structure_id: 'patella' },
      { id: 'femur_hs', label: '股骨远端', x: 50, y: 34, width: 35, height: 27, structure_id: 'distal_femur' },
      { id: 'tibia_hs', label: '胫骨近端', x: 58, y: 65, width: 31, height: 23, structure_id: 'proximal_tibia' },
      { id: 'patellar_tendon_hs', label: '髌腱', x: 51, y: 55, width: 16, height: 22, structure_id: 'patellar_tendon' }
    ],
    structures: [
      { id: 'patella', name: '髌骨', category: '籽骨', description: '位于股四头肌腱内，可增加伸膝装置的力臂。', clinical_note: '髌骨位置和轨迹异常可引起膝前疼痛。' },
      { id: 'distal_femur', name: '股骨远端', category: '关节骨', description: '内外侧髁与胫骨平台构成胫股关节。', clinical_note: '股骨髁损伤需要关注关节面平整度。' },
      { id: 'proximal_tibia', name: '胫骨近端', category: '关节骨', description: '胫骨平台承担来自股骨的主要负荷。', clinical_note: '胫骨平台骨折可能合并半月板或韧带损伤。' },
      { id: 'patellar_tendon', name: '髌韧带（髌腱）', category: '伸膝装置', description: '连接髌骨下端与胫骨粗隆，传递股四头肌力量。', clinical_note: '髌腱断裂会导致主动伸膝障碍。' }
    ], source_label: 'Blausen Medical · NI011 · CC BY 3.0'
  },
  {
    id: 'hip_joint_detail', system: '运动系统', title: '髋关节精细图', subtitle: '第二层：髋臼、股骨头、关节囊与韧带', level: 'organ', parent_id: 'skeletal_overview',
    image: hipJointDetail, image_aspect: '1024 / 768', description: '髋关节是由髋臼容纳股骨头形成的球窝关节，兼顾负重稳定与多轴运动。', instruction: '点击主要关节结构查看稳定机制',
    hotspots: [
      { id: 'acetabulum_hs', label: '髋臼', x: 40, y: 43, width: 24, height: 30, structure_id: 'acetabulum' },
      { id: 'femoral_head_hip_hs', label: '股骨头', x: 52, y: 46, width: 24, height: 29, structure_id: 'femoral_head_hip' },
      { id: 'hip_capsule_hs', label: '关节囊', x: 63, y: 50, width: 36, height: 38, structure_id: 'hip_capsule' },
      { id: 'femoral_neck_hs', label: '股骨颈', x: 67, y: 62, width: 28, height: 24, structure_id: 'femoral_neck' }
    ],
    structures: [
      { id: 'acetabulum', name: '髋臼', category: '关节窝', description: '由髂骨、坐骨和耻骨共同构成，髋臼唇可加深关节窝。', clinical_note: '髋臼骨折会影响负重关节面的稳定与匹配。' },
      { id: 'femoral_head_hip', name: '股骨头', category: '关节头', description: '近似球形并覆盖关节软骨，与髋臼形成髋关节。', clinical_note: '股骨头血供受损可导致缺血性坏死。' },
      { id: 'hip_capsule', name: '髋关节囊与韧带', category: '稳定结构', description: '强韧的关节囊及髂股、耻股和坐股韧带限制过度活动。', clinical_note: '髋关节脱位常伴关节囊损伤，并需评估坐骨神经。' },
      { id: 'femoral_neck', name: '股骨颈', category: '股骨近端', description: '连接股骨头和转子区，将负荷传向股骨干。', clinical_note: '股骨颈骨折需特别关注股骨头血供。' }
    ], source_label: 'Blausen Medical · NI010 · CC BY 3.0'
  },
  {
    id: 'skeletal_muscle_detail', system: '运动系统', title: '骨骼肌纤维超微结构', subtitle: '第二层：从肌纤维进入肌原纤维与兴奋-收缩耦联结构', level: 'organ', parent_id: 'skeletal_overview',
    image: skeletalMuscleDetail, image_aspect: '2000 / 1823', description: '骨骼肌纤维是多核细胞，内部含大量肌原纤维；T管与肌浆网共同将电信号转化为收缩。', instruction: '点击细胞膜、肌原纤维和细胞器查看功能',
    hotspots: [
      { id: 'sarcolemma_hs', label: '肌膜', x: 52, y: 54, width: 58, height: 58, structure_id: 'sarcolemma' },
      { id: 'myofibrils_hs', label: '肌原纤维', x: 57, y: 52, width: 30, height: 31, structure_id: 'myofibrils' },
      { id: 'triad_hs', label: 'T管与三联体', x: 37, y: 65, width: 25, height: 23, structure_id: 'triad' },
      { id: 'muscle_mito_hs', label: '线粒体', x: 67, y: 68, width: 24, height: 19, structure_id: 'muscle_mitochondria' }
    ],
    structures: [
      { id: 'sarcolemma', name: '肌膜', category: '细胞膜', description: '包围肌纤维并传导动作电位，向内形成T管。', clinical_note: '肌膜相关蛋白异常可造成部分遗传性肌病。' },
      { id: 'myofibrils', name: '肌原纤维', category: '收缩装置', description: '由重复肌节组成，粗细肌丝滑行产生肌肉收缩。', clinical_note: '肌节蛋白异常会影响肌力和心肌或骨骼肌功能。' },
      { id: 'triad', name: 'T管与肌浆网三联体', category: '兴奋-收缩耦联', description: '一条T管与两侧终池构成三联体，调控胞内钙释放。', clinical_note: '钙调控异常会影响收缩强度和肌肉代谢。' },
      { id: 'muscle_mitochondria', name: '线粒体', category: '能量供应', description: '为持续收缩提供ATP，耐力型肌纤维中相对丰富。', clinical_note: '线粒体病可表现为运动不耐受和肌无力。' }
    ], source_label: 'Blausen Medical · NI013 · CC BY 3.0'
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
      { id: 'resp_nose_hs', label: '鼻腔与咽', x: 39, y: 24, width: 24, height: 20, target_id: 'upper_respiratory_detail', structure_id: 'nasal_cavity' },
      { id: 'resp_larynx_hs', label: '喉', x: 45, y: 40, width: 13, height: 12, structure_id: 'resp_larynx' },
      { id: 'resp_trachea_hs', label: '气管', x: 48, y: 54, width: 12, height: 25, target_id: 'trachea_detail', structure_id: 'trachea_cartilage' },
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
    id: 'upper_respiratory_detail', system: '呼吸系统', title: '上呼吸道矢状面', subtitle: '第二层：鼻腔、鼻旁窦、咽与喉入口', level: 'organ', parent_id: 'respiratory_overview',
    image: upperRespiratoryDetail, image_aspect: '2500 / 2200', description: '上呼吸道对吸入空气进行过滤、加温和湿化，并通过咽与下呼吸道相连。', instruction: '点击鼻腔、鼻旁窦和咽部分区查看说明',
    hotspots: [
      { id: 'nasal_cavity_hs', label: '鼻腔与鼻甲', x: 69, y: 28, width: 33, height: 32, structure_id: 'nasal_cavity' },
      { id: 'paranasal_sinus_hs', label: '鼻旁窦', x: 62, y: 15, width: 35, height: 19, structure_id: 'paranasal_sinuses' },
      { id: 'nasopharynx_hs', label: '鼻咽', x: 43, y: 38, width: 21, height: 17, structure_id: 'nasopharynx' },
      { id: 'oropharynx_hs', label: '口咽', x: 43, y: 52, width: 20, height: 18, structure_id: 'oropharynx' },
      { id: 'laryngopharynx_hs', label: '喉咽', x: 43, y: 64, width: 19, height: 18, structure_id: 'laryngopharynx' }
    ],
    structures: [
      { id: 'nasal_cavity', name: '鼻腔与鼻甲', category: '上呼吸道', description: '鼻甲增加黏膜表面积并形成气流通道，有助于空气处理。', clinical_note: '鼻甲肥大或黏膜水肿可能造成鼻阻塞。' },
      { id: 'paranasal_sinuses', name: '鼻旁窦', category: '含气腔', description: '额窦、筛窦、蝶窦和上颌窦通过开口与鼻腔相通。', clinical_note: '窦口引流受阻可促进鼻窦炎发生。' },
      { id: 'nasopharynx', name: '鼻咽', category: '咽', description: '位于鼻腔后方，咽鼓管咽口开于其侧壁。', clinical_note: '鼻咽病变可能影响中耳通气。' },
      { id: 'oropharynx', name: '口咽', category: '咽', description: '位于口腔后方，是空气和食物的共同通道。', clinical_note: '口咽检查需观察扁桃体、软腭和咽后壁。' },
      { id: 'laryngopharynx', name: '喉咽', category: '咽', description: '向前通向喉，向下延续为食管。', clinical_note: '吞咽协调异常可导致误吸。' }
    ], source_label: 'Blausen Medical · NI032 · CC BY 3.0'
  },
  {
    id: 'trachea_detail',
    system: '呼吸系统',
    title: '气管与主支气管精细图',
    subtitle: '第二层：观察气管软骨、隆嵴和左右主支气管',
    level: 'organ',
    parent_id: 'respiratory_overview',
    image: tracheaDetail,
    image_aspect: '2800 / 3000',
    description: '气管由一系列C形透明软骨环支撑，在胸骨角附近分为左右主支气管，分叉处内面形成隆嵴。',
    instruction: '点击气管、隆嵴或主支气管查看临床关联',
    hotspots: [
      { id: 'trachea_cartilage_hs', label: '气管软骨与上皮', x: 51, y: 39, width: 17, height: 36, target_id: 'respiratory_epithelium_detail', structure_id: 'ciliated_epithelium' },
      { id: 'carina_hs', label: '气管隆嵴', x: 51, y: 67, width: 20, height: 15, structure_id: 'trachea_carina' },
      { id: 'right_main_bronchus_hs', label: '右主支气管', x: 38, y: 72, width: 24, height: 18, structure_id: 'right_main_bronchus' },
      { id: 'left_main_bronchus_hs', label: '左主支气管', x: 66, y: 72, width: 24, height: 18, structure_id: 'left_main_bronchus' }
    ],
    structures: [
      { id: 'trachea_cartilage', name: '气管软骨', category: '气道支架', description: 'C形透明软骨环维持气道开放，后方缺口由膜壁和气管肌封闭。', clinical_note: '气管插管深度过大可能越过隆嵴并进入单侧主支气管。' },
      { id: 'trachea_carina', name: '气管隆嵴', category: '气管分叉', description: '位于气管分叉内面的敏感嵴，是支气管镜定位的重要标志。', clinical_note: '隆嵴受刺激可引发强烈咳嗽反射。' },
      { id: 'right_main_bronchus', name: '右主支气管', category: '传导气道', description: '相较左侧更短、更粗且走行更陡直。', clinical_note: '吸入异物和误入的气管导管更常进入右主支气管。' },
      { id: 'left_main_bronchus', name: '左主支气管', category: '传导气道', description: '较右侧细长且更倾斜，从主动脉弓下方进入左肺门。', clinical_note: '影像和支气管镜检查需结合左右分支角度辨认。' }
    ],
    source_label: 'Blausen Medical · NI034 · CC BY 3.0'
  },
  {
    id: 'respiratory_epithelium_detail', system: '呼吸系统', title: '呼吸上皮精细结构', subtitle: '第三层：纤毛柱状细胞、黏液层与黏液纤毛清除', level: 'detail', parent_id: 'trachea_detail',
    image: respiratoryEpitheliumDetail, image_aspect: '2500 / 2500', description: '典型传导气道上皮由纤毛细胞、杯状细胞和基底细胞等组成，黏液捕获颗粒后由纤毛向咽部运送。', instruction: '点击纤毛、黏液和细胞层查看防御功能',
    hotspots: [
      { id: 'cilia_hs', label: '纤毛', x: 70, y: 61, width: 20, height: 27, structure_id: 'cilia' },
      { id: 'mucus_layer_hs', label: '黏液层', x: 67, y: 49, width: 21, height: 21, structure_id: 'mucus_layer' },
      { id: 'ciliated_epithelium_hs', label: '纤毛柱状细胞', x: 79, y: 66, width: 26, height: 42, structure_id: 'ciliated_epithelium' },
      { id: 'basement_membrane_hs', label: '基底膜与固有层', x: 82, y: 87, width: 28, height: 19, structure_id: 'basement_membrane' }
    ],
    structures: [
      { id: 'cilia', name: '纤毛', category: '细胞表面结构', description: '同步摆动将黏液和捕获颗粒推向咽部。', clinical_note: '纤毛功能障碍可导致反复呼吸道感染。' },
      { id: 'mucus_layer', name: '黏液层', category: '气道防御', description: '黏液捕获吸入的颗粒和微生物。', clinical_note: '黏液分泌过多或黏稠可影响气道通畅和清除。' },
      { id: 'ciliated_epithelium', name: '假复层纤毛柱状上皮', category: '呼吸上皮', description: '多数传导气道由此类上皮覆盖，包含多种功能细胞。', clinical_note: '长期刺激可引起上皮化生并削弱清除功能。' },
      { id: 'basement_membrane', name: '基底膜与固有层', category: '上皮支持层', description: '连接上皮与下方结缔组织，固有层内含血管和免疫成分。', clinical_note: '慢性气道炎症可伴基底膜下重塑。' }
    ], source_label: 'Blausen Medical · NI035 · CC BY 3.0'
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
      { id: 'kidney_cortex_hs', label: '肾皮质与肾单位', x: 72, y: 76, width: 28, height: 20, target_id: 'nephron_detail', structure_id: 'renal_corpuscle' },
      { id: 'kidney_medulla_hs', label: '肾髓质', x: 65, y: 54, width: 32, height: 42, structure_id: 'kidney_medulla' },
      { id: 'kidney_pelvis_hs', label: '肾盂肾盏', x: 63, y: 41, width: 25, height: 28, structure_id: 'kidney_pelvis' },
      { id: 'kidney_hilum_hs', label: '肾门', x: 46, y: 51, width: 18, height: 34, structure_id: 'kidney_hilum' },
      { id: 'kidney_ureter_hs', label: '完整泌尿通路', x: 45, y: 78, width: 11, height: 36, target_id: 'urinary_tract_detail', structure_id: 'urinary_ureter' }
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
    id: 'urinary_tract_detail', system: '泌尿系统', title: '女性泌尿系统总览', subtitle: '第二层：双肾、输尿管、膀胱与尿道', level: 'organ', parent_id: 'urinary_overview',
    image: urinarySystemFemaleDetail, image_aspect: '768 / 1024', description: '尿液由双肾生成，经输尿管进入膀胱储存，最终由尿道排出。', instruction: '点击完整尿路的各器官查看功能',
    hotspots: [
      { id: 'urinary_kidneys_hs', label: '双肾', x: 50, y: 28, width: 43, height: 23, structure_id: 'urinary_kidneys' },
      { id: 'urinary_ureters_hs', label: '双侧输尿管', x: 50, y: 48, width: 34, height: 31, structure_id: 'urinary_ureter' },
      { id: 'urinary_bladder_hs', label: '膀胱', x: 50, y: 64, width: 27, height: 18, target_id: 'urinary_sphincter_detail', structure_id: 'bladder_detrusor' },
      { id: 'urinary_urethra_hs', label: '女性尿道', x: 50, y: 74, width: 15, height: 15, target_id: 'urinary_sphincter_detail', structure_id: 'urethral_sphincters' }
    ],
    structures: [
      { id: 'urinary_kidneys', name: '双肾', category: '泌尿器官', description: '滤过血液、调节内环境并形成尿液。', clinical_note: '肾功能评估需结合滤过、尿检和影像信息。' },
      { id: 'urinary_ureter', name: '输尿管', category: '尿液通道', description: '通过平滑肌蠕动将尿液由肾盂送至膀胱。', clinical_note: '肾盂输尿管连接处、跨髂血管处和膀胱壁内段是常见狭窄位置。' },
      { id: 'bladder_detrusor', name: '膀胱', category: '储尿器官', description: '由逼尿肌围成，可顺应性储存并在排尿时收缩。', clinical_note: '排尿功能取决于逼尿肌和括约肌协调。' },
      { id: 'urethral_sphincters', name: '女性尿道', category: '排尿通道', description: '较短并穿过盆底到达外口。', clinical_note: '女性尿路感染风险与尿道较短等因素相关。' }
    ], source_label: 'Blausen Medical · NI037 · CC BY-SA 4.0'
  },
  {
    id: 'urinary_sphincter_detail', system: '泌尿系统', title: '膀胱与尿道括约肌', subtitle: '第三层：逼尿肌、膀胱颈和尿道括约机制', level: 'detail', parent_id: 'urinary_tract_detail',
    image: urinarySphincterDetail, image_aspect: '1500 / 1500', description: '膀胱逼尿肌收缩推动排尿，尿道括约结构在储尿期维持关闭并在排尿时协调松弛。', instruction: '点击膀胱壁、膀胱颈和括约肌查看排尿机制',
    hotspots: [
      { id: 'bladder_detrusor_hs', label: '逼尿肌', x: 45, y: 25, width: 54, height: 28, structure_id: 'bladder_detrusor' },
      { id: 'bladder_neck_hs', label: '膀胱颈', x: 36, y: 53, width: 20, height: 17, structure_id: 'bladder_neck' },
      { id: 'urethral_sphincters_hs', label: '尿道括约肌', x: 35, y: 64, width: 25, height: 27, structure_id: 'urethral_sphincters' },
      { id: 'urethra_detail_hs', label: '尿道', x: 34, y: 79, width: 17, height: 30, structure_id: 'urethra_detail' }
    ],
    structures: [
      { id: 'bladder_detrusor', name: '逼尿肌', category: '膀胱壁平滑肌', description: '舒张时允许储尿，收缩时提高膀胱内压推动尿液排出。', clinical_note: '逼尿肌过度活动可引起尿急和急迫性尿失禁。' },
      { id: 'bladder_neck', name: '膀胱颈', category: '膀胱出口', description: '位于膀胱向尿道移行处，是出口阻力调节区域。', clinical_note: '膀胱出口梗阻可导致残余尿增加。' },
      { id: 'urethral_sphincters', name: '尿道括约肌', category: '控尿结构', description: '平滑肌与横纹肌成分共同参与储尿和排尿控制。', clinical_note: '括约机制损伤可能造成压力性尿失禁。' },
      { id: 'urethra_detail', name: '尿道', category: '排尿通道', description: '将尿液由膀胱输送至体外。', clinical_note: '尿道及周围支持结构是尿控评估的重要部分。' }
    ], source_label: 'Blausen Medical · NI044 · CC BY-SA 4.0'
  },
  {
    id: 'nephron_detail',
    system: '泌尿系统',
    title: '肾单位精细图',
    subtitle: '第二层：从肾小体沿肾小管到集合管',
    level: 'organ',
    parent_id: 'urinary_overview',
    image: nephronDetail,
    image_aspect: '1600 / 1600',
    description: '肾单位是肾脏形成尿液的基本功能单位，包括肾小体和肾小管，并与周围毛细血管密切配合。',
    instruction: '点击肾小体、肾小管或血管区域查看功能',
    hotspots: [
      { id: 'renal_corpuscle_hs', label: '肾小体', x: 61, y: 39, width: 20, height: 20, structure_id: 'renal_corpuscle' },
      { id: 'proximal_tubule_hs', label: '近曲小管', x: 74, y: 31, width: 20, height: 20, structure_id: 'proximal_tubule' },
      { id: 'nephron_loop_hs', label: '髓袢', x: 68, y: 74, width: 23, height: 34, structure_id: 'nephron_loop' },
      { id: 'distal_tubule_hs', label: '远曲小管', x: 86, y: 39, width: 20, height: 23, structure_id: 'distal_tubule' },
      { id: 'collecting_duct_hs', label: '集合管', x: 91, y: 72, width: 13, height: 44, structure_id: 'collecting_duct' }
    ],
    structures: [
      { id: 'renal_corpuscle', name: '肾小体', category: '滤过结构', description: '由肾小球和肾小囊组成，血浆在此完成超滤。', clinical_note: '肾小球滤过率是评价肾功能的核心指标之一。' },
      { id: 'proximal_tubule', name: '近曲小管', category: '重吸收结构', description: '重吸收大部分水、钠、葡萄糖和氨基酸等滤过物。', clinical_note: '近端小管损伤可出现葡萄糖、磷酸盐等重吸收障碍。' },
      { id: 'nephron_loop', name: '肾单位袢', category: '浓缩结构', description: '降支和升支建立髓质渗透梯度，参与尿液浓缩和稀释。', clinical_note: '袢利尿剂主要作用于粗升支的离子转运。' },
      { id: 'distal_tubule', name: '远曲小管', category: '调节结构', description: '参与电解质和酸碱平衡的精细调节。', clinical_note: '噻嗪类利尿剂主要影响远曲小管钠氯同向转运。' },
      { id: 'collecting_duct', name: '集合管', category: '终末调节结构', description: '接受多个肾单位的滤液，在激素调节下决定终尿水和电解质组成。', clinical_note: '抗利尿激素通过增加集合管水通透性调节尿液浓缩。' }
    ],
    source_label: 'Blausen Medical · NI043 · CC BY-SA 4.0'
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
      { id: 'male_prostate_hs', label: '前列腺与盆底', x: 53, y: 62, width: 17, height: 14, target_id: 'male_pelvic_floor_detail', structure_id: 'male_pelvic_floor' },
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
    id: 'male_pelvic_floor_detail', system: '生殖系统', title: '男性盆腔与盆底矢状面', subtitle: '第二层：膀胱、前列腺、尿道、直肠与盆底', level: 'organ', parent_id: 'male_reproductive_overview',
    image: malePelvicFloorDetail, image_aspect: '1500 / 1500', description: '男性盆腔矢状面展示泌尿、生殖和消化结构的前后毗邻，以及盆底对盆腔器官的支持。', instruction: '点击前列腺、尿道、直肠和盆底查看关系',
    hotspots: [
      { id: 'male_bladder_hs', label: '膀胱', x: 39, y: 28, width: 34, height: 26, structure_id: 'male_bladder' },
      { id: 'male_prostate_detail_hs', label: '前列腺', x: 53, y: 42, width: 19, height: 18, structure_id: 'male_prostate_detail' },
      { id: 'male_urethra_detail_hs', label: '男性尿道', x: 27, y: 62, width: 38, height: 18, structure_id: 'male_urethra_detail' },
      { id: 'male_rectum_hs', label: '直肠', x: 70, y: 46, width: 29, height: 46, structure_id: 'male_rectum' },
      { id: 'male_pelvic_floor_hs', label: '男性盆底', x: 48, y: 69, width: 35, height: 19, structure_id: 'male_pelvic_floor' }
    ],
    structures: [
      { id: 'male_bladder', name: '膀胱', category: '泌尿器官', description: '位于耻骨联合后方，充盈时向上扩展。', clinical_note: '盆腔影像需结合充盈程度判断膀胱形态。' },
      { id: 'male_prostate_detail', name: '前列腺', category: '男性附属腺', description: '位于膀胱颈下方并包绕前列腺部尿道。', clinical_note: '增生可压迫尿道并增加排尿阻力。' },
      { id: 'male_urethra_detail', name: '男性尿道', category: '泌尿生殖通道', description: '依次经过前列腺部、膜部和海绵体部。', clinical_note: '不同节段的损伤机制和处理方式不同。' },
      { id: 'male_rectum', name: '直肠', category: '消化道', description: '位于膀胱、精囊和前列腺后方。', clinical_note: '直肠指检可触及前列腺后面。' },
      { id: 'male_pelvic_floor', name: '男性盆底肌', category: '支持结构', description: '支持盆腔器官并参与控尿、控便及性功能。', clinical_note: '盆底训练可用于部分术后尿控康复。' }
    ], source_label: 'Blausen Medical · NI052 · CC BY-SA 4.0'
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
      { id: 'female_vagina_hs', label: '阴道与盆底', x: 48, y: 42, width: 15, height: 18, target_id: 'female_pelvic_floor_detail', structure_id: 'levator_ani' },
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
    id: 'female_pelvic_floor_detail', system: '生殖系统', title: '女性盆底肌精细图', subtitle: '第三层：从下方观察肛提肌及盆腔出口', level: 'detail', parent_id: 'female_reproductive_overview',
    image: femalePelvicFloorDetail, image_aspect: '1500 / 1500', description: '盆底肌群封闭骨盆下口并支持盆腔器官，其中肛提肌是维持控尿、控便和盆腔器官位置的关键结构。', instruction: '点击主要盆底肌和尿道区域查看功能',
    hotspots: [
      { id: 'pubococcygeus_hs', label: '耻骨尾骨肌', x: 37, y: 55, width: 28, height: 28, structure_id: 'pubococcygeus' },
      { id: 'puborectalis_hs', label: '耻骨直肠肌', x: 60, y: 56, width: 22, height: 25, structure_id: 'puborectalis' },
      { id: 'iliococcygeus_hs', label: '髂骨尾骨肌', x: 66, y: 72, width: 31, height: 22, structure_id: 'iliococcygeus' },
      { id: 'pelvic_urethra_hs', label: '尿道', x: 50, y: 49, width: 12, height: 15, structure_id: 'pelvic_urethra' }
    ],
    structures: [
      { id: 'pubococcygeus', name: '耻骨尾骨肌', category: '肛提肌', description: '起自耻骨并向后走行，参与支持盆腔器官和控制盆底开口。', clinical_note: '妊娠分娩或神经肌肉损伤可削弱盆底支持。' },
      { id: 'puborectalis', name: '耻骨直肠肌', category: '肛提肌', description: '呈吊带状绕过直肠肛管交界，维持肛直肠角。', clinical_note: '排便时该肌需适当松弛，协调障碍可造成排便困难。' },
      { id: 'iliococcygeus', name: '髂骨尾骨肌', category: '肛提肌', description: '形成较薄的盆底肌板，协同承托盆腔脏器。', clinical_note: '盆底松弛与器官脱垂风险相关。' },
      { id: 'pelvic_urethra', name: '女性尿道', category: '盆底开口', description: '穿过盆底向前下方开口，长度较男性短。', clinical_note: '盆底支持和尿道括约机制共同影响尿控。' }
    ], source_label: 'Blausen Medical · NI050 · CC BY-SA 4.0'
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
      { id: 'brain_cerebrum_hs', label: '脑室系统', x: 31, y: 43, width: 38, height: 63, target_id: 'brain_ventricles_detail', structure_id: 'lateral_ventricles' },
      { id: 'brain_cortex_hs', label: '大脑脑叶', x: 14, y: 62, width: 20, height: 25, target_id: 'brain_lobes_detail', structure_id: 'frontal_lobe' },
      { id: 'brain_callosum_hs', label: '胼胝体', x: 25, y: 35, width: 20, height: 20, structure_id: 'brain_callosum' },
      { id: 'brain_hemisphere_hs', label: '左右半球', x: 77, y: 49, width: 36, height: 65, structure_id: 'brain_hemispheres' },
      { id: 'brain_fissure_hs', label: '大脑纵裂', x: 77, y: 19, width: 15, height: 19, structure_id: 'brain_fissure' },
      { id: 'cranial_nerves_entry_hs', label: '十二对脑神经', x: 50, y: 74, width: 34, height: 22, target_id: 'cranial_nerves_detail' },
      { id: 'spinal_cord_entry_hs', label: '脊髓横断面', x: 51, y: 91, width: 24, height: 13, target_id: 'spinal_cord_section_detail' },
      { id: 'brainstem_entry_hs', label: '脑干', x: 50, y: 61, width: 20, height: 19, target_id: 'brainstem_detail', structure_id: 'midbrain' },
      { id: 'neuron_entry_hs', label: '神经元结构', x: 87, y: 82, width: 24, height: 18, target_id: 'multipolar_neuron_detail' },
      { id: 'sympathetic_entry_hs', label: '交感神经', x: 16, y: 88, width: 25, height: 17, target_id: 'sympathetic_innervation_detail' },
      { id: 'parasympathetic_entry_hs', label: '副交感神经', x: 84, y: 96, width: 28, height: 14, target_id: 'parasympathetic_innervation_detail' }
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
    id: 'brain_lobes_detail', system: '神经系统', title: '大脑脑叶分区', subtitle: '第二层：额叶、顶叶、颞叶与枕叶', level: 'organ', parent_id: 'nervous_overview',
    image: brainLobesDetail, image_aspect: '2250 / 1350', description: '大脑半球表面依据主要脑沟分为不同脑叶，各脑叶承担相互联系又有所侧重的高级功能。', instruction: '点击不同颜色的脑叶查看功能定位',
    hotspots: [
      { id: 'frontal_lobe_hs', label: '额叶', x: 36, y: 39, width: 35, height: 43, structure_id: 'frontal_lobe' },
      { id: 'parietal_lobe_hs', label: '顶叶', x: 65, y: 35, width: 35, height: 38, structure_id: 'parietal_lobe' },
      { id: 'temporal_lobe_hs', label: '颞叶', x: 55, y: 59, width: 44, height: 31, structure_id: 'temporal_lobe' },
      { id: 'occipital_lobe_hs', label: '枕叶', x: 83, y: 51, width: 22, height: 32, structure_id: 'occipital_lobe' },
      { id: 'brain_layers_entry_hs', label: '脑膜与覆盖层', x: 50, y: 83, width: 34, height: 15, target_id: 'brain_layers_detail' }
    ],
    structures: [
      { id: 'frontal_lobe', name: '额叶', category: '大脑脑叶', description: '参与执行控制、行为、语言表达和随意运动。', clinical_note: '额叶损伤可出现人格、执行或运动语言功能改变。' },
      { id: 'parietal_lobe', name: '顶叶', category: '大脑脑叶', description: '整合躯体感觉并参与空间注意和身体图式。', clinical_note: '优势侧和非优势侧顶叶损害表现存在差异。' },
      { id: 'temporal_lobe', name: '颞叶', category: '大脑脑叶', description: '参与听觉、记忆、语言理解和情绪加工。', clinical_note: '颞叶癫痫可表现为复杂的感觉和行为症状。' },
      { id: 'occipital_lobe', name: '枕叶', category: '大脑脑叶', description: '以视觉信息处理为主要功能。', clinical_note: '枕叶病变常引起视野缺损或视觉识别异常。' }
    ], source_label: 'Blausen Medical · NI075 · CC BY 3.0'
  },
  {
    id: 'brainstem_detail', system: '神经系统', title: '脑干精细图', subtitle: '第二层：中脑、脑桥与延髓', level: 'organ', parent_id: 'nervous_overview',
    image: brainstemDetail, image_aspect: '1500 / 1500', description: '脑干连接大脑、小脑和脊髓，包含多组脑神经核及维持生命的重要神经中枢。', instruction: '点击脑干三个分部查看功能与定位',
    hotspots: [
      { id: 'midbrain_hs', label: '中脑', x: 59, y: 52, width: 20, height: 17, structure_id: 'midbrain' },
      { id: 'pons_hs', label: '脑桥', x: 59, y: 62, width: 20, height: 19, structure_id: 'pons' },
      { id: 'medulla_hs', label: '延髓', x: 55, y: 72, width: 18, height: 22, structure_id: 'medulla' },
      { id: 'vertebrobasilar_hs', label: '椎-基底动脉', x: 55, y: 81, width: 19, height: 28, structure_id: 'vertebrobasilar' }
    ],
    structures: [
      { id: 'midbrain', name: '中脑', category: '脑干', description: '位于间脑和脑桥之间，参与眼球运动、瞳孔反射和运动调节。', clinical_note: '中脑病变可出现眼球运动障碍与交叉性体征。' },
      { id: 'pons', name: '脑桥', category: '脑干', description: '位于中脑和延髓之间，与小脑联系密切。', clinical_note: '脑桥损害可影响面部、眼球运动及长传导束。' },
      { id: 'medulla', name: '延髓', category: '脑干', description: '向下延续为脊髓，包含呼吸循环等重要调节中枢。', clinical_note: '延髓损伤可能危及呼吸、循环和吞咽。' },
      { id: 'vertebrobasilar', name: '椎-基底动脉系统', category: '后循环', description: '椎动脉汇合成基底动脉，为脑干、小脑和部分后脑供血。', clinical_note: '后循环缺血可表现为眩晕、复视、共济失调等。' }
    ], source_label: 'Blausen Medical · NI076 · CC BY 3.0'
  },
  {
    id: 'brain_ventricles_detail',
    system: '神经系统',
    title: '脑室系统精细图',
    subtitle: '第二层：侧脑室、第三脑室、中脑水管与第四脑室',
    level: 'organ',
    parent_id: 'nervous_overview',
    image: brainVentriclesDetail,
    image_aspect: '2988 / 1432',
    description: '脑室系统内含脑脊液，各腔室依次相通并延续至脊髓中央管及蛛网膜下腔。',
    instruction: '点击蓝色脑室结构查看脑脊液通路',
    hotspots: [
      { id: 'lateral_ventricles_hs', label: '侧脑室与脑脊液', x: 27, y: 33, width: 30, height: 34, target_id: 'csf_system_detail', structure_id: 'csf_production' },
      { id: 'third_ventricle_hs', label: '第三脑室', x: 45, y: 43, width: 18, height: 22, structure_id: 'third_ventricle' },
      { id: 'cerebral_aqueduct_hs', label: '中脑水管', x: 46, y: 55, width: 16, height: 19, structure_id: 'cerebral_aqueduct' },
      { id: 'fourth_ventricle_hs', label: '第四脑室', x: 45, y: 65, width: 20, height: 22, structure_id: 'fourth_ventricle' }
    ],
    structures: [
      { id: 'lateral_ventricles', name: '侧脑室', category: '脑室', description: '位于左右大脑半球内，经室间孔与第三脑室相通。', clinical_note: '侧脑室形态和宽度是头颅影像评估的重要指标。' },
      { id: 'third_ventricle', name: '第三脑室', category: '脑室', description: '位于间脑正中，两侧主要邻近丘脑和下丘脑。', clinical_note: '邻近占位可能阻塞脑脊液通路并引起梗阻性脑积水。' },
      { id: 'cerebral_aqueduct', name: '中脑水管', category: '狭窄通道', description: '穿过中脑，连接第三和第四脑室。', clinical_note: '中脑水管狭窄是梗阻性脑积水的重要原因。' },
      { id: 'fourth_ventricle', name: '第四脑室', category: '脑室', description: '位于脑桥、延髓与小脑之间，通过孔道与蛛网膜下腔相通。', clinical_note: '后颅窝病变可能压迫第四脑室并影响脑脊液循环。' }
    ],
    source_label: 'Blausen Medical · NI079 · CC BY 3.0'
  },
  {
    id: 'csf_system_detail', system: '神经系统', title: '脑脊液循环系统', subtitle: '第三层：脑室产生、循环与蛛网膜下腔回流', level: 'detail', parent_id: 'brain_ventricles_detail',
    image: csfSystemDetail, image_aspect: '1024 / 768', description: '脑脊液主要由脉络丛产生，经脑室系统流入蛛网膜下腔，最终回吸收入静脉循环。', instruction: '点击脑室和蛛网膜下腔查看循环路径',
    hotspots: [
      { id: 'csf_lateral_hs', label: '侧脑室', x: 44, y: 31, width: 27, height: 22, structure_id: 'csf_production' },
      { id: 'csf_third_hs', label: '第三脑室', x: 46, y: 44, width: 18, height: 16, structure_id: 'csf_third' },
      { id: 'csf_fourth_hs', label: '第四脑室', x: 58, y: 58, width: 18, height: 19, structure_id: 'csf_fourth' },
      { id: 'subarachnoid_space_hs', label: '蛛网膜下腔', x: 55, y: 34, width: 52, height: 58, structure_id: 'subarachnoid_space' }
    ],
    structures: [
      { id: 'csf_production', name: '侧脑室与脉络丛', category: '脑脊液产生', description: '脉络丛是脑脊液产生的主要部位。', clinical_note: '脑脊液产生、循环或吸收失衡均可能造成脑积水。' },
      { id: 'csf_third', name: '第三脑室通路', category: '脑脊液循环', description: '侧脑室经室间孔进入第三脑室，再经中脑水管向后流动。', clinical_note: '中脑水管是脑脊液通路的狭窄部位。' },
      { id: 'csf_fourth', name: '第四脑室出口', category: '脑脊液循环', description: '脑脊液由第四脑室孔进入蛛网膜下腔。', clinical_note: '第四脑室出口受阻可导致梗阻性脑积水。' },
      { id: 'subarachnoid_space', name: '蛛网膜下腔', category: '脑脊液循环', description: '脑脊液环绕脑和脊髓，起缓冲和内环境调节作用。', clinical_note: '腰椎穿刺通常在低位腰椎间隙获取脑脊液。' }
    ], source_label: 'Blausen Medical · NI080 · CC BY 3.0'
  },
  {
    id: 'cranial_nerves_detail',
    system: '神经系统',
    title: '十二对脑神经总览',
    subtitle: '第二层：从脑底辨认感觉、运动与混合性脑神经',
    level: 'organ',
    parent_id: 'nervous_overview',
    image: cranialNervesDetail,
    image_aspect: '2250 / 1350',
    description: '十二对脑神经与嗅觉、视觉、眼球运动、面部感觉和运动、听觉平衡、吞咽、内脏调节及舌运动等功能相关。',
    instruction: '点击功能分组查看常用查体和定位提示',
    hotspots: [
      { id: 'cn_special_senses_hs', label: 'Ⅰ、Ⅱ、Ⅷ 特殊感觉', x: 65, y: 17, width: 42, height: 25, structure_id: 'cn_special_senses' },
      { id: 'cn_eye_movement_hs', label: 'Ⅲ、Ⅳ、Ⅵ 眼球运动', x: 69, y: 31, width: 42, height: 16, structure_id: 'cn_eye_movement' },
      { id: 'cn_face_hs', label: 'Ⅴ、Ⅶ 面部功能', x: 70, y: 47, width: 43, height: 23, structure_id: 'cn_face' },
      { id: 'cn_bulbar_hs', label: 'Ⅸ—Ⅻ 后组脑神经', x: 70, y: 76, width: 48, height: 31, structure_id: 'cn_bulbar' }
    ],
    structures: [
      { id: 'cn_special_senses', name: '嗅、视与前庭蜗神经', category: '特殊感觉', description: 'Ⅰ、Ⅱ、Ⅷ分别主要传递嗅觉、视觉以及听觉和平衡信息。', clinical_note: '检查嗅觉、视力视野和听力平衡有助于神经定位。' },
      { id: 'cn_eye_movement', name: '动眼、滑车与展神经', category: '眼球运动', description: 'Ⅲ、Ⅳ、Ⅵ共同支配眼外肌并参与瞳孔反射。', clinical_note: '复视方向、眼位和瞳孔变化可帮助区分受损神经。' },
      { id: 'cn_face', name: '三叉与面神经', category: '面部感觉与运动', description: 'Ⅴ主要负责面部感觉和咀嚼，Ⅶ主要负责面肌运动并参与味觉。', clinical_note: '角膜反射传入支主要为Ⅴ1，传出支主要为Ⅶ。' },
      { id: 'cn_bulbar', name: '后组脑神经', category: '延髓相关神经', description: 'Ⅸ—Ⅻ参与吞咽、发声、内脏调节、肩颈运动和舌运动。', clinical_note: '构音、吞咽、咽反射、耸肩和伸舌检查用于后组脑神经评估。' }
    ],
    source_label: 'Blausen Medical · NI078 · CC BY 3.0'
  },
  {
    id: 'spinal_cord_section_detail',
    system: '神经系统',
    title: '脊髓横断面精细图',
    subtitle: '第二层：灰质角、白质索、神经根与中央管',
    level: 'organ',
    parent_id: 'nervous_overview',
    image: spinalCordSectionDetail,
    image_aspect: '1200 / 1200',
    description: '脊髓横断面中央为蝶形灰质，外围为白质；背根传入感觉信息，腹根发出运动信息。',
    instruction: '点击灰质、白质和神经根辨认传入传出关系',
    hotspots: [
      { id: 'posterior_horn_hs', label: '后角', x: 68, y: 43, width: 17, height: 20, structure_id: 'posterior_horn' },
      { id: 'anterior_horn_hs', label: '前角', x: 67, y: 62, width: 18, height: 22, structure_id: 'anterior_horn' },
      { id: 'white_columns_hs', label: '白质索', x: 62, y: 48, width: 48, height: 47, structure_id: 'white_columns' },
      { id: 'dorsal_root_hs', label: '后根与脊神经节', x: 31, y: 44, width: 26, height: 19, structure_id: 'dorsal_root' },
      { id: 'ventral_root_hs', label: '前根', x: 31, y: 67, width: 24, height: 16, structure_id: 'ventral_root' },
      { id: 'sensory_pathway_entry_hs', label: '感觉上行束', x: 60, y: 19, width: 26, height: 15, target_id: 'spinal_sensory_pathways_detail' },
      { id: 'motor_pathway_entry_hs', label: '运动下行束', x: 60, y: 84, width: 26, height: 15, target_id: 'spinal_motor_pathways_detail' }
    ],
    structures: [
      { id: 'posterior_horn', name: '灰质后角', category: '感觉中继', description: '接受由后根进入的躯体和内脏感觉信息。', clinical_note: '后角及感觉通路损害可产生节段性或传导束性感觉异常。' },
      { id: 'anterior_horn', name: '灰质前角', category: '躯体运动', description: '含下运动神经元，其轴突经前根离开脊髓。', clinical_note: '前角细胞损害表现为弛缓性无力、肌萎缩和反射减弱。' },
      { id: 'white_columns', name: '白质索', category: '传导束区域', description: '前、侧、后索包含多条上行感觉和下行运动传导束。', clinical_note: '不同束路受损可形成具有定位意义的感觉运动组合。' },
      { id: 'dorsal_root', name: '后根与脊神经节', category: '感觉传入', description: '后根携带传入纤维，胞体主要位于脊神经节。', clinical_note: '神经根病常沿相应皮节出现疼痛或感觉异常。' },
      { id: 'ventral_root', name: '前根', category: '运动传出', description: '主要携带来自脊髓前角的运动传出纤维。', clinical_note: '前根受损可导致相应肌群下运动神经元体征。' }
    ],
    source_label: 'Blausen Medical · NI081 · CC BY-SA 4.0'
  },
  {
    id: 'brain_layers_detail', system: '神经系统', title: '脑膜与颅脑覆盖层', subtitle: '第三层：从头皮、颅骨进入硬膜与蛛网膜下腔', level: 'detail', parent_id: 'brain_lobes_detail',
    image: brainLayersDetail, image_aspect: '1500 / 1500', description: '脑由头皮、颅骨和三层脑膜保护，脑脊液位于蛛网膜下腔并包绕中枢神经系统。', instruction: '点击覆盖层与间隙查看保护作用和临床意义',
    hotspots: [
      { id: 'scalp_hs', label: '头皮', x: 50, y: 37, width: 55, height: 14, structure_id: 'scalp' },
      { id: 'skull_layer_hs', label: '颅骨', x: 43, y: 48, width: 63, height: 15, structure_id: 'skull_layer' },
      { id: 'dura_hs', label: '硬脑膜', x: 38, y: 58, width: 63, height: 13, structure_id: 'dura_mater' },
      { id: 'subarachnoid_hs', label: '蛛网膜下腔', x: 60, y: 68, width: 66, height: 19, structure_id: 'subarachnoid_layer' }
    ],
    structures: [
      { id: 'scalp', name: '头皮', category: '颅外覆盖层', description: '由皮肤、致密结缔组织、帽状腱膜等层次组成。', clinical_note: '头皮血供丰富，裂伤可能出血明显。' },
      { id: 'skull_layer', name: '颅骨与骨膜', category: '骨性保护', description: '颅骨形成坚硬颅腔，外覆骨膜并保护脑组织。', clinical_note: '颅骨骨折的部位和走向可提示邻近血管或脑膜风险。' },
      { id: 'dura_mater', name: '硬脑膜', category: '脑膜', description: '最外层脑膜，在特定部位形成硬膜隔和静脉窦。', clinical_note: '硬膜外与硬膜下出血的来源和影像形态不同。' },
      { id: 'subarachnoid_layer', name: '蛛网膜下腔', category: '脑膜间隙', description: '位于蛛网膜与软脑膜之间，内含脑脊液和血管。', clinical_note: '蛛网膜下腔出血常出现突发剧烈头痛。' }
    ], source_label: 'Blausen Medical · NI074 · CC BY 3.0'
  },
  {
    id: 'spinal_sensory_pathways_detail', system: '神经系统', title: '脊髓感觉上行通路', subtitle: '第三层：后索、脊髓丘脑束与脊髓小脑束', level: 'detail', parent_id: 'spinal_cord_section_detail',
    image: spinalSensoryPathwaysDetail, image_aspect: '2500 / 2500', description: '感觉信息通过不同上行束传向脑干、丘脑与小脑，各束传递的感觉模态和交叉位置不同。', instruction: '点击彩色束区区分感觉模态',
    hotspots: [
      { id: 'posterior_columns_hs', label: '后索', x: 61, y: 39, width: 25, height: 24, structure_id: 'posterior_columns' },
      { id: 'spinothalamic_hs', label: '脊髓丘脑束', x: 71, y: 65, width: 24, height: 20, structure_id: 'spinothalamic' },
      { id: 'spinocerebellar_hs', label: '脊髓小脑束', x: 42, y: 57, width: 17, height: 29, structure_id: 'spinocerebellar' },
      { id: 'sensory_dorsal_root_hs', label: '后根与脊神经节', x: 31, y: 45, width: 26, height: 21, structure_id: 'sensory_dorsal_root' }
    ],
    structures: [
      { id: 'posterior_columns', name: '薄束与楔束（后索）', category: '上行感觉束', description: '主要传递精细触觉、振动觉和意识性本体感觉。', clinical_note: '后索损害可造成同侧振动觉和位置觉下降。' },
      { id: 'spinothalamic', name: '脊髓丘脑束', category: '上行感觉束', description: '主要传递痛温觉及部分粗触觉，纤维在脊髓节段附近交叉。', clinical_note: '束路定位需结合交叉位置解释感觉平面。' },
      { id: 'spinocerebellar', name: '脊髓小脑束', category: '上行感觉束', description: '将非意识性本体感觉送入小脑，参与姿势和运动协调。', clinical_note: '损害可出现同侧肢体共济失调。' },
      { id: 'sensory_dorsal_root', name: '后根与脊神经节', category: '感觉入口', description: '初级感觉神经元胞体位于脊神经节，轴突经后根进入脊髓。', clinical_note: '神经根受累常呈皮节性疼痛或感觉异常。' }
    ], source_label: 'Blausen Medical · NI082 · CC BY-SA 4.0'
  },
  {
    id: 'spinal_motor_pathways_detail', system: '神经系统', title: '脊髓运动下行通路', subtitle: '第三层：皮质脊髓束与脑干下行束', level: 'detail', parent_id: 'spinal_cord_section_detail',
    image: spinalMotorPathwaysDetail, image_aspect: '2200 / 2300', description: '下行运动束把大脑皮质和脑干的运动指令传向脊髓前角，调控随意运动、姿势和肌张力。', instruction: '点击主要下行束查看功能',
    hotspots: [
      { id: 'lateral_corticospinal_hs', label: '外侧皮质脊髓束', x: 67, y: 52, width: 19, height: 22, structure_id: 'lateral_corticospinal' },
      { id: 'anterior_corticospinal_hs', label: '前皮质脊髓束', x: 51, y: 64, width: 16, height: 22, structure_id: 'anterior_corticospinal' },
      { id: 'rubrospinal_hs', label: '红核脊髓束', x: 70, y: 61, width: 16, height: 18, structure_id: 'rubrospinal' },
      { id: 'brainstem_motor_tracts_hs', label: '前索脑干下行束', x: 47, y: 72, width: 31, height: 18, structure_id: 'brainstem_motor_tracts' }
    ],
    structures: [
      { id: 'lateral_corticospinal', name: '外侧皮质脊髓束', category: '锥体束', description: '大多数纤维在延髓锥体交叉后下行，精细调控远端肢体运动。', clinical_note: '脊髓内损害常引起病变以下同侧上运动神经元体征。' },
      { id: 'anterior_corticospinal', name: '前皮质脊髓束', category: '锥体束', description: '主要影响躯干和近端肌群，许多纤维在节段水平双侧投射。', clinical_note: '双侧支配使部分中轴肌功能在单侧病变后相对保留。' },
      { id: 'rubrospinal', name: '红核脊髓束', category: '脑干下行束', description: '起自红核并参与上肢屈肌活动调节，在人类作用相对次要。', clinical_note: '与其他下行系统共同影响异常姿势和肌张力。' },
      { id: 'brainstem_motor_tracts', name: '前庭、网状与顶盖脊髓束', category: '脑干下行束', description: '共同参与平衡、姿势、肌张力及头眼定向反应。', clinical_note: '脑干或脊髓病变可通过这些通路影响姿势控制。' }
    ], source_label: 'Blausen Medical · NI083 · CC BY-SA 4.0'
  },
  {
    id: 'multipolar_neuron_detail', system: '神经系统', title: '多极神经元结构', subtitle: '第二层：树突、胞体、轴突与突触末梢', level: 'organ', parent_id: 'nervous_overview',
    image: multipolarNeuronDetail, image_aspect: '2500 / 1612', description: '多极神经元通过树突接收信息，胞体整合信号，轴突将动作电位传至其他细胞。', instruction: '点击神经元各区查看信息流向',
    hotspots: [
      { id: 'neuron_dendrites_hs', label: '树突', x: 18, y: 51, width: 32, height: 72, structure_id: 'neuron_dendrites' },
      { id: 'neuron_soma_hs', label: '胞体与细胞核', x: 28, y: 52, width: 26, height: 35, structure_id: 'neuron_soma' },
      { id: 'neuron_axon_hs', label: '轴突', x: 57, y: 37, width: 52, height: 30, structure_id: 'neuron_axon' },
      { id: 'synaptic_terminals_hs', label: '突触末梢', x: 81, y: 34, width: 24, height: 35, structure_id: 'synaptic_terminals' }
    ],
    structures: [
      { id: 'neuron_dendrites', name: '树突', category: '输入区', description: '多分支突起扩大接收面积，接受来自其他神经元的突触输入。', clinical_note: '树突棘可随学习和疾病发生可塑性改变。' },
      { id: 'neuron_soma', name: '胞体与细胞核', category: '整合与代谢中心', description: '含细胞核和丰富细胞器，维持神经元代谢并整合输入。', clinical_note: '神经元胞体受损通常难以通过细胞分裂补充。' },
      { id: 'neuron_axon', name: '轴突与轴丘', category: '传导区', description: '动作电位常在轴丘附近触发并沿轴突向远端传播。', clinical_note: '脱髓鞘或轴索损伤会降低神经传导效率。' },
      { id: 'synaptic_terminals', name: '轴突终末与突触', category: '输出区', description: '终末释放神经递质，将信息传向下一个细胞。', clinical_note: '多种药物和毒素通过影响递质释放或受体发挥作用。' }
    ], source_label: 'Blausen Medical · NI086 · CC BY 3.0'
  },
  {
    id: 'sympathetic_innervation_detail', system: '神经系统', title: '交感神经支配总览', subtitle: '第二层：胸腰部起源、交感链与内脏神经', level: 'organ', parent_id: 'nervous_overview',
    image: sympatheticInnervationDetail, image_aspect: '1600 / 2000', description: '交感神经节前纤维主要起自胸腰段脊髓，经交感链或椎前神经节换元后支配全身器官。', instruction: '点击交感链、内脏神经和靶器官查看通路',
    hotspots: [
      { id: 'sympathetic_chain_hs', label: '交感干神经节', x: 28, y: 56, width: 25, height: 62, structure_id: 'sympathetic_chain' },
      { id: 'sympathetic_splanchnic_hs', label: '内脏神经与椎前节', x: 51, y: 54, width: 34, height: 31, structure_id: 'sympathetic_splanchnic' },
      { id: 'sympathetic_cardiopulmonary_hs', label: '心肺交感支配', x: 71, y: 29, width: 35, height: 28, structure_id: 'sympathetic_cardiopulmonary' },
      { id: 'sympathetic_abdominal_hs', label: '腹盆腔器官支配', x: 75, y: 62, width: 42, height: 53, structure_id: 'sympathetic_abdominal' }
    ],
    structures: [
      { id: 'sympathetic_chain', name: '交感干（交感链）', category: '椎旁神经节', description: '位于脊柱两侧，允许交感纤维上下行并分配至不同节段。', clinical_note: '颈交感通路受损可产生Horner综合征。' },
      { id: 'sympathetic_splanchnic', name: '内脏神经与椎前神经节', category: '腹盆腔通路', description: '节前纤维经内脏神经到达腹腔、肠系膜等椎前神经节换元。', clinical_note: '腹腔神经丛与部分内脏痛和介入镇痛相关。' },
      { id: 'sympathetic_cardiopulmonary', name: '心肺交感支配', category: '胸腔脏器', description: '可提高心率和心肌收缩力，并促进支气管舒张。', clinical_note: '自主神经平衡影响心率、血压和心律。' },
      { id: 'sympathetic_abdominal', name: '腹盆腔器官交感支配', category: '内脏调节', description: '参与消化道运动、血管张力、膀胱和生殖功能调节。', clinical_note: '自主神经病变可出现胃肠、排尿和性功能异常。' }
    ], source_label: 'Blausen Medical · NI087 · CC BY 3.0'
  },
  {
    id: 'parasympathetic_innervation_detail', system: '神经系统', title: '副交感神经支配总览', subtitle: '第二层：脑干与骶髓起源、迷走神经及盆神经', level: 'organ', parent_id: 'nervous_overview',
    image: parasympatheticInnervationDetail, image_aspect: '1600 / 2000', description: '副交感神经节前纤维起自脑干和骶髓，通过相关脑神经及盆内脏神经到达靶器官附近换元。', instruction: '点击颅部、迷走和骶部通路查看支配范围',
    hotspots: [
      { id: 'cranial_para_hs', label: '颅部副交感通路', x: 61, y: 18, width: 48, height: 27, structure_id: 'cranial_para' },
      { id: 'vagus_hs', label: '迷走神经通路', x: 60, y: 48, width: 48, height: 50, structure_id: 'vagus_pathway' },
      { id: 'pelvic_para_hs', label: '盆内脏神经', x: 47, y: 75, width: 36, height: 25, structure_id: 'pelvic_para' },
      { id: 'terminal_ganglia_hs', label: '器官旁或壁内神经节', x: 78, y: 55, width: 38, height: 46, structure_id: 'terminal_ganglia' }
    ],
    structures: [
      { id: 'cranial_para', name: '颅部副交感通路', category: '脑干起源', description: '通过Ⅲ、Ⅶ、Ⅸ脑神经相关通路调节瞳孔、泪腺和唾液腺。', clinical_note: '动眼神经副交感纤维受压可出现瞳孔散大。' },
      { id: 'vagus_pathway', name: '迷走神经', category: '脑干起源', description: '广泛支配胸腔和大部分腹腔脏器，参与心率和消化调节。', clinical_note: '迷走反射增强可引起心率减慢和血压下降。' },
      { id: 'pelvic_para', name: '盆内脏神经', category: '骶部起源', description: '起自骶髓S2—S4，支配远端结肠、膀胱和部分生殖器官。', clinical_note: '骶髓或盆神经损害可能导致膀胱直肠功能障碍。' },
      { id: 'terminal_ganglia', name: '器官旁或壁内神经节', category: '换元位置', description: '副交感神经节通常位于靶器官附近或器官壁内，因此节后纤维较短。', clinical_note: '该布局与交感神经的椎旁、椎前神经节形成对照。' }
    ], source_label: 'Blausen Medical · NI088 · CC BY 3.0'
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
      { id: 'endo_pancreas_hs', label: '胰腺与胰岛', x: 46, y: 70, width: 27, height: 13, target_id: 'pancreatic_islet_detail', structure_id: 'pancreatic_islet' },
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
    id: 'pancreatic_islet_detail', system: '内分泌系统', title: '胰岛与胰腺组织精细图', subtitle: '第二层：比较内分泌胰岛与外分泌腺泡', level: 'organ', parent_id: 'endocrine_overview',
    image: pancreaticIsletDetail, image_aspect: '2500 / 2500', description: '胰腺同时具有外分泌与内分泌功能。腺泡分泌消化酶，胰岛细胞通过丰富毛细血管向血液释放激素。', instruction: '点击胰岛、腺泡、胰管或血管查看差异',
    hotspots: [
      { id: 'pancreatic_islet_hs', label: '胰岛', x: 72, y: 62, width: 30, height: 28, structure_id: 'pancreatic_islet' },
      { id: 'pancreatic_acini_hs', label: '胰腺腺泡', x: 58, y: 62, width: 23, height: 30, structure_id: 'pancreatic_acini' },
      { id: 'pancreatic_duct_hs', label: '胰管', x: 67, y: 25, width: 27, height: 18, structure_id: 'pancreatic_duct' },
      { id: 'islet_capillary_hs', label: '胰岛毛细血管', x: 75, y: 65, width: 20, height: 18, structure_id: 'islet_capillary' }
    ],
    structures: [
      { id: 'pancreatic_islet', name: '胰岛', category: '内分泌部', description: '由多类内分泌细胞构成，分泌胰岛素、胰高血糖素等激素。', clinical_note: '胰岛β细胞功能和数量异常与糖尿病密切相关。' },
      { id: 'pancreatic_acini', name: '胰腺腺泡', category: '外分泌部', description: '腺泡细胞产生消化酶，经导管系统排入十二指肠。', clinical_note: '胰酶异常激活可参与急性胰腺炎。' },
      { id: 'pancreatic_duct', name: '胰管', category: '外分泌管道', description: '收集胰液并通常与胆总管共同或邻近开口于十二指肠。', clinical_note: '胰管扩张可能提示梗阻或慢性胰腺病变。' },
      { id: 'islet_capillary', name: '胰岛毛细血管', category: '内分泌血供', description: '丰富的有窗毛细血管有利于激素快速进入循环。', clinical_note: '内分泌腺体丰富血供是激素高效释放的结构基础。' }
    ], source_label: 'Blausen Medical · NI093 · CC BY 3.0'
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
      { id: 'heart_valves', label: '四组瓣膜', x: 50, y: 49, width: 42, height: 24, target_id: 'heart_chambers', structure_id: 'mitral_valve' },
      { id: 'heart_flow_hs', label: '心脏血流路径', x: 18, y: 84, width: 24, height: 18, target_id: 'heart_blood_flow_detail' },
      { id: 'heart_coronary_hs', label: '冠状动脉', x: 82, y: 84, width: 24, height: 18, target_id: 'coronary_arteries_detail' },
      { id: 'leg_veins_entry_hs', label: '下肢静脉', x: 82, y: 12, width: 24, height: 18, target_id: 'leg_veins_detail' }
    ],
    structures: [],
    source_label: 'Wikimedia Commons · CC BY-SA 3.0'
  },
  {
    id: 'heart_blood_flow_detail',
    system: '循环系统',
    title: '心脏血流路径图',
    subtitle: '第二层：静脉回流、肺循环和体循环出口',
    level: 'organ',
    parent_id: 'heart_overview',
    image: heartBloodFlowDetail,
    image_aspect: '768 / 1024',
    description: '静脉血经右心进入肺循环，氧合后回到左心，再由主动脉泵入体循环。箭头显示血流的单向路径。',
    instruction: '点击右心、肺循环、左心或主动脉查看路径',
    hotspots: [
      { id: 'flow_right_heart_hs', label: '右心血流', x: 37, y: 49, width: 34, height: 43, structure_id: 'flow_right_heart' },
      { id: 'flow_pulmonary_hs', label: '肺循环', x: 68, y: 31, width: 31, height: 25, structure_id: 'flow_pulmonary' },
      { id: 'flow_left_heart_hs', label: '左心血流', x: 65, y: 56, width: 30, height: 38, structure_id: 'flow_left_heart' },
      { id: 'flow_aorta_hs', label: '主动脉出口', x: 51, y: 20, width: 30, height: 22, structure_id: 'flow_aorta' }
    ],
    structures: [
      { id: 'flow_right_heart', name: '体静脉回流与右心', category: '低氧血路径', description: '体循环静脉血经腔静脉进入右心房，再经右心室射入肺动脉。', clinical_note: '右心衰竭可造成体静脉淤血和外周水肿。' },
      { id: 'flow_pulmonary', name: '肺循环', category: '气体交换循环', description: '肺动脉将低氧血送至肺，肺静脉将氧合血送回左心房。', clinical_note: '肺动脉承载低氧血、肺静脉承载氧合血，是血管命名中的重要例外。' },
      { id: 'flow_left_heart', name: '左心血流', category: '高氧血路径', description: '氧合血从左心房经二尖瓣进入左心室。', clinical_note: '左心功能下降可导致肺淤血和呼吸困难。' },
      { id: 'flow_aorta', name: '主动脉出口', category: '体循环起点', description: '左心室经主动脉瓣将血液射入主动脉和全身体循环。', clinical_note: '主动脉瓣狭窄会增加左心室射血阻力。' }
    ],
    source_label: 'Blausen Medical · NI057 · CC BY 3.0'
  },
  {
    id: 'coronary_arteries_detail',
    system: '循环系统',
    title: '冠状动脉精细图',
    subtitle: '第二层：左右冠状动脉及左冠主要分支',
    level: 'organ',
    parent_id: 'heart_overview',
    image: coronaryArteriesDetail,
    image_aspect: '4096 / 3072',
    description: '左右冠状动脉起自主动脉根部，沿心表面走行，为心肌提供血供。',
    instruction: '点击主要冠状动脉分支查看供血与临床意义',
    hotspots: [
      { id: 'right_coronary_hs', label: '右冠状动脉与动脉壁', x: 37, y: 53, width: 30, height: 28, target_id: 'artery_wall_detail', structure_id: 'tunica_intima' },
      { id: 'left_main_hs', label: '左冠状动脉主干', x: 61, y: 34, width: 26, height: 18, structure_id: 'left_main' },
      { id: 'lad_hs', label: '前室间支', x: 64, y: 64, width: 21, height: 36, structure_id: 'lad' },
      { id: 'circumflex_hs', label: '旋支', x: 72, y: 49, width: 25, height: 21, structure_id: 'circumflex' }
    ],
    structures: [
      { id: 'right_coronary', name: '右冠状动脉', category: '冠状动脉', description: '沿右冠状沟走行，常发出右缘支和后室间支。', clinical_note: '供血优势型由后室间支的来源判定，多数人为右优势型。' },
      { id: 'left_main', name: '左冠状动脉主干', category: '冠状动脉', description: '起自左主动脉窦，通常分为前室间支和旋支。', clinical_note: '左主干严重狭窄可危及大范围心肌。' },
      { id: 'lad', name: '前室间支', category: '左冠分支', description: '沿前室间沟下行，主要供应前壁、心尖和室间隔前部。', clinical_note: '前室间支闭塞是前壁心肌梗死的重要原因。' },
      { id: 'circumflex', name: '旋支', category: '左冠分支', description: '沿左侧房室沟绕向后方，供应左心房和左室外侧壁等区域。', clinical_note: '旋支病变可能造成侧壁或后壁心肌缺血。' }
    ],
    source_label: 'Blausen Medical · NI065 · CC BY 3.0'
  },
  {
    id: 'artery_wall_detail', system: '循环系统', title: '动脉壁精细结构', subtitle: '第三层：内膜、中膜、外膜与弹性膜', level: 'detail', parent_id: 'coronary_arteries_detail',
    image: arteryWallDetail, image_aspect: '2500 / 2500', description: '典型动脉壁由内膜、中膜和外膜构成，各层在血管顺应性、张力调节和结构支持中承担不同作用。', instruction: '点击血管壁各层查看组织结构与病理关联',
    hotspots: [
      { id: 'tunica_intima_hs', label: '内膜', x: 73, y: 57, width: 17, height: 34, structure_id: 'tunica_intima' },
      { id: 'tunica_media_hs', label: '中膜', x: 62, y: 57, width: 21, height: 39, structure_id: 'tunica_media' },
      { id: 'tunica_externa_hs', label: '外膜', x: 48, y: 58, width: 19, height: 41, structure_id: 'tunica_externa' },
      { id: 'elastic_membranes_hs', label: '弹性膜', x: 58, y: 68, width: 31, height: 31, structure_id: 'elastic_membranes' }
    ],
    structures: [
      { id: 'tunica_intima', name: '内膜', category: '动脉壁', description: '由内皮和薄层结缔组织构成，直接接触血流。', clinical_note: '动脉粥样硬化病变起始于内膜区域。' },
      { id: 'tunica_media', name: '中膜', category: '动脉壁', description: '富含平滑肌和弹性成分，调节血管口径和张力。', clinical_note: '中膜结构异常可影响血管强度和顺应性。' },
      { id: 'tunica_externa', name: '外膜', category: '动脉壁', description: '以结缔组织为主，将血管固定于周围组织。', clinical_note: '大血管外膜可含滋养血管和神经。' },
      { id: 'elastic_membranes', name: '内、外弹性膜', category: '弹性结构', description: '将动脉壁层次分隔并参与血管弹性回缩。', clinical_note: '弹性结构对维持脉动血流和舒张期灌注有重要作用。' }
    ], source_label: 'Blausen Medical · NI068 · CC BY 3.0'
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
    id: 'leg_veins_detail', system: '循环系统', title: '下肢静脉回流图', subtitle: '第二层：深静脉、浅静脉与隐股交界', level: 'organ', parent_id: 'heart_overview',
    image: legVeinsDetail, image_aspect: '1000 / 1500', description: '下肢静脉由深、浅两套系统组成，经穿通静脉相连并依靠静脉瓣和肌泵促进血液回流。', instruction: '点击主要深浅静脉查看走行和临床意义',
    hotspots: [
      { id: 'common_femoral_vein_hs', label: '股总静脉', x: 54, y: 25, width: 20, height: 19, structure_id: 'common_femoral_vein' },
      { id: 'femoral_vein_hs', label: '股静脉', x: 54, y: 43, width: 20, height: 31, structure_id: 'femoral_vein' },
      { id: 'great_saphenous_hs', label: '大隐静脉', x: 38, y: 54, width: 25, height: 58, structure_id: 'great_saphenous' },
      { id: 'popliteal_vein_hs', label: '腘静脉', x: 56, y: 64, width: 20, height: 18, structure_id: 'popliteal_vein' },
      { id: 'small_saphenous_hs', label: '小隐静脉', x: 72, y: 76, width: 24, height: 34, structure_id: 'small_saphenous' }
    ],
    structures: [
      { id: 'common_femoral_vein', name: '股总静脉', category: '深静脉', description: '位于腹股沟韧带下方，接收股静脉及大隐静脉等回流。', clinical_note: '该区域是中心静脉通路和血栓超声评估的重要部位。' },
      { id: 'femoral_vein', name: '股静脉', category: '深静脉', description: '伴随股动脉走行，是下肢深静脉回流的主干。', clinical_note: '近端深静脉血栓具有肺栓塞风险。' },
      { id: 'great_saphenous', name: '大隐静脉', category: '浅静脉', description: '自足内侧沿小腿和大腿内侧上行，汇入股静脉。', clinical_note: '常见于静脉曲张，也可作为血管移植材料。' },
      { id: 'popliteal_vein', name: '腘静脉', category: '深静脉', description: '位于腘窝，向上延续为股静脉。', clinical_note: '腘静脉血栓属于近端深静脉血栓。' },
      { id: 'small_saphenous', name: '小隐静脉', category: '浅静脉', description: '由足外侧向小腿后方上行，通常汇入腘静脉。', clinical_note: '隐腘交界解剖变异较多，术前常需超声定位。' }
    ], source_label: 'Blausen Medical · NI069 · CC BY 3.0'
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
      { id: 'digestive_rectum', label: '直肠', x: 50, y: 79, width: 20, height: 13, target_id: 'rectum_detail' },
      { id: 'digestive_small_intestine', label: '空肠与回肠', x: 50, y: 58, width: 35, height: 24, target_id: 'small_intestine_detail' },
      { id: 'digestive_pancreas', label: '胰腺与胆道', x: 50, y: 38, width: 34, height: 16, target_id: 'pancreas_biliary_detail' },
      { id: 'digestive_oral', label: '口腔', x: 50, y: 8, width: 30, height: 12, target_id: 'oral_cavity_detail' },
      { id: 'digestive_liver', label: '肝脏', x: 36, y: 31, width: 33, height: 17, target_id: 'liver_detail' }
    ],
    structures: [],
    source_label: 'Wikimedia Commons · Public domain'
  },
  {
    id: 'small_intestine_detail', system: '消化系统', title: '小肠分段图', subtitle: '第二层：十二指肠、空肠与回肠', level: 'organ', parent_id: 'digestive_overview',
    image: smallIntestineDetail, image_aspect: '1500 / 1500', description: '小肠自幽门延续至回盲部，包括十二指肠、空肠和回肠，是消化吸收的主要场所。', instruction: '点击小肠各段查看位置与功能差异',
    hotspots: [
      { id: 'small_duodenum_hs', label: '十二指肠', x: 48, y: 48, width: 22, height: 18, structure_id: 'small_duodenum' },
      { id: 'jejunum_hs', label: '空肠', x: 55, y: 61, width: 35, height: 24, structure_id: 'jejunum' },
      { id: 'ileum_hs', label: '回肠', x: 57, y: 75, width: 36, height: 25, structure_id: 'ileum' },
      { id: 'ileocecal_hs', label: '回盲连接', x: 38, y: 72, width: 18, height: 18, structure_id: 'ileocecal_junction' }
    ],
    structures: [
      { id: 'small_duodenum', name: '十二指肠', category: '小肠起始段', description: '呈C形环绕胰头，接受胆汁和胰液。', clinical_note: '大乳头区域与胆胰疾病及内镜操作密切相关。' },
      { id: 'jejunum', name: '空肠', category: '小肠', description: '通常位于腹腔左上部，管径和环形皱襞相对明显。', clinical_note: '空回肠的血管弓和直血管形态有助于术中辨认。' },
      { id: 'ileum', name: '回肠', category: '小肠', description: '多位于右下腹和盆腔，末端接入盲肠。', clinical_note: '末端回肠是克罗恩病等疾病的常见受累部位。' },
      { id: 'ileocecal_junction', name: '回盲连接', category: '小肠末端', description: '回肠末端经回盲瓣进入盲肠。', clinical_note: '右下腹病变评估常需同时观察末端回肠、盲肠和阑尾。' }
    ], source_label: 'Blausen Medical · NI020 · CC BY 3.0'
  },
  {
    id: 'pancreas_biliary_detail', system: '消化系统', title: '胰腺、胆囊与十二指肠关系图', subtitle: '第二层：胰头体尾、胰管和胆总管', level: 'organ', parent_id: 'digestive_overview',
    image: pancreasBiliaryDetail, image_aspect: '2500 / 2000', description: '胰头被十二指肠环抱，胰管贯穿胰腺，胆总管与胰管在十二指肠降部附近开口。', instruction: '点击胰腺分部和胆胰管道查看毗邻关系',
    hotspots: [
      { id: 'pancreas_head_hs', label: '胰头', x: 54, y: 69, width: 24, height: 24, structure_id: 'pancreas_head' },
      { id: 'pancreas_body_hs', label: '胰体', x: 70, y: 56, width: 29, height: 23, structure_id: 'pancreas_body' },
      { id: 'pancreas_tail_hs', label: '胰尾', x: 88, y: 42, width: 20, height: 21, structure_id: 'pancreas_tail' },
      { id: 'common_bile_duct_hs', label: '胆总管与胆囊', x: 48, y: 58, width: 15, height: 28, target_id: 'gallbladder_detail', structure_id: 'common_bile_duct' },
      { id: 'pancreatic_duct_detail_hs', label: '主胰管', x: 70, y: 48, width: 40, height: 17, structure_id: 'main_pancreatic_duct' }
    ],
    structures: [
      { id: 'pancreas_head', name: '胰头', category: '胰腺分部', description: '位于十二指肠C形弯内，钩突向后内侧延伸。', clinical_note: '胰头占位可压迫胆总管并出现梗阻性黄疸。' },
      { id: 'pancreas_body', name: '胰体', category: '胰腺分部', description: '横跨腹主动脉和脊柱前方，位于胃后方。', clinical_note: '胰体病变症状可能较隐匿。' },
      { id: 'pancreas_tail', name: '胰尾', category: '胰腺分部', description: '向左延伸至脾门附近。', clinical_note: '胰尾手术需关注脾血管及脾脏。' },
      { id: 'common_bile_duct', name: '胆总管', category: '胆道', description: '输送胆汁并在胰头附近与主胰管关系密切。', clinical_note: '胆总管结石可同时引起胆道梗阻和胰腺炎。' },
      { id: 'main_pancreatic_duct', name: '主胰管', category: '胰管', description: '贯穿胰腺并收集外分泌胰液。', clinical_note: 'MRCP或ERCP可显示胆胰管道解剖和梗阻。' }
    ], source_label: 'Blausen Medical · NI028 · CC BY 3.0'
  },
  {
    id: 'oral_cavity_detail', system: '消化系统', title: '口腔精细解剖图', subtitle: '第二层：腭、悬雍垂、舌与口咽入口', level: 'organ', parent_id: 'digestive_overview',
    image: oralCavityDetail, image_aspect: '1024 / 768', description: '口腔是消化道入口，完成食物摄取、咀嚼、初步消化并参与吞咽和发音。', instruction: '点击腭、舌和扁桃体区域查看功能',
    hotspots: [
      { id: 'hard_palate_hs', label: '硬腭', x: 50, y: 22, width: 37, height: 18, structure_id: 'hard_palate' },
      { id: 'soft_palate_hs', label: '软腭', x: 50, y: 37, width: 44, height: 16, structure_id: 'soft_palate' },
      { id: 'uvula_hs', label: '悬雍垂', x: 50, y: 44, width: 14, height: 16, structure_id: 'uvula' },
      { id: 'tongue_hs', label: '舌', x: 50, y: 66, width: 49, height: 31, structure_id: 'tongue' },
      { id: 'tonsil_hs', label: '腭扁桃体', x: 30, y: 51, width: 15, height: 20, structure_id: 'palatine_tonsil' }
    ],
    structures: [
      { id: 'hard_palate', name: '硬腭', category: '口腔顶', description: '骨性结构将口腔与鼻腔前部隔开，提供舌挤压食团的支点。', clinical_note: '腭裂会影响进食、发音及中耳功能。' },
      { id: 'soft_palate', name: '软腭', category: '口腔顶', description: '肌性可动结构，吞咽时上抬以关闭鼻咽。', clinical_note: '软腭运动不对称可提示相关脑神经或肌肉异常。' },
      { id: 'uvula', name: '悬雍垂', category: '软腭', description: '位于软腭后缘正中，参与咽腔关闭与咽反射。', clinical_note: '观察悬雍垂偏斜可辅助评估迷走神经功能。' },
      { id: 'tongue', name: '舌', category: '肌性器官', description: '参与味觉、咀嚼、形成食团、吞咽和发音。', clinical_note: '伸舌偏斜可用于舌下神经定位。' },
      { id: 'palatine_tonsil', name: '腭扁桃体', category: '淋巴组织', description: '位于口咽侧壁的扁桃体窝内，是咽淋巴环组成部分。', clinical_note: '急性扁桃体炎或扁桃体周围脓肿可影响吞咽和气道。' }
    ], source_label: 'Blausen Medical · NI018 · CC BY 3.0'
  },
  {
    id: 'liver_detail', system: '消化系统', title: '肝脏整体解剖图', subtitle: '第二层：肝左右叶、膈面与肝门区域', level: 'organ', parent_id: 'digestive_overview',
    image: liverOrganDetail, image_aspect: '1200 / 900', description: '肝脏位于右上腹，是人体最大的实质性腺体，参与代谢、解毒、胆汁生成及多种蛋白合成。', instruction: '点击肝叶和肝门区域查看说明',
    hotspots: [
      { id: 'right_lobe_hs', label: '肝右叶', x: 41, y: 50, width: 52, height: 59, structure_id: 'right_lobe' },
      { id: 'left_lobe_hs', label: '肝左叶', x: 72, y: 48, width: 35, height: 42, structure_id: 'left_lobe' },
      { id: 'diaphragmatic_surface_hs', label: '膈面', x: 50, y: 27, width: 55, height: 21, structure_id: 'diaphragmatic_surface' },
      { id: 'porta_hepatis_hs', label: '肝门区域', x: 54, y: 66, width: 25, height: 22, structure_id: 'porta_hepatis' }
    ],
    structures: [
      { id: 'right_lobe', name: '肝右叶', category: '解剖分叶', description: '解剖体积较大，主要位于右季肋区。', clinical_note: '外科功能分段以门静脉、肝动脉和胆管分支为基础，并不等同于表面分叶。' },
      { id: 'left_lobe', name: '肝左叶', category: '解剖分叶', description: '跨越正中线延向左上腹，前方以镰状韧带与右叶分界。', clinical_note: '肝左叶与胃、小网膜等结构毗邻。' },
      { id: 'diaphragmatic_surface', name: '膈面', category: '肝表面', description: '光滑隆凸，贴近膈肌并与胸腔脏器隔膈相邻。', clinical_note: '肝上方病变或膈下积液可能刺激膈神经并产生肩部牵涉痛。' },
      { id: 'porta_hepatis', name: '肝门区域', category: '脏面结构', description: '肝固有动脉、门静脉和肝管等结构在此出入。', clinical_note: '肝十二指肠韧带内的门静脉三联结构是手术与影像定位重点。' }
    ], source_label: 'Blausen Medical · NI024 · CC BY-SA 4.0'
  },
  {
    id: 'gallbladder_detail', system: '消化系统', title: '胆囊与肝外胆道', subtitle: '第三层：胆囊、胆囊管、肝总管与胆总管', level: 'detail', parent_id: 'pancreas_biliary_detail',
    image: gallbladderOrganDetail, image_aspect: '1200 / 1200', description: '胆囊储存和浓缩胆汁，经胆囊管与肝总管汇合形成胆总管，将胆汁输送至十二指肠。', instruction: '点击胆囊和胆管辨认胆汁流向',
    hotspots: [
      { id: 'gallbladder_hs', label: '胆囊', x: 55, y: 57, width: 29, height: 40, structure_id: 'gallbladder' },
      { id: 'cystic_duct_hs', label: '胆囊管', x: 49, y: 42, width: 22, height: 20, structure_id: 'cystic_duct' },
      { id: 'common_hepatic_duct_hs', label: '肝总管', x: 42, y: 28, width: 18, height: 28, structure_id: 'common_hepatic_duct' },
      { id: 'bile_duct_hs', label: '胆总管', x: 43, y: 64, width: 17, height: 36, structure_id: 'bile_duct' }
    ],
    structures: [
      { id: 'gallbladder', name: '胆囊', category: '储胆器官', description: '位于肝脏脏面的胆囊窝，可分底、体和颈。', clinical_note: '胆囊结石和炎症常表现为右上腹痛。' },
      { id: 'cystic_duct', name: '胆囊管', category: '肝外胆道', description: '连接胆囊颈与肝总管，螺旋襞可维持管腔。', clinical_note: '胆囊管和肝总管解剖变异是胆囊手术的重要风险点。' },
      { id: 'common_hepatic_duct', name: '肝总管', category: '肝外胆道', description: '由左右肝管汇合形成，接收肝内产生的胆汁。', clinical_note: '肝门部梗阻可导致肝内胆管扩张。' },
      { id: 'bile_duct', name: '胆总管', category: '肝外胆道', description: '肝总管与胆囊管汇合后形成，向下进入十二指肠。', clinical_note: '胆总管结石可能引起梗阻性黄疸、胆管炎或胰腺炎。' }
    ], source_label: 'Blausen Medical · NI025 · CC BY-SA 4.0'
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

const rootBySystem: Record<string, string> = {
  运动系统: 'skeletal_overview', 循环系统: 'heart_overview', 呼吸系统: 'respiratory_overview', 消化系统: 'digestive_overview',
  泌尿系统: 'urinary_overview', 生殖系统: 'male_reproductive_overview', 神经系统: 'nervous_overview', 内分泌系统: 'endocrine_overview'
};
const primaryAssetIds = new Set([
  'NI001', 'NI003', 'NI005', 'NI009', 'NI010', 'NI011', 'NI013', 'NI015', 'NI018', 'NI020', 'NI021', 'NI022', 'NI024', 'NI025', 'NI028',
  'NI030', 'NI032', 'NI034', 'NI035', 'NI037', 'NI041', 'NI043', 'NI044', 'NI045', 'NI046', 'NI050', 'NI052', 'NI055', 'NI056',
  'NI057', 'NI059', 'NI066', 'NI068', 'NI069', 'NI074', 'NI075', 'NI076', 'NI078', 'NI079', 'NI080', 'NI081', 'NI082', 'NI083',
  'NI086', 'NI087', 'NI088', 'NI091', 'NI093'
]);

const appendedAtlasNodes: AnatomyAtlasNode[] = blausenAtlasAssets
  .filter((asset) => !primaryAssetIds.has(asset.id) && rootBySystem[asset.system] && blausenImage(asset.id))
  .map((asset) => ({
    id: `blausen_${asset.id.toLowerCase()}`,
    system: asset.system as AnatomySystemName,
    title: asset.topic,
    subtitle: `扩展图谱 · ${asset.id} · ${asset.level}`,
    level: asset.level === '精细结构' ? 'detail' : 'organ',
    parent_id: rootBySystem[asset.system],
    image: blausenImage(asset.id),
    image_aspect: '1 / 1',
    description: `${asset.topic}解剖图，按现有系统层级追加，可点击图片查看结构信息并进入相关知识图谱。`,
    instruction: '点击图片查看结构信息',
    hotspots: [{ id: `${asset.id}_image`, label: asset.topic, x: 50, y: 50, width: 100, height: 100, structure_id: `${asset.id}_structure` }],
    structures: [{ id: `${asset.id}_structure`, name: asset.topic, category: asset.level, description: `${asset.topic}的解剖形态、位置与毗邻关系。`, clinical_note: '可结合病例训练、体格检查和影像定位继续学习。' }],
    source_label: `Blausen Medical · ${asset.id} · ${asset.license}`
  }));

anatomyAtlasNodes.push(...appendedAtlasNodes);

export const anatomyAtlasSystems = ['运动系统', '循环系统', '呼吸系统', '消化系统', '泌尿系统', '生殖系统', '神经系统', '内分泌系统'] as const;
