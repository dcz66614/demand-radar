# Demand Radar：Muse 可直接执行的详细工程计划书

> **版本** v1.0 ｜ **编制日期** 2026-11-05 ｜ **执行主体** Muse 个人 Agent（可选 Muse Code） ｜ **状态** READY TO EXECUTE
>
> **一句话任务**：从真实的公开用户抱怨、GitHub Issues 和论坛讨论中寻找尚未被充分解决的软件痛点；保留逐条证据，验证与排名；形成 20 份可执行 PRD，并为经证据筛选的两个痛点各构建一个可运行、可测试的本地 MVP。
>
> **最重要的执行原则**：本文件已经完成需求分解、架构选择、数据模型、排序规则、验收设计。Muse 的工作是按任务卡实施、收集真实证据、运行测试与记录障碍；**不是重新头脑风暴、写长篇计划或凭空补足数量**。

---

## 0. 用户直接交给 Muse 的启动指令（连同本文件上传）

```text
执行附件《Demand Radar：Muse 可直接执行的详细工程计划书》v1.0。
这是已批准的实现规格，不要重写规划或让我重新选择技术栈。

先做 P00 环境预检、建立隔离工作目录，再按 P01→P10 的依赖关系运行。
允许对互不依赖的领域采集任务使用真实可用的子 Agent 并发；若不可用则串行执行，不得声称已并发。
所有外部证据必须保留原 URL、观察日期、可复核摘录或事实摘要；未知字段用 null，禁止虚构。
默认零额外付费，禁止购买/发送邮件/自动发帖/公开仓库/访问我的其他私有项目。
已知用户偏好：中文汇报；项目代码和数据库字段采用英文；最终代码可本地运行。

首个可验收检查点：完成 P00-P03，交付 6 个领域各 5 条真实候选（共目标 30 条）的 JSONL、SQLite、基础检索页面、质量门报告与 pytest 运行记录。完成后不要停在口头总结，若条件允许继续后续阶段。
每个阶段在 progress/STATUS.md 记录任务 ID、状态、产物路径、测试命令/结果和阻塞项；禁止把待办写成已完成。
遇到决定性信息缺失时依据本文件的降级规则处理；只有涉及额外付费、身份授权、私有数据或对外写入时才向我询问许可。
```

**若 Muse 不能读取附件**：把本文件全文贴入它的上下文；若无法持久访问文件系统，应明确汇报 `ENV_BLOCKED`，只交付数据与可下载源码，不要伪称完成了可执行程序。

## 1. 固定项目边界与结果定义

### 1.1 四层成果

1. **证据层**：公开原始线索（source item）及可核验的实际诉求，不是单纯热词列表。
2. **问题层**：去重后的 pain point（问题陈述、受影响用户、工作场景、当前替代、损失、证据）。
3. **决策层**：分数、竞品查证、风险、20 份产品需求卡（PRD）。
4. **软件层**：Demand Radar 工作台 + 最多 2 个真正可启动的 MVP，自动测试通过并有可执行复现说明。

**默认交付目标（目标 ≠ 必然完成）**：240 条不同的候选问题记录；≥120 条达到质量标准的去重问题；20 份 PRD；2 个通过选题门槛的独立 MVP。若真实世界中有效数量不足，交付真实数量、漏斗数据及缺口原因；不得拆分同一问题来凑数。开发两个 MVP 以达到独立的证据门槛为前提。

### 1.2 只研究六个领域

| ID | 领域 | 首要用户任务 | 排除项 |
|---|---|---|---|
| AI | AI 工具与开发工作流 | 调试、Agent 编排、API/成本可见性、导出/迁移 | 仅抱怨模型答复不好、没有具体复现步骤 |
| RES | 科研与论文工作流 | 文献证据追踪、实验复现、数据/方法对照 | 纯文学性观点、缺乏可实现任务 |
| BIO | 生物医学工程与教育 | 信号处理、可视化、实验教学、可重复分析 | 临床诊断/医疗决策软件 |
| FIN | 金融信息研究 | SEC 申报阅读、可追溯分析、公开资料对照 | 自动真实交易、个股荐股、代客理财 |
| JOB | 学生实习与求职 | 资格筛选、截止日管理、职位证据、投递准备 | 自动提交申请、代替用户陈述事实 |
| UK | 英国生活与公共交通 | 多来源出行比较、约束筛选、费用/时刻证据 | 自动购票、支付、访问个人票务账户 |

每个领域以**约 40 条候选**为发现目标；另有 5 条的先导实验（pilot）。目标不是配额驱动造假：任何域缺少真实数据，应记录 `SOURCE_LIMITED`。

### 1.3 不做什么

不建立多租户 SaaS、不使用付费 API、不注册服务、不将用户信息上传外部网站、不做真实商业化发布、不触碰已有 Quantbot、Obsidian 或私人仓库、不训练任何模型、不复制整站内容、不绕过登录/风控/速率限制。数据和软件默认只保存在 Muse 的**新建隔离目录**。

## 2. 已确定的技术栈和约束

| 层 | 决策 | 理由 |
|---|---|---|
| 运行环境 | Python 3.12（可用 3.11/3.13，前提是依赖安装通过） | 易于在 Linux 云 VM 运行 |
| 虚拟环境 | 标准库 `venv` | 不依赖专有编排器 |
| HTTP | `requests` + timeout + per-host 限速 | 简单可审计 |
| 数据验证 | `pydantic`、标准化 JSONL | 强类型、可隔离子 Agent 写入 |
| 数据存储 | SQLite（`sqlite3`） | 零运维、可重跑、可本地查看 |
| 页面 | Streamlit | 最快完成可操作审查后台 |
| 相似去重 | `rapidfuzz` + 确定性规则 | 先召回，后人工/独立 Agent 复核 |
| 测试 | `pytest` + `ruff` | 确定性反馈，防止假完成 |
| 批处理入口 | `python -m demand_radar ...` | 不依赖 Muse 自定义命令/私有 API |
| 可选并发 | Muse 原生 subagents（若实际开放） | 仅作用于独立的领域采集/审查 |
| 可选 Muse Code | Git worktree + 本地测试 | 适合独立软件开发，但不能假定所有版本有 workflow engine |

### 2.1 最小系统架构

```text
公开数据源（GitHub Issues / Hacker News / 官方文档）
       | 限速只读采集
       v
source_items JSONL --校验--> SQLite source_items
       |                      |
       v                      v
pain_point extraction     原始证据与来源清单
       |
       v
独立二审 -- 按定义去重 -- competitor checks
       |
       v
可解释评分(0-100) -> PRD(20) -> MVP gate(<=2)
       |                       |
       v                       v
Streamlit Dashboard       两个独立本地可运行 MVP
       \_______________________/
                 |
           pytest/ruff + 审计包
```

### 2.2 目录结构：必须按此创建

```text
demand-radar/
├── README.md
├── pyproject.toml
├── .gitignore
├── .env.example                  # 只列变量名称，绝不放真实密钥
├── config/
│   ├── domains.yaml             # 6 个固定领域与排除词
│   ├── sources.yaml             # 官方允许的读取入口
│   ├── queries.yaml             # 30 个固定查询模板
│   ├── scoring.yaml             # 固定评分规则
│   └── limits.yaml              # 限流、重试与支出上限
├── src/demand_radar/
│   ├── __init__.py
│   ├── __main__.py               # CLI
│   ├── config.py
│   ├── models.py                 # Pydantic 模型
│   ├── db.py                     # 事务/迁移
│   ├── ingest.py                 # JSONL 校验、幂等入库
│   ├── collectors/
│   │   ├── github_issues.py
│   │   └── hackernews.py
│   ├── extract.py                # 痛点抽取与证据引用
│   ├── normalize.py              # URL/文本规范化
│   ├── dedupe.py                 # 去重建议，不静默删除
│   ├── verification.py           # 验证工作流
│   ├── score.py                  # 确定性打分
│   ├── competitors.py            # 竞品证据
│   ├── prd.py                    # PRD 模板与导出
│   ├── selection.py              # MVP 确定性选题门
│   └── export.py
├── app/
│   └── streamlit_app.py
├── data/
│   ├── inbox/{AI,RES,BIO,FIN,JOB,UK}/
│   ├── snapshots/               # 小型、合法摘录，不是整页存档
│   ├── demand_radar.sqlite
│   └── exports/
├── reports/
│   ├── pilot_report.md
│   ├── coverage_report.md
│   ├── evidence_audit.md
│   ├── source_failures.csv
│   ├── ranking.csv
│   ├── prds/
│   └── final_report.md
├── mvps/
│   ├── mvp_a/
│   └── mvp_b/
├── tests/
│   ├── fixtures/
│   ├── test_models.py
│   ├── test_collectors.py
│   ├── test_ingest.py
│   ├── test_dedupe.py
│   ├── test_score.py
│   ├── test_selection.py
│   ├── test_export.py
│   └── test_app_smoke.py
└── progress/
    ├── STATUS.md
    ├── decisions.md
    ├── blockers.md
    └── run_log.jsonl
```

### 2.3 初次启动的精确命令（Linux Shell）

先检查，再创建新目录；不要覆盖已有目录：

```bash
pwd
python3 --version
git --version
mkdir -p "$HOME/projects/demand-radar"
cd "$HOME/projects/demand-radar"
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install 'requests>=2.32,<3' 'pydantic>=2.9,<3' \
  'pandas>=2.2,<4' 'streamlit>=1.40,<3' 'rapidfuzz>=3.10,<4' \
  'PyYAML>=6,<7' 'pytest>=8,<10' 'ruff>=0.7,<1'
```

> 上述是**兼容范围**而非已验证锁定版本；实际安装成功后生成依赖锁文件并记录 Python/平台版本。若 Shell 不可用，不得虚构这些命令的执行结果。不要运行第三方未知来源的一键安装脚本。

## 3. 外部数据：精确来源、方法和合规降级

### 3.1 主要来源：只读优先

**A. GitHub Issues（P1，默认）**

- 官方文档：<https://docs.github.com/en/rest/issues/issues>；搜索语法：<https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/filtering-and-searching-issues-and-pull-requests>。
- 首选公开 Issues：`GET https://api.github.com/repos/{owner}/{repo}/issues?state=all&per_page=100&page=1`，需要识别并排除响应中的 `pull_request` 项。
- 跨仓库搜索仅作为补充；显式查询 `is:issue`，分页及限额按返回 headers 实际执行，不依赖硬编码的速率假设。
- `User-Agent: DemandRadarResearch/1.0`，设置 `timeout=(5,20)`；尊重 `Retry-After`、`X-RateLimit-Remaining` 与 `X-RateLimit-Reset`。
- 优先 issue 作者的具体问题描述、实际复现步骤、可行的替代方案；团队发布的项目介绍不能单独算用户需求。

**B. Hacker News（P1，默认）**

- 官方 API：<https://github.com/HackerNews/API>。
- `GET https://hacker-news.firebaseio.com/v0/askstories.json` 获取最新 Ask HN ID，然后 `/v0/item/{id}.json` 获取内容；必要时检查 `showstories.json`、`newstories.json`。
- **官方 HN API 不等于全文检索接口**。先取有界窗口、本地关键词筛选，若想用 Algolia HN Search，必须验证其当下可用性和服务条款，作为可选辅助而非依赖。
- 只收集与具体任务有关的公开讨论，保存 item ID、时间、链接和不超过 300 字符的说明/短摘录。

**C. 产品官方文档与公开反馈（P2，候选二审）**

- 用于核查“现有竞品能不能解决这件事”，不自动当作独立用户抱怨证据。
- 留存版本/发布日期/功能页面 URL。产品 marketing 文案视为厂商主张，不当作用户调查结论。

**D. Reddit（P3，仅获授权时）**

- 官方说明：<https://support.reddithelp.com/hc/en-us/articles/14945211791892-Developer-Platform-Accessing-Reddit-Data>。
- Reddit API 对开发者访问、研究用途和商业化有额外准入条款。**禁止默认批量采集或绕过登录与 API 权限**。
- 若 Muse 当前账户确有合法允许的访问方式，则记录权限范围并按许可执行；否则将其标记为 `DISABLED_PERMISSION`，使用 GitHub/HN/官方社区替代。浏览器人工可见内容不等于获得可批量复制的授权。

### 3.2 已核实的种子仓库（只读）

| 领域 | 可开始检查的项目 | 线索方向 |
|---|---|---|
| AI | `microsoft/markitdown`；`ServiceNow/AgentLab` | 文件格式解析、Agent 调试和浏览器测试 |
| RES | `jupyterlab/jupyterlab`（先核实可达）；`microsoft/markitdown` | Notebook 复现、文件与引用提取 |
| BIO | `neuropsychology/NeuroKit`；`MIT-LCP/wfdb-python` | ECG 处理、数据库转换、复现实验 |
| FIN | `dgunning/edgartools`；`openbb-finance/OpenBB`（可能有重定向） | 财报提取、数据接口、对齐与导出 |
| JOB | `speedyapply/JobSpy` | 职位字段缺失、地区/资格限制、招聘源质量 |
| UK | `planarnetwork/gb-transit`；`opentripplanner/OpenTripPlanner`（先核实） | GTFS、换乘路径、时刻与数据验证 |

种子库只定义搜索起点，不能提前判断存在什么需求；若链接跳转/归档，记录实际 URL 与日期。每域可再通过 GitHub Search 寻找 3–8 个活跃仓库，不需要用户审批。

### 3.3 搜索任务矩阵（写入 `config/queries.yaml`）

对每个领域执行以下 5 个 **不同问题角度**；每条查询至少在 GitHub 或 HN 中尝试一种可行来源：

| 角度 | 英文查询提示词 | 识别目标 |
|---|---|---|
| A：重复手工劳动 | `manual steps`, `every time`, `takes hours` | 工作量可计算、自动化价值明确 |
| B：失败与异常 | `bug`, `fails when`, `cannot export` | 可复现的功能阻塞 |
| C：跨工具衔接 | `integration`, `sync`, `migration`, `format` | 数据在多个工具间断裂 |
| D：功能限制 | `feature request`, `missing support`, `workaround` | 用户明确寻求替代做法 |
| E：新手认知成本 | `confusing`, `documentation`, `setup`, `onboarding` | 上手困难与学习成本 |

再使用领域关键词限定上下文，例如 `ECG R peak annotation`、`SEC XBRL amended filings`、`sponsorship eligibility internships`、`GTFS fare transfer`。**禁止把 30 条提示词当作 30 个独立证据**，独立性以真实发布者及工作场景衡量。

### 3.4 覆盖范围与配额规则

- 默认最近 365 天（运行时动态计算 UTC 日期），为了发现持续痛点允许回看至 24 个月，但较早的线索必须有近期佐证才可标记 `CURRENT`。
- 每个领域每个来源分多次小批次抽样；单一仓库最多贡献某领域已验证问题的 35%，以防一个热门仓库扭曲全体需求。
- 每个领域先收集 5 条真实候选；通过试运行再扩展到 40 条左右，不得一次性大量下载。
- API 请求失败：HTTP 429/403 依文档退避；至多 3 次有间隔重试，失败后保留原因并切换来源，不得绕过限制。
- 禁止用虚构帖子、未经核查的搜索摘要或纯模型猜测填补空缺。

## 4. 数据结构与判定标准（不再让 Muse 重新设计）

### 4.1 核心对象

- **source_item**：平台上的一条公开内容及其上下文（不是痛点）。
- **pain_point**：针对某个人群、某个工作流、某种失败或成本的具体问题。
- **evidence_link**：把问题和一条可查实的来源关联起来；一个问题可有多个独立证据。
- **competitor_check**：至少检查两个可能的现有解决办法或记录确实找不到的查证路径。
- **prd_card**：含用户故事、最小解决方案、负面边界、验证实验及开发限制的需求书。
- **mvp_run**：独立应用的实际执行和测试记录。

### 4.2 固定 SQLite DDL（保存至 `src/demand_radar/schema.sql`）

```sql
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS source_items (
  source_id TEXT PRIMARY KEY,
  platform TEXT NOT NULL CHECK(platform IN ('github','hackernews','official','reddit_authorized')),
  external_id TEXT NOT NULL,
  url TEXT NOT NULL,
  canonical_url TEXT NOT NULL,
  author_key TEXT,                     -- 可为空或不可逆摘要；导出时不含用户名
  title TEXT,
  excerpt TEXT NOT NULL,               -- <= 300 chars; 合法短摘录/摘要
  published_at TEXT,
  fetched_at TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  source_type TEXT NOT NULL,
  domain TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'FETCHED',
  UNIQUE(platform, external_id)
);
CREATE TABLE IF NOT EXISTS pain_points (
  pain_id TEXT PRIMARY KEY,
  domain TEXT NOT NULL CHECK(domain IN ('AI','RES','BIO','FIN','JOB','UK')),
  who TEXT NOT NULL,
  job_to_be_done TEXT NOT NULL,
  blocker TEXT NOT NULL,
  current_workaround TEXT,
  impact TEXT,
  status TEXT NOT NULL DEFAULT 'CANDIDATE'
     CHECK(status IN ('CANDIDATE','PENDING_REVIEW','VERIFIED','REJECTED','SOURCE_LIMITED')),
  cluster_key TEXT,
  evidence_count INTEGER NOT NULL DEFAULT 0,
  score INTEGER,
  score_reason TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS evidence_links (
  pain_id TEXT NOT NULL REFERENCES pain_points(pain_id),
  source_id TEXT NOT NULL REFERENCES source_items(source_id),
  is_firsthand INTEGER NOT NULL DEFAULT 0,
  independence_group TEXT NOT NULL,
  evidence_note TEXT NOT NULL,
  checked_at TEXT,
  review_status TEXT NOT NULL DEFAULT 'PENDING',
  PRIMARY KEY(pain_id, source_id)
);
CREATE TABLE IF NOT EXISTS competitor_checks (
  check_id TEXT PRIMARY KEY,
  pain_id TEXT NOT NULL REFERENCES pain_points(pain_id),
  product TEXT NOT NULL,
  checked_url TEXT NOT NULL,
  does_solve INTEGER,                  -- 1/0/null
  gaps TEXT,
  checked_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS prd_cards (
  prd_id TEXT PRIMARY KEY,
  pain_id TEXT NOT NULL UNIQUE REFERENCES pain_points(pain_id),
  status TEXT NOT NULL DEFAULT 'DRAFT',
  template_id TEXT NOT NULL,
  md_path TEXT NOT NULL,
  gate_reason TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS run_events (
  event_id TEXT PRIMARY KEY,
  stage_id TEXT NOT NULL,
  agent_role TEXT NOT NULL,
  event_type TEXT NOT NULL,
  detail_json TEXT NOT NULL,
  event_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sources_domain ON source_items(domain, published_at);
CREATE INDEX IF NOT EXISTS idx_pain_domain_status ON pain_points(domain, status);
CREATE INDEX IF NOT EXISTS idx_evidence_independence ON evidence_links(independence_group);
```

**完整性补充**：SQLite `CHECK` 不检查所有复杂业务约束；在 `models.py` 实现 URL 为 HTTPS（允许官方 HN HTTP 仅自动规范化为 HTTPS）、发布时间 UTC ISO-8601、`excerpt` ≤300 Unicode 字符、非空问题陈述、`score` 为 0–100、canonical URL 不带追踪参数等 Pydantic 校验。`source_id=sha256(platform + ':' + external_id)[:20]`；`pain_id=sha256(domain + '|' + normalized(job_to_be_done) + '|' + normalized(blocker))[:20]`，必要时对重名后缀做确定性冲突处理。不要用浮动 LLM 文本作为唯一业务主键。

### 4.3 子 Agent 输出的 JSONL 合同

每行一个 JSON；字段缺失用 `null`，不要伪造：

```json
{"platform":"github","external_id":"owner/repo#123","url":"https://github.com/owner/repo/issues/123","title":"Example title","excerpt":"Short evidence-based excerpt or neutral summary","published_at":"2026-10-01T11:00:00Z","fetched_at":"2026-11-05T00:00:00Z","domain":"AI","source_type":"firsthand_issue","who":"developer","job_to_be_done":"export structured records","blocker":"export fails on nested tables","current_workaround":null,"impact":null,"evidence_note":"Issue describes the exact failed output","review_status":"PENDING"}
```

> 上述 JSON **仅是数据结构示例，不是真实采集结果**，不能直接入正式证据库。真实数据必须带能打开的实际 Issue URL 与平台 ID。

### 4.4 有效问题（VERIFIED）的强制门槛

必须同时满足：

1. 至少一个可打开的一级公开来源；链接与内容相符，原始发布日期可确认或标记未知。
2. 清楚描述“谁 / 想做什么 / 卡在哪里”，不能只是“希望更智能”。
3. 能说明实际影响（有具体损失优先，但未知可写 null）。
4. 不与已保留问题完全重复；合并时保留原始多个来源，不删除出处。
5. 不涉及不合规收集个人数据、违法绕过、临床诊断或真实投资交易。
6. 证据核查由**不同于采集者**的审查角色完成；如果单 Agent 模式，用不同运行阶段重新打开 URL 复核并记录限制。

**强/弱证据区别**：`VERIFIED` 表示“公开来源确有这类问题”，**不代表存在规模化市场需求**。至少 2 个独立一手来源才具备“高置信选题”资格；转帖、同一 Issue 的评论、引用同一新闻稿，不构成独立证明。

### 4.5 去重与独立性

- 先对 URL 规范化，按 `platform + external_id` 精确去重。
- 再将同一 `domain`、相近 `job_to_be_done` 与 `blocker` 进行 RapidFuzz 文本相似度建议（起始阈值 90/100），**只生成 merge suggestion，不自动把不同问题静默合并**。
- 跨域类似问题原则上保留，除非相同用户工作流、输出和阻塞完全一致。
- 可信独立性单元优先是不同发帖者 + 不同组织/仓库或不同实际场景；同一人跨平台转帖仍计一个独立单元。
- 记录 `duplicates.csv`：保留 ID、候选合并 ID、理由、审查者与时间。

## 5. 排名规则：纯确定性、可单元测试

**总分 = 证据力度（30） + 严重程度（25） + 技术可实现性（20） + 竞品缺口（15） + 用户学习价值（10）**。

### 5.1 固定评分表

| 维度 | 评分方法 |
|---|---|
| 证据力度 `E` /30 | 1、2、3、4、≥5 个**独立一手来源**分别记 `10/15/20/25/30`；0 个记 0。无独立核验证据不可进入 MVP。
| 严重程度 `S` /25 | 0 无明确痛点；5 轻微不便；10 反复费时；15 任务明显受阻；20 核心流程失败；25 造成有出处的显著损失。必须记录原因。
| 可实现性 `F` /20 | 0 不可行/违法；5 要付费服务或不稳定访问；10 有明显数据/工程障碍；15 可用免费基础完成但有复杂限制；20 可在本地、公开数据下独立开发与测试。
| 竞品缺口 `G` /15 | 0 已有免费可靠方案完整解决；5 已有但有边界限制；10 有明显未覆盖场景；15 查证后未发现能满足核心场景的可用方案。每项至少留两条竞品检查路径。
| 学习价值 `L` /10 | 0 无新技术能力；5 可重复使用的程序技能；10 同时覆盖数据工程、可测试软件与目标领域。只影响最后排序，不代表市场证明。

**额外不可变规则**：不足 2 个独立一手来源的最高展示分为 **59**；证据 URL 失效或二审未完成显示 `UNVERIFIED`，不得进入 PRD Top 20；明显违规或高风险项目直接 `REJECTED`。最终分数及每维理由必须写入 SQLite 与 CSV，可逐项复算。

### 5.2 PRD 选择算法

1. 仅选 `VERIFIED`、不少于 2 个独立一手来源、`score >= 60`、至少核查 2 个竞品/替代路径的问题。
2. 按 score 降序、独立证据数降序、最近一手来源日期降序、pain_id 字典序升序。
3. 每个领域最多 5 份；若候选充足，先保证每域至少 2 份，再按总分填充至 20 份。
4. 不足 20 份则报告真实份数及原因；不降低门槛凑数。

## 6. MVP 产品选择：四个固定模板，不重新自由构思

> 方案优先级基于**真实需求选题**，但设计模式和技术边界已先冻结。Muse 只需把经过验证的用户任务映射到以下模板，不允许临时发明需要复杂外部服务的系统。

| 模板 ID | 场景 | 预先确定的可运行实现 | 不得做的功能 |
|---|---|---|---|
| T1 `issue_triage` | 重复 Issue、错误复现、交付协作混乱 | GitHub 公共 issue CSV/JSON 输入 → 问题聚类 → 可复核 triage 看板与导出 | 自动写回 GitHub、代替维护者关闭 Issue |
| T2 `doc_trace` | 论文/文档不同版本和证据难比对 | 导入公开 Markdown/CSV → 段落/表格归一 → 差异和来源视图 | 私有论文自动上传、宣称确定学术结论 |
| T3 `eligibility_check` | 招聘/学生资格难比对 | 导入公开规则 CSV → 结构化条件检索 → 证据链接与待确认项 | 冒充签证/移民法律判断、代投申请 |
| T4 `comparison_tracker` | 多源工具/公开产品规格难比较 | 导入结构化快照 → 可追溯字段比较、版本变化、CSV 导出 | 自动付款、隐性联网账户抓取 |

**确定性映射**：问题主对象为 Issues 则 T1；文档与实验记录则 T2；多条件资格/规则则 T3；多来源产品或服务比较则 T4。无法准确映射者只出 PRD，不进入本轮 MVP。两个 MVP 需满足 `score >= 70`、至少 2 个独立一手证据、可在免费资源下本地完成、自动测试可定义、无外部敏感写入；优先来自不同领域。若同域只有两条合格，先只做第一条并记录第二项目 `NOT_SELECTED`。

**MVP 固定功能边界**（每个）：一个本地导入入口（JSONL/CSV/Markdown 中相关格式）；一个结果表格；至少 2 个过滤器；原始证据/来源链接；CSV 导出；一个错误状态提示；README；≥10 个有断言的测试；零外部必需付费依赖。不得在 MVP 阶段加入登录、支付、邮件群发、消息推送或多租户架构。

## 7. 分阶段逐条任务卡（Muse 按顺序执行）

> 每张任务卡的 `DoD` 即 Definition of Done。**阶段编号与文件名是固定的**；允许在不破坏此规范的情况下实现内部函数。

### P00｜隔离环境与能力探测（强制首步）

**负责人**：Coordinator；**依赖**：无。

1. 识别当前执行面：Muse 个人 Agent VM / Muse Code / 仅浏览器。写 `progress/STATUS.md` 的 `execution_surface`。
2. 读取 Python/网络/文件系统/目录的实际能力，检查所需软件版本与可写空间。禁止默认拥有 GitHub 登录态或任意 API Token。
3. 创建**新**根目录和结构，生成 `README.md`、`.gitignore`（忽略 `.venv/`、`.env`、`data/*.sqlite`、缓存）、`config/limits.yaml`（零额外支出）。
4. 记录环境检查命令与真实 stdout 到 `reports/environment.md`；所有外部连接默认只读。

**DoD**：目录存在，`python --version` 有真实结果（否则 `ENV_BLOCKED`）；`pytest --version` 可运行或明确记录依赖安装阻断；原有目录未被修改。

### P01｜模型/数据库/CLI 最小骨架

**负责人**：Builder；**依赖**：P00。

1. 实现 `schema.sql` 及 `db.py`，支持 `init_db()` 与安全 `UPSERT`；每次入库使用显式事务。
2. 写 `models.py` 验证 JSONL 结构、URL、时间、领域和状态。
3. 写 `__main__.py` 的 CLI：`init`、`ingest --file`、`report --stage`、`score`、`export --format csv/json`；不可用选项须退出非零状态。
4. `tests/fixtures/` 用**清楚标记的 synthetic fixture**测试，不与真实搜集数据混在同一数据库。

**DoD**：运行 `python -m demand_radar init` 成功创建 DB；`pytest` 中数据库与 Pydantic 相关测试通过。

### P02｜两个真实数据源采集器

**负责人**：Collector Engineer；**依赖**：P01。

1. `github_issues.py` 能分页读公开 Issue、排除 PR、处理 304/403/429、记录 API 返回的 rate limit headers。
2. `hackernews.py` 用官方 Firebase API 获取 Ask/Show/HN Item，进行本地关键词过滤；HTML 只做安全文本提取。
3. 任何失败写 `reports/source_failures.csv`，包含 host、HTTP 状态、失败时间、重试次数、下次允许访问时间（如可判定）。
4. 在 `tests/test_collectors.py` 以 mock 响应测试成功/空列表/429/无字段/网络超时/重复 ID。

**DoD**：能成功收集**至少一个真实公开结果**并记录来源；限速测试和失败退避测试通过。网络被禁用则 `COLLECTOR_BLOCKED` 并中止真实数据部分，不能转入伪造。

### P03｜六领域 Pilot：各 5 条真实候选

**负责人**：6 个 Researcher（按实际可用并发分波次）；**依赖**：P02。

1. 每域选择经证实可访问的仓库与 HN 入口，按 `queries.yaml` 至少 2 个角度搜索。
2. 每域最多提交 5 条不同的公开候选，总目标 30 条；写 `data/inbox/{DOMAIN}/pilot.jsonl`。
3. Coordinator 批量校验 JSONL，合并到 DB；独立 Reviewer 重新打开来源并对照问题陈述。
4. 输出 `reports/pilot_report.md`：6 域候选/通过/失败/独立来源数、质量问题、未授权来源处理情况。
5. 构建初版 `app/streamlit_app.py`：证据列表、域筛选、来源打开按钮（只读）、采集时间。

**DoD**：目标 30 条都是真实 URL（若不足则展示真实数量）；SQLite 与 JSONL 行数对账；`python -m streamlit run app/streamlit_app.py` 实际启动（或注明运行环境阻断）。

**先导门 G1**：如果 30 条中核验通过不足 12 条，先修来源选择/抽取模板；如仍不足，进入证据不足的降级报告而非直接扩展。

### P04｜扩展收集：六领域各约 40 条候选

**负责人**：Researchers；**依赖**：P03 G1 PASS。

1. 分 3 波扩展，每波围绕**未覆盖角度**补采；领域单独 JSONL，不共享改写一个文件。
2. 每批实际写入前进行来源级去重、`source_id` 幂等校验、URL 复核与摘录长度检查。
3. 每个领域写 `reports/coverage_{DOMAIN}.md`：五个角度覆盖、来源份额、重复率、失败源、真实数量。
4. Coordinator 只在各 Agent 完成后把 JSONL 作为单写者事务入库。

**DoD**：提供候选漏斗：尝试抓取数、HTTP 成功数、有效来源数、有效问题数、去重后数；目标 240（不足必须说明），无整站抓取或重复灌库。

### P05｜二审、去重与竞品核查

**负责人**：Independent Reviewer + Competitor Analyst；**依赖**：P04 可部分并行。

1. 对每条候选按 §4.4 二审；不符合标准明确 `REJECTED` 并记录拒绝原因。
2. 执行相似度建议并复核，保留不同来源的 `evidence_links`。记录合并决策到 `reports/duplicates.csv`。
3. 为预计可能进入 Top 20 的条目逐条调查至少两个现有方案/替代路径，填 `competitor_checks`。
4. 若发现现成产品完整覆盖，分配更低竞品缺口分；不能仅因为搜索不到竞品就宣称“市场空白”。
5. 统计独立来源，输出 `reports/evidence_audit.md`（含代表性误判与复核发现）。

**DoD**：所有保留问题至少一手来源，所有被排除条目有理由；`VERIFIED` 是“有真实问题”，不是“已证明有市场”。

### P06｜确定性评分与 20 份 PRD

**负责人**：Scorer + Product Writer；**依赖**：P05。

1. 根据 §5 编写 `score.py`，每个维度的人工判断转为**受限定的离散值**，并保存原始理由。
2. 生成 `reports/ranking.csv`，每项含 `E,S,F,G,L,total,cap_applied,evidence_count,verified_at`。
3. 根据固定排序及每域覆盖约束选 Top 20，生成 `reports/prds/PRD_{pain_id}.md`。
4. 每份 PRD 填写下列固定 11 节，不得使用空泛模板句：背景与来源；用户画像；Job-to-be-Done；当前阻塞；可衡量影响；竞品差距；MVP 输入/输出；功能与明确排除项；3–5 个验收场景；隐私合规；未知/停止条件。
5. 独立审计 20 份 PRD 的来源一致性，不允许给不存在的引用加脚注。

**DoD**：`pytest tests/test_score.py tests/test_selection.py` 全过；评分能复算；有效 PRD 真实数量和达标率可核查。

### P07｜选题门：最多选两个 MVP

**负责人**：Coordinator + Reviewer；**依赖**：P06。

1. 运行 `selection.py` 的固定映射与阈值，导出 `reports/mvp_selection.json`：`selected[]`、`not_selected[]`、每个排除原因。
2. 对两个候选分别评估：是否无需登录/付费；是否可从公开小样本构造测试；是否会泄露用户信息；是否存在强竞争产品已解决问题。
3. 如第一名不可映射，按顺序尝试下一名；不能为了凑两个项目而违反选题门。
4. 在 `progress/decisions.md` 固定两个 MVP 的模板、痛点 ID、真实证据 URL 和禁止范围，不再反复重选。

**DoD**：每个入选 MVP 有 `score >= 70`、2 个以上独立来源、真实 PRD、已写明的 10 个测试需求；否则标记 `MVP_GATE_NOT_PASSED` 并结束该分支。

### P08｜MVP A 端到端构建

**负责人**：Builder-A + Test-A；**依赖**：P07 选中 A。

1. 使用 `mvps/mvp_a/` 自建隔离 Python 项目，不修改主工作台的数据模型。
2. 只使用 §6 对应的 T1/T2/T3/T4 预设计模板实现输入/输出、证据视图、过滤器、导出、异常提示。
3. 测试人员**先**根据 PRD 写最少 10 个可自动判定的测试，开发者再实现功能；不得改测试来迎合错误实现。
4. 本地用 1 份 synthetic fixture + 1 份公开真实小样本做 smoke test；真实数据引用保留 URL。
5. 留存执行日志、输入摘要、输出截图/文本结果，以及 `pytest -q` 退出码。

**DoD**：`README` 中的一条启动命令可运行；至少 10 个独立有效断言通过；不是只展示 mock 数据的空壳。

### P09｜MVP B 构建与独立审计

**负责人**：Builder-B + Test-B + Independent Reviewer；**依赖**：P07 选中 B；可与 P08 在隔离目录中并行。

1. 与 A 相同规范，但使用不同的 `mvps/mvp_b/` 环境、测试和数据目录。
2. 独立审计在不改变代码的情况下重新执行 A、B 的 README 启动与测试步骤，核对结果。
3. 检查是否依赖不存在的账号/私有文件/付费 API；有则报阻断，不得暗中创建账户。

**DoD**：两套项目均能从干净环境启动，且有独立测试报告；否则如实交付通过的部分。

### P10｜综合质量验证、交付和可选重复运行

**负责人**：Independent QA；**依赖**：P06，若有 MVP 则 P08/P09。

1. 运行以下检查：`python -m pytest -q`、`python -m ruff check .`、`python -m demand_radar report --stage final`、`python -m demand_radar export --format csv`。
2. 核对 100% 的 Top 20 PRD 来源 URL 格式，抽样重新打开至少 20 条关键证据；记录链接失效率与摘要误判率。
3. 再次计算候选数、去重数、验证数、独立双证据数、PRD 数、已执行 MVP 数与测试通过率。不得使用“估计”代替查询结果。
4. 写 `reports/final_report.md`（真实数据漏斗、前 20 需求、两个 MVP、失败原因、可复现命令、剩余风险）。
5. 在 `data/exports/` 导出可携带的 CSV、JSON、SQLite schema 文本；保留来源 URL，不导出作者的个人信息。
6. 将最终源代码与报告打包为本地只读归档（如运行环境支持），**不自动公开上传**。
7. 后续刷新必须用户再次发出命令或 Muse 在实际产品能力允许且用户已批准的情况下设置低频只读任务；默认不创建定时任务。

**DoD**：交付清单逐个文件可打开；有真实测试运行记录；所有未完成项以 `BLOCKED/NOT_DONE` 标示。

## 8. Agent 调度表：固定角色和写入边界

| 角色 | 任务卡 | 输入 | 唯一可写路径 | 必须输出 |
|---|---|---|---|---|
| Coordinator | P00/P04/P07/P10 | 本计划、阶段状态 | `progress/`, 集中写 DB | 阶段状态与签收 |
| Collector AI | P03/P04 | AI 搜索词/来源 | `data/inbox/AI/` | 来源 JSONL |
| Collector RES | P03/P04 | RES 搜索词/来源 | `data/inbox/RES/` | 来源 JSONL |
| Collector BIO | P03/P04 | BIO 搜索词/来源 | `data/inbox/BIO/` | 来源 JSONL |
| Collector FIN | P03/P04 | FIN 搜索词/来源 | `data/inbox/FIN/` | 来源 JSONL |
| Collector JOB | P03/P04 | JOB 搜索词/来源 | `data/inbox/JOB/` | 来源 JSONL |
| Collector UK | P03/P04 | UK 搜索词/来源 | `data/inbox/UK/` | 来源 JSONL |
| Reviewer | P03/P05/P06/P09/P10 | 原来源 URL、候选 | `reports/evidence_audit.md`, 审查 JSONL | 审核结果 |
| Builder | P01/P02/P08/P09 | PRD、接口合同 | `src/`, `app/`, `mvps/` 独立子目录 | 运行代码 |
| QA | 每个 gate | 测试脚本、真实执行输出 | `tests/`, `reports/` | 通过/失败证据 |

**并行约束**：首次以 `coordinator + 最多 3 个领域 collector + reviewer` 为逻辑编排；由 Muse 实际能力决定并发数，不能探测到则顺序运行。同一时间**只有 Coordinator 能写 SQLite**；子 Agent 仅写自己的 JSONL。Builder-A 与 Builder-B 不修改同一文件，冲突时各用独立工作树或目录。审查角色不能给自己编写的测试自行签发“独立通过”。

### 8.1 子 Agent 的可直接复制任务合同

```text
角色：COLLECTOR_{DOMAIN}
目标：对唯一指定领域 {DOMAIN} 收集当前批次最多 {N} 条真实公开软件痛点。
只读来源：config/sources.yaml 中标记允许的 GitHub/HN/官方页面。
执行：打开原始页面→核实时间与内容→提炼 who/job/blocker→保留短摘录和 URL→产出 JSONL。
写入位置：data/inbox/{DOMAIN}/{BATCH_ID}.jsonl，绝不写主 DB、不改其他目录。
禁止：凭空编造、绕过权限、把同一转帖当独立证据、发帖联系用户、生成超过 300 字符的引用。
输出：有效条目数、失败数、URL 列表、限流/访问问题、文件 SHA256。
验收：逐行符合 models.py；对于不能验证的字段用 null。
```

```text
角色：INDEPENDENT_REVIEWER
输入：上一批 collector 产生的 JSONL，以及原始 URL。
逐条确认链接和摘录一致、问题陈述完整、没有把产品宣传当用户需求、同一需求没有重复拆分。
输出 VERIFIED/REJECTED/PENDING、每条简短理由、独立证据分组与合并建议。
禁止修改原始采集文件；写审查结果到 reports/ 并交给 coordinator 合并。
```

```text
角色：MVP_BUILDER_{A|B}
输入：selection.json 指定的 pain_id、T1-T4 模板之一、单份 PRD。
只能写 mvps/mvp_{a|b}/。先建立测试，再实现公开样本端到端跑通。
MVP 最低功能：可读取真实数据、结果表、2 个过滤器、证据链接、导出、错误提示、README。
报告真实测试命令/退出码和未解决项；不得更改测试来伪造成功。
```

## 9. 自动化验收：明确要写的测试（不可省略）

| 测试编号 | 最低断言 | 类型 |
|---|---|---|
| T01 | 同一 GitHub Issue 重试 3 次仍仅有 1 条 `source_items` | 幂等性 |
| T02 | GitHub `pull_request` 对象不作为 Issue 采集 | 来源准确性 |
| T03 | 429 时遵守 Retry-After、没有立刻无限重试 | 访问合规 |
| T04 | 缺少 URL/不可解析日期按预期拒绝或标注未知 | Schema |
| T05 | URL 追踪参数差异不使相同帖子重复计数 | 规范化 |
| T06 | 相同作者跨平台转发不增加独立证据计数 | 证据独立性 |
| T07 | 相同领域与强相似内容只建议合并，不静默删除 | 去重 |
| T08 | E=30、S=25、F=20、G=15、L=10 时总分为 100 | 评分上界 |
| T09 | 仅 1 个独立来源即使子项评分高也被封顶 59 | 评分风险阈值 |
| T10 | 无 VERIFIED 状态/无 2 个独立来源不会进入 PRD | 门槛 |
| T11 | 仅有 1 条合格 MVP 时 selection 返回 1 条，不假造第 2 条 | 选题 |
| T12 | CSV 导出保留 URL，不导出 author_key / 个人联系方式 | 隐私 |
| T13 | 取消网络后应用仍能浏览已入库数据 | 离线可用 |
| T14 | 错误输入不导致 Streamlit 白屏或数据丢失 | UI 容错 |
| T15 | 以真实采集文件重跑 ingest 后报告计数不变 | 回归 |
| T16 | 独立 QA 从 README 复现主程序启动与查询 | 集成 |

**每个 MVP 另需 ≥10 个具体断言**：覆盖导入、正常结果、空结果、损坏数据、缺列、重复行、两个过滤器、来源保留、导出一致性和无外部账号依赖。真实 API 集成测试与本地 mock 单元测试必须在报告中区别列出，mock 通过不代表联网抓取成功。

## 10. 失败分支与执行停止规则

| 情景 | 处理决定 | 状态码 |
|---|---|---|
| Muse 无 Shell 或文件读写 | 尝试 Muse Code；不可用则只输出结构化工件，不宣称程序可运行 | `ENV_BLOCKED` |
| GitHub/HN 被防护或限额限制 | 退避三次，记录 headers/时间，换其他允许的公共源 | `SOURCE_RATE_LIMITED` |
| Reddit 未授权 | 禁用 Reddit 采集模块，不绕过、不花钱 | `DISABLED_PERMISSION` |
| 30 条 Pilot 中有效少于 12 | 检查查询质量、重新选择种子源；最多两轮定向修正 | `PILOT_REWORK` |
| 240 个候选无法收满 | 按真实采集数交付、注明覆盖不足和偏差 | `SOURCE_LIMITED` |
| 少于 20 份符合门槛的 PRD | 交付实际 N 份，不放宽标准 | `PRD_SHORTFALL` |
| 没有 2 个符合约束的 MVP | 仅构建 0–1 个；保留未满足 gate 的原因 | `MVP_GATE_NOT_PASSED` |
| 测试修复 3 轮仍不通过 | 保留失败用例与日志，不偷偷删除测试 | `TEST_BLOCKED` |
| 有需用户付款、授权、发信、公开发布的步骤 | 跳过并等待显式许可，不影响其他可执行分支 | `APPROVAL_REQUIRED` |
| 超出订阅内可用计算 / 服务限制 | 保存断点，不额外消费付费 API | `RESOURCE_LIMIT` |

**任务完成条件**：截至当前实际可用数据与能力，所有阶段均有 `DONE/NOT_DONE/BLOCKED/NOT_APPLICABLE` 记录；材料、结果和错误可被下一位工程师复核。不得以“已经想清楚怎么做”代替工作产物。

## 11. 汇报合同：Muse 每阶段只能按这个格式总结

```text
[STAGE] P0X - <stage name>
STATUS: DONE | BLOCKED | PARTIAL
REAL_COUNT: fetched=?, source_items=?, candidates=?, verified=?, rejected=?
ARTIFACTS: exact relative path(s)
TESTS: command, passed/failed/skipped, exit code
EVIDENCE_SAMPLE: 3 actually-opened URLs (or NONE + reason)
DECISION: PASS_NEXT_GATE | REWORK | STOP_WITH_EVIDENCE
BLOCKERS: concrete error messages, no estimates
NEXT: next dependency task ID
```

**最终汇报 10 项硬清单**：① six-domain coverage；② candidate/verified/unique counts；③ source provenance；④ ranking.csv；⑤ PRDs；⑥ MVP selection reasons；⑦ A/B runnable code；⑧ pytest+ruff logs；⑨ security/privacy confirmation；⑩ archive or exact artifact paths。

## 12. 交付清单（按实际存在核验）

| 交付物 | 路径 | 验收 |
|---|---|---|
| 运行指南 | `README.md` | 环境、安装、运行、数据局限、验证命令 |
| 数据库 | `data/demand_radar.sqlite` | 只含真实采集与已标注状态 |
| 证据表 | `data/exports/source_items.csv` | 可追溯 URL、时间、短摘录 |
| 问题排名 | `reports/ranking.csv` | 五维可复算分数、独立来源数 |
| 领域覆盖 | `reports/coverage_report.md` | 真实分母与失败来源 |
| 二审记录 | `reports/evidence_audit.md` | 独立复核样本和误判记录 |
| PRD 包 | `reports/prds/` | 最多 20 份达标产品需求书 |
| MVP A/B | `mvps/mvp_a/`, `mvps/mvp_b/` | 真正启动、实际输入输出、自动测试 |
| 测试 | `tests/` + `reports/final_report.md` | pytest/ruff 真实输出与命令 |
| 决策与阻断 | `progress/` | 阶段、评分、选题和受阻理由 |

## 13. 真实资料依据（2026-11-05 核验）

1. Meta Muse 个人 Agent 与 Secure VM：<https://research.meta.ai/blog/security-and-safety-for-ai-agents-our-approach-with-muse>。
2. Meta Muse 官方介绍（支持长期目标与浏览器，但功能可能按账号和地区开放）：<https://about.fb.com/news/2026/09/introducing-muse-personal-ai-agent/>。
3. Muse Code 说明与 Workflow rollout：<https://dev.meta.ai/docs/muse-code>、<https://dev.meta.ai/docs/muse-code/workflows>。
4. GitHub 官方 Issues API：<https://docs.github.com/en/rest/issues/issues>。
5. GitHub REST API 限流与退避：<https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api>。
6. Hacker News 官方 API：<https://github.com/HackerNews/API>。
7. Reddit 官方开发与研究权限：<https://support.reddithelp.com/hc/en-us/articles/14945211791892-Developer-Platform-Accessing-Reddit-Data>。
8. Streamlit 官方启动说明：<https://docs.streamlit.io/develop/concepts/architecture/run-your-app>。
9. 参考开源项目：<https://github.com/microsoft/markitdown>；<https://github.com/ServiceNow/AgentLab>；<https://github.com/neuropsychology/NeuroKit>；<https://github.com/dgunning/edgartools>；<https://github.com/planarnetwork/gb-transit>。

---

## 附录 A：人类只需做什么

1. 向 Muse 发送本文件和第 0 节启动指令。
2. 只在它真的请求**付费、身份授权、私有账户写入或对外发布**时决定是否批准（默认不批准）。
3. 检查 `P03` 的真实 URL 与测试日志；最终检查 MVP 是否能重新运行。

剩下的调查问题、结构设计、编排、来源核查、评分、文档、编码、测试、失败分支均由本执行计划约束，不需要用户反复决定。

## 附录 B：预先指定的首个可运行验收命令

```bash
cd "$HOME/projects/demand-radar"
. .venv/bin/activate
python -m demand_radar init
python -m demand_radar ingest --file data/inbox/AI/pilot.jsonl
python -m demand_radar score
python -m demand_radar report --stage pilot
python -m pytest -q
python -m ruff check .
python -m streamlit run app/streamlit_app.py
```

如果 `python -m demand_radar` 报 `No module named demand_radar`，应在 `pyproject.toml` 配置正确的 `src/` 包布局并使用 `python -m pip install -e .`，**不是**通过改写验收命令掩盖工程问题。
