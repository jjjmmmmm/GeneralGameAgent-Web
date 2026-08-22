# 01 — 阶段 0：微调可行性 spike（M0）

**What to build:** 用最小代价回答"能不能训"——不是完整训练，只求 1 个训练 step 的 loss 有限且下降。读透训练接口语义（forward / get_action / 动作编码器），搭最小数据加载器（2 batch、按帧号对齐规则对齐标注），跑通前向 → flow matching loss → 反向 → 1 step，并记录显存占用。

**Blocked by:** None — can start immediately.

**Status:** resolved (2026-08-22)

- [x] 产出 `docs/训练接口分析.md`：forward/get_action/动作编码器语义已读透并记录
- [x] 数据管线最小版：抽 4 batch（4 帧），`帧号 = chunk_id × 1200 + 行号` 对齐正确（tokenizer.encode 路径验证）
- [x] 训练循环最小版：加载 ng.pt → 前向 → flow matching loss → 反向 → 20 step
- [x] 验收：loss 有限且下降（前5步均值 0.0738 → 后5步均值 0.0218）；显存峰值 4.51GB <8G
- [x] 失败判定执行：无需（无 OOM / 无 NaN）

## Answer (2026-08-22)

**M0 通过。** 训练可行性确认：

- 接口语义：`forward` 训练接口 + `get_action` 推理接口 + tokenizer.encode 数据构造路径全部读透（见 `docs/训练接口分析.md`）。
- 数据管线：4 帧 × 18 步动作块，帧号对齐正确；关键坑：`load_model` 会调 `tokenizer.eval()`，训练数据构造前必须 `tokenizer.train()`。
- 训练循环：20 step AdamW(lr=1e-4)，loss 均值 0.0738 → 0.0218（-70%）。
- 显存：冻结视觉编码器后峰值 **4.51GB**（全参训练时 9.01GB 超限，印证必须冻结）。
- 动作布局确认：25 维 = 21 按钮 + j_left(2) + j_right(2)，摇杆归一化 [0,1]。

**遗留风险（记录，不阻塞）**：同 seed 恢复 RNG 的单步 loss 对比不可靠（CUDA RNG 恢复精度），改用"前后 5 步均值对比"判定收敛；正式训练（阶段 2）沿用此判定。
