# backend · FastAPI 服务

提供结果集多版本化接口（`?version=baseline|ft`）：

- `GET /api/results` —— 结果集列表（baseline, ft, 各自生成时间）
- `GET /api/metrics?version=` —— 评测指标 JSON（M4 全套：按键准确率/触发召回率/摇杆相关）
- `GET /api/segments?version=` —— 曲线段列表（段起点、top5 差异帧、差值）
- `GET /api/figures/<name>` —— 可视化图（PNG/JSON）

**设计原则（立项书 §3 F3）**：从 v1 就多版本化，前端 v2 只加视图不加数据格式。

## 状态

待实现（阶段 1）。
