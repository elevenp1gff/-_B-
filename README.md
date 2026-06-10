# zero-shot-ceiling

**1000-class ImageNet classification with 3.7 images per class. Zero-shot beats fine-tuning. Ensemble saturates at ~90%.**

实验二：基于预训练 CNN 的 ImageNet-1K 子集分类。

## Key Findings

- Zero-shot baseline with ConvNeXt-V2-Huge hits **89.43%** top-1; our V1 estimate was 0.5–2%.
- TTA (+0.20%) + class prototype fusion (+0.40%) → **90.03%** val, **0.90** Kaggle LB.
- Dual-model ensemble **reduced** accuracy (89.73%). Three-model weighted ensemble hit 91.04% val but LB stayed at 0.89.
- Model prediction agreement: **93.35%**. Oracle ensemble upper bound: only 91.84%.
- The 65-image public LB has 95% CI ≈ [0.80, 0.96]. All five submissions in [0.89, 0.90] — indistinguishable noise.

## Core Insight

> Pre-training paradigm diversity ≠ prediction error diversity. At ~90% accuracy on clean ImageNet validation, model diversity saturates.

## Structure

```
├── exp2-cnn-solution.py      # Single model: V2H + TTA + prototype (LB 0.90)
├── exp2-cnn-ensemble.py      # Dual-model ensemble + joint prototype
├── exp2-squeeze.py           # Three-model weighted ensemble + temperature search
├── exp2-eva-solo.py          # EVA-02 single model 6-view TTA
├── exp2-vlm-review.py        # Low-confidence review task builder + merger
├── exp2-agreement.py         # Model prediction agreement analysis
├── exp2-figures-nature.py    # Nature-style figure generation (8 panels)
├── exp2-report.md            # Full experiment report (English)
├── 44_朱思逸_202463220038.docx  # Final report (Chinese, embedded figures)
├── figures/                  # SVG + PDF + 600 DPI PNG
└── submission_quick.csv      # Best Kaggle submission
```

## Models

| Model | Params | Resolution | Val Top-1 |
|-------|--------|-----------|-----------|
| ConvNeXt-V2-Huge (FCMAE) | 660M | 512 | 89.83% |
| ConvNeXt-XXLarge-CLIP | 350M | 384 | 89.33% |
| EVA-02-Large (MIM) | 304M | 448 | **90.43%** |
| BEiT-Large | 306M | 512 | 89.22% |

## Hardware

NVIDIA RTX 4060 Laptop GPU (8 GB VRAM), FP16 inference.

## License

MIT
