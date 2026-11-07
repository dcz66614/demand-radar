# MUSE 指令：Demand Radar REWORK2（执行冻结版）

## 0. 任务与权限

请先逐字阅读：
1. REWORK1 全部源码、SQLite、5 份 `*_r1.md`、R01–R07 审查记录；
2. `Demand_Radar_REWORK1_Independent_Review_2026-11-05.md`；
3. `Demand_Radar_REWORK2_Regression_Tests.py`（把文件复制到 `tests/test_rework2_adversarial.py` 并先运行，保留 RED 日志）。

**本次目标**：修复已证实的代码错误、纠正需求归纳/评分逻辑、重写可追溯的当前版本报告。**不准**继续扩增线索、生成大批 PRD 或制造额外 MVP 来替代整改。任何阶段都不能降低既定门槛或伪造测试结果。

使用单独 `demand-radar-rework2/` 工作目录，不覆盖原 ZIP 或 REWORK1；不推送 GitHub、不发帖、不联系 Issue 作者、不调用付费 API、不提供真实券商/医学应用、不访问其他个人项目。必要时允许只读的公开 Issue/文档访问并记录 URL/日期。对所有关键缺陷采用独立测试者的先红后绿机制。

## R2-01 — 首先修好五个可复现的独立失败测试（P0，第一优先级）

目标文件：`mvps/r1_b/signalcheck.py`、`mvps/r1_a/validator.py`。

**RSA：** 删除“RSA 必须>=0”的数学前提。当前实现 `rel=abs(reported-expected)/expected` 有符号分母错误。建议：
- `delta=abs(reported-expected)`；`scale=max(abs(expected), 1e-8)`；使用严格界限 `delta <= max(abs_tol, rel_tol*scale)`，其中 `abs_tol`、`rel_tol` 应作为受审参数，在文档解释为何适合该指标，避免“任意抄 5%”作为科学事实。
- 对非有限值 NaN/inf 立即拒绝；在 `expected≈0` 使用绝对容差。
- 正确负值应通过，千万/百万量级错报必须失败。独立复算 RSA 的定义及单位。不要单纯写 `abs(expected)` 然后保留 `reported>=0`。
- 补充 ≥12 组正、负、近零、非有限值、缺项与短序列案例。

**呼吸相位：** 在 `zip` 前拒绝 `len(reported_durations)!=len(intervals)`，验证 `fs>0`、单位、区间递增、非有限值；增加多余值 `[1,1,999]` 的回归测试。

**JSON 模式：** `bool` 不能被 `int` 检查当成整数，`isinstance(True,int)` 是 Python 特性，必须显式排除；增加 bool/int/float/str、数组/对象嵌套测试。

**流式函数调用：** 从单个 `_pending` 改为按真实 `item_id`/`output_index`/调用 ID 关联的状态字典。每一个唯一 `function_call` 的 done 事件恰好产生一个 completed；不丢、不重复、不串参。至少覆盖两个交错函数调用、重复 done、异常顺序、没有 done 和单调用的旧行为。若真实事件合同不支持所设计的字段，必须先从可靠 SDK 文档或已记录事件中核实，不能猜协议。

**退出条件：** 五项 `test_rework2_adversarial.py` 全绿；所有原有生产相关测试仍绿；独立 QA 调用真实函数再做至少一组随机参数反例。修不好则按 `BLOCKED` 停止并交付证据，不要掩盖。

## R2-02 — 跨版本兼容与真实 UI 执行

目标：修复 `test_signal_power_does_not_use_removed_trapz`。删除 `assert not hasattr(np,'trapz')`，因为 NumPy 2.3.5 中该属性存在，测试不应把某版本的实现状态当作软件要求。保留对 `numpy.trapezoid` 计算数值及代码中未调用旧 API 的明确测试。

在可用的隔离环境中记录 Python、NumPy、Streamlit、pytest、ruff 版本及 requirements 解析结果。建议测试 Python 3.12/3.13 × NumPy 2.3.x 与当前版本，受平台安装能力限制时清楚标注。运行三套 Streamlit 应用的 AppTest 流程；录下每一项实际测试命令、退出码、日志，以及 UI 滤镜/导出行为。

**不得**用反复重跑直到偶然变绿的方式掩盖随机失败；若 AppTest 因竞态失败，写出确定的等待条件及超时断言。

## R2-03 — 修正主题语义与证据入选机制（不准降低门槛）

新增字段 `problem_signature`：至少区分 `actor`, `input_artifact`, `operation`, `observed_failure`, `expected_output`, `affected_product`, `version_or_environment`。旧数据不覆盖，建立 `evidence_assessment` 新表或迁移表，保留判决原因/来源/日期。

逐条审查目前 5 个入选主题的证据链接，分类为：`DIRECT_SAME_PAIN`、`ADJACENT_CONTEXT`、`DUPLICATE`、`OUT_OF_SCOPE`、`UNKNOWN`。

必查错误样例：
- BIO signals：NeuroKit #1176 文档 CI、#1160 包管理、#1236 setuptools PIN 不得作为“信号函数算错/崩溃”的直接证据；WFDB #538/GDF 数据读取与 MNE #14321/EDF edge artefact 不得未经论证就给 NeuroKit 核心算法问题贡献独立组织数。
- FIN workspace：EdgarTools #1848 13F 头寸、OpenBB #7744 图表 RFC、yfinance #3011/#3012 CVE 是不同产品问题，不得混成一个已被 3 组织交叉证实的产品需求。
- AI reliability：AgentLab Docker 部署 / CAPTCHA / 基准复现问题与 tokenizer/streaming 问题分开；LangChain #41708/#41709/#41710 同一报告多次发帖，仍不得增加独立需求量。

为每个新候选 PRD 保存精确可复现的样本、期待结果、独立支持来源组、未解决状态和匹配理由。只允许 `DIRECT_SAME_PAIN` 进入 PRD 的独立计数。跨组织独立性必须要求同一问题，不是同一宽泛领域。

## R2-04 — 修正评分与竞品证据

当前 `score.py` 中未证实可行性仍 F=15，缺乏复用证据仍 L=5；全体入选主题的 `current_workaround='see linked issues'`，PRD 却明确承认没有真实 workaround。把这种占位符转为 NULL/UNKNOWN，不能得肯定分。提出证据绑定的评分规则并让审查 Agent 独立确认，保留旧评分供 diff。原始门槛 70 不能为了保留入选数量而放松。

竞品研究必须对准 **同一 user task 的同一 acceptance case**：记录产品版本、实际可执行功能、证据链接、为什么能/不能解决该输入。单凭官方首页的营销话术或“它就是出问题的库”不能支撑 `does_solve=0` 的结论；拿不准记录 UNKNOWN 并阻断 G 正分及选题门。

运行 `score` 和 R05 gate；对每个入选资格输出旧分/新分、直接证据数、跨组织数、作者数、真实竞品证据及被剔除的旁证。**允许全部或多数主题不合格**，必须在报告中清楚说明。

## R2-05 — 正确定位两个 MVP

在 R2-01 技术修复后，检查 R1-A 和 R1-B 是否至少拥有一种真实输入验证：
- API：使用匿名/脱敏的真实事件序列离线回放；对已知模型，明确接入真实 tokenizer 或按文档明确标记近似算法；事实正确性不得靠自身预设 `factual=False` 取得“识别真实错误”的宣传结论。
- BIO：对一个可公开分发的信号/复现样本执行实际解析、算法输出校验，最好覆盖目标 NeuroKit/wfdb 等上游 API 的真实版本；另外保留本地无网络的故障注入测试。

若仍只能在合成 fixture 中测试，交付应标记 `SIMULATION_PROTOTYPE / NOT_REAL_WORLD_VALIDATED`；不得将其当作已经解决真实用户需求的正式 MVP。项目中的两个 validator 可以保留，但不得用它们抵消被重新评分淘汰的原 PRD。

## R2-06 — 更新当前唯一交付报告并重新验收

- 保留旧 `reports/final_report.md`、`progress/STATUS.md` 作为历史版，但应移入 `reports/superseded/` 或加明显的 `SUPERSEDED` 顶部标识；生成 `reports/final_report_rework2.md` 与当前 `progress/STATUS.md`。新文件的数字必须从现存 DB/脚本实际计算，不得手写旧数字。
- 明确 `mvp_selection.json` 的 5 个是“PRD-eligible”而非“实际已经构建”，使用 `prd_eligible`、`mvp_built` 两种字段或独立两个文件；更新消费者并重新跑测试。
- 留存真实测试日志、版本清单、数据库迁移摘要、SHA、URL 证据、不合格/未测试列表和未完成事项。
- 原 REWORK1 ZIP 和原版 ZIP 都只读保留，新的 ZIP 拥有不同文件名，打包完再从 ZIP 解压并做一次干净复测。
- QA 结论只能是 `ACCEPTED`、`ACCEPTED_RESEARCH_PROTOTYPE_ONLY`、`REWORK_REQUIRED` 或 `BLOCKED`，给出为什么。

## 强制测试与交付

1. 五项新的失败回归测试全绿；不能修改测试预期使错误实现通过，除非附上明确的原始规范证据并经独立审查认可。
2. 原有单元测试不得退化；报告真实 pass/fail/skip/blocked 数。
3. 每个合格 PRD 的具体失败机制与证据实际对应；不合格时从 qualified 中剔除。
4. SQLite source 状态、证据链接、PRD 卡片、gate CSV、MVP 选择状态与最终报告逐一对齐。
5. 所有仍存的真实缺陷与环境限制都有状态记录，不能出现 “PASS” 掩盖 `NOT_TESTED`。
6. 新交付包含一个 `README_REWORK2.md`，从解压到运行命令可以直接复制；交付 ZIP、审计报告、评分 diff、全部测试日志与源代码。

现在从 R2-01 的 RED 测试开始执行。不再重写总计划、不扩大数据量、不重复无价值研究。完成所有阶段后让独立 QA 审查者用新鲜提取的交付 ZIP 做最终复核，然后提交审计结果与实际状态。
