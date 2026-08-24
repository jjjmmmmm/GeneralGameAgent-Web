# 摇杆加权 loss 重训 ft（GeneralGameAgent-Web）

**Status:** ready-for-agent
**Source:** 2026-08-24 对话 + 诊断结论 + `docs/计划-摇杆加权重训.md`

---

## Problem Statement

M4 摇杆相关系数仍未达标（旧 ft +0.126 < 0.4，唯一未达标指标）。用 `train/diagnose_train_set.py` 诊断发现：ft 在**训练集**（模型见过的帧）上摇杆相关也仅 +0.042，与测试集同量级 → 模型**没学会**"画面→摇杆"映射，而非泛化差。根因 = flow matching loss 对 25 维等权，摇杆只占 4/25=16%，梯度被按钮主导。扩数据（A 方案）对摇杆无效（连见过的帧都学不会），已放弃。

## Solution

给摇杆 4 维在 loss 里放大权重，让梯度不被按钮淹没，重训 ft 冲击 ≥0.4。加权手段利用现有 forward 语义：loss 内的 `mask` 直接来自数据可控的 `actions_mask`，且归一化分母为 `mask.sum()`——把 `actions_mask` 从全 1 换成 float 权重矩阵（21 按钮 = 1，4 摇杆 = w）即可实现梯度加权，**不改 NitroGen 源码、不 monkey-patch**。

## User Stories

1. 作为研究员，我希望训练 loss 能对摇杆维度放大权重，以便解决"摇杆被按钮主导而学不会"的根因。
2. 作为研究员，我希望加权通过训练数据可控的 `actions_mask` 实现，以便不改 NitroGen 源码。
3. 作为研究员，我希望 `--j_weight` 默认 1（等权），以便默认行为与旧训练完全一致。
4. 作为研究员，我希望用几百步快速验证（复用诊断脚本）即可判断加权是否让训练集摇杆相关抬头，以便低投入决定是否值得正式训练。
5. 作为研究员，我希望选定权重后正式训练并保存新 ft 权重，以便评测与展示。
6. 作为研究员，我希望测试集评测对比 baseline / 旧 ft / 新 ft 全指标，以便如实判断是否达标。
7. 作为研究员，我希望按键准确率不因加权显著回退（≥88%），以便不牺牲已达标指标。
8. 作为研究员，若加权后仍不达标，我希望如实记录并归档，以便结论可信（延续 R3 预案）。

## Implementation Decisions

- **加权机制**：在训练数据构造时，将 `actions_mask`（tokenizer.encode 输出、forward 内 mask 的来源）替换为 float 权重张量 `(1,18,25)`：21 个按钮列 = 1，4 个摇杆列（layout 21~24，即 j_left 2 + j_right 2）= `w`。forward 内 `raw_loss * mask` 与 `mask.sum()` 归一化天然按 `w_j / Σw` 加权梯度。
- **参数**：`train_lora.py` 新增 `--j_weight`（默认 1 = 等权，不影响旧行为）。
- **权重范围**：从 `w=4` 起，快速验证对比 `w=4` 与 `w=8`，监控按键准确率与训练集摇杆相关。
- **验证口径**：训练集诊断复用 `train/diagnose_train_set.py`（chunk 0000~0031，200 帧，K=3）；测试集评测复用 `train/evaluate_ft.py`（chunk 0032~0034，200 帧，K=3，与既有结果可比）。
- **训练配置**：沿用 r8 / lr 1e-4 / 1500 步（快速验证 400 步），梯度累积与 8G 显存约束不变。

## Testing Decisions

- **S1（最高 seam）端到端**：重训后跑 `diagnose_train_set.py`，断言训练集摇杆相关较旧 ft(+0.042) 明显抬头（>0.1 即有效信号，"学会了"）。这是"加权生效"的外部可观察行为，不测 loss 数值内部细节。
- **S2 测试集**：`evaluate_ft.py` 对比，断言新 ft 摇杆相关 ≥ 旧 ft(+0.126)（目标 ≥0.4）、按键准确率 ≥88%、召回率不显著回退。
- **不做单元测试**：loss 加权是数值实现细节，由 S1 端到端覆盖；现有测试体系（metrics_lib 回归等）不受影响。

## Out of Scope

- 扩数据（A 方案，已诊断放弃；仅按键泛化有边际价值，备用文档保留）。
- 修改 NitroGen 源码 / monkey-patch。
- 前端改动（除非达标后更新对比数据，另行排期）。
- 超参穷举（只允许 `w` 快速验证 2~3 档 + 正式训练一次）。

## Further Notes

- 诊断结论：`train/diagnose_train_set.py` + 日志 `train/diagnose.log`；计划详见 `docs/计划-摇杆加权重训.md`。
- 相关坑：训练/评测需 `HF_HUB_OFFLINE=1`；托管后台进程用 `cmd /c` 包装 + `python -u` 实时日志。
