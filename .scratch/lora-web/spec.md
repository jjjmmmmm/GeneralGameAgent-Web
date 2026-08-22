# LoRA 微调 + 可视化前端（GeneralGameAgent-Web）

**Status:** ready-for-agent
**Source:** 立项书.md + 总计划.md + 2026-08-21 对话决策

---

## Problem Statement

课程课题七完成了 NitroGen 模型的离线评测体系，但 **M4 摇杆相关系数不达标**（baseline -0.1，要求 ≥0.4），归因是无条件 zero-shot 模型能力上限（无 game conditioning）。现在需要两条路同时走：

1. **训练侧**：NitroGen 官方仓库无训练代码，微调 500M DiT（flow matching）是最大不确定项——8G 显存是否装得下、训练循环是否写得对、loss 是否收敛，全未知。必须先花半天验证"能不能训"，不能等前端做完才碰。
2. **展示侧**：需要一个 Web 前端把评测结果展示出来。但若前端 v1 只按"只有零样本结果"设计，微调完数据结构变了（多一套指标），组件全要重写。

## Solution

- **LoRA 微调** `ng.pt` 适配 rocket_league：行为克隆 + flow matching loss，统计集训练、测试集隔离，把 M4 摇杆相关从 -0.1 拉到 ≥0.4。
- **API 从第一天多版本化**：结果集版本（`baseline` / `ft`）作为一等字段，v1 只有 baseline 也能跑，v2 加一个选择器/对比视图即可，数据格式不变、组件复用——"补一遍前端"变成"加一个视图"。
- **前端 v2** 展示微调前后对比（指标并排 + 曲线叠加）。

## User Stories

1. 作为研究员，我希望能先跑通 1 个训练 step（loss 可算且下降、显存 <8G），以便在投入正式训练前确认微调可行性（阶段 0）。
2. 作为研究员，我想要一份训练接口理解记录（forward / get_action / 动作编码器语义），以便自研训练循环有依据。
3. 作为研究员，我希望数据管线能按 `帧号 = chunk_id × 1200 + 行号` 对齐抽帧与标注，以便喂给模型的是正确输入-输出对。
4. 作为研究员，我希望抽帧能缓存、同段不重抽，以便训练/评测数据管线不重复 IO。
5. 作为研究员，我希望用 LoRA（冻结视觉编码器+主干，只训 attention 低秩旁路）微调，以便在 8G 显存内跑 500M DiT。
6. 作为研究员，我希望训练循环使用 flow matching loss（MSE 速度场）+ AdamW + 梯度累积，以便模型真正学到 rocket_league 的控制行为。
7. 作为研究员，我希望训练能保存 ft 权重，以便后续评测和展示复用。
8. 作为研究员，我希望在隔离的测试集（3600 帧）上评测 ft vs baseline，以便结论不掺训练数据。
9. 作为研究员，我希望评测复用课程口径（按键准确率/触发召回率/F1/摇杆相关），以便与课程结果可比。
10. 作为研究员，我希望 ft 结果能写 JSON 入库（metrics/segments），以便前端展示。
11. 作为研究员，若训练不收敛/指标不达标，我希望如实呈现 ft 与 baseline 对比（不修饰），以便结论可信。
12. 作为访问者，我希望 API 能列出所有结果集版本（`/api/results` → baseline, ft），以便知道有什么可看。
13. 作为访问者，我希望 `/api/metrics?version=baseline|ft` 返回指定版本的四指标，以便指标卡展示。
14. 作为访问者，我希望 `/api/segments?version=baseline|ft` 返回曲线段数据，以便查看器画曲线。
15. 作为访问者，我希望 `/api/figures/<name>` 返回静态图，以便展示差异帧/分布图。
16. 作为前端用户，我希望仪表盘显示 baseline 的 M4 四指标卡片+达标判定，以便一眼看到现状。
17. 作为前端用户，我希望查看器能看 21 段曲线（缩放/筛选/差异帧标注），以便深入分析。
18. 作为前端用户，我希望 v2 能切换 baseline/ft，指标卡更新为对应版本数值，以便对比。
19. 作为前端用户，我希望 v2 曲线能叠加显示 gt / baseline pred / ft pred，以便直观看到微调带来的差异。
20. 作为开发者，我希望 API 的 version 字段从 v1 就存在，以便 v2 只加视图、不动数据格式（防返工）。
21. 作为开发者，我希望阶段 0 与阶段 1 并行推进，以便微调可行性结论与前端 v1 同时拿到。
22. 作为开发者，我希望指标计算逻辑抽公共库，以便后端与评测共用同一口径。

## Implementation Decisions

- **训练方案**：LoRA 微调，优先尝试 `peft`（若适配自定义模型），否则手写 attention 低秩旁路（~100 行）。冻结视觉编码器与主干，batch=1 + 梯度累积（防 OOM），必要时 fp16。
- **训练目标**：flow matching loss = MSE 速度场（对齐 NitroGen forward 语义）；优化器 AdamW + 学习率调度。
- **数据管线**：抽帧缓存（同段不重抽，`data/` 目录，不入仓）；对齐规则 `帧号 = chunk_id × 1200 + 行号`，视频秒 = 帧号/60。
- **评测口径**：指标计算抽公共库（`metrics_lib`），与课程 `scripts/evaluate.py` 共享口径——按键准确率（去 0==0 虚高）、触发召回率、F1、摇杆相关系数；随机性用 K=3 多数票（flow matching 采样非确定）。
- **API 契约**（v1 就多版本化）：
  - `GET /api/results` → 结果集列表 `["baseline", "ft"]`
  - `GET /api/metrics?version=baseline|ft` → 四指标 JSON
  - `GET /api/segments?version=baseline|ft` → 曲线段数据
  - `GET /api/figures/<name>` → 静态图
- **数据来源**：baseline 从课程 `results/`（test_set_metrics.md / 21 段 top5 / m5 对比表）转结构化 JSON 入库；ft 由训练评测产生。
- **领域词汇**：M4（摇杆相关达标项）、baseline（零样本）/ ft（微调后）、结果集版本、触发召回率、摇杆相关系数。
- **不做**（延续立项书）：全参微调、其他游戏泛化、实时游戏接入、从零训练、修改 NitroGen、真机手柄。

## Testing Decisions

测试只断言外部行为，不测实现细节。seams（从高到低）：

- **S1 训练循环**（最高 seam）：`train_step` 跑 1 步，断言 loss 为有限值且比起点下降；显存 `torch.cuda.max_memory_allocated()` <8G。这是 M0 验收。
- **S2 metrics_lib**：四指标纯函数，用课程已知结果做回归断言（数值与 `test_set_metrics.md` 一致），保证口径复用正确。
- **S3 数据管线**：抽帧/对齐为纯函数，断言给定 chunk 行号能得到正确帧号与标注键（含 j_left/j_right 范围、17 键 schema）。
- **S4 FastAPI 端点**：用 TestClient 请求 `/api/metrics?version=baseline`，断言 JSON 结构 + 版本字段生效；`/api/results` 返回版本列表。
- **前端不测**：ECharts 渲染层测试价值低；数据正确性由 S2/S4 保证，前端靠可复现 JSON。

## Out of Scope

- 前端 v1 只展示 baseline（ft 视图留 v2）。
- 正式训练的超参调优穷举（只允许按 R3 重试一次）。
- 批量推理加速（3.5，时间够才做）。
- 报告/演示文档（延伸项目同理：用户没叫写就不写）。

## Further Notes

- 依赖链：阶段0 →(可行性)→ 阶段2；阶段1 →(前端基础)→ 阶段3；阶段2 →(ft 数据)→ 阶段3。**阶段 0 与阶段 1 可并行**。
- 里程碑：M0=spike 通过（0.5~1天）；M1=后端+前端v1（2~3天）；M2=ft 权重+评测达标（1~2天）；M3=前端v2+收尾（1~2天）。
- 风险 R1（读不懂 forward 语义）/ R2（OOM）：阶段 0 验证；R3（不收敛）：调一次重试，仍不达标如实呈现。
- 前端实现开始前需等待用户提供新 skill（用户已声明）。
