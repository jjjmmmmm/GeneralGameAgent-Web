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

      <!-- 大标题：优先 Three.js + GLSL 顶点涟漪；WebGL2 不可用时自动降级 2D 像素涟漪 -->
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
// 大标题涟漪：优先 Three.js + GLSL 顶点 shader（鼠标为圆心、半径内流体扰动）；
// WebGL2 不可用时自动降级 2D 像素涟漪（逐像素偏移采样，效果等价，任何浏览器可见）。

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

// ================= 标题涟漪入口 =================
function showFallback() {
  document.querySelector('.title-fallback')?.classList.add('show')
  titleThreeWrap.value?.remove()
}

// WebGL2 可用 → three；否则 → 2D 像素涟漪
function setupTitleEffect() {
  const wrap = titleThreeWrap.value
  if (!wrap) { showFallback(); return }
  let webgl2 = false
  try { webgl2 = !!document.createElement('canvas').getContext('webgl2') } catch { /* ignore */ }
  if (webgl2) setupThreeTitle()
  else setupRipple2D()
}

// three 失败 → 自动降级 2D
function fallbackTo2D() {
  cleanupThreeTitle()
  setupRipple2D()
}

// ================= Three.js 文字平面 + GLSL 顶点涟漪 =================
let threeCtx = null

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
  if (!wrap || !titleEl) { fallbackTo2D(); return }

  let renderer
  try {
    renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })
    renderer.debug.onShaderError = () => fallbackTo2D()
  } catch (err) {
    console.warn('[landing] three renderer failed, downgrade to 2d:', err)
    fallbackTo2D()
    return
  }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  wrap.appendChild(renderer.domElement)

  const scene = new THREE.Scene()
  const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 50)
  camera.position.z = 8

  const tex = makeTextTexture('TEACHING AGENTS\nTO PLAY')
  const aspect = tex.image.width / tex.image.height
  const geo = new THREE.PlaneGeometry(1, 1 / aspect, 180, 48)

  const mat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    uniforms: {
      u_map: { value: tex },
      u_mouse: { value: new THREE.Vector2(99, 99) },
      u_radius: { value: 0.5 },
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
        float falloff = 1.0 - smoothstep(0.0, u_radius, d);
        float wave = sin(d * 9.0 - u_time * 3.0) * 0.5 + 0.5;
        float mag = falloff * falloff * wave;
        pos.z += mag * 0.3;
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
        if (t.a < 0.4) discard;
        float edge = 1.0 - smoothstep(0.35, 0.85, t.a);
        vec3 neon = vec3(0.66, 0.55, 0.98);
        vec3 col = t.rgb * 0.92 + neon * (v_glow * 0.55 + edge * 0.25);
        gl_FragColor = vec4(col, t.a);
      }
    `,
  })

  const mesh = new THREE.Mesh(geo, mat)
  scene.add(mesh)

  function resize() {
    const rect = titleEl.getBoundingClientRect()
    if (rect.width < 10 || rect.height < 10) return
    renderer.setSize(rect.width, rect.height)
    camera.aspect = rect.width / rect.height
    const viewH = 2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * camera.position.z
    const viewW = viewH * camera.aspect
    mesh.scale.setScalar(Math.max(viewW * 0.86, 0.1))
    camera.updateProjectionMatrix()
  }
  resize()
  const ro = new ResizeObserver(resize)
  ro.observe(titleEl)

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

  const clock = new THREE.Clock()
  function animate() {
    threeCtx.raf = requestAnimationFrame(animate)
    cur.lerp(target, 0.12)
    mat.uniforms.u_mouse.value.copy(cur)
    mat.uniforms.u_time.value = clock.getElapsedTime()
    renderer.render(scene, camera)
  }
  animate()

  threeCtx = { renderer, scene, camera, mesh, mat, geo, tex, raf: null, ro, onMove, onLeave }
}

function cleanupThreeTitle() {
  if (!threeCtx) return
  cancelAnimationFrame(threeCtx.raf)
  threeCtx.ro?.disconnect()
  threeCtx.wrap.removeEventListener('pointermove', threeCtx.onMove)
  threeCtx.wrap.removeEventListener('pointerleave', threeCtx.onLeave)
  threeCtx.renderer.dispose()
  threeCtx.geo.dispose()
  threeCtx.mat.dispose()
  threeCtx.tex.dispose()
  threeCtx.renderer.domElement.remove()
  threeCtx = null
}

// ================= 2D 像素涟漪（WebGL 不可用时的等价降级） =================
let ripple2d = null

function setupRipple2D() {
  const wrap = titleThreeWrap.value
  const titleEl = document.querySelector('.landing-title')
  if (!wrap || !titleEl) { showFallback(); return }

  try {
    // 离屏源：高分辨率白字 + 紫色霓虹光晕
    const font = '800 110px -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif'
    const src = document.createElement('canvas')
    const sctx = src.getContext('2d')
    const lines = ['TEACHING AGENTS', 'TO PLAY']
    const lineH = 134
    const pad = 26
    sctx.font = font
    src.width = Math.ceil(Math.max(...lines.map(l => sctx.measureText(l).width)) + pad * 2)
    src.height = Math.ceil(lines.length * lineH + pad)
    sctx.font = font
    sctx.textAlign = 'center'
    sctx.textBaseline = 'middle'
    sctx.shadowColor = 'rgba(124, 58, 237, 0.6)'
    sctx.shadowBlur = 26
    sctx.fillStyle = '#f4f4f6'
    lines.forEach((l, i) => sctx.fillText(l, src.width / 2, pad + (i + 0.5) * lineH))
    const srcData = sctx.getImageData(0, 0, src.width, src.height)

    // 可见 canvas：0.5 降采样保证每帧流畅
    const cv = document.createElement('canvas')
    wrap.appendChild(cv)
    const ctx = cv.getContext('2d')

    const R = 150         // 扰动半径（css px）
    const STRENGTH = 16   // 最大偏移（目标像素）
    const FREQ = 0.05
    const SPEED = 3.0

    let target = { x: -999, y: -999 }
    let mouse = { x: -999, y: -999 }
    let t = 0
    let last = performance.now()

    function resize() {
      const rect = titleEl.getBoundingClientRect()
      if (rect.width < 10 || rect.height < 10) return
      cv.width = Math.round(rect.width * 0.5)
      cv.height = Math.round(rect.height * 0.5)
      cv.style.width = rect.width + 'px'
      cv.style.height = rect.height + 'px'
    }
    resize()
    const ro = new ResizeObserver(resize)
    ro.observe(titleEl)

    const onMove = e => {
      const r = wrap.getBoundingClientRect()
      target.x = e.clientX - r.left
      target.y = e.clientY - r.top
    }
    const onLeave = () => { target.x = -999; target.y = -999 }
    wrap.addEventListener('pointermove', onMove)
    wrap.addEventListener('pointerleave', onLeave)

    function frame() {
      ripple2d.raf = requestAnimationFrame(frame)
      const now = performance.now()
      t += Math.min((now - last) / 1000, 0.05)
      last = now
      mouse.x += (target.x - mouse.x) * 0.1
      mouse.y += (target.y - mouse.y) * 0.1

      const W = cv.width, H = cv.height
      if (W < 4 || H < 4) return
      const iw = srcData.width, ih = srcData.height
      const s0 = srcData.data
      const dst = ctx.createImageData(W, H)
      const d0 = dst.data
      const mx = mouse.x * (W / cv.clientWidth)
      const my = mouse.y * (H / cv.clientHeight)
      const sx = iw / W, sy = ih / H

      for (let y = 0; y < H; y++) {
        const rowBase = y * W
        for (let x = 0; x < W; x++) {
          const dx = x - mx, dy = y - my
          const d = Math.sqrt(dx * dx + dy * dy)
          let u = x * sx, v = y * sy
          if (d < R && d > 0.001) {
            const fall = 1 - d / R
            const off = Math.sin(d * FREQ - t * SPEED) * fall * fall * STRENGTH
            const inv = 1 / d
            u += dx * inv * off * sx
            v += dy * inv * off * sy
          }
          const si = (Math.floor(v) * iw + Math.floor(u)) * 4
          if (si < 0 || si + 3 >= s0.length) continue
          const di = (rowBase + x) * 4
          d0[di] = s0[si]
          d0[di + 1] = s0[si + 1]
          d0[di + 2] = s0[si + 2]
          d0[di + 3] = s0[si + 3]
        }
      }
      ctx.putImageData(dst, 0, 0)
    }
    frame()

    ripple2d = { wrap, cv, ro, raf: null, onMove, onLeave }
  } catch (err) {
    console.warn('[landing] 2d ripple failed:', err)
    showFallback()
  }
}

function cleanupRipple2D() {
  if (!ripple2d) return
  cancelAnimationFrame(ripple2d.raf)
  ripple2d.ro.disconnect()
  ripple2d.wrap.removeEventListener('pointermove', ripple2d.onMove)
  ripple2d.wrap.removeEventListener('pointerleave', ripple2d.onLeave)
  ripple2d.cv.remove()
  ripple2d = null
}

// ================= 生命周期 =================
onMounted(() => {
  const eyebrow = document.querySelector('.landing-eyebrow')
  if (eyebrow) splitEyebrow(eyebrow)

  const typed = document.querySelector('.landing-typed .typed-text')
  if (typed) typeLoop(typed, 'FROM ZERO-SHOT TO FINE-TUNED')

  try { setupTitleEffect() } catch (err) { console.warn('[landing] title effect failed:', err); fallbackTo2D() }
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
  cleanupRipple2D()
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
  cursor: none;
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
  pointer-events: none;
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
