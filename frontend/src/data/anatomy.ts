export const mockAnatomyExercises = [
  {
    "id": "heart_position",
    "title": "心脏定位",
    "system": "循环系统",
    "target": "心脏",
    "prompt": "请选择心脏的标准解剖位置。",
    "answer_zone": "left_chest",
    "standard_region": "left_chest",
    "explanation": "心脏位于纵隔内，体表投影略偏左。",
    "clinical_link": "点击心脏后推荐 ACS、心电图和胸痛病例。",
    "graph_node_ids": [
      "acs",
      "ecg",
      "case_emergency_chest_pain"
    ]
  },
  {
    "id": "aorta_course",
    "title": "主动脉定位",
    "system": "循环系统",
    "target": "主动脉",
    "prompt": "请选择主动脉的标准解剖位置。",
    "answer_zone": "midline_chest_abdomen",
    "standard_region": "midline_chest_abdomen",
    "explanation": "主动脉自胸部纵隔向下走行至腹部。",
    "clinical_link": "主动脉夹层鉴别需要结合胸背痛和CTA。",
    "graph_node_ids": [
      "aortic_dissection",
      "cta",
      "chest_pain"
    ]
  },
  {
    "id": "pulmonary_artery",
    "title": "肺动脉定位",
    "system": "循环系统",
    "target": "肺动脉",
    "prompt": "请选择肺动脉的标准解剖位置。",
    "answer_zone": "upper_mid_chest",
    "standard_region": "upper_mid_chest",
    "explanation": "肺动脉位于心脏流出道附近并进入双肺。",
    "clinical_link": "与肺栓塞和呼吸困难训练相关。",
    "graph_node_ids": [
      "pulmonary_embolism",
      "dyspnea"
    ]
  },
  {
    "id": "trachea",
    "title": "气管定位",
    "system": "呼吸系统",
    "target": "气管",
    "prompt": "请选择气管的标准解剖位置。",
    "answer_zone": "neck_midline",
    "standard_region": "neck_midline",
    "explanation": "气管位于颈部和上纵隔中线。",
    "clinical_link": "与呼吸困难、喘鸣和气道评估相关。",
    "graph_node_ids": [
      "dyspnea",
      "airway"
    ]
  },
  {
    "id": "left_lung",
    "title": "左肺定位",
    "system": "呼吸系统",
    "target": "左肺",
    "prompt": "请选择左肺的标准解剖位置。",
    "answer_zone": "left_lung",
    "standard_region": "left_lung",
    "explanation": "左肺位于左胸腔，分为上叶和下叶。",
    "clinical_link": "点击肺后推荐呼吸困难、肺栓塞和胸部影像。",
    "graph_node_ids": [
      "dyspnea",
      "pulmonary_embolism",
      "chest_xray"
    ]
  },
  {
    "id": "right_lung",
    "title": "右肺定位",
    "system": "呼吸系统",
    "target": "右肺",
    "prompt": "请选择右肺的标准解剖位置。",
    "answer_zone": "right_lung",
    "standard_region": "right_lung",
    "explanation": "右肺位于右胸腔，通常分为上中下三叶。",
    "clinical_link": "与肺炎、COPD和胸片判读相关。",
    "graph_node_ids": [
      "pneumonia",
      "copd",
      "chest_xray"
    ]
  },
  {
    "id": "liver_position",
    "title": "肝脏定位",
    "system": "消化系统",
    "target": "肝脏",
    "prompt": "请选择肝脏的标准解剖位置。",
    "answer_zone": "right_upper_abdomen",
    "standard_region": "right_upper_abdomen",
    "explanation": "肝脏主要位于右上腹，部分越过正中线。",
    "clinical_link": "点击肝脏后推荐黄疸、肝功能和腹部超声。",
    "graph_node_ids": [
      "jaundice",
      "liver_function",
      "abdominal_ultrasound"
    ]
  },
  {
    "id": "stomach_position",
    "title": "胃定位",
    "system": "消化系统",
    "target": "胃",
    "prompt": "请选择胃的标准解剖位置。",
    "answer_zone": "left_upper_abdomen",
    "standard_region": "left_upper_abdomen",
    "explanation": "胃主要位于左上腹和上腹部，毗邻肝左叶、脾脏和胰腺。",
    "clinical_link": "与上腹痛和消化系统鉴别相关。",
    "graph_node_ids": [
      "abdominal_pain",
      "pancreatitis"
    ]
  },
  {
    "id": "pancreas_position",
    "title": "胰腺定位",
    "system": "消化系统",
    "target": "胰腺",
    "prompt": "请选择胰腺的标准解剖位置。",
    "answer_zone": "epigastrium",
    "standard_region": "epigastrium",
    "explanation": "胰腺位于上腹部偏后方。",
    "clinical_link": "急性胰腺炎训练需结合淀粉酶和腹部CT。",
    "graph_node_ids": [
      "pancreatitis",
      "amylase"
    ]
  },
  {
    "id": "gallbladder_position",
    "title": "胆囊定位",
    "system": "消化系统",
    "target": "胆囊",
    "prompt": "请选择胆囊的标准解剖位置。",
    "answer_zone": "right_upper_abdomen",
    "standard_region": "right_upper_abdomen",
    "explanation": "胆囊位于肝脏下方右上腹区域。",
    "clinical_link": "与胆囊炎、黄疸和腹部超声相关。",
    "graph_node_ids": [
      "cholecystitis",
      "jaundice"
    ]
  },
  {
    "id": "small_intestine",
    "title": "小肠定位",
    "system": "消化系统",
    "target": "小肠",
    "prompt": "请选择小肠的标准解剖位置。",
    "answer_zone": "central_abdomen",
    "standard_region": "central_abdomen",
    "explanation": "小肠主要位于中腹部。",
    "clinical_link": "与肠梗阻、腹痛和脱水评估相关。",
    "graph_node_ids": [
      "acute_abdomen",
      "abdominal_pain"
    ]
  },
  {
    "id": "large_intestine",
    "title": "大肠定位",
    "system": "消化系统",
    "target": "大肠",
    "prompt": "请选择大肠的标准解剖位置。",
    "answer_zone": "colon_frame",
    "standard_region": "colon_frame",
    "explanation": "大肠呈框架样围绕腹腔。",
    "clinical_link": "与腹痛、便血和肠梗阻相关。",
    "graph_node_ids": [
      "acute_abdomen",
      "abdominal_ct"
    ]
  },
  {
    "id": "kidney_position",
    "title": "肾脏定位",
    "system": "泌尿系统",
    "target": "肾脏",
    "prompt": "请选择肾脏的标准解剖位置。",
    "answer_zone": "flank_bilateral",
    "standard_region": "flank_bilateral",
    "explanation": "双肾位于腹膜后脊柱两侧。",
    "clinical_link": "与腰痛、尿检和肾功能评估相关。",
    "graph_node_ids": [
      "urinalysis",
      "renal_function"
    ]
  },
  {
    "id": "ureter_course",
    "title": "输尿管定位",
    "system": "泌尿系统",
    "target": "输尿管",
    "prompt": "请选择输尿管的标准解剖位置。",
    "answer_zone": "ureter_bilateral",
    "standard_region": "ureter_bilateral",
    "explanation": "输尿管从肾盂向下进入膀胱。",
    "clinical_link": "与肾绞痛和泌尿系统影像相关。",
    "graph_node_ids": [
      "urinary_stone"
    ]
  },
  {
    "id": "bladder_position",
    "title": "膀胱定位",
    "system": "泌尿系统",
    "target": "膀胱",
    "prompt": "请选择膀胱的标准解剖位置。",
    "answer_zone": "pelvis_midline",
    "standard_region": "pelvis_midline",
    "explanation": "膀胱位于盆腔正中。",
    "clinical_link": "与尿潴留、尿路感染和尿常规相关。",
    "graph_node_ids": [
      "urinalysis"
    ]
  },
  {
    "id": "brain_position",
    "title": "大脑定位",
    "system": "神经系统",
    "target": "大脑",
    "prompt": "请选择大脑的标准解剖位置。",
    "answer_zone": "head",
    "standard_region": "head",
    "explanation": "大脑位于颅腔内。",
    "clinical_link": "与头痛、脑卒中和头颅影像相关。",
    "graph_node_ids": [
      "headache",
      "stroke",
      "head_ct"
    ]
  },
  {
    "id": "cerebellum_position",
    "title": "小脑定位",
    "system": "神经系统",
    "target": "小脑",
    "prompt": "请选择小脑的标准解剖位置。",
    "answer_zone": "posterior_head",
    "standard_region": "posterior_head",
    "explanation": "小脑位于后颅窝。",
    "clinical_link": "与共济失调和神经系统查体相关。",
    "graph_node_ids": [
      "neurologic_exam"
    ]
  },
  {
    "id": "brainstem_position",
    "title": "脑干定位",
    "system": "神经系统",
    "target": "脑干",
    "prompt": "请选择脑干的标准解剖位置。",
    "answer_zone": "lower_head",
    "standard_region": "lower_head",
    "explanation": "脑干连接大脑和脊髓。",
    "clinical_link": "与意识、呼吸循环中枢和危重神经定位相关。",
    "graph_node_ids": [
      "stroke"
    ]
  },
  {
    "id": "spinal_cord",
    "title": "脊髓定位",
    "system": "神经系统",
    "target": "脊髓",
    "prompt": "请选择脊髓的标准解剖位置。",
    "answer_zone": "spine_midline",
    "standard_region": "spine_midline",
    "explanation": "脊髓位于椎管内。",
    "clinical_link": "与感觉运动障碍和神经定位相关。",
    "graph_node_ids": [
      "neurologic_exam"
    ]
  }
] as const;
