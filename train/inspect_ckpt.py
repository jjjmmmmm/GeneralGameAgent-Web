# -*- coding: utf-8 -*-
"""阶段 0.1：检查环境 + ng.pt 的 ckpt_config 实际值（action_dim/horizon/timestep 等）

不加载模型本体（1.97GB），只读 checkpoint 字典里的 ckpt_config，确认训练接口的关键参数。
用法：venv 的 python 运行本文件。
"""
import sys
import json
from pathlib import Path

import torch

sys.stdout.reconfigure(encoding="utf-8")

CKPT = Path(r"D:/2+课产品/_models/ng.pt")

print("=== 环境 ===")
print(f"torch: {torch.__version__}")
print(f"cuda available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"gpu: {torch.cuda.get_device_name(0)}")
    print(f"mem total: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")

try:
    import diffusers
    print(f"diffusers: {diffusers.__version__}")
except ImportError:
    print("diffusers: MISSING")
try:
    import transformers
    print(f"transformers: {transformers.__version__}")
except ImportError:
    print("transformers: MISSING")
try:
    import polars
    print(f"polars: {polars.__version__}")
except ImportError:
    print("polars: MISSING")

print("\n=== ckpt_config ===")
ckpt = torch.load(CKPT, map_location="cpu", weights_only=False)
print(f"ckpt keys: {list(ckpt.keys())}")
print(json.dumps(ckpt["ckpt_config"], indent=2, default=str))
