# frontend · Vue3 可视化前端

技术栈：Vue 3 + Vite + ECharts。

- **v1**（已完成）：评测工作台——M4 指标卡（含达标判定）、动作曲线查看器（21 段 top5 差异帧 + 200 帧摇杆/按键曲线）、演示帧对比条，接入 baseline
- **v2**（计划）：微调前后对比视图（指标并排 + 曲线叠加）

## 状态

✅ 阶段 1 完成：v1 工作台已实现并 E2E 验证通过。

## 开发运行

```powershell
# 1) 先启动后端（见 backend/README.md，端口 8000）
# 2) 启动前端（vite dev 代理 /api → 127.0.0.1:8000）
cd D:\2+课产品\GeneralGameAgent-Web\GeneralGameAgent-Web\frontend
npm install   # 首次
npm run dev   # http://127.0.0.1:5173/
```

## 结构

- `src/App.vue` —— 单页工作台（顶栏 / 指标区 / 查看器 / 演示条）
- `src/lib/api.js` —— 多版本 API 封装（v2 切 version 即可，不改组件）
- `src/styles/base.css` —— 深色操作台设计系统

## 设计说明

- 深色"实验室操作台"风格：细边框网格 + 等宽数字（tabular-nums），强调色只用于数据层，状态色（绿/红）只用于达标判定
- 指标数值大字号，达标/未达标徽标直观
- 查看器：左侧段缩略图 + top5 差异帧表，右侧 ECharts 200 帧评测曲线（摇杆 MSE / 按键准确率双轴）
- 响应式：宽屏左右布局，窄屏折叠为单列
