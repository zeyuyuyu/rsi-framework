"""Addendum 24: the self-repair study on Yangquan. Nine plans, yq_oftgb_{fixed,full,llm_harness}_s{1,2,3}, from the
collapsing BC start (addendum 12). Everything but the program and the proposer is the yq_oftg_llm_harness plan.
usage: mkplans_bcstart.py   -> writes plans/<name>.json and uploads them to BOS plans/"""
import copy, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
base = json.load(open(os.path.join(HERE, "plans", "yq_oftg_llm_harness_s1.json")))
bc_start = {"solver": {"temperature": 1.6},
            "update": {"operator": "bc", "steps": 100, "batch": 64, "lr": 1e-5, "ratio": "matched",
                       "loss_agg": "episode", "bc_temp": "unit"},
            "curation": {"rule": "verified", "adv": "center"}, "curriculum": {"cases": 64}}
arms = {"fixed": ({"proposer": "fixed"}, 1),
        "full": ({"proposer": "numeric", "space": "harness"}, 2),
        "llm_harness": (dict(base["meta"]), 2)}
for arm, (meta, cands) in arms.items():
    for seed in (1, 2, 3):
        p = copy.deepcopy(base)
        p["program"] = copy.deepcopy(bc_start)
        p["meta"] = meta
        p["engine"] = dict(base["engine"], seed=seed)
        if cands == 2:
            p["engine"]["candidates_per_round"] = 2
        else:
            p["engine"].pop("candidates_per_round", None)
        name = f"yq_oftgb_{arm}_s{seed}"
        path = os.path.join(HERE, "plans", f"{name}.json")
        json.dump(p, open(path, "w"), indent=2)
        st = subprocess.run([sys.executable, os.path.join(HERE, "bos_rw.py"), "put", "bos-research-team",
                             f"shitianyu-rsi/plans/{name}.json", path, "application/json"], capture_output=True, text=True)
        print(name, st.stdout.strip()[:40])
