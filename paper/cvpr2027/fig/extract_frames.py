"""Extract the camera frames shown in Figure 1 from two recorded practice episodes (program output, no editing).

The episodes are practice attempts of the initial OpenVLA-OFT policy in round 1 of `a8_spatmain_fixed_s0` (A800 node,
call 00004, sample mode, training seeds only; no gate, audit or test episode is used). Placement seed 101010000 of
LIBERO-Spatial task 0 was attempted several times; attempt a0 succeeded (170 steps) and attempt a2 failed (512 steps,
time limit), as recorded by the simulator's success check in the call's results file. Each episode file holds the
224x224 camera images the policy received, one per action chunk.

    python paper/cvpr2027/fig/extract_frames.py <folder with the two .npz files>
writes frames/<attempt>_<k>.png (four evenly spaced frames per episode) and frames/frames.json."""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
EPISODES = [("libero_spatial-t0-r1-s101010000-a0", True, 170), ("libero_spatial-t0-r1-s101010000-a2", False, 512)]
TASK = "pick up the black bowl between the plate and the ramekin and place it on the plate"


def main(src):
    out = os.path.join(HERE, "frames")
    os.makedirs(out, exist_ok=True)
    meta = {"run": "a8_spatmain_fixed_s0", "call": "00004-rollout-1794287711", "suite": "libero_spatial", "task_id": 0,
            "task": TASK, "placement_seed": 101010000, "policy": "initial OpenVLA-OFT (Openvla-oft-SFT-libero-spatial-traj1)",
            "mode": "sample, temperature 1.6", "episodes": []}
    for name, success, steps in EPISODES:
        z = np.load(os.path.join(src, name + ".npz"))
        assert bool(z["success"]) == success, name
        frames = z["frames"]
        idx = np.linspace(0, len(frames) - 1, 4).round().astype(int).tolist()
        files = []
        for k, i in enumerate(idx):
            f = f"{name.rsplit('-', 1)[1]}_{k}.png"
            Image.fromarray(frames[i]).save(os.path.join(out, f), optimize=True)
            files.append(f)
        meta["episodes"].append({"id": name, "success": success, "steps": steps, "chunks": len(frames),
                                 "frame_index": idx, "files": files})
    json.dump(meta, open(os.path.join(out, "frames.json"), "w"), indent=1)
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1])
