"""OpenVLA-OFT backend: the OpenVLA backend (same-task sharding, subset GPU admission, OOM retry,
worker cleanup, LoRA versions merged at load, receipts) driving OFT workers that reproduce
SimpleVLA-RL's LIBERO inference: one parallel-decoding forward per chunk of 8 actions (56 tokens).

``VLAConfig.openvla_root`` is the SimpleVLA-RL checkout; the workers import its OFT model code.
"""

from pathlib import Path

from ..openvla.backend import VLABackend, VLAConfig


class OFTBackend(VLABackend):
    worker_dir = Path(__file__).resolve().parent


__all__ = ["OFTBackend", "VLAConfig"]
