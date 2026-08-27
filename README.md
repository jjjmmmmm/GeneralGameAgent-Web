# GeneralGameAgent-Web

NitroGen 领域适配微调（rocket_league）与可视化前端。

> 课后延伸项目（独立仓库）。前身：课程课题七"通用游戏智能体"（离线推理评测体系）。
> 目标：LoRA 微调让模型适配 rocket_league（摇杆相关系数 -0.1 → ≥0.4），并用 Web 前端展示微调前后对比。
> **跨游戏评测（2026-08-27）**：摇杆相关与游戏类型强相关——糖豆人 zero-shot **+0.674 ✅ 达标**，rocket_league/FPS 属结构性难点（如实呈现），详见 [`train/RESULTS.md`](train/RESULTS.md)。

> **想上手跑一遍完整演示？先读 [`docs/演示说明.md`](docs/演示说明.md)** —— 含环境清单、启动命令、逐功能演示脚本与排障，可复现。

完整范围、验收标准与风险见 [`docs/立项书.md`](docs/立项书.md)。

## 阶段（全部完成）

| 阶段 | 内容 | 状态 |
|------|------|------|
| 阶段 0 | 微调可行性 spike（跑通 1 个训练 step） | ✅ 2026-08-22 |
| 阶段 1 | 后端 API（多版本化）+ 前端 v1（查看器/仪表盘） | ✅ 2026-08-22 |
| 阶段 2 | LoRA 训练 + 评测 + ft 结果入库 | ✅ 2026-08-22（按键达标；摇杆 rocket_league 未达 0.4，跨游戏评测见 RESULTS.md）|
| 阶段 3 | 前端 v2（微调前后对比视图）+ 收尾 | ✅ 2026-08-23 |

**M2 结果**：按键召回率 4.25%→65.75%（15 倍）、F1 0.079→0.643；摇杆相关 -0.111→+0.126（rocket_league 未达 0.4，两次重试均如此，按预案如实对比）。详见 [`train/RESULTS.md`](train/RESULTS.md)。

**跨游戏评测（2026-08-27，部分游戏达标）**：对 3 个**未训练过**的游戏（抽中间段 200 帧，K=3）评测 baseline/ft：

| 游戏 | baseline 摇杆相关 | ft 摇杆相关 | 按键准确率（baseline/ft）|
|------|------------------|------------|------------------------|
| Fall Guys（糖豆人）| **+0.674 ✅** | **+0.609 ✅** | 99.3% / 96.9% |
| XDefiant | +0.293 | -0.102 | 96.7% / 91.0% |
| Spelunky 2 | +0.160 | +0.237 | 98.4% / 95.4% |

**结论修正**：摇杆相关低**不是模型能力绝对边界，而是与游戏类型强相关**——糖豆人（左摇杆=人物移动方向，映射直接）zero-shot 即达标 0.4；赛车（rocket_league）与 FPS（双摇杆）因映射复合属结构性难点。ft 跨游戏泛化不稳定（XDefiant 上相关转负）。

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
| 数据集 | `D:/2+课产品/_data/SHARD_0088/Z1r1S--MJS4/` | 训练（chunk 0-31）/ 测试（chunk 32-34）标注 |
| 视频 | `D:/2+课产品/TOP 1 IN 2S _ Ranked 2v2 w_ oKhaliD (1).mp4` | 抽帧 |
| NitroGen 模块 | `D:/2+课产品/NitroGen/` | 只读 import（不改源码） |

## 从 0 搭建（新机器 / 新环境）

> 代码使用**绝对路径约定**：本仓库位于 `D:/2+课产品/GeneralGameAgent-Web/GeneralGameAgent-Web`，外部资源位于 `D:/2+课产品/`（venv / `_models` / `_data` / `NitroGen` / 视频），路径硬编码在 `backend/app/inference.py`、`train/*.py`、`backend/scripts/start_web.py`。
> **换机器时**：① 按下方"资源放置"搭出同构目录；② 或全局搜索替换代码中的 `D:/2+课产品` 为你的路径。

### 1) Python 环境（Python 3.12，Blackwell 显卡需 PyTorch cu128）

```powershell
py -3.12 -m venv D:/2+课产品/GeneralGameAgent/GeneralGameAgent/.venv
# 激活后安装：
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128   # RTX 50 系必需 cu128
pip install transformers polars peft matplotlib
cd <仓库>/backend && pip install -r requirements.txt   # fastapi/uvicorn/pytest/httpx/python-multipart
```

### 2) 资源获取（来源 + 放置，均不入 git）

| 资源 | 来源 | 放置位置 |
|------|------|---------|
| NitroGen 模块 | `git clone https://github.com/MineDojo/NitroGen.git` | `D:/2+课产品/NitroGen/` |
| 基座模型 `ng.pt`（1.97GB） | HF 模型库 `nvidia/NitroGen`（单文件 `ng.pt`） | `D:/2+课产品/_models/ng.pt` |
| 数据集分片 `SHARD_0088`（4GB tar） | HF 数据集 `nvidia/NitroGen`（`SHARD_0088.tar`） | `D:/2+课产品/_data/SHARD_0088/`，只需保留 `Z1r1S--MJS4/` |
| 原始视频（703.8s） | YouTube `https://www.youtube.com/watch?v=Z1r1S--MJS4`（即分片 `metadata.json` 的 `original_video.url`） | 文件名**必须**为 `TOP 1 IN 2S _ Ranked 2v2 w_ oKhaliD (1).mp4`，放 `D:/2+课产品/` |
| siglip2 视觉编码器 | HF `google/siglip2-large-patch16-256` | 首次加载自动下载（联网；无代理用 hf-mirror） |
| 微调模型 `ft_lora.pt`（2GB） | 本项目训练产物：从原机器拷贝，或跑 `train/train_lora.py` 重新训练 | `<仓库>/train/ckpt/ft_lora.pt` |

```powershell
# 下载命令示例（hf 需网络；无梯子先设 $env:HF_ENDPOINT="https://hf-mirror.com"）
huggingface-cli download nvidia/NitroGen ng.pt --local-dir D:/2+课产品/_models
huggingface-cli download nvidia/NitroGen SHARD_0088.tar --repo-type dataset --local-dir D:/2+课产品/_data
tar -xf D:/2+课产品/_data/SHARD_0088.tar -C D:/2+课产品/_data   # 解压出 SHARD_0088/

# 视频（yt-dlp；YouTube 限流时可按课程方法用 cookies）
yt-dlp -f "bv*[height<=1080]+ba/b[height<=1080]" -o "D:/2+课产品/TOP 1 IN 2S _ Ranked 2v2 w_ oKhaliD (1).mp4" "https://www.youtube.com/watch?v=Z1r1S--MJS4"
```

> **注意**：数据集只含动作标注（parquet + metadata），**不含视频帧**；帧需用 ffmpeg 从视频抽取（`帧号 = chunk_id × 1200 + 行号`，秒 = 帧号/60）。`metadata.json` 含 `bbox_controller_overlay`（画面手柄遮挡框）。

### 3) 前端依赖

```powershell
cd <仓库>/frontend
npm install   # 仅 vue + echarts + vite
```

依赖就绪后进入下方启动步骤。

## 启动步骤

### 一键启动（推荐）

双击仓库根目录 **`start_web.bat`**，自动启动后端（:8000）+ 前端（:5173），就绪后打开浏览器 http://127.0.0.1:5173/。关闭窗口或 Ctrl+C 停止服务。日志：`backend/_uvicorn.log`、`frontend/_vite.log`。

前置：课程 venv 已装 torch(cu128)/transformers/polars/peft/fastapi/uvicorn/python-multipart；前端已 `npm install`。

### 手动启动

```powershell
# 1) 后端（FastAPI，端口 8000；首次 /api/predict 懒加载 ng.pt 约 10s）
cd D:\2+课产品\GeneralGameAgent-Web\GeneralGameAgent-Web\backend
D:\2+课产品\GeneralGameAgent\GeneralGameAgent\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 2) 前端（Vite dev，端口 5173，/api 代理到 8000；必须 --host 127.0.0.1 否则只监听 IPv6）
cd ..\frontend
npm run dev -- --host 127.0.0.1
```

打开 http://127.0.0.1:5173/

### 克隆后（新机器）能看什么？

| 数据 | 入仓 | 克隆后 |
|------|------|--------|
| 指标 JSON（`baseline.json` / `comparison.json` / `ft.json`） | ✅ | 有——指标卡、曲线、对比视图正常 |
| 静态图 PNG（段图 `figures/curves/`、演示图 `figures/demo/`、分布图，共 10.8MB） | ✅ | **有**——查看器段图/演示条完整 |
| 素材工作台数据（`backend/data/assets/`，1.5GB） | ❌ | 无——功能可用，无预置素材 |
| 模型权重 `ng.pt` / `ft_lora.pt`（3.8GB） | ❌ | 无——在线推理需手动部署 |
| NitroGen 模块、数据集、视频、HF 视觉编码器缓存 | ❌ | 无——推理/训练需部署 |

**部署分层**：
- **仅查看/对比**：clone + `npm install` + 课程 venv 即可，`start_web.bat` 一键启动，无需任何大文件。
- **在线推理 / 素材评测**：需从原环境拷贝 `_models/ng.pt`、`train/ckpt/ft_lora.pt`、`../NitroGen/`、视频与 `_data/SHARD_0088/`，并确保 HF `siglip2-large-patch16-256` 有本地缓存（或首次联网加载）。

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
- **诚实呈现**：摇杆相关 rocket_league 未达 0.4 如实展示（前端对比卡标注"未达标"）；跨游戏评测（糖豆人 +0.674）证明该指标与游戏类型强相关
