# backend · FastAPI 服务

提供结果集多版本化接口（`?version=baseline|ft`）：

- `GET /api/results` —— 结果集列表（baseline, ft, 各自标签）
- `GET /api/metrics?version=` —— 评测指标 JSON（M4 全套：按键准确率/触发召回率/摇杆相关 + 判定）
- `GET /api/segments?version=` —— 曲线段列表（段起点、top5 差异帧、差值）
- `GET /api/frames?version=&limit=&offset=` —— 每帧明细（查看器曲线数据，分页）
- `GET /api/button-freq?version=` —— 按钮频率表（统计集/测试集）
- `GET /api/demo?version=` —— M5 演示帧对比
- `GET /api/figures/<name>` —— 可视化图（PNG，含 curves/ 子目录）

**设计原则（立项书 §3 F3）**：从 v1 就多版本化，前端 v2 只加视图不加数据格式。

## 状态

✅ 阶段 1 完成：baseline 数据入库 + 四端点 + metrics_lib + 15 个测试全过。

## 本地运行

```powershell
cd D:\2+课产品\GeneralGameAgent-Web\GeneralGameAgent-Web\backend
D:\2+课产品\GeneralGameAgent\GeneralGameAgent\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

依赖（已装进课程 venv）：`fastapi` `uvicorn` `pytest` `httpx`。

## 测试

```powershell
D:\2+课产品\GeneralGameAgent\GeneralGameAgent\.venv\Scripts\python.exe -m pytest tests
```

## 数据结构

- `data/results/baseline.json`：由 `scripts/build_baseline_json.py` 从课程 results md 生成（来源：test_set_metrics/stats_summary/curves index/m5_demo_table）
- `data/figures/`：课程结果图（joystick_distribution / seq_overview / curves/seq_*）
- ft 结果未来由阶段 2 评测生成 `data/results/ft.json`（schema 与 baseline 相同），前端 v2 自动可见
