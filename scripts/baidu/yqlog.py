"""Full log of a Yangquan job (pages through DescribeJobLogs). usage: yqlog.py <job> [grep-regex] [tail-n]"""
import os, re, sys
os.environ.setdefault("AIHC_HOST", "aihc.yq.baidubce.com"); os.environ.setdefault("AIHC_POOL", "aihc-serverless")
os.environ.setdefault("AIHC_QUEUE", "aihcq-4yv1euenciip")
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import aihc_job
job = sys.argv[1]; pat = sys.argv[2] if len(sys.argv) > 2 else ""; n = int(sys.argv[3]) if len(sys.argv) > 3 else 15
lines, marker = [], None
for _ in range(40):
    st, out = aihc_job.logs(job, 1000, marker)
    if st != 200: print("HTTP", st, str(out)[:200]); break
    lines += [str(l).split(" F ", 1)[-1] for l in out.get("logs", [])]
    marker = out.get("nextMarker")
    if not marker: break
print("lines", len(lines))
sel = [l for l in lines if re.search(pat, l)] if pat else lines
print("\n".join(l[:230] for l in sel[-n:]))
