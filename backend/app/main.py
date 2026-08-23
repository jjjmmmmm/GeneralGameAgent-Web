# -*- coding: utf-8 -*-
"""FastAPI 后端：结果集多版本化（baseline / ft）+ 四个端点。

设计原则（立项书 §3 F3）：API 从 v1 就多版本化——version 是资源的一等字段，
前端 v2 只加视图、不加数据格式。

端点：
  GET /api/results                 → 结果集列表（版本、标签、生成时间）
  GET /api/metrics?version=        → 该版本四指标 + M4 判定
  GET /api/segments?version=       → 该版本 21 段曲线 top5（含图文件名）
  GET /api/figures/<name>          → 静态图（PNG）
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from . import assets, inference, metrics_lib

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RESULTS_DIR = DATA_DIR / "results"
FIGURES_DIR = DATA_DIR / "figures"

app = FastAPI(title="GeneralGameAgent-Web API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 前端开发阶段任意 origin；上线前收紧
    allow_methods=["*"],
    allow_headers=["*"],
)

_cache: dict[str, dict] = {}


def _load(version: str) -> dict:
    if version not in _cache:
        p = RESULTS_DIR / f"{version}.json"
        if not p.exists():
            raise HTTPException(status_code=404, detail=f"未知结果集版本: {version}")
        _cache[version] = json.loads(p.read_text(encoding="utf-8"))
    return _cache[version]


def _list_versions() -> list[dict]:
    out = []
    for p in sorted(RESULTS_DIR.glob("*.json")):
        if p.stem == "comparison":
            continue  # comparison 是逐帧对比数据（v2 曲线用），不是结果集版本
        data = json.loads(p.read_text(encoding="utf-8"))
        out.append({
            "version": data.get("version", p.stem),
            "label": data.get("label", p.stem),
            "source": data.get("source", ""),
        })
    return out


@app.get("/api/results")
def list_results() -> dict:
    return {"versions": _list_versions()}


@app.get("/api/metrics")
def get_metrics(version: str = "baseline") -> dict:
    data = _load(version)
    metrics = data.get("metrics", {})
    return {
        "version": version,
        "label": data.get("label", version),
        "metrics": metrics,
        "verdict": metrics_lib.m4_verdict(metrics),
        "targets": {
            "btn_accuracy": metrics.get("m4", {}).get("btn_accuracy_target", 0.5),
            "jl_corr": metrics.get("m4", {}).get("jl_corr_target", 0.4),
        },
    }


@app.get("/api/segments")
def get_segments(version: str = "baseline") -> dict:
    data = _load(version)
    return {"version": version, "segments": data.get("segments", [])}


@app.get("/api/frames")
def get_frames(version: str = "baseline", limit: int = 200, offset: int = 0) -> dict:
    """每帧明细（前端查看器画曲线用）。limit/offset 分页。"""
    data = _load(version)
    frames = data.get("frames", [])
    return {
        "version": version,
        "total": len(frames),
        "offset": offset,
        "frames": frames[offset: offset + limit],
    }


@app.get("/api/button-freq")
def get_button_freq(version: str = "baseline") -> dict:
    data = _load(version)
    return {"version": version, "button_freq": data.get("button_freq", {})}


@app.get("/api/comparison")
def get_comparison() -> dict:
    """微调前后逐帧对比（gt / baseline / ft 摇杆 + 按键），前端 v2 曲线叠加用。"""
    p = RESULTS_DIR / "comparison.json"
    if not p.exists():
        raise HTTPException(status_code=404, detail="对比数据不存在（先跑 train/export_comparison.py）")
    return json.loads(p.read_text(encoding="utf-8"))


@app.get("/api/demo")
def get_demo(version: str = "baseline") -> dict:
    data = _load(version)
    return {"version": version, "demo": data.get("demo", [])}


@app.get("/api/figures/{name:path}")
def get_figure(name: str) -> FileResponse:
    """返回静态图。name 支持子路径（如 demo/seq01_f0.png、curves/seq_060.png）。"""
    p = (FIGURES_DIR / name).resolve()
    # 防目录穿越：必须仍在 FIGURES_DIR 内
    if not p.is_relative_to(FIGURES_DIR.resolve()) or not p.is_file():
        raise HTTPException(status_code=404, detail=f"未找到图: {name}")
    return FileResponse(p, media_type="image/png")


class HealthResp(BaseModel):
    status: str
    versions: list[str]


@app.get("/api/health")
def health() -> HealthResp:
    return HealthResp(status="ok", versions=[v["version"] for v in _list_versions()])


# ===== 在线推理（用户 2026-08-22 确认：懒加载 + 集成进 FastAPI）=====

class PredictReq(BaseModel):
    fid: int | None = None          # 视频帧号（优先）
    sec: float | None = None        # 或秒数（可选）
    k: int = 1                      # 推理次数（多数票，flow matching 随机性控制）
    asset_id: str | None = None     # 素材 id（None=课程默认 SHARD）


@app.get("/api/infer/status")
def infer_status() -> dict:
    """模型加载状态（懒加载 → 前端显示"加载中/就绪"）。"""
    return {"loaded": inference.is_loaded()}


def _resolve_asset(asset_id: str | None, fid: int | None) -> tuple[dict | None, int | None]:
    """asset_id → asset dict；素材帧用拆帧索引 fid（1 基）查绝对秒。"""
    if asset_id is None:
        return None, fid
    asset = inference.load_asset(asset_id)
    meta = json.loads((assets.ASSETS_DIR / asset_id / "meta.json").read_text(encoding="utf-8"))
    frame_secs = meta.get("frame_secs", {})
    sec = frame_secs.get(str(fid))
    if sec is None:
        raise HTTPException(status_code=400, detail=f"素材中不存在帧索引 {fid}（先拆帧）")
    asset["sec"] = float(sec)
    return asset, fid


@app.post("/api/predict")
def predict(req: PredictReq) -> dict:
    """单帧在线推理：抽帧 → K 次多数票 → pred vs gt 对比。

    asset_id 提供 → fid 是素材拆帧索引（1 基），秒从 frame_secs 查；
    否则 fid 是课程全局帧号（秒=fid/60）或 sec 直接给秒。
    """
    if req.asset_id:
        if req.fid is None:
            raise HTTPException(status_code=400, detail="素材推理需提供 fid（拆帧索引）")
        asset, fid = _resolve_asset(req.asset_id, req.fid)
        sec = None
    else:
        asset = None
        fid = req.fid if req.fid is not None else int(round((req.sec or 0) * inference.FPS))
        sec = req.sec

    if not inference.is_loaded():
        inference._load_session()  # 首次加载（约 30s，单请求内阻塞）
    try:
        result = inference.predict_fid(fid, k=req.k, asset=asset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推理失败: {e}")
    return result


class EvaluateReq(BaseModel):
    n: int = 200
    k: int = 3
    save: bool = False          # True 时结果写入 data/results/ft.json（前端 /api/results 自动多一个版本）
    label: str = "微调后（ft）"  # 保存时的结果集标签
    asset_id: str | None = None
    fids: list[int] | None = None   # 素材拆帧的 0 基索引列表（配合 asset_id）


@app.post("/api/evaluate")
def evaluate(req: EvaluateReq) -> dict:
    """批量评测：默认课程测试集；或素材（asset_id + fids 拆帧索引）→ metrics。"""
    asset = None
    if req.asset_id:
        asset = inference.load_asset(req.asset_id)
        # 素材帧：由拆帧索引列表 → (fid=索引, sec=绝对秒, row=行号)
        meta = json.loads((assets.ASSETS_DIR / req.asset_id / "meta.json").read_text(encoding="utf-8"))
        frame_secs = meta.get("frame_secs", {})
        fids = req.fids if req.fids else []
        if not fids:
            raise HTTPException(status_code=400, detail="素材评测需提供 fids（拆帧索引）")
        asset["frames"] = []
        for idx in fids:
            sec = frame_secs.get(str(idx))
            if sec is None:
                raise HTTPException(status_code=400, detail=f"素材中不存在帧索引 {idx}（先拆帧）")
            asset["frames"].append({"fid": idx, "sec": float(sec)})

    if asset is None and (req.n < 1 or req.n > 3600):
        raise HTTPException(status_code=400, detail="n 需在 1~3600")
    if not inference.is_loaded():
        inference._load_session()
    try:
        result = inference.run_evaluate(n=req.n, k=req.k, asset=asset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"评测失败: {e}")

    if req.save:
        ft_path = RESULTS_DIR / "ft.json"
        ft_path.write_text(json.dumps({
            "version": "ft",
            "label": req.label,
            "source": "在线批量评测（Web /api/evaluate）",
            "metrics": result["metrics"],
            "frames": result["frames"],
            "segments": [],   # 曲线段图沿用 baseline（未重新生成段图）
            "demo": [],
            "button_freq": {},
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        _cache.pop("ft", None)  # 使缓存失效，下次读取新文件
        result["saved_as"] = "ft.json"

    return result


# ===== 素材评测工作台（ticket 06：上传视频+标注 → 拆帧 → 选帧对比）=====

class AssetCreateReq(BaseModel):
    name: str


@app.get("/api/assets")
def list_assets_api() -> dict:
    return {"assets": assets.list_assets()}


@app.post("/api/assets")
def create_asset_api(req: AssetCreateReq) -> dict:
    aid = assets.create_asset(req.name or "未命名素材")
    return {"asset_id": aid}


@app.post("/api/assets/{aid}/video")
async def upload_video(aid: str, file: UploadFile = File(...)) -> dict:
    ext = "." + (file.filename or "video.mp4").rsplit(".", 1)[-1].lower()
    data = await file.read()
    try:
        assets.save_video(aid, data, ext)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"asset_id": aid, "video": True}


@app.post("/api/assets/{aid}/actions")
async def upload_actions(aid: str, file: UploadFile = File(...)) -> dict:
    ext = "." + (file.filename or "actions.parquet").rsplit(".", 1)[-1].lower()
    data = await file.read()
    try:
        assets.save_actions(aid, data, ext)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"asset_id": aid, "actions": True}


@app.post("/api/assets/{aid}/actions-dir")
async def upload_actions_dir(aid: str, files: list[UploadFile] = File(...)) -> dict:
    """文件夹上传标注：接收多个 parquet（文件名保留相对路径含 chunk_id）。"""
    collected = []
    for f in files:
        data = await f.read()
        collected.append((f.filename or "", data))
    try:
        result = assets.import_actions_dir(aid, collected)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"asset_id": aid, "actions": True, **result}


class ExtractReq(BaseModel):
    start_sec: float
    end_sec: float
    fps: int = 1


@app.post("/api/assets/{aid}/frames")
def extract_frames_api(aid: str, req: ExtractReq) -> dict:
    try:
        return assets.extract_frames(aid, req.start_sec, req.end_sec, req.fps)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/assets/{aid}/frames/{fname}")
def frame_image(aid: str, fname: str) -> FileResponse:
    p = (assets.ASSETS_DIR / aid / "frames" / fname).resolve()
    frames_dir = (assets.ASSETS_DIR / aid / "frames").resolve()
    if not p.is_relative_to(frames_dir) or not p.is_file():
        raise HTTPException(status_code=404, detail=f"未找到帧: {fname}")
    return FileResponse(p, media_type="image/png")


@app.delete("/api/assets/{aid}")
def delete_asset_api(aid: str) -> dict:
    assets.delete_asset(aid)
    return {"deleted": aid}
