# 03 — 阶段 2：LoRA 微调 + 评测（M2）

**What to build:** 正式训练出 ft 权重并在隔离测试集上评测达标。统计集 38400 帧抽帧缓存 + 对齐 + 训练/验证 split；LoRA 实现（优先 peft，否则手写 attention 低秩旁路）；训练循环（flow matching loss + AdamW + 梯度累积）；后台跑数小时保存 ft 权重；测试集 3600 帧 baseline vs ft 对比，结果 JSON 入库。

**Blocked by:** 01（阶段 0 spike 证明可行）、02（阶段 1 的 metrics_lib 口径，供评测复用）

**Status:** ready-for-agent

- [ ] 数据管线完整版：38400 帧抽帧缓存（同段不重抽）+ 对齐 + 训练/验证 split
- [ ] LoRA 实现：peft 适配或手写低秩旁路（~100 行），冻结视觉编码器+主干
- [ ] 训练循环：flow matching loss（MSE 速度场）+ AdamW + 学习率调度 + 梯度累积（batch=1×N 防 OOM）
- [ ] 正式训练（后台数小时）→ 保存 ft 权重
- [ ] 验收：测试集摇杆相关 ft ≥0.4；按键召回率 ≥2 倍提升；结果写入 JSON
- [ ] 失败预案执行：指标不达标 → 调 LoRA 秩/层/学习率重试一次；仍不达标 → 如实对比呈现，不修饰
