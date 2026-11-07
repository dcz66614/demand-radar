# Demand Radar REWORK1 — 独立二次验收报告

**验收时间**：2026-11-05（以本次会话所见 Drive 快照为准）  
**交付件**：`demand-radar-rework1-2026-11-05.zip`（Google Drive）  
**SHA-256**：`0e736693b535f75641abce5e265c8e9ee91a5b63224fd0c5b9972e2ba89ea5c3`  
**原版保留**：`demand-radar-2026-11-05.zip`，SHA-256 `963568deaff04e778123d17cd4f5cdaba7f9957212d248079240c12588f2b261`  
**最终裁定**：**REWORK2_REQUIRED / NOT_ADOPTED**。底层数据管道的大部分 R01–R07 工程修复有效，但科研数值验证、模拟 API 校验和需求评分仍有能够独立复现的关键错误。

## 1. 审阅范围与核查方式

- Drive 当前文件夹包含两个 ZIP（原版和 REWORK1）；新 ZIP 192 个目录/文件条目、156 个实际文件、压缩后 839,767 字节。通过 ZIP CRC 完整性检查，随包 `MANIFEST.sha256` 检验无异常。
- 审阅项目主 README、P00–P10 原始计划、R01–R07 状态与报告、5 份新 PRD、评分/选题/竞品模块、两个 MVP 验证器及测试、SQLite 数据库、CSV 与 JSONL 证据、原版与新版 ZIP 文件差异；对代表性公开 Issue 使用 GitHub 连接器核实标题、状态和原文。
- **可复现的直接运行**：`PYTHONPATH=src python -m demand_radar init`；`score`；`report --stage final`；R05 gate runner；重算 ranking 文件 SHA-256 与 gate fingerprint。
- 单独运行了非 UI 测试和新的对抗性回归测试。当前验收容器缺少 Streamlit，且无法联网下载安装，因此不能独立重跑 Streamlit UI/AppTest，也不能在这里证实 Muse 声称的 154 全通过；当前环境无 Ruff 命令，亦未独立运行 lint。
- **范围限制**：218 条来源的状态、索引和审查字段做了结构及汇总一致性核查；不是对 218 条原始 Issue 一字不差的逐条外部全文审阅。代表性 Issue 已独立核对。不能以本报告证明未抽样的 200 条来源全部真实有效。

## 2. 确认修复、应当保留的成果

| 部分 | 当前实际观测 | 结论 |
|---|---|---|
| ZIP、SHA、数据库 | ZIP CRC 正常；`PRAGMA integrity_check=ok`；无外键错误 | PASS |
| 来源判决 | `source_items=218`；VERIFIED=200，REJECTED=18；状态与判决相符 | PASS（内部一致性） |
| 证据链接 | 369 条；VERIFIED=356，REJECTED=13；不再把 REJECTED 当作被采纳证据 | PASS（内部一致性） |
| 竞品记录 | 34 条、每个 17 个旧主题候选各两条；均保留 URL、能力和差距描述 | 记录齐全，论证有效性另见 P1 |
| PRD 数据状态 | 5 个 QUALIFIED，12 个 SUPERSEDED；文件路径有效 | PASS |
| 执行日志 | `run_events` 80 行 | PASS |
| CLI 评分与 R05 | `score` 确实更新 221 个 pain；排名文件重新运行前后 SHA 相同；R05 选出 5 个、拒绝 216 个，fingerprint `3463d495...6ed6b8` | PASS（代码确定性，不等于方法有效性） |
| 归档 | 17 份旧 PRD 与旧演示 MVP 被移入 superseded | PASS |

这比原版显著进步，尤其消除了上轮的空竞品表、默认全 FETCHED、PRD 路径失效和评分 CLI 空操作。

## 3. 实际测试结果

- `PYTHONPATH=src pytest -q --ignore=mvps/r1_a/tests --ignore=mvps/r1_b/tests --ignore=tests/test_r07_fixes.py --ignore=mvps/superseded`：**72 passed**。
- `PYTHONPATH=src pytest -q --ignore=mvps/r1_a/tests/test_app_r1a.py --ignore=mvps/r1_b/tests/test_app_r1b.py --ignore=tests/test_r07_fixes.py`：**141 passed, 1 failed**。
- `PYTHONPATH=src pytest -q --ignore=mvps/r1_a/tests/test_app_r1a.py --ignore=mvps/r1_b/tests/test_app_r1b.py -k 'not test_signal_power_does_not_use_removed_trapz'`：**147 passed, 1 deselected**。
- 普通 `PYTHONPATH=src pytest -q`：在测试收集阶段因缺少 `streamlit` 报两个 `ModuleNotFoundError`；这是本验收环境依赖缺失，不是项目已被证实在 Muse 环境中无法运行。
- 错误测试 `mvps/r1_b/tests/test_signalcheck.py::test_signal_power_does_not_use_removed_trapz`：在 **NumPy 2.3.5** 中 `np.trapz` 仍存在；测试错误地强制断言它不存在，尽管被测生产代码已经使用 `np.trapezoid`。它是可复现的跨版本测试缺陷。
- 新建五个独立对抗性测试（`Demand_Radar_REWORK2_Regression_Tests.py`）：**5/5 失败**，具体见下文及随附原始 pytest 输出。这些测试针对真正的漏检而非重复既有 happy path。

## 4. 阻断项 — P0

### P0-01：RSA 验证器在数学上错误，能让任意大错误值通过

位置：`mvps/r1_b/signalcheck.py` 的 `check_rsa()`。

代码 `rel = abs(reported_rsa - expected) / expected` 错把可能为负的期望值放在分母。对于 `expected<0`，相对误差变成负数，随后满足 `rel<=0.05`。同时 `reported_rsa>=0` 的硬性门槛把本身正确的负结果判错。

构造测试：`period_ms=[1000+0.1*sin(2*pi*i/16) for i in range(64)]`。内部 `rsa_from_period()` 返回 **-6.321501084325317**。验证器对 `reported=-6.3215` 返回 FAIL，对 `reported=1_000_000` 返回 PASS（已在当前环境直接执行确认）。本缺陷使“数值验证”这一 MVP 核心承诺失效。

**必须修复**：取消“RSA 一定非负”前提；以明确的绝对/相对容差检验 `abs(reported-expected)`，相对误差分母使用 `max(abs(expected), epsilon)` 并妥善处理近零和非有限值。对负数、零、正数、极大误差及非有限值测试。

### P0-02：主题级证据并非同一项待解决需求，入选门槛缺乏真实支撑

位置：`reports/prds/PRD_4bb734fac7245033d327_r1.md`、`PRD_0b7adcf63ec0f2075fab_r1.md`、`src/demand_radar/selection.py`。

- BIO“正确处理生理信号”主题计为 **19 条/3 个组织/15 位作者**，但其中包括 [NeuroKit #1176](https://github.com/neuropsychology/NeuroKit/issues/1176) 的 GitHub Actions 文档部署、NeuroKit #1160 的 pip/conda 包版本差异、#1236 的 setuptools 版本约束。这些不能直接证明生理信号算法的错误结果。其可运行 MVP 的六个样例几乎全部来自 NeuroKit 本身。
- FIN“金融研究工具”主题把 [EdgarTools #1848](https://github.com/dgunning/edgartools/issues/1848)（13F 头寸对齐）、[OpenBB #7744](https://github.com/openbq-org/OpenBB/issues/7744)（图表渲染接口 RFC）和 [yfinance #3011/#3012](https://github.com/ranaroussi/yfinance/issues/3012)（底层解码依赖安全问题，同一报告二次提交）包装成一个“同一需求”，但三者的输入、用户任务、失败机制和可验收产品根本不同。
- AI 主题包含 AgentLab 的 Google CAPTCHA、Docker 部署、基准结果复现、LangChain 的压缩功能提案，与 API token 计数错误/streaming completed event 归入同一宽泛“可靠性”主题。这些来源并不相互证实同一可交付问题。

**必须修复**：先定义 `problem_signature = actor + input_artifact + operation + observable_failure + expected_output`，只有同一细粒度问题才能计入独立证据/组织数。相邻 issue 可以作为背景，但不能提高 PRD 过门槛的分值。重算资格并允许最终符合条件的 PRD/MVP **少于 5/2，甚至为 0**，不得为保留数量重新放松门槛。

## 5. 重要问题 — P1

### P1-01：评分存在“无证据给分”，5 个 PRD 全部刚好达到 70

`src/demand_radar/score.py`：5 个过门槛主题的得分构成完全相同：`E=20, S=20, F=15, G=10, L=5`。其中 5 个主题的 `current_workaround` 都只是字面值 **`see linked issues`**，但新 PRD 明确写着 **“No workaround is documented in the record.”**。因此 F=15 的依据与正式 PRD 自相矛盾。L=5 的理由明说“没有复用证据”仍给分。S=20 则来自模型归纳的宽泛 blocker 是否含 `wrong`/`crash`，不是真实损失衡量。G=10 基于两条竞品记录全都 `does_solve=0`，不少记录只是核实产品首页或把出问题的产品本身当成竞品，不是针对同一复现样例的功能测试。

将未经证实的 F 与 L 只作为“未知/未评分”而不是肯定价值时，五项均会由 70 降至 **50**（保留其余原有项目的假定得分，仅作敏感性演示，并非新的正式评分）。这表明“5 个 QUALIFIED”的结论对默认加分高度敏感，不能用于产品选型批准。

### P1-02：API JSON 类型验证把布尔值当成合法整数

位置：`mvps/r1_a/validator.py::_validate_payload()`。使用 `isinstance(value, int)` 会让 `True` 满足 `int`。直接复现：要求 `{'n':'int'}`，实际 `{'n':True}` 时程序返回 `('ok', True, ...)`。应当明确区分 bool 与 int，测试 `True/False`、整数、字符串与浮点数。

### P1-03：多并发 function_call 的 completed 结果丢失却判定通过

位置：`mvps/r1_a/validator.py::StreamingHandler` 与 `validate_stream()`。单个 `_pending` 缓冲区会被第二个 function_call 覆盖。给两个 added + 两个 done，实际只完成第二个；验证器仍认为“1 个完成事件=通过”。应按 `item_id`/`output_index` 等真实事件关联键分别跟踪完成项，每个已结束调用必须各有一次 completed，丢失/重复/错配都失败。

### P1-04：呼吸相位结果数组长度不匹配仍被接受

位置：`mvps/r1_b/signalcheck.py::check_rsp_phase()`。`zip(reported_durations,expected)` 截断额外输出；输入两个区间、上报三个时长 `[1,1,999]` 时程序错误返回 PASS。应在逐项比较前验证长度完全相等、采样率和输入有限且有效。

### P1-05：最终用户可见报告仍是旧版，版本状态不一致

- `reports/final_report.md` 写 207 VERIFIED/11 REJECTED、17 PRD、两个 80 分 MVP、40 passed、旧 demo 路径。
- `progress/STATUS.md` 对外仍记录旧 P10 和原 ZIP，没有指向 REWORK1 作为当前版本。
- 新 SQLite 实际是 200 VERIFIED/18 REJECTED、5 QUALIFIED PRD、2 个新的 validator 型 MVP，文件中没有一个无歧义且一致的当前“最终报告”。
- `reports/mvp_selection.json` 中的 `selected` 数量是 **5**（PRD-eligible pool），但真正构建 MVP 是 **2**；字段名称对下游消费者存在歧义。

应保留旧记录但移入 `reports/superseded/` 或标注历史版；重建当前唯一 `final_report_rework1.md`，区分 `prd_qualified` 和 `mvp_built`，README 直接指向新版。

### P1-06：新 MVP 的外部有效性仍未证实

R1-A 的 tokenizer 是自己写的近似计数器，并且 `count_tokens_for_model()` 故意忽略传入 `model`；`SimulatedTransport` 的错误响应由事先注入 `fault` 或 `factual=False` 标志告知验证器，它不能据此证明能检测真实 API 的事实错误。R1-B 使用合成信号与手工模拟的错误路径，并没有对上游 NeuroKit 方法或真实记录执行同一套断言。双方 README 承认局限，因此可以作为**教学/仿真原型**，但不能作为“在真实系统上通过验收的问题解决产品”。要验收 MVP，需至少加入无外部写入的真实录制载荷/公开数据与目标库调用对照，或明确将交付目标降为 `SIMULATION_PROTOTYPE`、不宣称解决上游 bug。

## 6. P2 与残余风险

- `review_r02_raw_github.json`（约 20MB）按说明被省略，ZIP 中只有哈希及裁剪后的审核记录。理由与路径已披露，但仅凭 ZIP 无法离线完整重建 218 个 body 的审阅全过程；若要求强可复现研究，应附压缩原文或关键摘录的内容哈希及定量回放样本。
- NumPy 的 `np.trapz` 是否仍存在是外部库版本行为，不是本项目正确性的判据。移除依赖该属性的断言，直接验证本项目使用 `np.trapezoid` 且数值计算正确。
- 当前系统无法离线安装 Streamlit/Ruff，UI 视觉、交互、完整 154 项测试和 lint 的本机复核仍 **NOT_TESTED**；Muse 提供的日志不是独立验证。
- 数据中 102 条 GitHub issue 标记 CLOSED；关闭不等于修复，但也不能把其当作当前未满足的需求。应按 `closed_reason`、目标版本和复现状态分别标记“历史痛点/仍有效/未知”。

## 7. 本次 R01–R07 逐项再裁定

| 阶段 | 二次结论 | 证据 |
|---|---|---|
| R01 工程安装、CLI | 基本通过，有依赖矩阵待复测 | CLI 确实重算且确定性；默认导出正确 |
| R02 来源审核 | 条目/状态记录通过，语义校验不充分 | 200/18 内部自洽，但来源与 *同一个痛点* 的关联错误 |
| R03 独立性计数 | 算法修复通过，分组粒度未通过 | 3 org 不等于 3 个相同需求的证据 |
| R04 竞品记录 | 记录完整、实证结论不足 | 34 行但“does_solve=0”缺任务级验证 |
| R05 PRD / Gate | **不通过** | 所有 70 分均依赖未证实的 F/L 等加分；PRD 粒度失真 |
| R06 两个 MVP | **不通过** | RSA 数值假阳性/假阴性；API 丢调用与类型校验错误 |
| R07 最终 QA | **不通过** | 存在五个新对抗性失败测试 + NumPy 跨版本断言错误；终报陈旧 |

## 8. 建议验收门槛

1. 随附五项失败回归测试必须全部转绿，并另外加入随机/边界数值测试；不能通过删除测试或特例硬编码让它们通过。
2. RSA 正确值（可正、可负）通过；量级错误必须失败。至少另一个独立数学实现交叉检验；容差要说明实际统计意义。
3. 同一细粒度痛点才可进行跨组织计数；重算 PRD、竞品和 MVP 资格。缺证据允许停止，不允许保留恰好 70 的虚假合格者。
4. API/信号 MVP 至少一条真实读取或回放路径；否则正式降级为模拟原型，而不是“已解决真实问题”。
5. 修复 NumPy 跨版本测试；至少在 Muse 可用的两套 NumPy/ Python 组合中运行完整测试，留环境锁与退出码。
6. 旧最终报告明确归档，生成一份与 DB 和新版代码一致的唯一最终交付报告；清楚说明 5 个 PRD-eligible 与 2 个已构建候选的区别。
7. 未验证事项必须列为 `NOT_TESTED`，不能以自证日志代替独立验收。

**结论：** 本轮应认可其完成的工程改进，但仍判 **REWORK2_REQUIRED / NOT_ADOPTED**。现在的关键不是再增加爬取量或测试数量，而是提升核心数值计算、任务语义与外部验证的可靠性。
