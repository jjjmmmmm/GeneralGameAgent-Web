# -*- coding: utf-8 -*-
"""素材管理：上传视频 + 上传操作标注（parquet）+ 指定区间拆帧 + 帧/缩略图列表。

设计（用户 2026-08-22 确认）：
  - 标注格式 = parquet，与课程 actions_processed.parquet 同构（17 布尔键 + j_left + j_right）
  - 拆帧 = 指定秒数区间（含起止秒 + 密度参数，默认 1fps）
  - 帧号对齐：帧号 = 秒 × 60（与课程 FPS 约定一致）；parquet 行号 = 秒 × 60 行（每行一帧）
  - 素材目录：backend/data/assets/<id>/{video.mp4, actions_processed.parquet, frames/f<fid>.png}
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import uuid
from pathlib import Path

import polars as pl

ASSETS_DIR = Path(__file__).resolve().parent.parent / "data" / "assets"
FPS = 60
ALLOWED_VIDEO_EXT = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
ALLOWED_ACTION_EXT = {".parquet", ".csv", ".tsv"}
BUTTONS = [
    "back", "dpad_down", "dpad_left", "dpad_right", "dpad_up", "east",
    "guide", "left_shoulder", "left_thumb", "left_trigger", "north",
    "right_shoulder", "right_thumb", "right_trigger", "south", "start", "west",
]


def meta_get(aid: str) -> dict:
    """读素材的 meta.json。"""
    d = _asset_dir(aid)
    p = d / "meta.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _asset_dir(aid: str) -> Path:
    d = ASSETS_DIR / aid
    if not d.is_dir():
        raise FileNotFoundError(f"素材不存在: {aid}")
    return d


def list_assets() -> list[dict]:
    out = []
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    for d in sorted(ASSETS_DIR.iterdir()):
        if not d.is_dir():
            continue
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8")) if (d / "meta.json").exists() else {}
        n_frames = len(list((d / "frames").glob("f*.png"))) if (d / "frames").exists() else 0
        out.append({
            "id": d.name,
            "name": meta.get("name", d.name),
            "video": (d / "video.mp4").exists(),
            "actions": (d / "actions_processed.parquet").exists() or (d / "actions_processed.csv").exists(),
            "frames": n_frames,
            "range": meta.get("range", None),
            "actions_rows": meta.get("actions_rows"),  # 标注总行数
            "actions_coverage_sec": round(meta.get("actions_rows", 0) / FPS, 1) if meta.get("actions_rows") else None,
        })
    return out


def create_asset(name: str) -> str:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    aid = uuid.uuid4().hex[:12]
    d = ASSETS_DIR / aid
    d.mkdir(parents=True, exist_ok=False)
    (d / "frames").mkdir()
    (d / "meta.json").write_text(json.dumps({"name": name}, ensure_ascii=False), encoding="utf-8")
    return aid


def save_video(aid: str, data: bytes, ext: str) -> None:
    if ext.lower() not in ALLOWED_VIDEO_EXT:
        raise ValueError(f"不支持的视频格式: {ext}")
    d = _asset_dir(aid)
    p = d / f"video{ext.lower()}"
    p.write_bytes(data)
    # 统一命名为 video.mp4（ffmpeg 对 mp4 最稳）；其他格式保留原名，拆帧时按实际路径
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    meta["video_file"] = p.name
    (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")


def actions_rows(aid: str) -> int:
    """素材标注总行数（=video 帧数 = 60fps × 标注覆盖秒数）。"""
    return _load_actions(aid).height


def save_actions(aid: str, data: bytes, ext: str) -> None:
    if ext.lower() not in ALLOWED_ACTION_EXT:
        raise ValueError(f"不支持的标注格式: {ext}")
    d = _asset_dir(aid)
    p = d / f"actions_processed{ext.lower()}"
    p.write_bytes(data)
    # 校验列结构（读一次）
    try:
        df = _load_actions(aid)
        missing = [c for c in BUTTONS if c not in df.columns] + ["j_left", "j_right"]
        missing = [c for c in missing if c not in df.columns]
        if missing:
            raise ValueError(f"标注缺少列: {missing}")
    except Exception as e:
        p.unlink(missing_ok=True)
        raise ValueError(f"标注文件校验失败: {e}")
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    meta["actions_file"] = p.name
    meta["actions_rows"] = df.height  # 标注行数 = 60fps × 覆盖秒数
    (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")


def import_actions_dir(aid: str, files: list[tuple[str, bytes]]) -> dict:
    """从文件夹导入标注：接收多个 actions_processed.parquet（文件名含 chunk_id）。

    files = [(相对路径如 'Z1r1S--MJS4_chunk_0000/actions_processed.parquet', bytes), ...]
    按 chunk_id 排序拼接成一个连续标注（row = 秒×60 对齐完整视频）。
    """
    d = _asset_dir(aid)
    dfs = []
    for rel, data in files:
        m = re.search(r"chunk_(\d{4})", rel)
        if not m or not rel.endswith("actions_processed.parquet"):
            continue  # 只收 actions_processed，跳过 raw/metadata
        cid = int(m.group(1))
        tmp = d / f"_chunk_{cid:04d}.parquet"
        tmp.write_bytes(data)
        try:
            df = pl.read_parquet(tmp)
        except Exception:
            tmp.unlink(missing_ok=True)
            continue
        tmp.unlink()
        dfs.append((cid, df))
    if not dfs:
        raise ValueError("未找到任何 actions_processed.parquet（请选择含 chunk_XXXX 的文件夹）")

    dfs.sort(key=lambda x: x[0])
    merged = pl.concat([df for _, df in dfs])
    out = d / "actions_processed.parquet"
    merged.write_parquet(out)

    # 校验
    missing = [c for c in BUTTONS if c not in merged.columns] + ["j_left", "j_right"]
    missing = [c for c in missing if c not in merged.columns]
    if missing:
        out.unlink(missing_ok=True)
        raise ValueError(f"标注缺少列: {missing}")

    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    meta["actions_file"] = out.name
    meta["chunks"] = [c for c, _ in dfs]
    meta["actions_rows"] = merged.height  # 拼接后总行数
    (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")

    return {"n_chunks": len(dfs), "rows": merged.height, "chunk_ids": [c for c, _ in dfs]}


def _load_actions(aid: str) -> pl.DataFrame:
    d = _asset_dir(aid)
    for cand in (d / "actions_processed.parquet", d / "actions_processed.csv", d / "actions_processed.tsv"):
        if cand.exists():
            if cand.suffix == ".parquet":
                return pl.read_parquet(cand)
            return pl.read_csv(cand, separator="\t" if cand.suffix == ".tsv" else ",")
    raise FileNotFoundError(f"素材 {aid} 未上传操作标注")


def get_video_path(aid: str) -> Path:
    d = _asset_dir(aid)
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    vf = meta.get("video_file", "video.mp4")
    return d / vf


def extract_frames(aid: str, start_sec: float, end_sec: float, fps: int = 1) -> dict:
    """指定秒数区间拆帧。帧号 = 秒 × 60（与标注对齐）。返回统计。"""
    if fps < 1 or fps > 60:
        raise ValueError("fps 需在 1~60")
    if end_sec <= start_sec:
        raise ValueError("end 需大于 start")
    d = _asset_dir(aid)
    video = get_video_path(aid)
    if not video.exists():
        raise FileNotFoundError(f"素材 {aid} 未上传视频")

    # 校验标注覆盖范围：end_sec×60 不能超过标注总行数
    rows = meta_get(aid).get("actions_rows") or 0
    if rows and end_sec * FPS > rows:
        cover = round(rows / FPS, 1)
        raise ValueError(
            f"拆帧区间超出标注覆盖范围：end_sec={end_sec}s 需要 {int(end_sec*FPS)} 行，"
            f"素材标注仅 {rows} 行（覆盖 {cover}s）。请缩小区间或上传完整标注"
        )

    frames_dir = d / "frames"
    frames_dir.mkdir(exist_ok=True)
    # 清空旧帧（重拆）
    for old in frames_dir.glob("f*.png"):
        old.unlink()

    # 用 ffmpeg 按 fps 抽帧（fps=1 → 每秒 1 帧）
    out_pattern = str(frames_dir / "f%d.png")
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y",
         "-ss", f"{start_sec:.3f}", "-to", f"{end_sec:.3f}",
         "-i", str(video),
         "-vf", f"fps={fps}",
         "-q:v", "2", out_pattern],
        check=True, capture_output=True,
    )

    # 帧名 = 1 基索引（f1.png, f2.png, ...）；每帧绝对秒 = start + (idx-1)/fps
    files = list(frames_dir.glob("f*.png"))
    if not files:
        raise RuntimeError("拆帧结果为空（检查区间是否超出视频时长）")
    fids = sorted(int(p.stem[1:]) for p in files)  # 数字排序，保证 f1,f2,...f10
    frame_secs = {idx: round(start_sec + (idx - 1) / fps, 3) for idx in fids}

    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    meta["range"] = {"start": start_sec, "end": end_sec, "fps": fps}
    meta["frame_secs"] = {str(k): v for k, v in frame_secs.items()}
    (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")

    return {
        "asset_id": aid,
        "range": {"start": start_sec, "end": end_sec, "fps": fps},
        "n_frames": len(fids),
        "fids": fids,  # 帧索引（1 基）
    }


def parse_frame_spec(spec: str) -> list[int]:
    """解析帧选择：'1~20' → [1..20]；'1,5,9' → [1,5,9]；'3' → [3]。
    返回的是 0 基索引（对帧列表）还是帧号？这里返回帧号（1 基秒号 × fps 需调用方处理）。
    实际语义：spec 是"帧列表索引"（1 基，第 1 帧=拆出的第 1 帧）。"""
    items = []
    for part in spec.replace(" ", "").split(","):
        if not part:
            continue
        m = re.fullmatch(r"(\d+)(?:~|-)(\d+)", part)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if a > b:
                a, b = b, a
            items.extend(range(a, b + 1))
        elif part.isdigit():
            items.append(int(part))
        else:
            raise ValueError(f"无法解析帧选择: {part}")
    if not items:
        raise ValueError("帧选择为空")
    return items


def delete_asset(aid: str) -> None:
    d = ASSETS_DIR / aid
    if d.exists():
        shutil.rmtree(d)
