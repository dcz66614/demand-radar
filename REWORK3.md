# 直接交给 Muse：Demand Radar REWORK3（定点修复，冻结任务）

## 目标

这不是新项目、不是重新大规模研究。REWORK2 已修好旧五项回归，最终合格 PRD 为 0，这个事实应保留。任务是修正刚发现的**错误 PASS**，完成开箱可复现的交付，保持历史数据和 70 分门槛。仅需修改与缺陷直接相关的最少文件。

**先读：** `Demand_Radar_REWORK2_Independent_Audit_2026-11-06.md`、`Demand_Radar_REWORK2_Independent_Regression_Tests.py`、`Demand_Radar_REWORK2_Independent_RED.log`，以及现有 REWORK2 源码/报告。

## R3-00：固定基线

1. 从 REWORK2 ZIP 提取一个全新、隔离的 rework3 目录；保留原 ZIP、不覆盖原数据库和历史报告。
2. 运行原始五项回归，必须 5/5 GREEN。
3. 把新的四项测试拷贝到 `tests/test_independent_r2.py`，先运行确认 RED，并留存未经修改的红灯日志。
4. 记录源码文件哈希、Python/依赖版本、是否能运行 Streamlit/NeuroKit/WFDB，不能把 SKIP 写成 PASS。

## R3-01：修复真正的多函数调用参数关联（P1，最高优先级）

**文件：** `mvps/r1_a/validator.py`。

- 以 `response.output_item.added` 的 `item.id` 作为 canonical identity；为每条新增调用建立 `item_id`、`call_id`、`output_index` 的唯一映射，避免不同字段/不同命名空间的字符串碰撞。
- `response.function_call_arguments.delta` 同时有 `item_id` 和 `output_index` 时，必须解析成同一个已存在的 item，不能先拿字符串 `"0"` 当 canonical key。
- 多个调用的 delta 可交错；逐条追加到相应调用；对重复 sequence、key 冲突和未知 item_id 做出明确失败/未知标记，不能静默投给上一个调用。
- `response.output_item.done` 中有最终 `item.arguments` 时，用它与累积参数交叉验证，并明确最终合法 JSON/空参数的语义。保留真正无参数调用的合法情形。
- `validate_stream` 必须检查**完成数 + 正确关联 + 参数完整性**，而非只比较完成事件计数。出错为 `wrong-result` / `not-checked`，不得 `ok`。
- 新四项测试中的 `test_parallel_stream_preserves_each_arguments_payload` 以及原有 streaming 测试全绿；另外增加：交错三调用、duplicate done、delta 重复、无 done、done 先到、同 index 冲突等契约测试。

**真实协议参考：** `https://github.com/openai/openai-python/blob/main/src/openai/types/responses/response_function_call_arguments_delta_event.py`，`https://github.com/openai/openai-python/blob/main/src/openai/lib/streaming/responses/_responses.py`。禁止猜事件字段格式。

## R3-02：修复内容真值校验的错误 PASS（P1）

**文件：** `mvps/r1_a/validator.py`。

- 将 `expected_answer` 与 `expected_keywords` 的检查定义分开。如果只提供 `expected_answer`，必须实际比较，或者报告 `NOT_CHECKED/UNKNOWN`，不能继续自动 `ok`。
- 明确文本是否要求 exact match / normalized exact match；一般自然语言语义与逻辑否定不能靠子串包含判为“事实正确”。
- `"Paris is NOT the capital"` 命中关键词 `paris` 不应被宣传为“已证实事实正确”。若能力不足，诚实地只声明“关键字规则通过、事实真值未检查”。
- 测试已知正确、相反答案、拒答、带否定句、关键词缺失、只有 expected_answer、只有 forbidden_claims、没有规则等情形。

## R3-03：Schema 输入 fail-closed（P2）

- `int` / `integer` 的含义必须明确，不能因为用户写了不认识的 schema 类型就无条件 PASS。
- 对未支持的 schema spec，返回可读配置错误/UNKNOWN；如果支持 JSON Schema 标准类型，要用明确契约并补测试。
- 不接受 `float('nan')`、正负无穷等非有限 JSON 数字；bool 不得满足 number/integer。
- 检查嵌套数组/对象中的同类错误，不能只修顶层。

## R3-04：让 ZIP 按 README 一键安装（P1）

- 二选一：ZIP 内统一加入 `demand-radar-rework3/` 顶层目录；或 README 先 `mkdir`、`cd` 到新目录，再解压 `../...zip`。
- **必须真正从一个空的临时目录**复制 ZIP，原样执行 README 的每条命令并记录退出码；若有依赖网络/包版本限制，逐项标明，不允许假装执行过。
- 重新生成完整源文件哈希清单，并验证 ZIP CRC、文件完整性、SQLite integrity。

## R3-05：保持研究结论正确及独立验收

- 不扩大数据量，不增造 PRD，不降 70 分门槛、不更改旧来源或评分以保住两套 MVP。
- 新总报告仍应明确 `0 qualifying PRDs` 和 `2 partially real-world validated prototypes`（除非新的真实证据使它们发生可审计的改变；本次明确禁止新增外部数据）。
- 更新 MVP A 功能声明，区分 `stream event count`、`function argument integrity` 和 `factual truth` 三种完全不同的能力。
- 固定旧 5 + 新 4 共 9 项的基线回归；跑完整 suite 和 Streamlit AppTest（可执行则执行；不可执行如实 SKIP/BLOCK）。
- 交付：新 ZIP、`reports/rework3/` 中的 RED/GREEN 日志、修复 diff、独立验证结果、SHA 清单、当前唯一 final_report/STATUS。

## 停机与验收

如修不了任何一项 P1，不得自称 ACCEPTED；直接交付 `BLOCKED` 的具体证据。成功标记必须来源于真实可复现输出。不得靠修改独立回归测试中的预期来“修复”。不能对用户账户、金融账户、医学诊断、付费服务或现有 GitHub 仓库执行写操作。
