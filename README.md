# GeneralGameAgent-Web

NitroGen 领域适配微调（rocket_league）与可视化前端。

> 课后延伸项目（独立仓库）。前身：课程课题七"通用游戏智能体"（离线推理评测体系，M4 摇杆未达标）。
> 目标：LoRA 微调让模型适配 rocket_league（摇杆相关系数 -0.1 → ≥0.4），并用 Web 前端展示微调前后对比。

完整范围、验收标准与风险见 [`docs/立项书.md`](docs/立项书.md)。

## 阶段（当前进度）

| 阶段 | 内容 | 状态 |
|------|------|------|
| 阶段 0 | 微调可行性 spike（跑通 1 个训练 step） | ⬜ |
| 阶段 1 | 后端 API（多版本化）+ 前端 v1（查看器/仪表盘） | ⬜ |
| 阶段 2 | LoRA 训练 + 评测 + ft 结果入库 | ⬜ |
| 阶段 3 | 前端 v2（微调前后对比视图）+ 收尾 | ⬜ |

## 项目结构

```
GeneralGameAgent-Web/
├── docs/          # 立项书、方案、进展
├── backend/       # FastAPI：/api/results|metrics|segments|figures（多版本化 baseline/ft）
├── train/         # LoRA 微调管线（数据管线、训练循环、评测）
├── frontend/      # Vue3 + Vite + ECharts
├── data/          # 抽帧缓存（不入仓）
├── results/       # 指标 JSON / md（baseline/ft 对比）
└── README.md
```

## 依赖与数据（只读复用课程产物）

| 资源 | 位置 | 用途 |
|------|------|------|
| ng.pt 权重 | `../GeneralGameAgent/../_models/ng.pt` | 微调基座 |
| 数据集 | `../GeneralGameAgent/../_data/SHARD_0088/Z1r1S--MJS4/` | 训练/测试标注 |
| 视频 | `../GeneralGameAgent/../TOP 1 IN 2S...mp4` | 抽帧 |
| NitroGen 模块 | `../NitroGen/` | 只读 import |

## 快速开始（随开发补全）

- 后端：`cd backend && uvicorn main:app`（待实现）
- 前端：`cd frontend && npm run dev`（待实现）
- 训练：`cd train && python train_lora.py`（待实现）
