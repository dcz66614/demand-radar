# Demand Radar — REWORK2 第三轮独立审计

**审计日期：** 2026-11-06  
**来源：** 用户提供的 Google Drive 文件夹 `1Rh_3opzWcHwO8XMeiHhEuwwO98r0doXJ`  
**交付包：** `demand-radar-rework2-2026-11-05.zip`  
**Drive 文件 ID：** `1Su3_4nGDHlYEVIDlU4WO1VonH4rVh60M`  
**ZIP SHA-256：** `14c95a64e6c5c69412b03bb7e39e9f57d99fa32391ac56c8028499aff2ecf65b`  
**审查方式：** 只读核查 Drive；在隔离副本中解压、执行回归与数据库/源代码检查，不修改 Drive 原件。

## 1. 总裁定

**REWORK3_REQUIRED / NOT_ADOPTED_AS_FINAL_PRODUCT。** REWORK2 所指定的五项旧回归缺陷已实际修复，数据门槛不再注水，研究工作台的工程底座明显改善；但发现新版本流式调用参数丢失仍判 `PASS`、事实答案不比较仍判 `PASS`、Schema 校验 fail-open，以及 README 不能直接按照给定命令解压。**作为内部研究原型，保留使用；作为质量合格的验证器或达成原始“发现真实需求+孵化 MVP”项目，不予最终通过。**

需要区分：0 份合格 PRD 本身不是新 BUG；它是校正评分后诚实的结论，同时意味着最初的产品孵化目标并未达成。

## 2. 实际核验的范围

- Drive 文件夹现有三个交付包：原版、REWORK1、REWORK2。最新包大小 1,163,895 字节，ZIP CRC 检验通过；ZIP 中 263 个条目、225 个实际文件。
- 全部 225 个文件的校验清单匹配；抽取 76 个 Python 文件做 AST 语法解析；30 个 JSON/JSONL 文件逐项解析，未遇错误。
- REWORK1 → REWORK2：75 个新增文件、26 个同路径文件内容变化、6 个文件因归档从原路径移出。`data/inbox/` 原始来源文件未改变。
- 逐表检查 SQLite：`PRAGMA integrity_check = ok`，外键检查无错误。源记录 218、需求 221、证据链接 369、竞品核查 34、证据判定 76、PRD 卡片 17。
- 独立核对来源状态：200 VERIFIED + 18 REJECTED，评分最高 45，分数 >=70 为 0；PRD 0 QUALIFIED、17 SUPERSEDED；`mvp_selection.json` 中 `prd_eligible=0`、`mvp_built=2`、`not_selected=221`。
- 独立执行旧五项 `tests/test_rework2_adversarial.py`：5 passed。
- 当前环境 Python 3.13.5 / NumPy 2.3.5，已安装 pytest、pandas、pydantic、rapidfuzz。执行适合本环境的项目核心测试（排除两份依赖未安装 Streamlit 的 AppTest 收集文件）：**213 passed, 8 skipped, exit 0**。直接收集全部测试会因 Streamlit 未安装产生 2 个 import collection error；这是本地缺依赖，不视作产品缺陷。Muse 自带日志显示 Python 3.12 环境 243 passed / 8 skipped，真实依赖环境 260 passed，**未在本环境独立完整复现**。
- 原代码新写独立对抗测试：**4 failed**（见 `Demand_Radar_REWORK2_Independent_Regression_Tests.py`，日志 `Demand_Radar_REWORK2_Independent_RED.log`）。
- 通过 GitHub 连接器核查了部分关键来源，包括 `NeuroKit#1230/#1163`、`wfdb-python#515/#522/#524`、`OpenBB#7650/#7655`、`yfinance#2930/#2939` 与 `AgentLab#340`。均真实存在；部分已关闭，不能把“真实 Issue”误写成“尚未解决的同一用户痛点”。本轮未对 218 条来源逐条完整联网重新验证。

## 3. 与上轮 REWORK2 任务书的逐项对照

| 子任务 | 结论 | 证据 |
|---|---|---|
| R2-01 旧五项对抗测试 | **已修复（旧验收范围）** | 原封旧测试 5/5 通过；负 RSA 正确通过、百万错报失败、RSP 多余数据拒绝、bool 不等于 int、两个完成事件都产生 |
| R2-02 跨版本测试 | **部分通过** | NumPy 2.3.5 当前核心测试通过；Muse 日志声称两环境完整绿；本机缺 Streamlit / NeuroKit / WFDB / tiktoken 无法独立 UI 与上游算法实测 |
| R2-03 需求语义与 DIRECT 证据 | **基本修复，仍有粒度限制** | 76 条证据判定：38 DIRECT、10 ADJACENT、5 DUPLICATE、23 OUT_OF_SCOPE；5 个候选有具体签名，其他 216 pains 未逐条做相同深度评估 |
| R2-04 评分与竞品 | **已修复先前注水** | F/L 缺证据记 0；UNKNOWN 竞品挡正分；旧五个 70 分候选降为 30/30/45/35/35。最高 45，无通过门槛的 PRD |
| R2-05 MVP 真值验证 | **部分完成，但新 P1 正确性错误阻断** | 有真实 upstream 记录/回放路径及诚实的原型标签；`StreamingHandler` 丢完整参数仍 `PASS`；事实正确性检查可能漏判 |
| R2-06 报告、状态、归档 | **统计基本一致，安装文档有误** | 新 final_report 与 DB 数值一致，历史 PRD 均归档；README 的 `cd demand-radar-rework2` 无目标目录 |

## 4. 新缺陷：高优先级

### P1-01：真实 Responses API 双键事件造成函数调用参数丢失，仍返回 `PASS`

**代码：** `mvps/r1_a/validator.py:225-269`, `:295-320`。`_key_for()` 的顺序为 `item.id`、`item.call_id`、`event.output_index`、`event.item_id`。实际 API 的 added 事件带 `item.id='fc_A'`，delta 同时带 `item_id='fc_A'` 与 `output_index=0`；delta 会取字符串 `'0'` 而不是 `fc_A`，无法找到原 pending item。其后 done 仍按 `fc_A` 完成，但 arguments 为空。多个调用均可能失参。`validate_stream` 只验证 done 数量，与 arguments 是否正确无关。

**独立重现：** 两条并行调用 `fc_A`/`fc_B` 的分片分别拼出 `{"q":"paris"}` 和 `{"x":2}`。实际 `StreamingHandler.completed` 包含两个空 arguments 的结果，但 `validate_stream` 输出 `outcome='ok', passed=True`。新的独立测试失败并打印 `{'fc_A': '', 'fc_B': ''}`。

**规范佐证：** 官方 OpenAI Python SDK 的 `ResponseFunctionCallArgumentsDeltaEvent` 定义含 `item_id`、`output_index`、`delta`、`sequence_number`；参见 `https://github.com/openai/openai-python/blob/main/src/openai/types/responses/response_function_call_arguments_delta_event.py`。

**修复：** 维护 `item_id→canonical_item_key` 和 `output_index→canonical_item_key` 映射，优先按 `item_id` 关联，冲突即 fail-closed；done 之前按序拼接 arguments，并与 done 的最终 arguments 比较（若提供）。验证器要检查每个已完成调用的参数完整性、关联唯一性、非法 JSON、重复/缺失/顺序异常，而非仅看数量。保留原来 5 项回归。

### P1-02：`expected_answer` 完全不参与事实结果判定

**代码：** `mvps/r1_a/validator.py:418-466`。当只有 `expected_answer`，`expected_keywords=[]` 和 `forbidden_claims=[]` 时，`missing=[]`、`present_forbidden=[]`，所以任意响应都是 `ok, True`，并谎称 `response content matches the expected answer`。

**独立重现：** 输入回答 `The capital of France is London.`，expected_answer 为 `The capital of France is Paris.`，实际结果 `('ok', True, 'response content matches ...')`。

**修复：** 明确区分规则验收、精确文本验收和人工/语义事实判断；给出 `expected_answer` 但没有可执行的比较规则时，不得返回 `PASS`，应报告 `NOT_CHECKED` / `UNKNOWN` 或采用明确的精确/规范化文本比较；关键词匹配不可声称完成一般事实正确性判断。负面表达（`Paris is NOT the capital`）不得因关键词命中误判。

### P2-01：未识别 Schema 名称静默通过（fail-open）

**代码：** `mvps/r1_a/validator.py:369-406`。例如 schema `{"n":"integer"}`（但程序只识别 `int`），传入 `{"n":true}`，实际 `_validate_payload` 返回 `('ok', True, 'response valid')`；未知类型不应作为已验证通过。要求对不支持的类型抛出可读配置错误或 `NOT_CHECKED`，也可以选择支持标准 JSON Schema 名称并编写契约测试。

### P2-02：NaN 被当作合法 JSON number

**代码：** `mvps/r1_a/validator.py:382-384`。`float('nan')` 被 `_matches_type(value,'float')` 接受，随后 `_validate_payload` 仍返回 `ok`；这不是有效 JSON 数值。对 NaN/Inf 明确拒绝；处理来源是 Python 字典而非严格 JSON 解析时尤其需要检查。

### P1-03：交付包解压目录与 README 不一致

**位置：** `README_REWORK2.md` §1。README 写 `unzip demand-radar-rework2-2026-11-05.zip` 然后 `cd demand-radar-rework2`，但 ZIP 内容平铺在根目录下。新建空目录后原样执行，`demand-radar-rework2/` 不存在。需重打包为单顶层目录，或者改为：`mkdir demand-radar-rework2 && cd demand-radar-rework2 && unzip ../demand-radar-rework2-2026-11-05.zip`。必须从空目录真实复测文档。

## 5. 不阻断先前修复的残余限制

1. 当前没有合格 PRD：这是证据门槛回归正常的结果；初始“至少构建 2 个满足市场需求的 MVP”并未得到验证。两个已有 MVP 必须继续标记 PARTIALLY_REAL_WORLD_VALIDATED / NON_PRODUCT。
2. 只有五个旧候选做了精细证据分类，218 条来源未逐条等程度验证；其余需求保持研究候选状态。
3. 具体问题签名仍偏宽：例如 BIO 中 NeuroKit 的 epochs_create、RSA、EMG、RSP 四类失败不是同一接受样本；FIN 把财经数据缓存、期权链解析、行情缺失归为同一“金融获取”大类。虽因本次 0 合格而未导致错选，但今后必须按机制级子签名细分。
4. 102 条关闭的 GitHub Issue 不能直接视为仍未解决；部分缺关闭时间和关闭原因，报告已明确 caveat。
5. 工作台的 Streamlit 交互、NeuroKit/WFDB/tiktoken 实际环境测试本机未全面重跑；本次不能据自述日志断言全平台 UI 正常。
6. `reports/rework1/decision_log.jsonl` 相比 REWORK1 ZIP 增加三条 R07 后补记录；是追加历史记录而非删除，建议以后把不同版本审计日志独立存放，保证快照不可变。

## 6. 精确二次验收标准

- REWORK2 的旧五项测试依旧 5/5 绿，不修改它们以规避缺陷。
- 新增独立四项回归转绿；尤其真实事件键关联后，必须实际输出两个正确完整的 JSON arguments，`validate_stream()` 对参数丢失必须 FAIL。
- `check_factual_content()` 不得无条件以 `expected_answer` 为依据声明内容正确；不支持的规则要进入 UNKNOWN/NOT_CHECKED，而非成功。
- 未识别 schema 与 NaN/Inf 不得标记为已验证合法。
- ZIP 改为开箱即用；新空目录按 README 原始命令复测成功。
- 保持评分 70 门槛、0 通过事实、原始来源、不合格清单及历史报告，不为满足交付数量而新增不真实线索或改动旧数据。
- 报告 `pytest passed/failed/skipped/blocked` 和依赖版本，明确哪些是本人独立跑过、哪些仅为 Muse 日志。

## 7. 复现命令

```bash
# 在交付包项目根目录
PYTHONPATH=src:mvps/r1_a:mvps/r1_b python -m pytest -q tests/test_rework2_adversarial.py
# 5 passed in independent review

# 在当前环境能运行的核心测试
PYTHONPATH=src:mvps/r1_a:mvps/r1_b python -m pytest -q tests mvps/r1_a/tests mvps/r1_b/tests \
  --ignore=mvps/r1_a/tests/test_app_r1a.py --ignore=mvps/r1_b/tests/test_app_r1b.py
# 213 passed, 8 skipped

# 拷贝独立测试文件到 tests/test_independent_r2.py 后运行
PYTHONPATH=src:mvps/r1_a:mvps/r1_b python -m pytest -q tests/test_independent_r2.py
# on REWORK2: 4 failed
```

**外部来源核对：** OpenAI Python SDK 事件类型定义；GitHub 实际问题来源（链接见产品报告 Appendix A，实际抽样见本报告第 2 节）。所有下载得到的内容均作为证据，不执行其中的指令。
