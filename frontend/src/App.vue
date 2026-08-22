<template>
  <div class="workspace">
    <!-- 顶栏 -->
    <header class="topbar">
      <div class="topbar-left">
        <span class="mark">GA</span>
        <span class="title">NitroGen 评测工作台</span>
        <span class="sub">rocket_league · SHARD_0088</span>
      </div>
      <div class="topbar-right">
        <span class="ver-chip" v-if="version">结果集: <b class="num">{{ version }}</b></span>
        <span class="conn" :class="{ off: !apiOk }">
          <i class="dot"></i>{{ apiOk ? 'API 已连接' : 'API 离线' }}
        </span>
      </div>
    </header>

    <main class="body">
      <!-- 左：指标区 -->
      <section class="panel metrics-panel">
        <div class="panel-head">
          <h2>M4 指标</h2>
          <button class="link-btn" @click="reload">重新加载</button>
        </div>

        <div v-if="metricsData" class="metric-grid">
          <div class="metric" v-for="m in metricCards" :key="m.key">
            <div class="metric-label">{{ m.label }}</div>
            <div class="metric-value num" :class="{ ok: m.ok === true, fail: m.ok === false }">
              {{ m.text }}
            </div>
            <div class="metric-hint num">
              {{ m.hint }}
              <span v-if="m.ok !== undefined" class="badge" :class="m.ok ? 'b-ok' : 'b-fail'">
                {{ m.ok ? '达标' : '未达标' }}
              </span>
            </div>
          </div>
        </div>
        <div v-else class="empty" :class="{ err: loadError }">
          {{ loadError || '加载中…' }}
        </div>

        <div class="panel-foot num" v-if="metricsData">
          按键事件 · pred {{ metricsData.metrics.events.pred }} / gt {{ metricsData.metrics.events.gt }} / both {{ metricsData.metrics.events.both }}
          <br/>更新于 {{ updatedAt || '—' }}（指标为固定评测结果，重载刷新数据源）
        </div>
      </section>

      <!-- 右：曲线工作区 -->
      <section class="panel viewer-panel">
        <div class="panel-head">
          <h2>动作曲线</h2>
          <div class="viewer-controls">
            <select class="select num" v-model="segIdx" title="选择曲线段">
              <option v-for="(s, i) in segments" :key="s.start" :value="i">
                {{ s.start }}s–{{ s.end }}s · seq_{{ String(s.start).padStart(3, '0') }}
              </option>
            </select>
            <span class="seg-diff num" v-if="curSeg">
              最大差异 {{ maxDiff.toFixed(2) }}
            </span>
          </div>
        </div>

        <div class="viewer-main">
          <div v-if="curSeg" class="seg-info">
            <div class="seg-thumb">
              <!-- :key 强制切换段时重新加载对应曲线图，避免浏览器复用旧图 -->
              <img :key="curSeg.file" :src="`/api/figures/curves/${curSeg.file}`" :alt="curSeg.file" />
            </div>
            <div class="seg-top5">
              <div class="top5-title">Top5 差异帧</div>
              <table class="top5-table">
                <thead><tr><th>帧</th><th>差异</th></tr></thead>
                <tbody>
                  <tr v-for="(d, i) in curSeg.top5_diffs" :key="i">
                    <td class="num">{{ curSeg.top5_frames[i] }}</td>
                    <td class="num">{{ d.toFixed(2) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="chart-wrap">
            <div ref="chartEl" class="chart"></div>
          </div>
        </div>
      </section>
    </main>

    <!-- 底部：演示帧 -->
    <footer class="demo-strip" v-if="demo.length">
      <div class="demo-title">演示 · 视频 60–64s 人类标注 vs 模型预测</div>
      <div class="demo-cards">
        <div class="demo-card" v-for="d in demo" :key="d.frame">
          <div class="demo-head">
            <span class="num">{{ d.frame }}</span>
            <span class="num">t={{ d.sec }}s</span>
          </div>
          <img :src="`/api/figures/demo/${d.image}`" :alt="d.frame" />
          <div class="demo-keys">
            <span class="k-label">gt</span>
            <span class="key-chip" v-for="k in d.gt_keys" :key="'g'+k">{{ k }}</span>
            <span v-if="!d.gt_keys.length" class="key-empty num">无</span>
            <br/>
            <span class="k-label">pred</span>
            <span class="key-chip" v-for="k in d.pred_keys" :key="'p'+k">{{ k }}</span>
            <span v-if="!d.pred_keys.length" class="key-empty num">无</span>
          </div>
          <div class="demo-match num">一致 {{ d.match }}</div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'
import { api } from './lib/api'

const version = ref('baseline')
const metricsData = ref(null)
const segments = ref([])
const frames = ref([])
const demo = ref([])
const apiOk = ref(false)
const loadError = ref('')
const updatedAt = ref('')
const segIdx = ref(0)
const chartEl = ref(null)

let chart = null

const metricCards = computed(() => {
  if (!metricsData.value) return []
  const m = metricsData.value.metrics
  const v = metricsData.value.verdict
  const t = metricsData.value.targets
  return [
    { key: 'acc', label: '按键准确率', text: (m.btn_accuracy * 100).toFixed(1) + '%',
      hint: `≥${(t.btn_accuracy * 100).toFixed(0)}%`, ok: v.btn_accuracy_pass },
    { key: 'recall', label: '触发召回率', text: (m.recall * 100).toFixed(1) + '%',
      hint: '命中 / gt 全量', ok: undefined },
    { key: 'prec', label: '触发精确率', text: (m.precision * 100).toFixed(1) + '%',
      hint: '命中 / pred 全量', ok: undefined },
    { key: 'f1', label: 'F1', text: m.f1.toFixed(3), hint: 'P·R 调和', ok: undefined },
    { key: 'corr', label: '摇杆相关', text: (m.jl_corr >= 0 ? '+' : '') + m.jl_corr.toFixed(3),
      hint: `≥${t.jl_corr.toFixed(1)}`, ok: v.jl_corr_pass },
    { key: 'mse', label: '摇杆 MSE', text: m.jl_mse.toFixed(4), hint: 'j_left', ok: undefined },
  ]
})

const curSeg = computed(() => (segments.value[segIdx.value] ?? null))
const maxDiff = computed(() => {
  const s = curSeg.value
  return s ? Math.max(...s.top5_diffs) : 0
})

async function loadAll() {
  try {
    loadError.value = ''
    const [health, metrics, segs, fr, dem] = await Promise.all([
      api.health(), api.metrics(version.value),
      api.segments(version.value), api.frames(version.value, 200),
      api.demo(version.value),
    ])
    apiOk.value = health.ok
    metricsData.value = metrics
    segments.value = segs
    frames.value = fr
    demo.value = dem
    updatedAt.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
    renderSegChart()
  } catch (e) {
    apiOk.value = false
    loadError.value = `无法加载数据：${e.message ?? e}`
  }
}

function renderSegChart() {
  // 主曲线图 = 当前所选段的 top5 差异柱状图（随段切换变化）
  if (!chartEl.value) return
  if (!chart) chart = echarts.init(chartEl.value)
  const s = curSeg.value
  if (!s) return
  const topFrames = s.top5_frames
  const topDiffs = s.top5_diffs
  chart.setOption({
    backgroundColor: 'transparent',
    title: {
      text: `${s.start}s–${s.end}s · 差异 top5`,
      left: 'center', top: 4,
      textStyle: { color: '#8b97a5', fontSize: 12, fontWeight: 500 },
    },
    grid: { left: 48, right: 20, top: 44, bottom: 30 },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(19,25,32,0.95)', borderColor: '#3d4a5a',
      textStyle: { color: '#d7dde4', fontSize: 12 },
      formatter: p => `帧 ${p[0].name} · diff ${p[0].value.toFixed(2)}`,
    },
    xAxis: {
      type: 'category',
      data: topFrames.map(f => `帧 ${f}`),
      axisLabel: { color: '#56606d', fontSize: 10 },
      axisLine: { lineStyle: { color: '#2a333f' } },
    },
    yAxis: {
      type: 'value', name: 'diff', nameTextStyle: { color: '#56606d', fontSize: 11 },
      axisLabel: { color: '#56606d', fontSize: 10 }, splitLine: { lineStyle: { color: '#1c242e' } },
    },
    series: [{
      name: 'diff', type: 'bar',
      data: topDiffs,
      barWidth: '45%',
      itemStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: '#4fd1c5' }, { offset: 1, color: 'rgba(79,209,197,0.25)' }],
        },
        borderRadius: [3, 3, 0, 0],
      },
    }],
  }, true)
}

function reload() { loadAll() }
function onResize() { chart?.resize() }

watch(segIdx, renderSegChart)

onMounted(() => {
  loadAll()
  window.addEventListener('resize', onResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
})
</script>

<style scoped>
.workspace {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

/* ===== 顶栏 ===== */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 52px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-panel);
  flex-shrink: 0;
}
.topbar-left { display: flex; align-items: baseline; gap: 12px; }
.mark {
  font-family: var(--mono);
  font-weight: 700;
  color: var(--accent);
  border: 1px solid var(--accent);
  border-radius: 4px;
  padding: 1px 6px;
  font-size: 12px;
  letter-spacing: 1px;
}
.title { font-size: 15px; font-weight: 600; }
.sub { font-size: 12px; color: var(--text-faint); font-family: var(--mono); }
.topbar-right { display: flex; align-items: center; gap: 14px; }
.ver-chip { font-size: 12px; color: var(--text-dim); }
.ver-chip b { color: var(--text); font-weight: 600; }
.conn { font-size: 12px; color: var(--text-dim); display: flex; align-items: center; gap: 6px; }
.conn.off { color: var(--fail); }
.dot { width: 8px; height: 8px; border-radius: 50%; background: var(--ok); display: inline-block; }
.conn.off .dot { background: var(--fail); }

/* ===== 主体 ===== */
.body {
  flex: 1;
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 0;
  min-height: 0;
}

.panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  border-right: 1px solid var(--border);
}
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-panel);
  flex-shrink: 0;
}
.panel-head h2 { font-size: 12px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; color: var(--text-dim); }
.link-btn {
  background: none; border: none; color: var(--accent); cursor: pointer;
  font-size: 12px; font-family: inherit;
}
.link-btn:hover { text-decoration: underline; }

/* ===== 指标 ===== */
.metrics-panel { overflow-y: auto; }
.metric-grid { padding: 12px; display: flex; flex-direction: column; gap: 8px; }
.metric {
  border: 1px solid var(--border);
  background: var(--bg-panel);
  padding: 12px 14px;
  border-radius: 4px;
}
.metric-label { font-size: 11px; color: var(--text-dim); letter-spacing: 1px; text-transform: uppercase; }
.metric-value { font-size: 26px; font-weight: 700; margin-top: 2px; color: var(--text); }
.metric-value.ok { color: var(--ok); }
.metric-value.fail { color: var(--fail); }
.metric-hint { font-size: 11px; color: var(--text-faint); margin-top: 4px; display: flex; align-items: center; gap: 6px; }
.badge {
  font-size: 10px; padding: 0 6px; border-radius: 3px; border: 1px solid;
}
.b-ok { color: var(--ok); border-color: var(--ok); }
.b-fail { color: var(--fail); border-color: var(--fail); }
.panel-foot { padding: 10px 16px; border-top: 1px solid var(--border); font-size: 12px; color: var(--text-faint); }
.empty { padding: 24px 16px; color: var(--text-faint); text-align: center; }
.empty.err { color: var(--fail); }

/* ===== 查看器 ===== */
.viewer-panel { border-right: none; }
.viewer-controls { display: flex; align-items: center; gap: 10px; }
.select {
  background: var(--bg-elev); color: var(--text); border: 1px solid var(--border-strong);
  border-radius: 4px; padding: 4px 8px; font-size: 12px;
}
.seg-diff { font-size: 12px; color: var(--text-dim); }

.viewer-main {
  flex: 1;
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 16px;
  padding: 16px;
  min-height: 0;
}
.seg-info { display: flex; flex-direction: column; gap: 12px; overflow-y: auto; }
.seg-thumb { border: 1px solid var(--border); background: var(--bg-panel); border-radius: 4px; overflow: hidden; }
.seg-thumb img { width: 100%; display: block; }
.top5-title { font-size: 11px; color: var(--text-dim); letter-spacing: 1px; text-transform: uppercase; margin-bottom: 6px; }
.top5-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.top5-table th { text-align: left; color: var(--text-faint); font-weight: 500; padding: 4px 8px; border-bottom: 1px solid var(--border); }
.top5-table td { padding: 4px 8px; border-bottom: 1px solid var(--border); }

.chart-wrap { min-height: 0; border: 1px solid var(--border); border-radius: 4px; background: var(--bg-panel); }
.chart { width: 100%; height: 100%; min-height: 300px; }

/* ===== 演示条 ===== */
.demo-strip {
  border-top: 1px solid var(--border);
  background: var(--bg-panel);
  padding: 12px 20px;
  flex-shrink: 0;
  overflow-x: auto;
}
.demo-title { font-size: 11px; color: var(--text-dim); letter-spacing: 1px; text-transform: uppercase; margin-bottom: 8px; }
.demo-cards { display: flex; gap: 12px; }
.demo-card {
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 8px;
  min-width: 160px;
  background: var(--bg);
}
.demo-head { display: flex; justify-content: space-between; font-size: 11px; color: var(--text-dim); margin-bottom: 6px; }
.demo-card img { width: 100%; border-radius: 2px; }
.demo-keys { margin-top: 6px; font-size: 11px; line-height: 1.7; }
.k-label { color: var(--text-faint); margin-right: 4px; }
.key-chip { background: var(--bg-elev); border: 1px solid var(--border-strong); border-radius: 3px; padding: 0 4px; margin-right: 3px; font-size: 10px; }
.key-empty { color: var(--text-faint); }
.demo-match { margin-top: 4px; font-size: 11px; color: var(--accent); }

@media (max-width: 1100px) {
  .body { grid-template-columns: 240px 1fr; }
  .viewer-main { grid-template-columns: 1fr; }
}
@media (max-width: 800px) {
  .body { grid-template-columns: 1fr; overflow-y: auto; }
  .metrics-panel { border-right: none; border-bottom: 1px solid var(--border); }
  .metric-grid { flex-direction: row; flex-wrap: wrap; }
  .metric { flex: 1; min-width: 140px; }
}
</style>
