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

      <!-- 大标题：Three.js + GLSL 顶点涟漪（WebGL 不可用时回退到 HTML 标题） -->
      <div class="landing-title">
        <div class="title-three" ref="titleThreeWrap" aria-hidden="true"></div>
        <h1 class="title-fallback" aria-label="TEACHING AGENTS TO PLAY">
          TEACHING<br />AGENTS <em>TO PLAY</em>
        </h1>
      </div>

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

    <!-- 自定义光标：小点跟手，圆环滞后跟随且不离开小点 -->
    <div class="cursor-dot" ref="cursorDot" aria-hidden="true"></div>
    <div class="cursor-ring" ref="cursorRing" aria-hidden="true"></div>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue'
import * as THREE from 'three'

// Web Tactics 风格门面页。
// 大标题 = Three.js 文字平面 + GLSL 顶点 shader：鼠标靠近时以鼠标为中心产生弹性涟漪扰动，
// 越近越强、远离平滑恢复（sin 波 * 半径衰减 * 时间流动）。
// 其余：循环打字机、滚动揭示、数字滚动、字幕条、自定义光标。

const cursorDot = ref(null)
const cursorRing = ref(null)
const titleThreeWrap = ref(null)

// ================= 自定义光标 =================
const RING_R = 18
let mouseX = -200, mouseY = -200
let ringX = -200, ringY = -200
let cursorRaf = null

function onMouseMove(e) {
  mouseX = e.clientX; mouseY = e.clientY
  if (cursorDot.value) {
    cursorDot.value.style.left = mouseX + 'px'
    cursorDot.value.style.top = mouseY + 'px'
  }
}

function cursorLoop() {
  if (!cursorRing.value) return
  ringX += (mouseX - ringX) * 0.16
  ringY += (mouseY - ringY) * 0.16
  // 小点（鼠标）始终不越过圆环：限制圆环中心到鼠标距离 ≤ RING_R
  let dx = mouseX - ringX, dy = mouseY - ringY
  const dist = Math.hypot(dx, dy)
  if (dist > RING_R) {
    const s = RING_R / dist
    ringX = mouseX - dx * s
    ringY = mouseY - dy * s
  }
  cursorRing.value.style.left = ringX + 'px'
  cursorRing.value.style.top = ringY + 'px'
  cursorRaf = requestAnimationFrame(cursorLoop)
}

function onMouseOver(e) {
  const interactive = e.target.closest('button, a, .index-item, .stat, .landing-btn')
  cursorRing.value?.classList.toggle('is-hover', !!interactive)
  cursorDot.value?.classList.toggle('is-hover', !!interactive)
}

function setupCursor() {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseover', onMouseOver)
  cursorRaf = requestAnimationFrame(cursorLoop)
}

function cleanupCursor() {
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseover', onMouseOver)
  if (cursorRaf) cancelAnimationFrame(cursorRaf)
}

// ================= 眉标逐字符入场 =================
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

// ================= 循环打字机（副标题） =================
function typeLoop(el, text, speed = 46, hold = 1800, eraseSpeed = 24) {
  let i = 0
  let deleting = false
  const tick = () => {
    el.textContent = text.slice(0, i)
    if (!deleting) {
      i++
      if (i > text.length) { deleting = true; setTimeout(tick, hold); return }
      setTimeout(tick, speed)
    } else {
      i--
      if (i < 0) { deleting = false; setTimeout(tick, 600); return }
      setTimeout(tick, eraseSpeed)
    }
  }
  setTimeout(tick, 900)
}

// ================= 数字滚动 =================
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

// ================= Three.js 标题：GLSL 顶点涟漪 =================
let threeCtx = null

function showFallback() {
  document.querySelector('.title-fallback')?.classList.add('show')
  titleThreeWrap.value?.remove()
}

// 用系统字体把标题画到离屏 canvas，作为文字平面纹理（保留原生字体轮廓，支持中文）
function makeTextTexture(text) {
  const font = '800 110px -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif'
  const c = document.createElement('canvas')
  const ctx = c.getContext('2d')
  ctx.font = font
  const lines = text.split('\n')
  const lineH = 134
  const pad = 26
  c.width = Math.ceil(Math.max(...lines.map(l => ctx.measureText(l).width)) + pad * 2)
  c.height = Math.ceil(lines.length * lineH + pad)
  ctx.font = font
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillStyle = '#f4f4f6'
  lines.forEach((l, i) => ctx.fillText(l, c.width / 2, pad + (i + 0.5) * lineH))
  const tex = new THREE.CanvasTexture(c)
  tex.minFilter = THREE.LinearFilter
  return tex
}

function setupThreeTitle() {
  const wrap = titleThreeWrap.value
  const titleEl = document.querySelector('.landing-title')
  if (!wrap || !titleEl) { showFallback(); return }

  // 防御：任何 Three/WebGL 初始化异常都回退 HTML 标题，且不阻断后续初始化
  try {
    const t = document.createElement('canvas')
    if (!(t.getContext('webgl') || t.getContext('webgl2') || t.getContext('experimental-webgl'))) {
      throw new Error('WebGL 不可用')
    }
  } catch (err) {
    console.warn('[landing] three title disabled:', err)
    showFallback()
    return
  }

  let renderer
  try {
    renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })
    // shader 编译失败（不抛 JS 异常）也回退 HTML 标题，避免空白
    renderer.debug.onShaderError = () => showFallback()
  } catch (err) {
    console.warn('[landing] three renderer failed:', err)
    showFallback()
    return
  }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  wrap.appendChild(renderer.domElement)

  const scene = new THREE.Scene()
  const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 50)
  camera.position.z = 8

  // 文字平面：宽 1 单位，高按纹理宽高比（局部坐标 x ∈ [-0.5, 0.5]）
  const tex = makeTextTexture('TEACHING AGENTS\nTO PLAY')
  const aspect = tex.image.width / tex.image.height
  const geo = new THREE.PlaneGeometry(1, 1 / aspect, 180, 48)

  // GLSL：顶点按到鼠标的距离做弹性涟漪（z 凸起），半径内越近越强，正弦波随时间流动
  const mat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    uniforms: {
      u_map: { value: tex },
      u_mouse: { value: new THREE.Vector2(99, 99) }, // 鼠标在文字平面局部坐标
      u_radius: { value: 0.42 },                     // 扰动半径（局部单位）
      u_time: { value: 0 },
    },
    vertexShader: `
      uniform vec2 u_mouse;
      uniform float u_radius;
      uniform float u_time;
      varying vec2 v_uv;
      varying float v_glow;
      void main() {
        v_uv = uv;
        vec3 pos = position;
        float d = distance(pos.xy, u_mouse);
        // 半径内衰减：越近越强（falloff^2 更柔和）
        float falloff = 1.0 - smoothstep(0.0, u_radius, d);
        // 空间涟漪：沿距离的正弦波 + 时间流动，形成流体弹性
        float wave = sin(d * 11.0 - u_time * 3.2) * 0.5 + 0.5;
        float mag = falloff * falloff * wave;
        pos.z += mag * 0.2;                  // 向屏幕外柔和鼓起
        v_glow = falloff * (0.4 + wave * 0.6);
        gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
      }
    `,
    fragmentShader: `
      uniform sampler2D u_map;
      varying vec2 v_uv;
      varying float v_glow;
      void main() {
        vec4 t = texture2D(u_map, v_uv);
        if (t.a < 0.4) discard;              // 透明区裁掉，保留字体轮廓
        // 淡紫霓虹：近鼠标处辉光 + 字形边缘紫边
        float edge = 1.0 - smoothstep(0.35, 0.85, t.a);
        vec3 neon = vec3(0.66, 0.55, 0.98);  // #a78bfa
        vec3 col = t.rgb * 0.92 + neon * (v_glow * 0.55 + edge * 0.25);
        gl_FragColor = vec4(col, t.a);
      }
    `,
  })

  const mesh = new THREE.Mesh(geo, mat)
  scene.add(mesh)

  // 尺寸适配：让文字宽度占容器可视宽度的 ~86%
  function resize() {
    const rect = titleEl.getBoundingClientRect()
    if (rect.width < 10 || rect.height < 10) return
    renderer.setSize(rect.width, rect.height)
    camera.aspect = rect.width / rect.height
    const viewH = 2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * camera.position.z
    const viewW = viewH * camera.aspect
    const s = Math.max(viewW * 0.86, 0.1)
    mesh.scale.setScalar(s)
    camera.updateProjectionMatrix()
  }
  resize()
  const ro = new ResizeObserver(resize)
  ro.observe(titleEl)

  // 鼠标：NDC → 世界（z=0 平面）→ 文字局部坐标（除以 mesh 缩放）
  const raycaster = new THREE.Raycaster()
  const ndc = new THREE.Vector2()
  const zPlane = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0)
  const target = new THREE.Vector2(99, 99)
  const cur = target.clone()
  const onMove = e => {
    const rect = wrap.getBoundingClientRect()
    ndc.set(((e.clientX - rect.left) / rect.width) * 2 - 1, -((e.clientY - rect.top) / rect.height) * 2 + 1)
    raycaster.setFromCamera(ndc, camera)
    const pt = new THREE.Vector3()
    if (raycaster.ray.intersectPlane(zPlane, pt)) {
      const s = mesh.scale.x || 1
      target.set(pt.x / s, pt.y / s)
    }
  }
  const onLeave = () => target.set(99, 99)
  wrap.addEventListener('pointermove', onMove)
  wrap.addEventListener('pointerleave', onLeave)

  // 动画循环：鼠标 lerp 平滑（弹性拖尾）、时间推进、渲染
  const clock = new THREE.Clock()
  function animate() {
    threeCtx.raf = requestAnimationFrame(animate)
    cur.lerp(target, 0.09)
    mat.uniforms.u_mouse.value.copy(cur)
    mat.uniforms.u_time.value = clock.getElapsedTime()
    renderer.render(scene, camera)
  }
  animate()

  threeCtx = {
    renderer, scene, camera, mesh, mat, geo, tex, raf: null, ro,
    listeners: [wrap, onMove, onLeave],
  }
}

function cleanupThreeTitle() {
  if (!threeCtx) return
  cancelAnimationFrame(threeCtx.raf)
  threeCtx.ro?.disconnect()
  threeCtx.renderer.dispose()
  threeCtx.geo.dispose()
  threeCtx.mat.dispose()
  threeCtx.tex.dispose()
  threeCtx.renderer.domElement.remove()
  threeCtx = null
}

// ================= 生命周期 =================
onMounted(() => {
  const eyebrow = document.querySelector('.landing-eyebrow')
  if (eyebrow) splitEyebrow(eyebrow)

  const typed = document.querySelector('.landing-typed .typed-text')
  if (typed) typeLoop(typed, 'FROM ZERO-SHOT TO FINE-TUNED')

  // 标题与光标解耦：Three 失败只回退标题，绝不阻断光标/滚动/计数
  try { setupThreeTitle() } catch (err) { console.warn('[landing] three title failed:', err); showFallback() }
  setupCursor()

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

onBeforeUnmount(() => {
  cleanupCursor()
  cleanupThreeTitle()
})
</script>

<style scoped>
/* ===== 配色：黑底 + 白字 + 紫色强调（Web Tactics） ===== */
.landing {
  --lp-accent: #a78bfa;
  --lp-bg: #0a0a0f;
  --lp-text: #f4f4f6;
  --lp-muted: #9aa0b0;
  --lp-line: rgba(167, 139, 250, 0.16);

  position: relative;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  background: var(--lp-bg);
  color: var(--lp-text);
  overflow-x: hidden;
  cursor: none;             /* 隐藏系统光标，使用自定义光标 */
}

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
.landing-logo { font-size: 15px; font-weight: 700; letter-spacing: 1px; }
.landing-logo-slash { color: var(--lp-accent); }
.landing-tag { font-size: 11px; letter-spacing: 0.24em; color: var(--lp-muted); }

/* Hero */
.landing-hero {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 7vh 24px 5vh;
}
.landing-eyebrow {
  font-size: 11px;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--lp-accent);
  margin-bottom: 22px;
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

/* 标题容器：Three.js canvas 绝对覆盖，h1 作为 WebGL 不可用时的回退 */
.landing-title {
  position: relative;
  width: min(100%, 960px);
  min-height: clamp(5.4rem, 16vw, 11.2rem);
  display: flex;
  align-items: center;
  justify-content: center;
}
.title-three {
  position: absolute;
  inset: 0;
}
.title-three canvas { display: block; width: 100% !important; height: 100% !important; }
.title-fallback {
  position: relative;
  opacity: 0;
  font-size: clamp(2.6rem, 8vw, 5.6rem);
  font-weight: 800;
  line-height: 0.98;
  letter-spacing: 0.01em;
  text-transform: uppercase;
  color: var(--lp-text);
}
.title-fallback em { font-style: italic; color: var(--lp-accent); }
.title-fallback.show { opacity: 1; }

.landing-typed {
  margin-top: 16px;
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
  margin-top: 20px;
  max-width: 46ch;
  font-size: 15px;
  line-height: 1.8;
  color: var(--lp-muted);
}
.landing-cta {
  margin-top: 34px;
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
.landing-hint { font-size: 11px; letter-spacing: 0.18em; color: var(--lp-muted); }

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
.marquee-track { display: flex; width: max-content; animation: marquee 26s linear infinite; }
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
.stat { background: var(--lp-bg); padding: 28px 24px; text-align: left; }
.stat-num { font-size: clamp(1.4rem, 3vw, 2.2rem); font-weight: 700; color: var(--lp-text); }
.stat-strong { color: var(--lp-accent); }
.stat-dim { color: var(--lp-muted); }
.stat-weak { color: #7d738f; }
.stat-label { margin-top: 10px; font-size: 12px; color: var(--lp-muted); letter-spacing: 0.04em; }

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
.index-num { font-size: 13px; color: var(--lp-accent); letter-spacing: 0.1em; padding-top: 3px; }
.index-name { font-size: 15px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; }
.index-desc { margin-top: 6px; font-size: 12px; color: var(--lp-muted); }

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
.reveal.in-view { opacity: 1; transform: none; }

/* ===== 自定义光标 ===== */
.cursor-dot, .cursor-ring {
  position: fixed;
  top: 0; left: 0;
  pointer-events: none;
  z-index: 9999;
  border-radius: 50%;
  transform: translate(-50%, -50%);
}
.cursor-dot {
  width: 8px; height: 8px;
  background: var(--lp-accent);
  transition: width 0.2s ease, height 0.2s ease, background 0.2s ease;
}
.cursor-ring {
  width: 36px; height: 36px;
  border: 1px solid rgba(167, 139, 250, 0.7);
  transition: width 0.25s ease, height 0.25s ease, border-color 0.25s ease;
}
.cursor-dot.is-hover { width: 10px; height: 10px; }
.cursor-ring.is-hover {
  width: 56px; height: 56px;
  border-color: var(--lp-accent);
  border-style: dashed;
}

/* 响应式 */
@media (max-width: 900px) {
  .landing-top { padding: 16px 20px; }
  .landing-hero { padding-top: 6vh; }
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
  .landing { cursor: auto; }
  .cursor-dot, .cursor-ring { display: none; }
}
</style>
