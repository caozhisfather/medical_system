# 班级管理升级与教师端 UI 交付说明

适用目录：`E:\合力杯\medical_system-2026-9-23-13th`。在现有 Vue 3 / TypeScript / Vite、FastAPI / Pydantic、SQLite 项目内增量开发；没有新建独立项目。

## 1. 原有功能与差异

原有班级模块包含创建班级、邀请码加入、学生作答汇总、教师学习建议和 AI 学习建议。原有学习记录保存在独立的 anatomy_learning SQLite 数据库，身份与会话保存在 auth 数据库。

本次补充班级元数据、软归档、学生软移出、名单导入与导出、入班申请审核、考勤、作业及任务、提交与人工批改、公告、小组、资料、教学日志、待办和真实统计。保留原学习建议页面及接口；新版学生管理页提供返回原工作台的入口。

保留平台侧边栏、DNA 背景、顶部智能体与用户信息；新增学生“我的班级”入口、管理员班级管理入口。样式限定在新组件内。

## 2. 文件清单

新增：

- `backend/app/services/teaching_service.py`：迁移、权限、事务、业务与统计。
- `backend/app/api/teaching.py`：认证 API、验证、导入、上传和导出。
- `backend/tests/test_teaching_management.py`：完整流程、隔离、迁移、并发初始化和申请审核回归测试。
- `frontend/src/teachingApi.ts`：带身份凭据的教学接口与文件下载。
- `frontend/src/views/TeacherClassManagementView.vue`：班级首页和七个管理功能区。
- `frontend/src/views/StudentClassPortalView.vue`：个人班级、作业提交、公告、个人考勤、资料与小组。
- `frontend/src/assets/medical/teacher-overview-medical-v2.webp`：新医学教学横幅。
- `frontend/src/assets/medical/teaching-library-banner.webp`：新教学知识库横幅。
- 本说明文件。

修改：

- `backend/app/main.py`：挂载教学路由。
- `backend/app/services/classroom_service.py`：兼容有效成员标识、重新加入、原有统计和入班日志。
- `backend/requirements.txt`：新增 openpyxl，读取 XLSX。
- `frontend/src/router/index.ts`：切换新版班级页，保留学习指导页，增加学生和管理员路由。
- `frontend/src/layouts/ProductShell.vue`：保留导航并新增真实可用的班级入口。
- `frontend/src/views/TeacherCaseLibraryView.vue`：参考图的横幅、五类资源统计、分类导航、真实病例推荐、快捷入口、筛选与资源表格；保留现有导入、OCR/向量管理、脱敏、查看、编辑及删除功能。
- `frontend/src/views/TeacherDashboardView.vue`：使用新医学教学横幅，调整小屏裁切与文字区域。
- `.gitignore`：排除本地教学数据库备份及班级上传文件，避免上传学生数据。

本工作区还保留了此前已修改、尚未提交的 `TeacherClassroomView.vue` 和其兼容横幅 `teacher-overview-banner.webp`，没有覆盖或丢弃。

## 3. 数据库升级

复用现有 `classrooms`、`classroom_memberships`、`classroom_guidance`，不重置数据库，不删除历史作答。

新增班级字段：`major`、`grade`、`semester`、`updated_at`。成员新增 `active` 和 `removed_at`，移出时保留成员行。归档只设置原有 `archived` 字段。

新增表：

| 表 | 用途 |
| --- | --- |
| teaching_schema_versions | 升级版本记录 |
| attendance_sessions / attendance_records | 考勤活动与固定活动名单、状态 |
| assignments / assignment_recipients / assignment_submissions | 作业和任务、发布名单、提交与教师批改 |
| class_announcements | 草稿、发布、置顶、撤回公告 |
| study_groups / study_group_members | 小组、组员、组长 |
| class_resources | 文件元数据、分类、可见权限、软删除 |
| class_activity_logs | 操作教师、类型、描述及时间 |
| teacher_todos | 教师自定义待办、优先级、截止与完成状态 |
| class_import_previews | 绑定教师及班级的导入预览，30 分钟有效且只能确认一次 |
| class_join_requests | 学生申请及教师审核结果 |

业务记录以班级为外键；考勤和作业名单引用班级成员复合主键。身份库与教学库分离，用户 ID 是外部引用，由服务端校验有效身份及班级归属。为班级、日期、状态、学生、教师等查询建立索引。

首次升级班级元数据前使用 SQLite 在线备份，保存为原数据库同目录的 `*.pre-teaching-v1.sqlite3`。升级幂等；应用初始化加锁，结构修改使用数据库写锁，避免列表与统计并发请求重复升级。

班级资料位于班级数据库同目录的 `class_resources/`，使用随机文件名。软删除后停止下载，文件保留用于历史追溯；后续可以按存储保留策略清理。

## 4. 新增 API 清单

除标注学生能力外，管理接口仅允许班级所属教师或管理员；所有接口都沿用 Bearer 身份认证。

前缀：`/api/teaching`。

| 方法 | 路径 | 能力 |
| --- | --- | --- |
| GET / POST | /classes | 有权限的班级分页筛选 / 创建 |
| PUT | /classes/{cid} | 编辑、管理员选择任课教师 |
| POST | /classes/{cid}/archive | 保留历史的归档 |
| GET | /metrics | 教师统计卡片 |
| GET | /teachers | 教师本人或管理员可选教师 |
| GET | /classes/{cid}/workspace | 班级工作区；学生只返回本人作业、考勤、已发布公告、开放资料和本人小组 |
| GET | /classes/{cid}/students/{sid}/archive | 教师查看班级内学生档案；学生仅能访问本人 |
| DELETE | /classes/{cid}/students/{sid} | 软移出班级 |
| GET | /import-template?format=csv或xlsx | 下载导入模板 |
| POST | /classes/{cid}/students/import-preview?filename=... | CSV/XLSX 预览、重复和错误检查 |
| POST | /classes/{cid}/students/import | 确认有效行，复核账号、名单和预览凭证 |
| GET | /classes/{cid}/export/students或attendance或grades | 带权限校验的 UTF-8 CSV 导出 |
| POST / PUT | /classes/{cid}/attendance[/{id}] | 创建考勤 / 批量登记与完成 |
| POST / PUT | /classes/{cid}/assignments[/{id}] | 作业/学习任务草稿及发布 |
| POST | /classes/{cid}/assignments/{aid}/submit | 接收学生提交，截止后禁止提交 |
| PUT | /classes/{cid}/assignments/{aid}/grades/{sid} | 教师确认成绩和评语 |
| POST / PUT | /classes/{cid}/announcements[/{id}] | 公告草稿、发布、编辑、置顶和撤回 |
| POST | /classes/{cid}/groups/preview?count=... | 均衡随机分组预览，不保存 |
| PUT | /classes/{cid}/groups | 教师确认保存，替换须显式确认 |
| POST / PUT | /classes/{cid}/todos[/{id}] | 自定义待办与完成状态 |
| GET | /classes/{cid}/logs | 分页动态 |
| POST | /classes/{cid}/resources?filename=... | 原始二进制文件上传、分类和可见性 |
| PATCH / DELETE | /classes/{cid}/resources/{rid} | 资料分类/权限 / 软删除 |
| GET | /classes/{cid}/resources/{rid}/download | 经班级和资料权限验证的附件下载 |
| POST | /join-requests | 学生凭邀请码申请加入 |
| GET | /join-requests/mine | 学生本人申请记录 |
| POST | /classes/{cid}/join-requests/{rid}/decision | 教师批准或拒绝申请 |

原有 `/api/classrooms/join` 邀请码直接加入和学习指导 API 继续工作。直接加入与申请审核是两条可选择的路径；邀请码本身代表直接加入授权。

## 5. 功能与统计口径

- 新版首页：班级列表、五项指标、七个功能入口、指定日期考勤概览、学习活跃度、动态、待办。创建、导入、发布、提交、批改、切换班级后重新从接口读取数据。
- 班级总数：当前教师有权限的未归档班级。管理员可查看全部班级。
- 在籍学生：上述班级中 `active=1` 的学生按用户 ID 跨班去重。
- 本月考勤率：采用北京时间月份，只统计已完成考勤。出勤及迟到计入出勤；请假从应考勤人次中扣除。没有分母时返回 null。
- 作业完成率：仅统计未归档班级内已发布、已经截止的作业。名单在发布时固定，提交数 / 应提交数；尚未截止作业不进入该指标。
- 平均学习进度：已发布学习任务的完成提交数 / 已分配人次。没有任务时显示“暂无数据”。学习任务提交代表学生申报完成，与考试成绩分开。
- 考勤概览：指定日期最近一次已完成活动的固定名单和状态，标明活动名称。不会把一次考勤状态当作学生长期学习状态。
- 活跃度：日期范围内，在籍学生当天完成空间定位练习、参与测验、提交作业或学习任务的去重人数 / 当前在籍人数。排除入班前记录及已移出学生；支持 7、30、90 天、悬停明细和自定义日期。测验采用原有存储中每题最近一次记录，不能重建原库未保存的重复作答历史。
- 学情：实际学习任务完成情况、作业提交数、所选范围内成绩分布、考勤变化、每日活跃明细。任务总进度和作业名单概览为累计值，日期过滤用于成绩、考勤和活跃事件。
- 待办：待批改作业、待审核发布的作业题目、待发布资料、待处理入班申请及自定义事项。已发布题目不允许直接改写，避免改变既有作答依据。这里的题目审核是班级作业草稿发布确认，未新增第二套题库。
- 学生：个人作业、成绩、考勤、班级公开资料与公告；不能取得其他学生的提交、成绩或完整名单。
- 导入：只接受已有的有效学生账号，不会自动创建登录账号或覆盖认证资料。UTF-8 CSV/XLSX，每次最多 2000 行、5 MB；显示错误行，确认时只导入有效新成员。CSV 导出防止公式注入。
- 文件：PDF、Office、PNG/JPEG/WebP，最大 25 MB；验证扩展名与文件签名/图片内容、Office 容器、展开尺寸和宏/可执行嵌入；下载使用附件响应，不直接公开存储路径。

## 6. 测试与验收

后端回归结果：9 项测试通过（包含原有测试）。

后端测试：`backend/tests/test_teaching_management.py`，连同原有 `test_classroom_service.py`、`test_classroom_api.py` 执行。覆盖完整教学流程、到期统计、事务回滚、学生数据隔离、跨班学生去重、越权拒绝、CSV/XLSX、资料权限、重复迁移、并发首次初始化、软移出历史保留、归档只读和申请审核/待办联动。

前端：`npm --prefix frontend run build`，包含 TypeScript 检查及生产构建。原有三维解剖大文件仍产生打包体积提示，不影响本次构建结果。

浏览器实际操作验收使用独立临时后端及 SQLite 数据库，真实点击完成创建班级、导入学生、完成考勤、发布作业、发布公告、预览并确认分组、上传并开放资料、学生接收并提交、教师批改、新建待办。没有把验收班级、名单、作业写入原项目的业务数据库。

教师班级页、知识库、教学总览在 1440px 和 561px 视口检查；均无整页横向溢出或页面脚本异常。资料与名单表格在自身区域内滚动。截图位于工作区 `runtime/qa/`，测试数据截图仅用于验收。

## 7. 配置、边界与后续扩展

- 现有学习指导和 AI 命题设置继续使用原工作台；班级作业可引用审核后的题目文本。本次没有建立结构化 AI 试卷自动导入或自动评分链路；正式成绩由教师手动确认。
- 可选的 AI 班级统计建议、限时学生签到、消息推送/邮件、附件式作业提交尚未接入。当前支持教师考勤登记、文本作答和站内公告，不将这些可选能力显示成虚假可用按钮。
- 后端需要安装 `backend/requirements.txt`（本地已有 openpyxl）。身份与历史学习库沿用原配置。数据库目录及其 `class_resources` 子目录需要读写权限。
- 没有接入外部恶意文件扫描服务；现有上传验证不能替代企业部署的病毒扫描。
- 当前基于项目既有 SQLite 与单班级所有者权限，管理员可调任课教师；多人协同授课授权、异步大规模导入及跨班批量发布可进一步扩展。
- 所有本地数据库备份和上传文件均排除在 Git 提交之外。本次开发未部署到远程服务器，仓库提交不包含本地业务数据库、备份和上传资料。

## 8. 横幅素材

使用内置图像生成工具生成并优化为 WebP，已复制进项目，页面不依赖临时文件或外部图片服务。两张横幅属于装饰插画，不代表真实患者影像或业务数据。

教学总览生成提示：

> Create a polished medical university TEACHER DASHBOARD hero background illustration, very wide horizontal panoramic 5:1 aspect ratio, no text, no letters, no numbers, no UI labels. Premium restrained blue-white medical education aesthetic, white and pale powder blue light gradient matching #F1F6FF and #155EEF. Left 58 percent is bright clean almost blank airy negative space for Chinese title overlay, no objects there. On right 42 percent compose one elegant translucent pale cyan upper human anatomical torso showing subtle lungs and heart in a respectful academic visualization, with two small floating clear glass cards containing a simple class network diagram and a small blue line chart, open medical textbook resting below. Refined delicate medical editorial rendering, clear normal human proportions, frosted glass, soft natural ambient light, slight blue depth, contemporary professional teaching platform. No laptop, no graduation cap, no human faces, no cartoon people, no busy neon, no watermark. Wide hero banner composition.

教学知识库生成提示：

> A single ultrawide 5:1 hero background illustration for a sophisticated Chinese medical teaching resource library. No text, no letters, no numbers, no labels, no watermark. Blue and white clinical editorial atmosphere. Left 55 percent dark cobalt to medium azure empty gradient for white title overlay. On the right a realistic elegant floating medical imaging glass panel with luminous blue lung anatomy illustration and a few smaller clinical scan thumbnails, clean modern hospital background softly blurred, delicate wave of cyan light along the bottom. Premium restrained medical education visual, not game sci-fi, no people, no faces, no dramatic effects, no neon overload, no symbols pretending to be actual patient records. Very wide panoramic website masthead with large clean negative space on the left.
