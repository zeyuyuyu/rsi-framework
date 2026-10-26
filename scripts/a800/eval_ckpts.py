"""Evaluate given versions of a code-WM run on the three test suites (dev-seed stage result)."""
import json, sys
from dataclasses import asdict
from pathlib import Path
from rsi.backends.llm.backend import LLMBackend, LLMConfig
from rsi.core.types import Version
from rsi.core.stats import paired_report
from rsi.domains.code_wm.domain import CodeWorldModelDomain, InputPredictionSuite, load_cruxeval, load_lcb_execution

run, out, gpu = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
plan = json.loads((run / "plan.json").read_text())
llm = json.loads(open(sys.argv[4]).read())["llm"]
llm.update(sample_gpus=(gpu,), train_gpus=(gpu,), workdir=str(out) + ".work", admission_gap=5.0)
llm["target_modules"] = tuple(llm.get("target_modules", ())) or LLMConfig.target_modules
backend = LLMBackend(LLMConfig(**llm))
H = "/data0/home/zeyuwang/rsi/data"
d = CodeWorldModelDomain()
o, i = load_cruxeval(f"{H}/cruxeval-org__cruxeval/test.jsonl")
l = load_lcb_execution(f"{H}/livecodebench__execution-v2/data/test-00000-of-00001.parquet")
suites = {"cruxeval_o": (d, o), "cruxeval_i": (InputPredictionSuite(), i), "lcb_exec": (d, l)}
accepted = [json.loads(x) for x in open(run / "accepted.jsonl")]
last = accepted[-1]["node"]
versions = {"n0": Version("base", llm["base_path"], None)}
r = json.loads((run / f"ckpt-{last}" / "receipt.json").read_text())
versions[last] = Version(**r["version"])
out.mkdir(parents=True)
res = {}
for name, (suite, cases) in suites.items():
    recs = {k: suite.evaluate(backend, v, cases) for k, v in versions.items()}
    a = [x.score for x in recs["n0"]]; b = [x.score for x in recs[last]]
    res[name] = dict(initial=sum(a) / len(a), final=sum(b) / len(b), paired=paired_report(a, b))
    for k, rs in recs.items():
        with open(out / f"test-{name}-{k}.jsonl", "w") as s:
            for x in rs: s.write(json.dumps(asdict(x)) + "\n")
(out / "stage_result.json").write_text(json.dumps(dict(run=str(run), final_node=last, results=res), indent=2))
print(json.dumps({k: (round(v["initial"], 4), round(v["final"], 4), round(v["paired"]["mean_gain"], 4), [round(c, 4) for c in v["paired"]["ci95"]], v["paired"].get("mcnemar_p")) for k, v in res.items()}))
