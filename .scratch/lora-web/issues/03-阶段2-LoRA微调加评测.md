# 03 — 阶段 2：LoRA 微调 + 评测（M2）

**What to build:** 正式训练出 ft 权重并在隔离测试集上评测达标。统计集 38400 帧抽帧缓存 + 对齐 + 训练/验证 split；LoRA 实现（优先 peft，否则手写 attention 低秩旁路）；训练循环（flow matching loss + AdamW + 梯度累积）；后台跑数小时保存 ft 权重；测试集 3600 帧 baseline vs ft 对比，结果 JSON 入库。

**Blocked by:** 01（阶段 0 spike 证明可行）、02（阶段 1 的 metrics_lib 口径，供评测复用）

**Status:** resolved (2026-08-22)

- [x] 数据管线完整版：38400 帧抽帧缓存 + 对齐 + 训练/验证 split（实测 37397 帧，视频末尾略短）
- [x] LoRA 实现：peft 0.20（补 base_model_prefix 属性），挂 DiT 8 层 + VL 4 层的 to_q/k/v/out，0.79M 参数，冻结视觉编码器
- [x] 训练循环：flow matching loss + AdamW + cosine + 梯度累积（accum=16）
- [x] 正式训练：r8 1500 步（2.9min）/ r16 4000 步（7.8min），保存 ft 权重（与 ng.pt 格式兼容，可 load_model）
- [x] 验收（部分达标）：按键召回率 8~15 倍✅、F1 7~8 倍✅、按键准确率 +2.6~3pp✅；**摇杆相关 0.048~0.126 < 0.4 ❌**、摇杆 MSE 变差 ❌
- [x] 失败预案执行：R3 重试一次（r16/4000 步）仍不达标 → 如实对比呈现，不修饰
- [x] 结果入库：`backend/data/results/ft.json`（前端 /api/results 自动多 ft 版本）

## Answer (2026-08-22)

**M2 部分达标。** 按键能力大幅提升（召回率 15 倍、F1 8 倍），**摇杆相关未达 0.4**（0.048~0.126），按 R3 预案如实呈现。

- 训练产物：`train/ckpt/ft_lora.pt`（r8）、`ft_lora_r16.pt`（r16），1.84GB，权重不入仓
- 评测结果：`train/RESULTS.md`（含两次重试对比）
- 前端：`/api/results` 现在返回 2 版本（baseline + ft），v2 对比视图可直接用
- 关键教训：flow matching loss 25 维等权，摇杆仅 4 维 → 梯度被按钮主导；peft 0.20 需 `base_model_prefix` 属性；`merge_and_unload` 会替换 config 需恢复 pydantic config
