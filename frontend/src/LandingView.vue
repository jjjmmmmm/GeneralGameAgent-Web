<template>
  <div class="landing">
    <!-- 背景：中心青绿光晕 + 极淡网格（装饰，不挡交互） -->
    <div class="landing-bg" aria-hidden="true"></div>

    <header class="landing-top">
      <span class="landing-logo num">GA<span class="landing-logo-slash">//</span>NITROGEN</span>
      <span class="landing-tag num">ML EVAL WORKBENCH</span>
    </header>

    <section class="landing-hero">
      <p class="landing-eyebrow num">ROCKET LEAGUE · DOMAIN ADAPTATION</p>
      <h1 class="landing-title">TEACHING<br />AGENTS <em>TO&nbsp;PLAY</em></h1>
      <p class="landing-sub">基于 LoRA 微调的 NitroGen 游戏智能体评测工作台，逐帧对比零样本与微调后的行为。</p>
      <div class="landing-cta">
        <button class="landing-btn" @click="$emit('enter')">ENTER WORKBENCH</button>
        <span class="landing-hint num">LoRA r8 · KEY ACC 91.3%</span>
      </div>
    </section>

    <section class="landing-stats" aria-label="关键指标">
      <div class="stat">
        <div class="stat-num num"><span class="stat-dim">88.3%</span> → <span class="stat-strong">91.3%</span></div>
        <div class="stat-label">按键准确率 · 零样本 → 微调</div>
      </div>
      <div class="stat">
        <div class="stat-num num stat-strong">15×</div>
        <div class="stat-label">按键触发召回提升</div>
      </div>
      <div class="stat">
        <div class="stat-num num"><span class="stat-dim">0.08</span> → <span class="stat-strong">0.64</span></div>
        <div class="stat-label">F1 · 零样本 → 微调</div>
      </div>
      <div class="stat">
        <div class="stat-num num stat-weak">0.13</div>
        <div class="stat-label">摇杆相关 · 未达 0.4，如实呈现</div>
      </div>
    </section>

    <section class="landing-index">
      <div class="index-item">
        <span class="index-num num">01//</span>
        <div class="index-body">
          <div class="index-name">VIEWER</div>
          <div class="index-desc">指标卡 · 逐帧曲线 · 微调前后对比</div>
        </div>
      </div>
      <div class="index-item">
        <span class="index-num num">02//</span>
        <div class="index-body">
          <div class="index-name">LIVE INFERENCE</div>
          <div class="index-desc">单帧 / 批量评测 · 模型切换</div>
        </div>
      </div>
      <div class="index-item">
        <span class="index-num num">03//</span>
        <div class="index-body">
          <div class="index-name">ASSET LAB</div>
          <div class="index-desc">上传视频与标注 · 选帧对比</div>
        </div>
      </div>
    </section>

    <footer class="landing-foot num">
      <span>NITROGEN ADAPTATION · 2026</span>
      <span>M4 摇杆相关 0.13 &lt; 0.4 · 结果如实呈现</span>
    </footer>
  </div>
</template>

<script setup>
// 门面首页：模仿 Web Tactics（深色 + 巨型大写标题 + 编号索引 + 等宽数字）。
// 点击 CTA 进入工作台（emit 'enter'，由 App.vue 切到 viewer）。
</script>

<style scoped>
.landing {
  position: relative;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  background: var(--bg);
  color: var(--text);
  overflow-x: hidden;
}

/* 背景：中心青绿光晕 + 极淡网格 */
.landing-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(ellipse 60% 45% at 50% 38%, rgba(79, 209, 197, 0.08), transparent 65%),
    linear-gradient(rgba(138, 151, 165, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(138, 151, 165, 0.04) 1px, transparent 1px);
  background-size: 100% 100%, 48px 48px, 48px 48px;
}

/* 顶栏 */
.landing-top {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 22px 36px;
  border-bottom: 1px solid var(--border);
}
.landing-logo {
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 1px;
  color: var(--text);
}
.landing-logo-slash { color: var(--accent); }
.landing-tag {
  font-size: 11px;
  letter-spacing: 0.24em;
  color: var(--text-faint);
}

/* Hero */
.landing-hero {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 9vh 24px 4vh;
}
.landing-eyebrow {
  font-size: 11px;
  letter-spacing: 0.3em;
  color: var(--accent);
  text-transform: uppercase;
  margin-bottom: 22px;
}
.landing-title {
  font-size: clamp(2.6rem, 8vw, 5.6rem);
  font-weight: 800;
  line-height: 0.98;
  letter-spacing: 0.01em;
  text-transform: uppercase;
  color: var(--text);
}
.landing-title em {
  font-style: italic;
  color: var(--accent);
}
.landing-sub {
  margin-top: 24px;
  max-width: 46ch;
  font-size: 15px;
  line-height: 1.8;
  color: var(--text-dim);
}
.landing-cta {
  margin-top: 36px;
  display: flex;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
  justify-content: center;
}
.landing-btn {
  background: var(--accent);
  color: #06231f;
  border: 1px solid var(--accent);
  font-family: var(--sans);
  font-weight: 700;
  font-size: 14px;
  letter-spacing: 0.14em;
  padding: 14px 30px;
  border-radius: 2px;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.15s ease, box-shadow 0.2s ease;
}
.landing-btn:hover {
  background: transparent;
  color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent);
}
.landing-btn:active {
  transform: scale(0.98);
}
.landing-hint {
  font-size: 11px;
  letter-spacing: 0.18em;
  color: var(--text-faint);
}

/* 指标区：等宽数字 */
.landing-stats {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1px;
  margin: 6vh 36px 0;
  border: 1px solid var(--border);
  background: var(--border);
}
.stat {
  background: var(--bg);
  padding: 26px 24px;
  text-align: left;
}
.stat-num {
  font-size: clamp(1.4rem, 3vw, 2.2rem);
  font-weight: 700;
  color: var(--text);
}
.stat-strong { color: var(--accent); }
.stat-dim { color: var(--text-faint); }
.stat-weak { color: #8a6a6a; }
.stat-label {
  margin-top: 10px;
  font-size: 12px;
  color: var(--text-faint);
  letter-spacing: 0.04em;
}

/* 功能索引 01//02//03 */
.landing-index {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1px;
  margin: 0 36px;
  border: 1px solid var(--border);
  border-top: none;
  background: var(--border);
}
.index-item {
  background: var(--bg);
  padding: 26px 24px;
  display: flex;
  align-items: flex-start;
  gap: 18px;
  transition: background 0.2s ease;
}
.index-item:hover { background: var(--bg-panel); }
.index-num {
  font-size: 13px;
  color: var(--accent);
  letter-spacing: 0.1em;
  padding-top: 3px;
}
.index-name {
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text);
}
.index-desc {
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-faint);
}

/* 页脚 */
.landing-foot {
  position: relative;
  z-index: 1;
  margin-top: auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  padding: 20px 36px;
  border-top: 1px solid var(--border);
  font-size: 11px;
  letter-spacing: 0.14em;
  color: var(--text-faint);
}

/* 入场动效（克制）：hero 渐显上移，指标/索引淡入 */
.landing-hero > * {
  opacity: 0;
  animation: rise 0.7s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
.landing-hero > *:nth-child(1) { animation-delay: 0.05s; }
.landing-hero > *:nth-child(2) { animation-delay: 0.14s; }
.landing-hero > *:nth-child(3) { animation-delay: 0.24s; }
.landing-hero > *:nth-child(4) { animation-delay: 0.34s; }
.landing-stats, .landing-index {
  opacity: 0;
  animation: fade 0.8s ease 0.5s forwards;
}
@keyframes rise {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes fade {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* 响应式 */
@media (max-width: 900px) {
  .landing-top { padding: 16px 20px; }
  .landing-hero { padding-top: 7vh; }
  .landing-stats { grid-template-columns: repeat(2, 1fr); margin: 5vh 20px 0; }
  .landing-index { grid-template-columns: 1fr; margin: 0 20px; }
  .landing-foot { padding: 16px 20px; }
}

@media (prefers-reduced-motion: reduce) {
  .landing-hero > *,
  .landing-stats,
  .landing-index {
    opacity: 1;
    animation: none;
  }
}
</style>
