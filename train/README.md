# train · LoRA 微调管线

自研行为克隆 + flow matching loss 训练循环（官方无训练代码）。

- 基座：`_models/ng.pt`（只读）
- 数据：统计集 38400 帧（chunk_0000~0031），测试集 3600 帧（chunk_0032~0034，隔离）
- 对齐：`帧号 = chunk_id × 1200 + 行号`
- 显存：8G 可行（冻结视觉编码器，只训 attention 低秩）

## 状态

待实现（阶段 0 spike 先验证 1 step 能训）。
