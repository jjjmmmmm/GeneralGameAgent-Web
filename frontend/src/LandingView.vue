<template>
  <div class="landing">
    <!-- 背景：中心紫色光晕 + 极淡网格（装饰，不挡交互） -->
    <div class="landing-bg" aria-hidden="true"></div>

    <header class="landing-top">
      <span class="landing-logo num">GA<span class="landing-logo-slash">//</span>NITROGEN</span>
      <span class="landing-tag num">ML EVAL WORKBENCH</span>
    </header>

    <section class="landing-hero">
      <p class="landing-eyebrow num">ROCKET LEAGUE · DOMAIN ADAPTATION</p>
      <h1 class="landing-title">
        <span class="decode" data-text="TEACHING">TEACHING</span><br />
        <span class="decode" data-text="AGENTS">AGENTS</span>
        <em class="decode" data-text="TO PLAY">TO PLAY</em>
      </h1>
      <div class="landing-typed num">
        <span class="typed-text"></span><span class="typed-cursor">|</span>
      </div>
      <p class="landing-sub reveal">基于 LoRA 微调的 NitroGen 游戏智能体评测工作台，逐帧对比零样本与微调后的行为。</p>
      <div class="landing-cta reveal">
        <button class="landing-btn" @click="$emit('enter')">ENTER WORKBENCH</button>
        <span class="landing-hint num">LoRA r8 · KEY ACC 91.3%</span>
      </div>
    </section>

    <!-- 滚动字幕条 -->
    <div class="landing-marquee">
      <div class="marquee-track">
        <div class="marquee-item num">NITROGEN ADAPTATION <span class="marquee-dot"></span> ROCKET LEAGUE <span class="marquee-dot"></span> DOMAIN ADAPTATION <span class="marquee-dot"></span> FROM ZERO-SHOT TO FINE-TUNED <span class="marquee-dot"></span></div>
        <div class="marquee-item num" aria-hidden="true">NITROGEN ADAPTATION <span class="marquee-dot"></span> ROCKET LEAGUE <span class="marquee-dot"></span> DOMAIN ADAPTATION <span class="marquee-dot"></span> FROM ZERO-SHOT TO FINE-TUNED <span class="marquee-dot"></span></div>
      </div>
    </div>

    <!-- 指标：数字滚动 -->
    <section class="landing-stats reveal" aria-label="关键指标">
      <div class="stat">
        <div class="stat-num num"><span class="stat-dim">88.3%</span> → <span class="stat-strong count" data-target="91.3" data-decimals="1">0</span><span class="stat-strong">%</span></div>
        <div class="stat-label">按键准确率 · 零样本 → 微调</div>
      </div>
      <div class="stat">
        <div class="stat-num num stat-strong"><span class="count" data-target="15">0</span>×</div>
        <div class="stat-label">按键触发召回提升</div>
      </div>
      <div class="stat">
        <div class="stat-num num"><span class="stat-dim">0.08</span> → <span class="stat-strong count" data-target="0.64" data-decimals="2">0</span></div>
        <div class="stat-label">F1 · 零样本 → 微调</div>
      </div>
      <div class="stat">
        <div class="stat-num num stat-weak">0.13</div>
        <div class="stat-label">摇杆相关 · 未达 0.4，如实呈现</div>
      </div>
    </section>

    <!-- 功能索引 01//02//03 -->
    <section class="landing-index">
      <div class="index-item reveal">
        <span class="index-num num">01//</span>
        <div class="index-body">
          <div class="index-name">VIEWER</div>
          <div class="index-desc">指标卡 · 逐帧曲线 · 微调前后对比</div>
        </div>
      </div>
      <div class="index-item reveal">
        <span class="index-num num">02//</span>
        <div class="index-body">
          <div class="index-name">LIVE INFERENCE</div>
          <div class="index-desc">单帧 / 批量评测 · 模型切换</div>
        </div>
      </div>
      <div class="index-item reveal">
        <span class="index-num num">03//</span>
        <div class="index-body">
          <div class="index-name">ASSET LAB</div>
          <div class="index-desc">上传视频与标注 · 选帧对比</div>
        </div>
      </div>
    </section>

    <footer class="landing-foot num reveal">
      <span>NITROGEN ADAPTATION · 2026</span>
      <span>M4 摇杆相关 0.13 &lt; 0.4 · 结果如实呈现</span>
    </footer>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'

// Web Tactics 风格动效：标题解码、打字机、滚动揭示、数字滚动、字幕条。
// 全部在 onMounted 执行（Vue 渲染完成），元素通过类名选择，不依赖响应式数据。

const DECODE_CHARS = '!<>-_\\/[]{}_=+*^?#&%$@'

function decodeText(el) {
  const target = el.dataset.text
  let frame = 0
  const total = 34
  const tick = () => {
    const reveal = Math.floor((frame / total) * target.length)
    let out = ''
    for (let i = 0; i < target.length; i++) {
      const c = target[i]
      if (c === ' ') { out += ' '; continue }
      out += i < reveal ? c : DECODE_CHARS[Math.floor(Math.random() * DECODE_CHARS.length)]
    }
    el.textContent = out
    frame++
    if (frame <= total) requestAnimationFrame(tick)
    else el.textContent = target
  }
  tick()
}

function typeText(el, text, speed = 42) {
  let i = 0
  const tick = () => {
    el.textContent = text.slice(0, i++)
    if (i <= text.length) setTimeout(tick, speed)
  }
  setTimeout(tick, 700)
}

function countUp(el) {
  const target = parseFloat(el.dataset.target)
  const decimals = parseInt(el.dataset.decimals || '0', 10)
  const dur = 1500
  const t0 = performance.now()
  const tick = now => {
    const p = Math.min((now - t0) / dur, 1)
    const eased = 1 - Math.pow(1 - p, 3)
    el.textContent = (eased * target).toFixed(decimals)
    if (p < 1) requestAnimationFrame(tick)
    else el.textContent = target.toFixed(decimals)
  }
  requestAnimationFrame(tick)
}

function splitEyebrow(el) {
  const text = el.textContent
  el.textContent = ''
  for (let i = 0; i < text.length; i++) {
    const s = document.createElement('span')
    s.className = 'eyebrow-char'
    s.textContent = text[i] === ' ' ? '\u00A0' : text[i]
    s.style.animationDelay = `${0.12 + i * 0.03}s`
    el.appendChild(s)
  }
}

onMounted(() => {
  const eyebrow = document.querySelector('.landing-eyebrow')
  if (eyebrow) splitEyebrow(eyebrow)

  document.querySelectorAll('.decode[data-text]').forEach(decodeText)

  const typed = document.querySelector('.landing-typed .typed-text')
  if (typed) typeText(typed, 'FROM ZERO-SHOT TO FINE-TUNED')

  const io = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('in-view')
        io.unobserve(e.target)
      }
    })
  }, { threshold: 0.12 })
  document.querySelectorAll('.reveal').forEach(el => io.observe(el))

  const ioCount = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        countUp(e.target)
        ioCount.unobserve(e.target)
      }
    })
  }, { threshold: 0.4 })
  document.querySelectorAll('.count[data-target]').forEach(el => ioCount.observe(el))
})
</script>

<style scoped>
/* ===== 配色：黑底 + 白字 + 紫色强调（Web Tactics） ===== */
.landing {
  --lp-accent: #a78bfa;      /* 紫罗兰 */
  --lp-accent-strong: #7c3aed;
  --lp-bg: #0a0a0f;          /* 纯黑偏蓝 */
  --lp-text: #f4f4f6;        /* 白 */
  --lp-muted: #9aa0b0;       /* 灰 */
  --lp-line: rgba(167, 139, 250, 0.16);

  position: relative;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  background: var(--lp-bg);
  color: var(--lp-text);
  overflow-x: hidden;
}

/* 背景：中心紫色光晕 + 极淡网格 */
.landing-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(ellipse 62% 46% at 50% 36%, rgba(124, 58, 237, 0.14), transparent 66%),
    linear-gradient(rgba(154, 160, 176, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(154, 160, 176, 0.05) 1px, transparent 1px);
  background-size: 100% 100%, 52px 52px, 52px 52px;
}

/* 顶栏 */
.landing-top {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 22px 36px;
  border-bottom: 1px solid var(--lp-line);
}
.landing-logo {
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 1px;
}
.landing-logo-slash { color: var(--lp-accent); }
.landing-tag {
  font-size: 11px;
  letter-spacing: 0.24em;
  color: var(--lp-muted);
}

/* Hero */
.landing-hero {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 8vh 24px 5vh;
}
.landing-eyebrow {
  font-size: 11px;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--lp-accent);
  margin-bottom: 24px;
}
.eyebrow-char {
  display: inline-block;
  opacity: 0;
  animation: charIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
@keyframes charIn {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: none; }
}

.landing-title {
  font-size: clamp(2.6rem, 8vw, 5.6rem);
  font-weight: 800;
  line-height: 0.98;
  letter-spacing: 0.01em;
  text-transform: uppercase;
  color: var(--lp-text);
  min-height: 2.1em;          /* 防止解码过程高度跳动 */
}
.landing-title em {
  font-style: italic;
  color: var(--lp-accent);
}

.landing-typed {
  margin-top: 18px;
  font-size: clamp(0.95rem, 2.2vw, 1.35rem);
  font-weight: 600;
  letter-spacing: 0.28em;
  color: var(--lp-accent);
  text-transform: uppercase;
  min-height: 1.6em;
}
.typed-cursor {
  display: inline-block;
  margin-left: 2px;
  animation: blink 1s steps(1) infinite;
}
@keyframes blink { 50% { opacity: 0; } }

.landing-sub {
  margin-top: 22px;
  max-width: 46ch;
  font-size: 15px;
  line-height: 1.8;
  color: var(--lp-muted);
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
  background: var(--lp-accent);
  color: #0a0a0f;
  border: 1px solid var(--lp-accent);
  font-family: var(--sans);
  font-weight: 700;
  font-size: 14px;
  letter-spacing: 0.14em;
  padding: 14px 30px;
  border-radius: 2px;
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease, box-shadow 0.2s ease, transform 0.15s ease;
}
.landing-btn:hover {
  background: transparent;
  color: var(--lp-accent);
  box-shadow: 0 0 22px rgba(167, 139, 250, 0.45);
}
.landing-btn:active { transform: scale(0.98); }
.landing-hint {
  font-size: 11px;
  letter-spacing: 0.18em;
  color: var(--lp-muted);
}

/* 滚动字幕条 */
.landing-marquee {
  position: relative;
  z-index: 1;
  overflow: hidden;
  border-top: 1px solid var(--lp-line);
  border-bottom: 1px solid var(--lp-line);
  padding: 14px 0;
  background: rgba(124, 58, 237, 0.05);
}
.marquee-track {
  display: flex;
  width: max-content;
  animation: marquee 26s linear infinite;
}
@keyframes marquee {
  from { transform: translateX(0); }
  to { transform: translateX(-50%); }
}
.marquee-item {
  white-space: nowrap;
  font-size: 12px;
  letter-spacing: 0.3em;
  color: var(--lp-text);
  opacity: 0.75;
  padding-right: 24px;
}
.marquee-dot {
  display: inline-block;
  width: 5px; height: 5px;
  border-radius: 50%;
  background: var(--lp-accent);
  margin: 0 18px 2px;
}

/* 指标区 */
.landing-stats {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1px;
  margin: 0 36px;
  border: 1px solid var(--lp-line);
  background: var(--lp-line);
}
.stat {
  background: var(--lp-bg);
  padding: 28px 24px;
  text-align: left;
}
.stat-num {
  font-size: clamp(1.4rem, 3vw, 2.2rem);
  font-weight: 700;
  color: var(--lp-text);
}
.stat-strong { color: var(--lp-accent); }
.stat-dim { color: var(--lp-muted); }
.stat-weak { color: #7d738f; }
.stat-label {
  margin-top: 10px;
  font-size: 12px;
  color: var(--lp-muted);
  letter-spacing: 0.04em;
}

/* 功能索引 */
.landing-index {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1px;
  margin: 0 36px;
  border: 1px solid var(--lp-line);
  border-top: none;
  background: var(--lp-line);
}
.index-item {
  background: var(--lp-bg);
  padding: 26px 24px;
  display: flex;
  align-items: flex-start;
  gap: 18px;
  transition: background 0.2s ease;
}
.index-item:hover { background: rgba(124, 58, 237, 0.08); }
.index-num {
  font-size: 13px;
  color: var(--lp-accent);
  letter-spacing: 0.1em;
  padding-top: 3px;
}
.index-name {
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.index-desc {
  margin-top: 6px;
  font-size: 12px;
  color: var(--lp-muted);
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
  border-top: 1px solid var(--lp-line);
  font-size: 11px;
  letter-spacing: 0.14em;
  color: var(--lp-muted);
}

/* 滚动揭示 */
.reveal {
  opacity: 0;
  transform: translateY(26px);
  transition: opacity 0.7s ease, transform 0.7s cubic-bezier(0.16, 1, 0.3, 1);
}
.reveal.in-view {
  opacity: 1;
  transform: none;
}

/* 响应式 */
@media (max-width: 900px) {
  .landing-top { padding: 16px 20px; }
  .landing-hero { padding-top: 7vh; }
  .landing-stats { grid-template-columns: repeat(2, 1fr); margin: 0 20px; }
  .landing-index { grid-template-columns: 1fr; margin: 0 20px; }
  .landing-foot { padding: 16px 20px; }
}

@media (prefers-reduced-motion: reduce) {
  .landing-hero > *,
  .landing-stats,
  .landing-index,
  .landing-foot { opacity: 1; transform: none; animation: none; }
  .landing-marquee { display: none; }
  .eyebrow-char { opacity: 1; animation: none; }
}
</style>
