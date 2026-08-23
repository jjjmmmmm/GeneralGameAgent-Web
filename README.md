# GeneralGameAgent-Web

NitroGen 领域适配微调（rocket_league）与可视化前端。

> 课后延伸项目（独立仓库）。前身：课程课题七"通用游戏智能体"（离线推理评测体系，M4 摇杆未达标）。
> 目标：LoRA 微调让模型适配 rocket_league（摇杆相关系数 -0.1 → ≥0.4），并用 Web 前端展示微调前后对比。

完整范围、验收标准与风险见 [`docs/立项书.md`](docs/立项书.md)。

## 阶段（全部完成）

| 阶段 | 内容 | 状态 |
|------|------|------|
| 阶段 0 | 微调可行性 spike（跑通 1 个训练 step） | ✅ 2026-08-22 |
| 阶段 1 | 后端 API（多版本化）+ 前端 v1（查看器/仪表盘） | ✅ 2026-08-22 |
| 阶段 2 | LoRA 训练 + 评测 + ft 结果入库 | ✅ 2026-08-22（按键达标，摇杆未达 0.4，如实呈现）|
| 阶段 3 | 前端 v2（微调前后对比视图）+ 收尾 | ✅ 2026-08-23 |

**M2 结果**：按键召回率 4.25%→65.75%（15 倍）、F1 0.079→0.643；摇杆相关 -0.111→+0.126（未达 0.4，两次重试均如此，按预案如实对比）。详见 [`train/RESULTS.md`](train/RESULTS.md)。

## 项目结构

```
GeneralGameAgent-Web/
├── docs/          # 立项书、总计划、训练接口分析
├── backend/       # FastAPI：/api/results|metrics|segments|frames|comparison|predict|evaluate|assets（多版本化）
├── train/         # LoRA 微调管线（data_pipeline / train_lora / evaluate_ft / export_*）
├── frontend/      # Vue3 + Vite + ECharts（v2 对比视图）
└── README.md
```

## 依赖与数据（只读复用课程产物，不入仓）

| 资源 | 位置 | 用途 |
|------|------|------|
| ng.pt 权重 | `D:/2+课产品/_models/ng.pt` | 微调基座（493M，float32） |
| 数据集 | `D:/2+课产品/_data/SHARD_0088/Z1r1S--MJS4/` | 训练（chunk 0~31）/ 测试（chunk 32~34）标注 |
| 视频 | `D:/2+课产品/TOP 1 IN 2S _ Ranked 2v2 w_ oKhaliD (1).mp4` | 抽帧 |
| NitroGen 模块 | `D:/2+课产品/NitroGen/` | 只读 import（不改源码） |

## 启动步骤

前置：课程 venv 已装 torch(cu128)/transformers/polars/peft/fastapi/uvicorn/python-multipart；前端已 `npm install`。

```powershell
# 1) 后端（FastAPI，端口 8000；首次 /api/predict 懒加载 ng.pt 约 10s）
cd D:\2+课产品\GeneralGameAgent-Web\GeneralGameAgent-Web\backend
D:\2+课产品\GeneralGameAgent\GeneralGameAgent\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 2) 前端（Vite dev，端口 5173，/api 代理到 8000）
cd ..\frontend
npm run dev
```

打开 http://127.0.0.1:5173/

## 训练与评测（可复现）

```powershell
# 数据管线：抽帧缓存（首次约 8 分钟）+ 动作标注
python train\data_pipeline.py

# LoRA 训练（r8/1500 步约 3 分钟；r16/4000 步约 8 分钟）
python train\train_lora.py --steps 1500 --lora_r 8

# 评测 baseline vs ft（200 帧 K=3 多数票，约 6 分钟）
python train\evaluate_ft.py

# 导出 ft.json（前端 /api/results 多版本）与 comparison.json（前端叠加曲线）
python train\export_ft_json.py
python train\export_comparison.py   # 需 HF_HUB_OFFLINE=1（强制本地缓存）
```

## 关键设计

- **API 从 v1 就多版本化**：`?version=baseline|ft` 是一等字段，v2 只加视图不改数据格式
- **在线推理**：`/api/predict`（单帧）、`/api/evaluate`（批量）；模型懒加载
- **素材评测工作台**：上传自己的视频+标注（parquet，与 NitroGen 同构）→ 指定区间拆帧 → 选帧跑 agent 对比
- **诚实呈现**：摇杆相关未达 0.4 如实展示（前端对比卡标注"未达标"），不修饰
