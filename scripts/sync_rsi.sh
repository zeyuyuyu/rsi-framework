#!/bin/bash
# Two-hourly results sync: small run records from cavin -> results/a800, Baidu logs -> results/baidu (if the log dir
# exists), recompute claims, refuse big files / secrets, commit + push. usage: sync_rsi.sh "<label>" [baidu_log_dir]
set -u
label=${1:-"Results sync $(date -u +%FT%H:%MZ)"}; logdir=${2:-}
cd /home/zeyu/rsi/rsi-framework || exit 1
inc=(--include='*/' --include='plan.json' --include='archive.jsonl' --include='accepted.jsonl' --include='round-[0-9][0-9].json' --include='report.json' --include='retained.json' --include='failure.json' --include='cancelled.json' --include='baseline*.json' --include='baseline*.jsonl' --include='backend-accounting.json' --include='receipt.json' --include='audit-rescore.json' --include='test-*.jsonl' --include='heldout_eval.json' --include='gate-*.jsonl' --include='audit-*.jsonl' --include='resume.json' --exclude='*')
timeout 900 rsync -az --prune-empty-dirs --exclude='*.work' --exclude='*.work/' --exclude='merged' --exclude='ckpt-*' --exclude='*-attempts-*' --exclude='*-cases-*' "${inc[@]}" cavin:/data0/home/zeyuwang/rsi/runs2/ results/a800/runs2/ && echo RSYNC_RUNS_OK || echo RSYNC_RUNS_FAIL
timeout 300 rsync -az --include='*.json' --exclude='*' cavin:/data0/home/zeyuwang/rsi/plans2/ results/a800/plans2/ && echo RSYNC_PLANS_OK || echo RSYNC_PLANS_FAIL
if [ -n "$logdir" ] && [ -d "$logdir" ]; then bash scripts/baidu/collect_yq.sh "$logdir" 80 | tail -n 3; python3 scripts/baidu/extract_results.py "$logdir" results/baidu >/dev/null && echo EXTRACT_OK; else echo "EXTRACT_SKIPPED (no log dir)"; fi
for suite in goal spatial l10; do python -m rsi.audit.compare_arms results --suite $suite --json results/claims_$suite.json >/dev/null 2>&1 && echo "claims_$suite ok" || echo "claims_$suite skipped"; done
big=$(find results -type f -size +5M | head); echo "big: $big"; [ -n "$big" ] && { echo "ABORT big files"; exit 2; }
sec=$(git diff --cached --name-only; git ls-files --others --exclude-standard results | xargs -r grep -lE "(ATATT|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{12,}|bce-auth|BEGIN [A-Z ]*PRIVATE KEY)" 2>/dev/null | head); echo "secrets: $sec"; [ -n "$sec" ] && { echo "ABORT secrets"; exit 3; }
git add results && n=$(git diff --cached --name-only | wc -l) && echo "changed files: $n"
if [ "$n" -gt 0 ]; then git commit -q -m "Sync run records (A800 + Baidu, $label)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" && git log --oneline -1; fi
for i in 1 2 3; do git push origin main 2>&1 | tail -1 && break; sleep 20; done; git status -sb | head -1
