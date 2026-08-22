# -*- coding: utf-8 -*-
"""2.2+2.3 LoRA 微调训练循环（peft）+ flow matching loss。

流程：
1. 加载 ng.pt（load_model）→ 冻结视觉编码器
2. peft LoraConfig 挂到 DiT(8层) + VL mixing(4层) 的 attn1/attn2 的 to_q/to_k/to_v/to_out.0
3. 单帧构造（spike 验证路径：tokenizer.encode 收 numpy）→ forward → loss → 梯度累积
4. 梯度累积（batch=1 × accum）+ AdamW + cosine schedule
5. 保存：merge LoRA → state_dict + ckpt_config → train/ckpt/ft_lora.pt

用法：
  python train_lora.py --steps 2000 --lr 1e-4 --lora_r 8 --accum 16 --log-every 100
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(r"D:/2+课产品/NitroGen")))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from peft import LoraConfig, get_peft_model  # noqa: E402
from data_pipeline import (  # noqa: E402
    build_actions_cache, build_frame_cache, load_frames, split_indices,
)
from nitrogen.inference_session import load_model  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

CKPT = r"D:/2+课产品/_models/ng.pt"
OUT_DIR = Path(__file__).resolve().parent / "ckpt"

LORA_TARGETS = ["to_q", "to_k", "to_v", "to_out.0"]


def build_lora_model(model, r: int, alpha: int, dropout: float):
    """冻结视觉编码器 + 挂 LoRA。"""
    # peft 0.20 需要 base_model_prefix（transformers 惯例），自定义 NitroGen 类缺省
    if not hasattr(model, "base_model_prefix"):
        model.base_model_prefix = ""
    for p in model.vision_encoder.parameters():
        p.requires_grad_(False)
    model_lora = get_peft_model(model, LoraConfig(
        r=r, lora_alpha=alpha, target_modules=LORA_TARGETS,
        lora_dropout=dropout, bias="none",
    ))
    n_lora = sum(p.numel() for p in model_lora.parameters() if p.requires_grad)
    print(f"LoRA 可训练参数: {n_lora/1e6:.2f}M")
    return model_lora


def encode_sample(tokenizer, frame, actions_row, device) -> dict:
    """单帧 → tokenizer.encode → unsqueeze → device。spike 验证路径。"""
    sample = {
        "frames": frame,                       # (1,3,256,256) tensor
        "dropped_frames": torch.zeros(1, dtype=torch.bool),
        "buttons": actions_row[None, :, :21],  # (1,18,21) numpy
        "j_left": actions_row[None, :, 21:23], # (1,18,2)
        "j_right": actions_row[None, :, 23:25],
        "game": None,
    }
    tokenized = tokenizer.encode(sample)
    out = {}
    for k, v in tokenized.items():
        if isinstance(v, torch.Tensor):
            out[k] = v.unsqueeze(0).to(device)
        elif isinstance(v, np.ndarray):
            out[k] = torch.tensor(v).unsqueeze(0).to(device)
        else:
            out[k] = [v]
    return out


def train(args):
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=== 数据 ===")
    build_frame_cache(force=args.refresh_cache, max_frames=None)
    frames = load_frames()
    actions = build_actions_cache()
    n_valid = min(len(frames), len(actions))
    train_idx, val_idx = split_indices(val_ratio=args.val_ratio, seed=args.seed)
    # 帧数可能略少于标注行数（视频末尾），只保留有效索引
    train_idx = train_idx[train_idx < n_valid]
    val_idx = val_idx[val_idx < n_valid]
    print(f"帧 {len(frames)} | 动作 {len(actions)} | 训练 {len(train_idx)} | 验证 {len(val_idx)}")

    print("=== 模型 ===")
    model, tokenizer, img_proc, ckpt_config, game_mapping, _ = load_model(CKPT)
    tokenizer.train()
    model_lora = build_lora_model(model, args.lora_r, args.lora_alpha, args.lora_dropout)
    model_lora.train()
    device = "cuda"

    opt = torch.optim.AdamW(
        [p for p in model_lora.parameters() if p.requires_grad],
        lr=args.lr, weight_decay=args.weight_decay,
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.steps)

    print("=== 训练 ===")
    rng = np.random.default_rng(args.seed)
    t0 = time.time()
    losses = []
    opt.zero_grad()
    step = 0
    while step < args.steps:
        # 随机选训练帧
        row = int(rng.choice(train_idx))
        frame = frames[row]
        pv = img_proc([frame], return_tensors="pt")["pixel_values"].to(device)
        model_input = encode_sample(tokenizer, pv, actions[row], device)

        loss = model_lora(model_input)["loss"] / args.accum
        loss.backward()
        losses.append(loss.item() * args.accum)

        if (step + 1) % args.accum == 0:
            torch.nn.utils.clip_grad_norm_(
                [p for p in model_lora.parameters() if p.requires_grad], args.max_grad_norm)
            opt.step()
            scheduler.step()
            opt.zero_grad()

        if (step + 1) % args.log_every == 0 or step + 1 == args.steps:
            avg = np.mean(losses[-args.log_every:])
            el = time.time() - t0
            print(f"[step {step+1}/{args.steps}] loss={avg:.6f} "
                  f"lr={scheduler.get_last_lr()[0]:.2e} 耗时={el/60:.1f}min")

        step += 1

    print("=== 保存 ===")
    model_lora.eval()
    # peft merge_and_unload 会读 model.config.get("tie_word_embeddings")，
    # 自定义 NitroGen.config 是 pydantic 对象不支持 .get → 临时换成 dict，合并后换回
    orig_config = model_lora.base_model.model.config
    model_lora.base_model.model.config = {"tie_word_embeddings": False}
    merged = model_lora.merge_and_unload()
    merged.config = orig_config  # 恢复 pydantic config（forward 里 self.config.noise_s 需要）
    merged.to(device)
    out_path = OUT_DIR / args.out_name
    torch.save({
        "ckpt_config": ckpt_config.model_dump(),
        "model": merged.state_dict(),
    }, out_path)
    print(f"已保存 ft 权重: {out_path} ({out_path.stat().st_size/1024**3:.2f} GB)")

    print("=== 验证 ===")
    merged.eval()
    v_rng = np.random.default_rng(7)
    val_losses = []
    for _ in range(min(20, len(val_idx))):
        row = int(v_rng.choice(val_idx))
        frame = frames[row]
        pv = img_proc([frame], return_tensors="pt")["pixel_values"].to(device)
        mi = encode_sample(tokenizer, pv, actions[row], device)
        with torch.no_grad():
            val_losses.append(merged(mi)["loss"].item())
    print(f"验证集 loss: {np.mean(val_losses):.6f} (n={len(val_losses)})")
    print("=== 训练完成 ===")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=1000)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--lora_r", type=int, default=8)
    ap.add_argument("--lora_alpha", type=int, default=16)
    ap.add_argument("--lora_dropout", type=float, default=0.05)
    ap.add_argument("--accum", type=int, default=16)
    ap.add_argument("--max_grad_norm", type=float, default=1.0)
    ap.add_argument("--weight_decay", type=float, default=0.01)
    ap.add_argument("--val_ratio", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--log_every", type=int, default=50)
    ap.add_argument("--refresh_cache", action="store_true")
    ap.add_argument("--out_name", default="ft_lora.pt")
    train(ap.parse_args())
