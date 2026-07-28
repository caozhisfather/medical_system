CASES = [
  {
    "id": "emergency_chest_pain",
    "title": "急诊胸痛",
    "department": "急诊医学",
    "difficulty": "中级",
    "chief_complaint": "胸痛2小时",
    "patient_profile": "45岁男性，虚拟教学病例",
    "speaking_style": "说话急促，担心胸痛原因",
    "present_illness": "两小时前上楼后胸骨后压榨样疼痛，伴出汗和恶心，休息后未完全缓解。",
    "past_history": "高血压5年，服药不规律。",
    "personal_history": "吸烟20余年，近期工作压力大。",
    "family_history": "父亲有冠心病史。",
    "physical_exam": "血压150/92mmHg，心率96次/分，双肺未闻及明显湿啰音。",
    "available_exams": [
      "心电图",
      "肌钙蛋白",
      "D-二聚体",
      "主动脉CTA",
      "胸片"
    ],
    "exam_results": {
      "心电图": "ST段轻度压低，需动态复查。",
      "肌钙蛋白": "初次轻度升高，建议复测动态变化。",
      "D-二聚体": "轻度升高，需结合风险分层。",
      "主动脉CTA": "未见典型夹层征象。"
    },
    "hidden_final_diagnosis": "急性冠脉综合征待排",
    "differential_diagnoses": [
      "急性冠脉综合征",
      "主动脉夹层",
      "肺栓塞",
      "气胸"
    ],
    "key_scoring_points": [
      "胸痛性质和放射痛",
      "心电图和肌钙蛋白",
      "主动脉夹层与肺栓塞鉴别"
    ],
    "high_risk_omissions": [
      {
        "id": "emergency_chest_pain_risk_1",
        "level": "danger",
        "text": "未询问胸痛性质",
        "suggestion": "围绕“询问胸痛性质”补充问诊或检查。",
        "keywords": [
          "询问胸痛性质"
        ]
      },
      {
        "id": "emergency_chest_pain_risk_2",
        "level": "warning",
        "text": "未排除主动脉夹层",
        "suggestion": "围绕“排除主动脉夹层”补充问诊或检查。",
        "keywords": [
          "排除主动脉夹层"
        ]
      },
      {
        "id": "emergency_chest_pain_risk_3",
        "level": "warning",
        "text": "未申请心电图和肌钙蛋白",
        "suggestion": "围绕“申请心电图和肌钙蛋白”补充问诊或检查。",
        "keywords": [
          "申请心电图",
          "肌钙蛋白"
        ]
      }
    ],
    "recommended_guidelines": [
      "胸痛基层诊疗指南",
      "急性冠脉综合征诊疗指南"
    ],
    "graph_node_ids": [
      "chest_pain",
      "acs",
      "ecg",
      "troponin",
      "aortic_dissection"
    ],
    "recommended_retraining": [
      "心电图导联",
      "肌钙蛋白动态变化",
      "主动脉夹层鉴别"
    ],
    "script": {
      "identity": "45岁男性，虚拟教学病例",
      "style": "说话急促，担心胸痛原因",
      "opening": "医生，我是胸痛2小时，想请您帮我看看。",
      "answers": [
        {
          "keywords": [
            "主诉",
            "哪里",
            "怎么了",
            "不舒服"
          ],
          "reply": "主要是胸痛2小时。两小时前上楼后胸骨后压榨样疼痛，伴出汗和恶心，休息后未完全缓解。"
        },
        {
          "keywords": [
            "现病史",
            "多久",
            "开始",
            "诱因",
            "经过"
          ],
          "reply": "两小时前上楼后胸骨后压榨样疼痛，伴出汗和恶心，休息后未完全缓解。"
        },
        {
          "keywords": [
            "既往",
            "以前",
            "基础病"
          ],
          "reply": "高血压5年，服药不规律。"
        },
        {
          "keywords": [
            "个人史",
            "吸烟",
            "饮酒",
            "饮食",
            "运动"
          ],
          "reply": "吸烟20余年，近期工作压力大。"
        },
        {
          "keywords": [
            "家族",
            "遗传"
          ],
          "reply": "父亲有冠心病史。"
        },
        {
          "keywords": [
            "查体",
            "体格",
            "体征"
          ],
          "reply": "血压150/92mmHg，心率96次/分，双肺未闻及明显湿啰音。"
        },
        {
          "keywords": [
            "检查",
            "化验",
            "结果"
          ],
          "reply": "目前可参考检查：心电图：ST段轻度压低，需动态复查。；肌钙蛋白：初次轻度升高，建议复测动态变化。；D-二聚体：轻度升高，需结合风险分层。；主动脉CTA：未见典型夹层征象。"
        },
        {
          "keywords": [
            "诊断",
            "是什么病",
            "最终"
          ],
          "reply": "我不知道最终诊断，只能根据这个虚拟病例告诉您我的症状和已知信息。"
        }
      ]
    }
  },
  {
    "id": "acute_abdominal_pain",
    "title": "急性腹痛",
    "department": "消化与急诊",
    "difficulty": "初中级",
    "chief_complaint": "右下腹痛6小时",
    "patient_profile": "22岁女性，虚拟教学病例",
    "speaking_style": "描述疼痛较具体，担心是否需要手术",
    "present_illness": "脐周隐痛后转移至右下腹，伴恶心，低热，无明显腹泻。",
    "past_history": "既往体健，无腹部手术史。",
    "personal_history": "近期饮食不规律，否认妊娠可能。",
    "family_history": "无类似家族史。",
    "physical_exam": "右下腹压痛，反跳痛可疑，肠鸣音稍弱。",
    "available_exams": [
      "腹部查体",
      "血常规",
      "CRP",
      "淀粉酶",
      "腹部超声",
      "腹部CT"
    ],
    "exam_results": {
      "血常规": "白细胞升高，中性粒细胞比例升高。",
      "CRP": "升高。",
      "淀粉酶": "未见明显升高。",
      "腹部超声": "右下腹管状结构增粗可疑。"
    },
    "hidden_final_diagnosis": "急性阑尾炎待排",
    "differential_diagnoses": [
      "阑尾炎",
      "胆囊炎",
      "胰腺炎",
      "消化道穿孔",
      "异位妊娠"
    ],
    "key_scoring_points": [
      "疼痛迁移史",
      "腹膜刺激征",
      "妊娠相关风险",
      "腹部影像选择"
    ],
    "high_risk_omissions": [
      {
        "id": "acute_abdominal_pain_risk_1",
        "level": "danger",
        "text": "未询问疼痛迁移",
        "suggestion": "围绕“询问疼痛迁移”补充问诊或检查。",
        "keywords": [
          "询问疼痛迁移"
        ]
      },
      {
        "id": "acute_abdominal_pain_risk_2",
        "level": "warning",
        "text": "未查腹膜刺激征",
        "suggestion": "围绕“查腹膜刺激征”补充问诊或检查。",
        "keywords": [
          "查腹膜刺激征"
        ]
      },
      {
        "id": "acute_abdominal_pain_risk_3",
        "level": "warning",
        "text": "未排除妊娠相关风险",
        "suggestion": "围绕“排除妊娠相关风险”补充问诊或检查。",
        "keywords": [
          "排除妊娠相关风险"
        ]
      }
    ],
    "recommended_guidelines": [
      "急腹症诊疗路径",
      "外科学急腹症教学要点"
    ],
    "graph_node_ids": [
      "abdominal_pain",
      "appendicitis",
      "abdominal_ct",
      "amylase"
    ],
    "recommended_retraining": [
      "腹部分区",
      "阑尾炎鉴别",
      "腹部超声"
    ],
    "script": {
      "identity": "22岁女性，虚拟教学病例",
      "style": "描述疼痛较具体，担心是否需要手术",
      "opening": "医生，我是右下腹痛6小时，想请您帮我看看。",
      "answers": [
        {
          "keywords": [
            "主诉",
            "哪里",
            "怎么了",
            "不舒服"
          ],
          "reply": "主要是右下腹痛6小时。脐周隐痛后转移至右下腹，伴恶心，低热，无明显腹泻。"
        },
        {
          "keywords": [
            "现病史",
            "多久",
            "开始",
            "诱因",
            "经过"
          ],
          "reply": "脐周隐痛后转移至右下腹，伴恶心，低热，无明显腹泻。"
        },
        {
          "keywords": [
            "既往",
            "以前",
            "基础病"
          ],
          "reply": "既往体健，无腹部手术史。"
        },
        {
          "keywords": [
            "个人史",
            "吸烟",
            "饮酒",
            "饮食",
            "运动"
          ],
          "reply": "近期饮食不规律，否认妊娠可能。"
        },
        {
          "keywords": [
            "家族",
            "遗传"
          ],
          "reply": "无类似家族史。"
        },
        {
          "keywords": [
            "查体",
            "体格",
            "体征"
          ],
          "reply": "右下腹压痛，反跳痛可疑，肠鸣音稍弱。"
        },
        {
          "keywords": [
            "检查",
            "化验",
            "结果"
          ],
          "reply": "目前可参考检查：血常规：白细胞升高，中性粒细胞比例升高。；CRP：升高。；淀粉酶：未见明显升高。；腹部超声：右下腹管状结构增粗可疑。"
        },
        {
          "keywords": [
            "诊断",
            "是什么病",
            "最终"
          ],
          "reply": "我不知道最终诊断，只能根据这个虚拟病例告诉您我的症状和已知信息。"
        }
      ]
    }
  },
  {
    "id": "fever_unknown",
    "title": "发热待查",
    "department": "感染与内科",
    "difficulty": "中级",
    "chief_complaint": "反复发热3天",
    "patient_profile": "31岁男性，虚拟教学病例",
    "speaking_style": "回答谨慎，常说记不太清具体时间",
    "present_illness": "三天来反复发热，最高39度，伴乏力和咽痛，无明显皮疹。",
    "past_history": "无结核史，无免疫抑制用药史。",
    "personal_history": "近期同事有人感冒，否认近期旅行。",
    "family_history": "无特殊家族史。",
    "physical_exam": "咽部充血，肺部听诊未闻及明显啰音，皮肤未见出血点。",
    "available_exams": [
      "血常规",
      "CRP",
      "PCT",
      "血培养",
      "胸部影像",
      "尿常规"
    ],
    "exam_results": {
      "血常规": "白细胞轻度升高。",
      "CRP": "升高。",
      "PCT": "轻度升高。",
      "血培养": "待回报。",
      "胸部影像": "未见明显实变。"
    },
    "hidden_final_diagnosis": "感染性发热待查",
    "differential_diagnoses": [
      "感染性发热",
      "结核",
      "风湿免疫病",
      "肿瘤性发热"
    ],
    "key_scoring_points": [
      "热型和伴随症状",
      "感染灶定位",
      "CRP/PCT/血培养选择"
    ],
    "high_risk_omissions": [
      {
        "id": "fever_unknown_risk_1",
        "level": "danger",
        "text": "未追问热型",
        "suggestion": "围绕“追问热型”补充问诊或检查。",
        "keywords": [
          "追问热型"
        ]
      },
      {
        "id": "fever_unknown_risk_2",
        "level": "warning",
        "text": "未寻找感染灶",
        "suggestion": "围绕“寻找感染灶”补充问诊或检查。",
        "keywords": [
          "寻找感染灶"
        ]
      },
      {
        "id": "fever_unknown_risk_3",
        "level": "warning",
        "text": "未安排血培养",
        "suggestion": "围绕“安排血培养”补充问诊或检查。",
        "keywords": [
          "安排血培养"
        ]
      }
    ],
    "recommended_guidelines": [
      "发热待查诊疗思路",
      "感染性疾病教学路径"
    ],
    "graph_node_ids": [
      "fever",
      "infection",
      "crp",
      "pct",
      "blood_culture"
    ],
    "recommended_retraining": [
      "热型问诊",
      "感染灶定位",
      "炎症指标解读"
    ],
    "script": {
      "identity": "31岁男性，虚拟教学病例",
      "style": "回答谨慎，常说记不太清具体时间",
      "opening": "医生，我是反复发热3天，想请您帮我看看。",
      "answers": [
        {
          "keywords": [
            "主诉",
            "哪里",
            "怎么了",
            "不舒服"
          ],
          "reply": "主要是反复发热3天。三天来反复发热，最高39度，伴乏力和咽痛，无明显皮疹。"
        },
        {
          "keywords": [
            "现病史",
            "多久",
            "开始",
            "诱因",
            "经过"
          ],
          "reply": "三天来反复发热，最高39度，伴乏力和咽痛，无明显皮疹。"
        },
        {
          "keywords": [
            "既往",
            "以前",
            "基础病"
          ],
          "reply": "无结核史，无免疫抑制用药史。"
        },
        {
          "keywords": [
            "个人史",
            "吸烟",
            "饮酒",
            "饮食",
            "运动"
          ],
          "reply": "近期同事有人感冒，否认近期旅行。"
        },
        {
          "keywords": [
            "家族",
            "遗传"
          ],
          "reply": "无特殊家族史。"
        },
        {
          "keywords": [
            "查体",
            "体格",
            "体征"
          ],
          "reply": "咽部充血，肺部听诊未闻及明显啰音，皮肤未见出血点。"
        },
        {
          "keywords": [
            "检查",
            "化验",
            "结果"
          ],
          "reply": "目前可参考检查：血常规：白细胞轻度升高。；CRP：升高。；PCT：轻度升高。；血培养：待回报。；胸部影像：未见明显实变。"
        },
        {
          "keywords": [
            "诊断",
            "是什么病",
            "最终"
          ],
          "reply": "我不知道最终诊断，只能根据这个虚拟病例告诉您我的症状和已知信息。"
        }
      ]
    }
  },
  {
    "id": "dyspnea",
    "title": "呼吸困难",
    "department": "呼吸与急诊",
    "difficulty": "中级",
    "chief_complaint": "活动后气促加重1天",
    "patient_profile": "68岁男性，虚拟教学病例",
    "speaking_style": "说话短句，活动后明显气促",
    "present_illness": "一日来气促加重，夜间平卧不适，偶有咳嗽，无明显胸痛。",
    "past_history": "COPD病史10年，高血压病史。",
    "personal_history": "长期吸烟，近期受凉。",
    "family_history": "母亲高血压。",
    "physical_exam": "呼吸频率24次/分，血氧91%，双肺散在哮鸣音，双下肢轻度水肿。",
    "available_exams": [
      "血氧",
      "动脉血气",
      "胸片",
      "BNP",
      "D-二聚体",
      "肺功能"
    ],
    "exam_results": {
      "血氧": "静息状态91%。",
      "动脉血气": "轻度低氧。",
      "胸片": "肺纹理增多，心影稍大。",
      "BNP": "升高。"
    },
    "hidden_final_diagnosis": "心衰与COPD急性加重鉴别",
    "differential_diagnoses": [
      "哮喘",
      "COPD急性加重",
      "心衰",
      "肺栓塞"
    ],
    "key_scoring_points": [
      "血氧和血气",
      "心肺鉴别",
      "BNP和D-二聚体选择"
    ],
    "high_risk_omissions": [
      {
        "id": "dyspnea_risk_1",
        "level": "danger",
        "text": "未评估低氧",
        "suggestion": "围绕“评估低氧”补充问诊或检查。",
        "keywords": [
          "评估低氧"
        ]
      },
      {
        "id": "dyspnea_risk_2",
        "level": "warning",
        "text": "未鉴别心衰",
        "suggestion": "围绕“鉴别心衰”补充问诊或检查。",
        "keywords": [
          "鉴别心衰"
        ]
      },
      {
        "id": "dyspnea_risk_3",
        "level": "warning",
        "text": "未询问喘息诱因",
        "suggestion": "围绕“询问喘息诱因”补充问诊或检查。",
        "keywords": [
          "询问喘息诱因"
        ]
      }
    ],
    "recommended_guidelines": [
      "呼吸困难急诊评估",
      "慢阻肺急性加重教学要点"
    ],
    "graph_node_ids": [
      "dyspnea",
      "copd",
      "heart_failure",
      "bnp",
      "oxygen_saturation"
    ],
    "recommended_retraining": [
      "血气分析",
      "心衰鉴别",
      "肺栓塞风险"
    ],
    "script": {
      "identity": "68岁男性，虚拟教学病例",
      "style": "说话短句，活动后明显气促",
      "opening": "医生，我是活动后气促加重1天，想请您帮我看看。",
      "answers": [
        {
          "keywords": [
            "主诉",
            "哪里",
            "怎么了",
            "不舒服"
          ],
          "reply": "主要是活动后气促加重1天。一日来气促加重，夜间平卧不适，偶有咳嗽，无明显胸痛。"
        },
        {
          "keywords": [
            "现病史",
            "多久",
            "开始",
            "诱因",
            "经过"
          ],
          "reply": "一日来气促加重，夜间平卧不适，偶有咳嗽，无明显胸痛。"
        },
        {
          "keywords": [
            "既往",
            "以前",
            "基础病"
          ],
          "reply": "COPD病史10年，高血压病史。"
        },
        {
          "keywords": [
            "个人史",
            "吸烟",
            "饮酒",
            "饮食",
            "运动"
          ],
          "reply": "长期吸烟，近期受凉。"
        },
        {
          "keywords": [
            "家族",
            "遗传"
          ],
          "reply": "母亲高血压。"
        },
        {
          "keywords": [
            "查体",
            "体格",
            "体征"
          ],
          "reply": "呼吸频率24次/分，血氧91%，双肺散在哮鸣音，双下肢轻度水肿。"
        },
        {
          "keywords": [
            "检查",
            "化验",
            "结果"
          ],
          "reply": "目前可参考检查：血氧：静息状态91%。；动脉血气：轻度低氧。；胸片：肺纹理增多，心影稍大。；BNP：升高。"
        },
        {
          "keywords": [
            "诊断",
            "是什么病",
            "最终"
          ],
          "reply": "我不知道最终诊断，只能根据这个虚拟病例告诉您我的症状和已知信息。"
        }
      ]
    }
  },
  {
    "id": "diabetes_education",
    "title": "糖尿病健康宣教",
    "department": "全科医学",
    "difficulty": "初级",
    "chief_complaint": "血糖控制不佳3个月",
    "patient_profile": "56岁女性，虚拟教学病例",
    "speaking_style": "关心饮食和药物副作用",
    "present_illness": "三个月来自测血糖偏高，偶尔漏服药，担心长期并发症。",
    "past_history": "2型糖尿病6年，高脂血症。",
    "personal_history": "饮食控制不规律，运动少。",
    "family_history": "母亲有糖尿病。",
    "physical_exam": "BMI偏高，足背动脉可触及，足部皮肤完整。",
    "available_exams": [
      "空腹血糖",
      "HbA1c",
      "尿微量白蛋白",
      "眼底检查",
      "足部检查",
      "血脂"
    ],
    "exam_results": {
      "空腹血糖": "8.6 mmol/L。",
      "HbA1c": "8.2%。",
      "尿微量白蛋白": "轻度升高。",
      "眼底检查": "建议预约筛查。"
    },
    "hidden_final_diagnosis": "2型糖尿病控制不佳",
    "differential_diagnoses": [
      "用药依从性差",
      "饮食运动不足",
      "低血糖风险",
      "并发症风险"
    ],
    "key_scoring_points": [
      "生活方式评估",
      "用药依从性",
      "低血糖识别",
      "并发症筛查"
    ],
    "high_risk_omissions": [
      {
        "id": "diabetes_education_risk_1",
        "level": "danger",
        "text": "未询问低血糖",
        "suggestion": "围绕“询问低血糖”补充问诊或检查。",
        "keywords": [
          "询问低血糖"
        ]
      },
      {
        "id": "diabetes_education_risk_2",
        "level": "warning",
        "text": "未安排HbA1c",
        "suggestion": "围绕“安排HbA1c”补充问诊或检查。",
        "keywords": [
          "安排HbA1c"
        ]
      },
      {
        "id": "diabetes_education_risk_3",
        "level": "warning",
        "text": "未做并发症筛查",
        "suggestion": "围绕“做并发症筛查”补充问诊或检查。",
        "keywords": [
          "做并发症筛查"
        ]
      }
    ],
    "recommended_guidelines": [
      "糖尿病基层管理指南",
      "慢病健康教育路径"
    ],
    "graph_node_ids": [
      "diabetes",
      "hba1c",
      "hypoglycemia",
      "microalbuminuria"
    ],
    "recommended_retraining": [
      "HbA1c解读",
      "低血糖识别",
      "足部护理"
    ],
    "script": {
      "identity": "56岁女性，虚拟教学病例",
      "style": "关心饮食和药物副作用",
      "opening": "医生，我是血糖控制不佳3个月，想请您帮我看看。",
      "answers": [
        {
          "keywords": [
            "主诉",
            "哪里",
            "怎么了",
            "不舒服"
          ],
          "reply": "主要是血糖控制不佳3个月。三个月来自测血糖偏高，偶尔漏服药，担心长期并发症。"
        },
        {
          "keywords": [
            "现病史",
            "多久",
            "开始",
            "诱因",
            "经过"
          ],
          "reply": "三个月来自测血糖偏高，偶尔漏服药，担心长期并发症。"
        },
        {
          "keywords": [
            "既往",
            "以前",
            "基础病"
          ],
          "reply": "2型糖尿病6年，高脂血症。"
        },
        {
          "keywords": [
            "个人史",
            "吸烟",
            "饮酒",
            "饮食",
            "运动"
          ],
          "reply": "饮食控制不规律，运动少。"
        },
        {
          "keywords": [
            "家族",
            "遗传"
          ],
          "reply": "母亲有糖尿病。"
        },
        {
          "keywords": [
            "查体",
            "体格",
            "体征"
          ],
          "reply": "BMI偏高，足背动脉可触及，足部皮肤完整。"
        },
        {
          "keywords": [
            "检查",
            "化验",
            "结果"
          ],
          "reply": "目前可参考检查：空腹血糖：8.6 mmol/L。；HbA1c：8.2%。；尿微量白蛋白：轻度升高。；眼底检查：建议预约筛查。"
        },
        {
          "keywords": [
            "诊断",
            "是什么病",
            "最终"
          ],
          "reply": "我不知道最终诊断，只能根据这个虚拟病例告诉您我的症状和已知信息。"
        }
      ]
    }
  },
  {
    "id": "headache_case",
    "title": "头痛病例",
    "department": "神经内科",
    "difficulty": "中级",
    "chief_complaint": "突发头痛4小时",
    "patient_profile": "52岁男性，虚拟教学病例",
    "speaking_style": "紧张，反复强调头痛很重",
    "present_illness": "四小时前突发剧烈头痛，伴恶心，无明确外伤。",
    "past_history": "高血压病史，近期控制不佳。",
    "personal_history": "饮酒偶尔，睡眠不足。",
    "family_history": "父亲脑卒中史。",
    "physical_exam": "血压188/106mmHg，颈抵抗可疑，肌力基本对称。",
    "available_exams": [
      "神经系统查体",
      "头颅CT",
      "头颅MRI",
      "腰穿指征评估",
      "血压监测"
    ],
    "exam_results": {
      "头颅CT": "需排除出血。",
      "血压监测": "持续偏高。",
      "神经系统查体": "未见明确偏瘫。"
    },
    "hidden_final_diagnosis": "脑出血或高血压急症待排",
    "differential_diagnoses": [
      "偏头痛",
      "脑出血",
      "脑膜炎",
      "高血压急症"
    ],
    "key_scoring_points": [
      "雷击样头痛",
      "神经系统查体",
      "头颅影像",
      "腰穿禁忌"
    ],
    "high_risk_omissions": [
      {
        "id": "headache_case_risk_1",
        "level": "danger",
        "text": "未识别突发剧烈头痛",
        "suggestion": "围绕“识别突发剧烈头痛”补充问诊或检查。",
        "keywords": [
          "识别突发剧烈头痛"
        ]
      },
      {
        "id": "headache_case_risk_2",
        "level": "warning",
        "text": "未测血压",
        "suggestion": "围绕“测血压”补充问诊或检查。",
        "keywords": [
          "测血压"
        ]
      },
      {
        "id": "headache_case_risk_3",
        "level": "warning",
        "text": "未做神经系统查体",
        "suggestion": "围绕“做神经系统查体”补充问诊或检查。",
        "keywords": [
          "做神经系统查体"
        ]
      }
    ],
    "recommended_guidelines": [
      "急性头痛评估路径",
      "脑血管病教学要点"
    ],
    "graph_node_ids": [
      "headache",
      "intracranial_hemorrhage",
      "hypertensive_emergency",
      "head_ct"
    ],
    "recommended_retraining": [
      "头颅CT",
      "脑膜刺激征",
      "高血压急症"
    ],
    "script": {
      "identity": "52岁男性，虚拟教学病例",
      "style": "紧张，反复强调头痛很重",
      "opening": "医生，我是突发头痛4小时，想请您帮我看看。",
      "answers": [
        {
          "keywords": [
            "主诉",
            "哪里",
            "怎么了",
            "不舒服"
          ],
          "reply": "主要是突发头痛4小时。四小时前突发剧烈头痛，伴恶心，无明确外伤。"
        },
        {
          "keywords": [
            "现病史",
            "多久",
            "开始",
            "诱因",
            "经过"
          ],
          "reply": "四小时前突发剧烈头痛，伴恶心，无明确外伤。"
        },
        {
          "keywords": [
            "既往",
            "以前",
            "基础病"
          ],
          "reply": "高血压病史，近期控制不佳。"
        },
        {
          "keywords": [
            "个人史",
            "吸烟",
            "饮酒",
            "饮食",
            "运动"
          ],
          "reply": "饮酒偶尔，睡眠不足。"
        },
        {
          "keywords": [
            "家族",
            "遗传"
          ],
          "reply": "父亲脑卒中史。"
        },
        {
          "keywords": [
            "查体",
            "体格",
            "体征"
          ],
          "reply": "血压188/106mmHg，颈抵抗可疑，肌力基本对称。"
        },
        {
          "keywords": [
            "检查",
            "化验",
            "结果"
          ],
          "reply": "目前可参考检查：头颅CT：需排除出血。；血压监测：持续偏高。；神经系统查体：未见明确偏瘫。"
        },
        {
          "keywords": [
            "诊断",
            "是什么病",
            "最终"
          ],
          "reply": "我不知道最终诊断，只能根据这个虚拟病例告诉您我的症状和已知信息。"
        }
      ]
    }
  },
  {
    "id": "anemia_case",
    "title": "贫血病例",
    "department": "血液内科",
    "difficulty": "初中级",
    "chief_complaint": "乏力面色苍白1个月",
    "patient_profile": "34岁女性，虚拟教学病例",
    "speaking_style": "语速慢，强调乏力和头晕",
    "present_illness": "一个月来乏力、头晕，活动后心慌，月经量偏多。",
    "past_history": "无慢性肾病史。",
    "personal_history": "饮食偏素。",
    "family_history": "母亲曾有贫血。",
    "physical_exam": "睑结膜苍白，心率92次/分。",
    "available_exams": [
      "血常规",
      "铁蛋白",
      "维生素B12",
      "叶酸",
      "网织红细胞",
      "便潜血"
    ],
    "exam_results": {
      "血常规": "小细胞低色素性贫血。",
      "铁蛋白": "降低。",
      "维生素B12": "正常。",
      "网织红细胞": "轻度升高。"
    },
    "hidden_final_diagnosis": "缺铁性贫血可能",
    "differential_diagnoses": [
      "缺铁性贫血",
      "巨幼细胞贫血",
      "溶血性贫血",
      "慢性病贫血"
    ],
    "key_scoring_points": [
      "MCV判断",
      "铁蛋白选择",
      "失血来源追问",
      "网织红细胞解读"
    ],
    "high_risk_omissions": [
      {
        "id": "anemia_case_risk_1",
        "level": "danger",
        "text": "未询问月经量",
        "suggestion": "围绕“询问月经量”补充问诊或检查。",
        "keywords": [
          "询问月经量"
        ]
      },
      {
        "id": "anemia_case_risk_2",
        "level": "warning",
        "text": "未申请铁蛋白",
        "suggestion": "围绕“申请铁蛋白”补充问诊或检查。",
        "keywords": [
          "申请铁蛋白"
        ]
      },
      {
        "id": "anemia_case_risk_3",
        "level": "warning",
        "text": "未鉴别溶血",
        "suggestion": "围绕“鉴别溶血”补充问诊或检查。",
        "keywords": [
          "鉴别溶血"
        ]
      }
    ],
    "recommended_guidelines": [
      "贫血诊断思路",
      "血常规判读教学"
    ],
    "graph_node_ids": [
      "anemia",
      "iron_deficiency_anemia",
      "ferritin",
      "reticulocyte"
    ],
    "recommended_retraining": [
      "血常规参数",
      "铁代谢",
      "失血评估"
    ],
    "script": {
      "identity": "34岁女性，虚拟教学病例",
      "style": "语速慢，强调乏力和头晕",
      "opening": "医生，我是乏力面色苍白1个月，想请您帮我看看。",
      "answers": [
        {
          "keywords": [
            "主诉",
            "哪里",
            "怎么了",
            "不舒服"
          ],
          "reply": "主要是乏力面色苍白1个月。一个月来乏力、头晕，活动后心慌，月经量偏多。"
        },
        {
          "keywords": [
            "现病史",
            "多久",
            "开始",
            "诱因",
            "经过"
          ],
          "reply": "一个月来乏力、头晕，活动后心慌，月经量偏多。"
        },
        {
          "keywords": [
            "既往",
            "以前",
            "基础病"
          ],
          "reply": "无慢性肾病史。"
        },
        {
          "keywords": [
            "个人史",
            "吸烟",
            "饮酒",
            "饮食",
            "运动"
          ],
          "reply": "饮食偏素。"
        },
        {
          "keywords": [
            "家族",
            "遗传"
          ],
          "reply": "母亲曾有贫血。"
        },
        {
          "keywords": [
            "查体",
            "体格",
            "体征"
          ],
          "reply": "睑结膜苍白，心率92次/分。"
        },
        {
          "keywords": [
            "检查",
            "化验",
            "结果"
          ],
          "reply": "目前可参考检查：血常规：小细胞低色素性贫血。；铁蛋白：降低。；维生素B12：正常。；网织红细胞：轻度升高。"
        },
        {
          "keywords": [
            "诊断",
            "是什么病",
            "最终"
          ],
          "reply": "我不知道最终诊断，只能根据这个虚拟病例告诉您我的症状和已知信息。"
        }
      ]
    }
  },
  {
    "id": "jaundice_case",
    "title": "黄疸病例",
    "department": "消化内科",
    "difficulty": "中级",
    "chief_complaint": "皮肤眼黄5天",
    "patient_profile": "46岁男性，虚拟教学病例",
    "speaking_style": "担心肝病，主动提到尿色变深",
    "present_illness": "五天来皮肤和巩膜黄染，尿色加深，伴右上腹不适。",
    "past_history": "乙肝疫苗接种不详，无已知肝硬化。",
    "personal_history": "近期饮酒增加，否认输血。",
    "family_history": "无明确肝病家族史。",
    "physical_exam": "巩膜黄染，右上腹轻压痛，未触及明显包块。",
    "available_exams": [
      "肝功能",
      "胆红素分型",
      "腹部超声",
      "病毒性肝炎标志物",
      "凝血功能"
    ],
    "exam_results": {
      "肝功能": "ALT、AST升高。",
      "胆红素分型": "直接胆红素升高为主。",
      "腹部超声": "胆管轻度扩张可疑。"
    },
    "hidden_final_diagnosis": "梗阻性或肝细胞性黄疸鉴别",
    "differential_diagnoses": [
      "肝细胞性黄疸",
      "梗阻性黄疸",
      "溶血性黄疸",
      "病毒性肝炎"
    ],
    "key_scoring_points": [
      "尿色和粪色",
      "胆红素分型",
      "肝胆超声",
      "病毒性肝炎筛查"
    ],
    "high_risk_omissions": [
      {
        "id": "jaundice_case_risk_1",
        "level": "danger",
        "text": "未询问尿色粪色",
        "suggestion": "围绕“询问尿色粪色”补充问诊或检查。",
        "keywords": [
          "询问尿色粪色"
        ]
      },
      {
        "id": "jaundice_case_risk_2",
        "level": "warning",
        "text": "未做胆红素分型",
        "suggestion": "围绕“做胆红素分型”补充问诊或检查。",
        "keywords": [
          "做胆红素分型"
        ]
      },
      {
        "id": "jaundice_case_risk_3",
        "level": "warning",
        "text": "未安排腹部超声",
        "suggestion": "围绕“安排腹部超声”补充问诊或检查。",
        "keywords": [
          "安排腹部超声"
        ]
      }
    ],
    "recommended_guidelines": [
      "黄疸诊断路径",
      "肝胆疾病教学要点"
    ],
    "graph_node_ids": [
      "jaundice",
      "bilirubin",
      "liver_function",
      "abdominal_ultrasound"
    ],
    "recommended_retraining": [
      "胆红素分型",
      "肝胆解剖",
      "腹部超声"
    ],
    "script": {
      "identity": "46岁男性，虚拟教学病例",
      "style": "担心肝病，主动提到尿色变深",
      "opening": "医生，我是皮肤眼黄5天，想请您帮我看看。",
      "answers": [
        {
          "keywords": [
            "主诉",
            "哪里",
            "怎么了",
            "不舒服"
          ],
          "reply": "主要是皮肤眼黄5天。五天来皮肤和巩膜黄染，尿色加深，伴右上腹不适。"
        },
        {
          "keywords": [
            "现病史",
            "多久",
            "开始",
            "诱因",
            "经过"
          ],
          "reply": "五天来皮肤和巩膜黄染，尿色加深，伴右上腹不适。"
        },
        {
          "keywords": [
            "既往",
            "以前",
            "基础病"
          ],
          "reply": "乙肝疫苗接种不详，无已知肝硬化。"
        },
        {
          "keywords": [
            "个人史",
            "吸烟",
            "饮酒",
            "饮食",
            "运动"
          ],
          "reply": "近期饮酒增加，否认输血。"
        },
        {
          "keywords": [
            "家族",
            "遗传"
          ],
          "reply": "无明确肝病家族史。"
        },
        {
          "keywords": [
            "查体",
            "体格",
            "体征"
          ],
          "reply": "巩膜黄染，右上腹轻压痛，未触及明显包块。"
        },
        {
          "keywords": [
            "检查",
            "化验",
            "结果"
          ],
          "reply": "目前可参考检查：肝功能：ALT、AST升高。；胆红素分型：直接胆红素升高为主。；腹部超声：胆管轻度扩张可疑。"
        },
        {
          "keywords": [
            "诊断",
            "是什么病",
            "最终"
          ],
          "reply": "我不知道最终诊断，只能根据这个虚拟病例告诉您我的症状和已知信息。"
        }
      ]
    }
  }
]
