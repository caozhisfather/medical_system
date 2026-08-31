ADMIN_DATA = {
  "dataSources": [
    {
      "id": "modelscope_med_qa",
      "name": "AI-ModelScope/med_qa",
      "platform": "ModelScope",
      "type": "医学考试问答",
      "modules": [
        "知识库",
        "医学考试题",
        "学习路径",
        "RAG"
      ],
      "license": "Apache License 2.0, use after dataset card review",
      "connected": false,
      "index_status": "planned",
      "sync_status": "mock metadata only",
      "url": "https://modelscope.cn/datasets/AI-ModelScope/med_qa",
      "mapping": {
        "question": "question",
        "options": "options",
        "answer": "answer",
        "explanation": "rationale",
        "language": "lang"
      }
    },
    {
      "id": "modelscope_m3d_vqa",
      "name": "GoodBaiBai88/M3D-VQA",
      "platform": "ModelScope",
      "type": "3D 医疗视觉问答",
      "modules": [
        "医学影像问答",
        "影像训练",
        "多模态RAG"
      ],
      "license": "Apache License 2.0 listed, page notes academic/non-commercial review required",
      "connected": false,
      "index_status": "license_review",
      "sync_status": "mock metadata only",
      "url": "https://www.modelscope.cn/datasets/GoodBaiBai88/M3D-VQA",
      "mapping": {
        "image_path": "Image Path",
        "question": "Question",
        "choices": "Choice A-D",
        "answer": "Answer",
        "question_type": "Question Type"
      }
    },
    {
      "id": "modelscope_m3d_cap",
      "name": "GoodBaiBai88/M3D-Cap",
      "platform": "ModelScope",
      "type": "3D 医学影像图文对",
      "modules": [
        "影像知识库",
        "病例摘要",
        "影像报告训练"
      ],
      "license": "Apache License 2.0 listed, large files and privacy compliance review required",
      "connected": false,
      "index_status": "deferred_large_file",
      "sync_status": "mock metadata only",
      "url": "https://modelscope.cn/datasets/GoodBaiBai88/M3D-Cap",
      "mapping": {
        "image": "3D CT slices",
        "report": "text report",
        "split": "M3D_Cap.json"
      }
    },
    {
      "id": "modelscope_m3d_seg",
      "name": "GoodBaiBai88/M3D-Seg",
      "platform": "ModelScope",
      "type": "3D 医学图像分割",
      "modules": [
        "解剖定位",
        "器官分割训练",
        "影像标注"
      ],
      "license": "Apache License 2.0 listed, dataset-specific upstream licenses need review",
      "connected": false,
      "index_status": "planned",
      "sync_status": "mock metadata only",
      "url": "https://www.modelscope.cn/datasets/GoodBaiBai88/M3D-Seg",
      "mapping": {
        "image": "image",
        "mask": "mask",
        "label_text": "term_dictionary.json",
        "dataset": "dataset_info.json"
      }
    },
    {
      "id": "pmph_undergraduate_textbooks",
      "name": "人民卫生出版社本科临床医学规划教材体系",
      "platform": "教材摘要",
      "type": "医学教材体系",
      "modules": [
        "教材路径",
        "知识库",
        "桥梁课程",
        "临床核心"
      ],
      "license": "仅做书目与摘要型mock, 不复制教材原文",
      "connected": true,
      "index_status": "mock_indexed",
      "sync_status": "curated_outline",
      "url": "https://www.pmph.com/",
      "mapping": {
        "stage": "curriculum_stage",
        "book": "textbook_title",
        "topic": "learning_objective"
      }
    },
    {
      "id": "clinical_guidelines",
      "name": "公开临床指南与专家共识目录",
      "platform": "指南",
      "type": "循证依据",
      "modules": [
        "RAG",
        "citation",
        "临床决策"
      ],
      "license": "只存目录、摘要和引用字段, 不复制大段正文",
      "connected": true,
      "index_status": "mock_indexed",
      "sync_status": "curated_outline",
      "url": "mock://guideline-catalog",
      "mapping": {
        "title": "title",
        "citation": "citation",
        "disease": "related_disease"
      }
    },
    {
      "id": "virtual_cases",
      "name": "临思智训虚拟教学病例库",
      "platform": "自建病例",
      "type": "虚拟教学病例",
      "modules": [
        "标准化病人",
        "评分",
        "报告"
      ],
      "license": "虚拟病例, 不含真实患者信息",
      "connected": true,
      "index_status": "mock_indexed",
      "sync_status": "local_json",
      "url": "local://data/cases.json",
      "mapping": {
        "case_id": "id",
        "script": "script.answers",
        "omissions": "high_risk_omissions"
      }
    }
  ],
  "adminUsers": [
    {
      "id": "u_admin",
      "name": "超级管理员",
      "account": "admin",
      "role": "super_admin",
      "status": "active",
      "department": "系统管理",
      "last_login": "演示环境",
      "permissions": [
        "users",
        "data_sources",
        "knowledge",
        "graph",
        "rag",
        "obsidian"
      ]
    },
    {
      "id": "u_teacher_01",
      "name": "李老师",
      "account": "teacher01",
      "role": "teacher",
      "status": "active",
      "department": "诊断学教研室",
      "last_login": "2026-07-27",
      "permissions": [
        "dashboard",
        "cases",
        "reports"
      ]
    },
    {
      "id": "u_teacher_02",
      "name": "周老师",
      "account": "teacher02",
      "role": "teacher",
      "status": "active",
      "department": "急诊医学教研室",
      "last_login": "2026-07-26",
      "permissions": [
        "dashboard",
        "reports"
      ]
    },
    {
      "id": "u_student_01",
      "name": "学生A",
      "account": "student01",
      "role": "student",
      "status": "active",
      "department": "临床医学五年制",
      "last_login": "2026-07-27",
      "permissions": [
        "training",
        "knowledge",
        "report"
      ]
    },
    {
      "id": "u_student_02",
      "name": "学生B",
      "account": "student02",
      "role": "student",
      "status": "review",
      "department": "临床医学五年制",
      "last_login": "2026-07-24",
      "permissions": [
        "training",
        "knowledge"
      ]
    }
  ]
}
