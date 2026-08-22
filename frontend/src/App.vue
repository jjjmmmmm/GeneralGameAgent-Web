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
      <!-- 左：指标区 + 在线推理 -->
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

        <!-- 在线推理 -->
        <div class="panel-head infer-head">
          <h2>在线推理</h2>
          <span class="infer-status num" :class="{ on: modelLoaded }">
            {{ modelLoaded ? '模型就绪' : '模型未加载' }}
          </span>
        </div>
        <div class="infer-body">
          <div class="infer-row">
            <input v-model="predictFid" class="select num" type="number" min="0" placeholder="帧号(如 38400)" />
            <button class="btn" :disabled="running" @click="runPredict">单帧推理</button>
          </div>
          <div class="infer-hint num" v-if="!modelLoaded">
            首次推理将加载模型（约 9s），请稍候
          </div>

          <div v-if="predictResult" class="infer-result">
            <div class="infer-result-title num">▸ 推理结果</div>
            <div class="infer-line num">
              帧 {{ predictResult.fid }}（t={{ predictResult.sec }}s）· 推理 {{ predictResult.infer_s }}s
            </div>
            <div class="infer-btns">
              <span class="infer-label">gt</span>
              <span class="key-chip" v-for="k in predictResult.buttons.gt" :key="'g'+k">{{ k }}</span>
              <span v-if="!predictResult.buttons.gt.length" class="key-empty num">无</span>
            </div>
            <div class="infer-btns">
              <span class="infer-label">pred</span>
              <span class="key-chip" v-for="k in predictResult.buttons.pred" :key="'p'+k">{{ k }}</span>
              <span v-if="!predictResult.buttons.pred.length" class="key-empty num">无</span>
            </div>
            <div class="infer-meta num">
              按键 {{ predictResult.buttons.n_correct }}/17 一致 · 摇杆 MSE {{ predictResult.j_left.mse.toFixed(4) }}
            </div>
          </div>
          <div v-if="predictError" class="infer-error num">{{ predictError }}</div>

          <div class="infer-row batch-row">
            <button class="btn" :disabled="running" @click="runEvaluate">批量评测 200 帧（K=3）</button>
            <button class="btn ghost" :disabled="running || !evalDone" @click="saveFt">保存为 ft 结果</button>
          </div>
          <div v-if="evaluateResult" class="infer-result">
            <div class="infer-line num">
              评测完成 · {{ evaluateResult.frames.length }} 帧 · 耗时 {{ evaluateResult.metrics.total_s }}s
            </div>
            <div class="infer-meta num">
              准确率 {{ (evaluateResult.metrics.btn_accuracy * 100).toFixed(1) }}% ·
              召回 {{ (evaluateResult.metrics.recall * 100).toFixed(1) }}% ·
              摇杆相关 {{ evaluateResult.metrics.jl_corr.toFixed(3) }}
            </div>
          </div>
          <div v-if="evalError" class="infer-error num">{{ evalError }}</div>
          <div v-if="saveMsg" class="infer-save num">{{ saveMsg }}</div>
        </div>

        <!-- 素材评测工作台 -->
        <div class="panel-head infer-head">
          <h2>素材评测</h2>
          <span class="infer-status num">{{ assetId ? '素材: ' + assetId.slice(0, 8) : '未选素材' }}</span>
        </div>
        <div class="infer-body">
          <div class="infer-row">
            <input v-model="assetName" class="select" placeholder="素材名称" />
            <button class="btn ghost" :disabled="assetBusy" @click="createAsset">新建</button>
            <select v-model="assetId" class="select" @change="onAssetChange">
              <option value="" disabled>选择素材</option>
              <option v-for="a in assetList" :key="a.id" :value="a.id">
                {{ a.name }}（{{ a.frames }} 帧）
              </option>
            </select>
          </div>

          <div class="upload-row" v-if="assetId">
            <label class="upload-btn">
              视频<input type="file" accept="video/*" @change="onVideoFile" hidden />
            </label>
            <label class="upload-btn">
              标注(文件夹)<input type="file" webkitdirectory multiple @change="onActionsDir" hidden />
            </label>
            <label class="upload-btn">
              标注(单文件)<input type="file" accept=".parquet,.csv,.tsv" @change="onActionsFile" hidden />
            </label>
            <span class="infer-hint num">{{ assetReady ? '视频✓ 标注✓' : (assetVideo ? '视频✓' : '') }}</span>
          </div>

          <div class="infer-row" v-if="assetReady">
            <input v-model="frameStart" class="select num" type="number" placeholder="起(秒)" />
            <input v-model="frameEnd" class="select num" type="number" placeholder="止(秒)" />
            <button class="btn" :disabled="assetBusy" @click="runExtract">拆帧</button>
          </div>
          <div v-if="assetError" class="infer-error num">{{ assetError }}</div>
          <div v-if="assetHint" class="infer-save num">{{ assetHint }}</div>

          <!-- 帧网格（1 基索引：第 1 帧=f1） -->
          <div v-if="assetFrames" class="frame-grid">
            <div
              v-for="i in assetFrames"
              :key="i"
              class="frame-cell"
              :class="{ sel: selectedFrames.has(i) }"
              @click="toggleFrame(i)"
            >
              <img :src="`/api/assets/${assetId}/frames/f${i}.png`" :alt="`帧${i}`" loading="lazy" />
              <span class="num">{{ i }}</span>
            </div>
          </div>

          <!-- 帧选择 + 推理 -->
          <div v-if="assetFrames" class="infer-row batch-row">
            <input v-model="frameSpec" class="select num" placeholder="如 1~20 或 1,3,5" />
            <button class="btn ghost" :disabled="assetBusy" @click="selectBySpec">按区间选</button>
          </div>
          <div v-if="assetFrames" class="infer-row">
            <button class="btn" :disabled="assetBusy || !selectedFrames.size" @click="runAssetPredict">
              推理选中 {{ selectedFrames.size }} 帧
            </button>
            <button class="btn ghost" :disabled="assetBusy || !selectedFrames.size" @click="runAssetBatch">
              批量对比
            </button>
          </div>
          <div v-if="assetResults.length" class="asset-results">
            <div class="asset-result" v-for="(r, i) in assetResults" :key="i">
              <div class="infer-line num">
                帧 {{ r.sec }}s · gt[{{ r.buttons.gt.join(',') || '无' }}] pred[{{ r.buttons.pred.join(',') || '无' }}]
                · {{ r.buttons.n_correct }}/17 · MSE {{ r.j_left.mse.toFixed(4) }}
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 右：曲线工作区（双图：总曲线 + 分段图） -->
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
          <!-- 左：段信息 -->
          <div v-if="curSeg" class="seg-info">
            <div class="seg-thumb">
              <img
                :key="curSeg.file + '-' + segIdx"
                :src="`/api/figures/curves/${curSeg.file}?t=${curSeg.start}`"
                :alt="curSeg.file"
              />
            </div>
            <div class="seg-top5">
              <div class="top5-title">Top5 差异帧（该段）</div>
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

          <!-- 右：总曲线 + 分段图 -->
          <div class="charts-col">
            <div class="chart-wrap">
              <div ref="chartEl" class="chart chart-total"></div>
            </div>
            <div class="chart-wrap">
              <div ref="segChartEl" class="chart chart-seg"></div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- 底部：随段变化的演示条 -->
    <footer class="demo-strip" v-if="curSeg">
      <div class="demo-title">
        当前段 {{ curSeg.start }}s–{{ curSeg.end }}s · {{ curSeg.file }}
        <span class="demo-diff num">最大差异 {{ maxDiff.toFixed(2) }}</span>
      </div>
      <div class="demo-cards">
        <!-- 段曲线大图 -->
        <div class="demo-card demo-wide">
          <img
            :key="'big-' + curSeg.file"
            :src="`/api/figures/curves/${curSeg.file}?t=${curSeg.start}`"
            :alt="curSeg.file"
          />
        </div>
        <!-- 若该段覆盖 60–64s（M5 演示段），追加演示帧对比 -->
        <template v-if="curSeg.start === 60">
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
        </template>
        <!-- 其他段：展示该段 top5 差异帧（与左侧"段大图"对应，曲线在大图里） -->
        <template v-else>
          <div class="demo-card" v-for="(f, i) in curSeg.top5_frames" :key="'t'+i">
            <div class="demo-head">
              <span class="demo-rank num">#{{ i + 1 }}</span>
              <span class="num">diff {{ curSeg.top5_diffs[i].toFixed(2) }}</span>
            </div>
            <div class="demo-frame-note">
              <div class="num">段内帧 {{ f }}</div>
              <div class="demo-frame-sub">该帧曲线在左侧大图中</div>
            </div>
          </div>
        </template>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
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

// 在线推理状态
const modelLoaded = ref(false)
const running = ref(false)
const predictFid = ref(38400)
const predictResult = ref(null)
const predictError = ref('')
const evaluateResult = ref(null)
const evalError = ref('')
const evalDone = ref(false)
const saveMsg = ref('')

const chartEl = ref(null)
const segChartEl = ref(null)
let chart = null
let segChart = null

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
    const [health, metrics, segs, fr, dem, status] = await Promise.all([
      api.health(), api.metrics(version.value),
      api.segments(version.value), api.frames(version.value, 200),
      api.demo(version.value), api.inferStatus(),
    ])
    apiOk.value = health.ok
    metricsData.value = metrics
    segments.value = segs
    frames.value = fr
    demo.value = dem
    modelLoaded.value = status.loaded
    updatedAt.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
    await nextTick()
    renderChart()
    renderSegChart()
  } catch (e) {
    apiOk.value = false
    loadError.value = `无法加载数据：${e.message ?? e}`
  }
}

function renderChart() {
  // 总曲线 = 测试集 200 帧逐帧指标
  if (!chartEl.value) return
  if (!chart) chart = echarts.init(chartEl.value)
  if (!frames.value.length) return
  const x = frames.value.map(f => f.fid)
  const jl = frames.value.map(f => f.jl_mse)
  const acc = frames.value.map(f => f.accuracy)
  chart.setOption({
    backgroundColor: 'transparent',
    title: {
      text: '总览 · 测试集 200 帧逐帧指标',
      left: 'center', top: 2,
      textStyle: { color: '#8b97a5', fontSize: 11, fontWeight: 400 },
    },
    grid: { left: 52, right: 68, top: 36, bottom: 26 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(19,25,32,0.95)', borderColor: '#3d4a5a',
      textStyle: { color: '#d7dde4', fontSize: 12 },
    },
    legend: { top: 16, textStyle: { color: '#8b97a5' }, data: ['j_left MSE', '按键准确率'] },
    xAxis: {
      type: 'category', data: x, name: '帧号',
      nameTextStyle: { color: '#56606d', fontSize: 10 },
      axisLabel: { color: '#56606d', fontSize: 9 },
      axisLine: { lineStyle: { color: '#2a333f' } },
    },
    yAxis: [
      {
        type: 'value', name: 'MSE', nameTextStyle: { color: '#56606d', fontSize: 10 },
        axisLabel: { color: '#56606d', fontSize: 10 }, splitLine: { lineStyle: { color: '#1c242e' } },
      },
      {
        type: 'value', name: '准确率', nameGap: 16, nameTextStyle: { color: '#56606d', fontSize: 10 },
        axisLabel: { color: '#56606d', fontSize: 10, formatter: v => (v * 100) + '%' }, splitLine: { show: false },
      },
    ],
    series: [
      { name: 'j_left MSE', type: 'line', showSymbol: false, lineStyle: { width: 1.2, color: '#4fd1c5' }, data: jl, yAxisIndex: 0 },
      { name: '按键准确率', type: 'line', showSymbol: false, lineStyle: { width: 1.2, color: '#e6b45c' }, data: acc, yAxisIndex: 1 },
    ],
  }, true)
}

function renderSegChart() {
  // 分段图 = 当前所选段的 top5 差异柱状图（随段切换变化）
  if (!segChartEl.value) return
  if (!segChart) segChart = echarts.init(segChartEl.value)
  const s = curSeg.value
  if (!s) return
  segChart.setOption({
    backgroundColor: 'transparent',
    title: {
      text: `分段 · ${s.start}s–${s.end}s 差异 top5`,
      left: 'center', top: 2,
      textStyle: { color: '#8b97a5', fontSize: 11, fontWeight: 400 },
    },
    grid: { left: 44, right: 16, top: 36, bottom: 26 },
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(19,25,32,0.95)', borderColor: '#3d4a5a',
      textStyle: { color: '#d7dde4', fontSize: 12 },
      formatter: p => `帧 ${p[0].name} · diff ${p[0].value.toFixed(2)}`,
    },
    xAxis: {
      type: 'category', data: s.top5_frames.map(f => `帧 ${f}`),
      axisLabel: { color: '#56606d', fontSize: 10 },
      axisLine: { lineStyle: { color: '#2a333f' } },
    },
    yAxis: {
      type: 'value', name: 'diff', nameTextStyle: { color: '#56606d', fontSize: 10 },
      axisLabel: { color: '#56606d', fontSize: 10 }, splitLine: { lineStyle: { color: '#1c242e' } },
    },
    series: [{
      name: 'diff', type: 'bar', data: s.top5_diffs, barWidth: '45%',
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

// ===== 在线推理 =====
async function runPredict() {
  running.value = true
  predictError.value = ''
  predictResult.value = null
  try {
    predictResult.value = await api.predict(Number(predictFid.value), 1)
    modelLoaded.value = true
  } catch (e) {
    predictError.value = e.message ?? String(e)
  } finally {
    running.value = false
  }
}

async function runEvaluate() {
  running.value = true
  evalError.value = ''
  evaluateResult.value = null
  evalDone.value = false
  try {
    evaluateResult.value = await api.evaluate(200, 3, false)
    modelLoaded.value = true
    evalDone.value = true
    saveMsg.value = ''
  } catch (e) {
    evalError.value = e.message ?? String(e)
  } finally {
    running.value = false
  }
}

async function saveFt() {
  saveMsg.value = ''
  try {
    await api.evaluate(200, 3, true, '微调后（ft）')
    saveMsg.value = '已保存 ft.json → /api/results 现含 ft 版本'
  } catch (e) {
    saveMsg.value = '保存失败: ' + (e.message ?? e)
  }
}

// ===== 素材评测工作台 =====
const assetList = ref([])
const assetId = ref('')
const assetName = ref('')
const assetBusy = ref(false)
const assetError = ref('')
const assetHint = ref('')
const assetVideo = ref(false)
const assetActions = ref(false)
const assetReady = computed(() => !!assetId.value && assetVideo.value && assetActions.value)
const frameStart = ref('0')
const frameEnd = ref('60')
const assetFrames = ref(0)          // 帧数量（帧索引 1 基：1..assetFrames）
const selectedFrames = ref(new Set())
const frameSpec = ref('')
const assetResults = ref([])

async function loadAssets() {
  assetList.value = await api.assets()
}

async function createAsset() {
  assetBusy.value = true
  assetError.value = ''
  try {
    assetId.value = await api.createAsset(assetName.value || '新素材')
    await loadAssets()
    await onAssetChange()
  } catch (e) {
    assetError.value = e.message ?? String(e)
  } finally {
    assetBusy.value = false
  }
}

async function onAssetChange() {
  assetError.value = ''
  assetFrames.value = 0
  selectedFrames.value = new Set()
  assetResults.value = []
  if (!assetId.value) return
  const a = assetList.value.find(x => x.id === assetId.value)
  assetVideo.value = a?.video ?? false
  assetActions.value = a?.actions ?? false
  if (assetVideo.value && assetActions.value) {
    await refreshFrames()
  }
}

async function refreshFrames() {
  const a = assetList.value.find(x => x.id === assetId.value)
  assetFrames.value = a?.frames ?? 0
  if (assetFrames.value) frameSpec.value = ''
}

async function onVideoFile(e) {
  const file = e.target.files?.[0]
  if (!file) return
  assetBusy.value = true
  assetError.value = ''
  try {
    await api.uploadVideo(assetId.value, file)
    assetVideo.value = true
    await loadAssets()
  } catch (err) {
    assetError.value = err.message ?? String(err)
  } finally {
    assetBusy.value = false
    e.target.value = ''
  }
}

async function onActionsFile(e) {
  const file = e.target.files?.[0]
  if (!file) return
  assetBusy.value = true
  assetError.value = ''
  try {
    await api.uploadActions(assetId.value, file)
    assetActions.value = true
    await loadAssets()
  } catch (err) {
    assetError.value = err.message ?? String(err)
  } finally {
    assetBusy.value = false
    e.target.value = ''
  }
}

async function onActionsDir(e) {
  const files = e.target.files ? [...e.target.files] : []
  if (!files.length) return
  assetBusy.value = true
  assetError.value = ''
  try {
    const r = await api.uploadActionsDir(assetId.value, files)
    assetActions.value = true
    await loadAssets()
    assetHint.value = `已导入 ${r.n_chunks} 个 chunk（${r.rows} 行标注）`
  } catch (err) {
    assetError.value = err.message ?? String(err)
  } finally {
    assetBusy.value = false
    e.target.value = ''
  }
}

async function runExtract() {
  assetBusy.value = true
  assetError.value = ''
  selectedFrames.value = new Set()
  assetResults.value = []
  try {
    const r = await api.extractFrames(assetId.value, Number(frameStart.value), Number(frameEnd.value), 1)
    assetFrames.value = r.n_frames
    await loadAssets()
  } catch (e) {
    assetError.value = e.message ?? String(e)
  } finally {
    assetBusy.value = false
  }
}

function toggleFrame(i) {
  const s = new Set(selectedFrames.value)
  s.has(i) ? s.delete(i) : s.add(i)
  selectedFrames.value = s
}

function selectBySpec() {
  // spec 是 1 基索引（1~20 → 拆出的第1~20帧）
  const idxs = (frameSpec.value || '').split(',').map(s => s.trim()).filter(Boolean).flatMap(part => {
    const m = part.match(/^(\d+)(?:~|-)(\d+)$/)
    if (m) {
      const a = +m[1], b = +m[2]
      return Array.from({ length: Math.abs(b - a) + 1 }, (_, i) => Math.min(a, b) + i)
    }
    return [+part]
  }).filter(i => i >= 1 && i <= assetFrames.value)
  selectedFrames.value = new Set(idxs)
}

async function runAssetPredict() {
  assetBusy.value = true
  assetError.value = ''
  assetResults.value = []
  try {
    const out = []
    for (const idx of [...selectedFrames.value].sort((a, b) => a - b)) {
      // 素材帧：fid=idx（1 基拆帧索引），秒由后端 frame_secs 反推
      const r = await api.predict(idx, 1, assetId.value, null)
      out.push({ ...r, frameIdx: idx })
    }
    assetResults.value = out
  } catch (e) {
    assetError.value = e.message ?? String(e)
  } finally {
    assetBusy.value = false
  }
}

async function runAssetBatch() {
  assetBusy.value = true
  assetError.value = ''
  assetResults.value = []
  try {
    const r = await api.evaluate(0, 1, false, '', assetId.value, [...selectedFrames.value])
    assetResults.value = r.frames.map((f, i) => ({
      sec: f.fid,
      buttons: {
        gt: f.gt_press ? ['…'] : [],
        pred: f.pred_press ? ['…'] : [],
        n_correct: parseInt(f.correct_keys || '0'),
      },
      j_left: { mse: f.jl_mse },
      frameIdx: [...selectedFrames.value][i],
    }))
  } catch (e) {
    assetError.value = e.message ?? String(e)
  } finally {
    assetBusy.value = false
  }
}

function reload() { loadAll() }
function onResize() {
  chart?.resize()
  segChart?.resize()
}

watch(segIdx, async () => {
  await nextTick()
  renderSegChart()
})

onMounted(() => {
  loadAll()
  loadAssets()
  window.addEventListener('resize', onResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
  segChart?.dispose()
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
  grid-template-columns: 320px 1fr;
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

/* ===== 在线推理 ===== */
.infer-head { border-top: 1px solid var(--border); }
.infer-status { font-size: 11px; color: var(--text-faint); }
.infer-status.on { color: var(--ok); }
.infer-body { padding: 12px 16px; display: flex; flex-direction: column; gap: 10px; }
.infer-row { display: flex; gap: 8px; }
.infer-row input { flex: 1; min-width: 0; }
.btn {
  background: var(--accent); color: #06231f; border: none; border-radius: 4px;
  padding: 6px 12px; font-size: 12px; font-weight: 600; cursor: pointer;
  font-family: var(--sans);
}
.btn:disabled { opacity: 0.4; cursor: not-allowed; }
.btn.ghost { background: none; border: 1px solid var(--border-strong); color: var(--text-dim); }
.btn.ghost:not(:disabled):hover { color: var(--text); border-color: var(--accent); }
.infer-hint { font-size: 11px; color: var(--text-faint); }
.infer-result {
  border: 1px solid var(--accent); border-radius: 4px; padding: 10px;
  background: var(--accent-dim);
  display: flex; flex-direction: column; gap: 6px;
}
.infer-result-title { font-size: 11px; color: var(--accent); font-weight: 600; letter-spacing: 1px; text-transform: uppercase; }
.infer-line { font-size: 12px; color: var(--text); }
.infer-btns { font-size: 11px; line-height: 1.7; }
.infer-label { color: var(--text-faint); margin-right: 4px; }
.infer-meta { font-size: 11px; color: var(--accent); }
.infer-error { font-size: 11px; color: var(--fail); }
.infer-save { font-size: 11px; color: var(--ok); }
.batch-row { margin-top: 2px; }
.key-chip { background: var(--bg-elev); border: 1px solid var(--border-strong); border-radius: 3px; padding: 0 4px; margin-right: 3px; font-size: 10px; }
.key-empty { color: var(--text-faint); }

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
  grid-template-columns: 300px 1fr;
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

.charts-col { display: flex; flex-direction: column; gap: 16px; min-height: 0; }
.chart-wrap { flex: 1; min-height: 0; border: 1px solid var(--border); border-radius: 4px; background: var(--bg-panel); }
.chart { width: 100%; height: 100%; }
.chart-total { min-height: 220px; }
.chart-seg { min-height: 220px; }

/* ===== 演示条 ===== */
.demo-strip {
  border-top: 1px solid var(--border);
  background: var(--bg-panel);
  padding: 12px 20px;
  flex-shrink: 0;
  max-height: 260px;
  overflow-y: hidden;
  overflow-x: auto;
}
.demo-title { font-size: 11px; color: var(--text-dim); letter-spacing: 1px; text-transform: uppercase; margin-bottom: 8px; }
.demo-diff { margin-left: 12px; color: var(--accent); }
.demo-cards { display: flex; gap: 12px; align-items: flex-start; }
.demo-card {
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 8px;
  min-width: 160px;
  max-width: 180px;
  background: var(--bg);
}
.demo-card.demo-wide {
  min-width: 280px;
  max-width: 360px;
  flex-shrink: 0;
}
.demo-head { display: flex; justify-content: space-between; font-size: 11px; color: var(--text-dim); margin-bottom: 6px; }
.demo-card img {
  width: 100%;
  max-height: 180px;
  object-fit: contain;
  border-radius: 2px;
  display: block;
  background: var(--bg-elev);
}
.demo-keys { margin-top: 6px; font-size: 11px; line-height: 1.7; }
.k-label { color: var(--text-faint); margin-right: 4px; }
.demo-match { margin-top: 4px; font-size: 11px; color: var(--accent); }
.demo-frame-note { font-size: 11px; color: var(--text-faint); line-height: 1.6; padding: 6px 0; }
.demo-frame-sub { font-size: 10px; color: var(--text-faint); opacity: 0.7; margin-top: 2px; }
.demo-rank { color: var(--accent); font-weight: 600; }

@media (max-width: 1200px) {
  .body { grid-template-columns: 280px 1fr; }
  .viewer-main { grid-template-columns: 1fr; }
  .seg-info { flex-direction: row; flex-wrap: wrap; max-height: 200px; overflow-y: auto; }
  .seg-thumb { flex: 1; min-width: 220px; max-width: 360px; }
  /* 窄屏下双图改左右并排，避开垂直堆叠空间不足导致重叠 */
  .charts-col { flex-direction: row; min-height: 280px; }
  .chart-wrap { flex: 1; min-width: 0; min-height: 280px; }
}
@media (max-width: 800px) {
  .body { grid-template-columns: 1fr; overflow-y: auto; }
  .metrics-panel { border-right: none; border-bottom: 1px solid var(--border); }
  .metric-grid { flex-direction: row; flex-wrap: wrap; }
  .metric { flex: 1; min-width: 140px; }
  .viewer-main { min-height: 700px; }
  .charts-col { flex-direction: column; }
  .chart-wrap { min-height: 220px; }
}

/* ===== 素材评测工作台 ===== */
.upload-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.upload-btn {
  display: inline-block; padding: 6px 10px; font-size: 12px; color: var(--text-dim);
  border: 1px dashed var(--border-strong); border-radius: 4px; cursor: pointer;
}
.upload-btn:hover { color: var(--text); border-color: var(--accent); }
.frame-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(72px, 1fr));
  gap: 6px; max-height: 240px; overflow-y: auto; border: 1px solid var(--border);
  border-radius: 4px; padding: 8px; background: var(--bg-panel);
}
.frame-cell {
  border: 1px solid var(--border); border-radius: 3px; padding: 3px; cursor: pointer;
  background: var(--bg); text-align: center; font-size: 10px; color: var(--text-dim);
}
.frame-cell img { width: 100%; height: 40px; object-fit: cover; display: block; border-radius: 2px; }
.frame-cell.sel { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent); }
.asset-results { display: flex; flex-direction: column; gap: 6px; max-height: 200px; overflow-y: auto; }
.asset-result { border: 1px solid var(--border); border-radius: 4px; padding: 8px; background: var(--bg-panel); font-size: 11px; }
</style>
