# -*- coding: utf-8 -*-
"""阶段 1.2：把课程 results 的 md 评测结果转成结构化 JSON 入库。

输入（课程仓库，只读）：
  results/test_set_metrics.md      → metrics + 每帧明细
  results/stats_summary.md         → 统计集/测试集按钮频率
  results/figures/curves/index.md  → 21 段曲线 top5
  results/m5_demo_table.md         → 演示 5 帧

输出：
  backend/data/results/baseline.json

设计：结果集版本化（baseline / ft），前端 v2 只加视图不改 schema。
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

COURSE = Path(r"D:/2+课产品/GeneralGameAgent/GeneralGameAgent")
OUT = Path(__file__).resolve().parent.parent / "data" / "results" / "baseline.json"


def parse_pct(s: str) -> float:
    return float(s.strip().rstrip("%")) / 100.0


def parse_metrics(md: str) -> dict:
    def grab(pattern: str) -> str:
        m = re.search(pattern, md)
        assert m, f"missing metric: {pattern}"
        return m.group(1)

    return {
        "btn_accuracy": float(grab(r"按键准确率（17 键全对比例）: \*\*([\d.]+)%\*\*")) / 100,
        "precision": float(grab(r"触发精确率（pred 命中/pred 全）: \*\*([\d.]+)%\*\*")) / 100,
        "recall": float(grab(r"触发召回率（pred 命中/gt 全）: \*\*([\d.]+)%\*\*")) / 100,
        "f1": float(grab(r"F1: \*\*([\d.]+)\*\*")),
        "jl_mse": float(grab(r"摇杆 j_left MSE: \*\*([\d.]+)\*\*")),
        "jl_corr": float(grab(r"摇杆 j_left 相关系数: \*\*([+-][\d.]+)\*\*")),
        "avg_infer_s": float(grab(r"单帧推理均时: ([\d.]+)s")),
        "events": {
            "pred": int(grab(r"总按键事件: pred=(\d+)")),
            "gt": int(grab(r"pred=\d+, gt=(\d+)")),
            "both": int(grab(r"共同命中=(\d+)")),
        },
        "m4": {
            "btn_accuracy_target": 0.5,
            "jl_corr_target": 0.4,
            "btn_accuracy_pass": "达标" in re.search(r"按键准确率 ≥50%: \*\*(.*?)\*\*", md).group(1),
            "jl_corr_pass": "达标" in re.search(r"摇杆相关系数 ≥0.4: \*\*(.*?)\*\*", md).group(1),
        },
    }


def parse_frames(md: str) -> list[dict]:
    rows = []
    in_table = False
    for line in md.splitlines():
        if line.startswith("| idx |"):
            in_table = True
            continue
        if in_table and line.startswith("|"):
            if line.startswith("|---"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 10:
                continue
            idx, fid, pred, gt, both, correct, acc, mse, corr, t = cells[:10]
            rows.append({
                "idx": int(idx), "fid": int(fid),
                "pred_press": int(pred), "gt_press": int(gt), "both": int(both),
                "correct_keys": correct, "accuracy": parse_pct(acc),
                "jl_mse": float(mse),
                "jl_corr": None if corr == "+nan" else float(corr),
                "time_s": float(t.rstrip("s")),
            })
    return rows


def parse_button_freq(md: str) -> dict:
    sections = {"stat": {}, "test": {}}
    current = None
    for line in md.splitlines():
        if "统计集频率表" in line:
            current = "stat"
            continue
        if "测试集频率表" in line:
            current = "test"
            continue
        if "全部 35 chunks" in line:
            break
        if current is None:
            continue
        m = re.match(r"\|\s*(\w+)\s*\|\s*(\d+)\s*\|\s*([\d.]+)%\s*\|", line)
        if m:
            sections[current][m.group(1)] = {
                "presses": int(m.group(2)),
                "ratio": float(m.group(3)) / 100.0,
            }
    return sections


def parse_curves(md: str) -> list[dict]:
    segs = []
    in_table = False
    for line in md.splitlines():
        if line.startswith("| start |"):
            in_table = True
            continue
        if in_table and line.startswith("|"):
            if line.startswith("|---"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 5:
                continue
            start, end, file, top5, vals = cells[:5]
            segs.append({
                "start": int(start), "end": int(end), "file": file,
                "top5_frames": [int(x) for x in re.findall(r"\d+", top5)],
                "top5_diffs": [float(x) for x in re.findall(r"[\d.]+", vals)],
            })
    return segs


def parse_demo(md: str) -> list[dict]:
    demo = []
    in_table = False
    for line in md.splitlines():
        if line.startswith("| 帧 |"):
            in_table = True
            continue
        if in_table and line.startswith("|"):
            if line.startswith("|---"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 7:
                continue
            frame, sec, img, gt, pred, stick, match = cells[:7]
            demo.append({
                "frame": frame, "sec": int(sec.rstrip("s")), "image": img,
                "gt_keys": [k.strip() for k in gt.split(",") if k.strip()],
                "pred_keys": [k.strip() for k in pred.split(",") if k.strip() and k != "（无）"],
                "stick": stick, "match": match,
            })
    return demo


def main():
    metrics_md = (COURSE / "results" / "test_set_metrics.md").read_text(encoding="utf-8")
    stats_md = (COURSE / "results" / "stats_summary.md").read_text(encoding="utf-8")
    curves_md = (COURSE / "results" / "figures" / "curves" / "index.md").read_text(encoding="utf-8")
    demo_md = (COURSE / "results" / "m5_demo_table.md").read_text(encoding="utf-8")

    data = {
        "version": "baseline",
        "label": "零样本（NitroGen 原生）",
        "source": "课程 results md（test_set_metrics / stats_summary / curves/index / m5_demo_table）",
        "metrics": parse_metrics(metrics_md),
        "frames": parse_frames(metrics_md),
        "button_freq": parse_button_freq(stats_md),
        "segments": parse_curves(curves_md),
        "demo": parse_demo(demo_md),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"WROTE {OUT}")
    print(f"  frames={len(data['frames'])}, segments={len(data['segments'])}, demo={len(data['demo'])}")
    print(f"  metrics={json.dumps({k: v for k, v in data['metrics'].items() if k != 'm4'}, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
