#!/bin/bash
# Event stream for a Monitor: new failure.json / round files / report files under cavin runs2 and runner launches/finishes.
# Prints only lines not seen before (state file $1, default /tmp/mon_cavin_seen.txt). Loops every 5 min.
seen=${1:-/tmp/mon_cavin_seen.txt}; touch "$seen"
while true; do
  out=$(timeout 60 ssh -o ConnectTimeout=20 cavin 'cd ~/rsi/runs2 && find . -maxdepth 2 -name failure.json -mmin -40 | grep -v -E "failed|void" | while read f; do echo "FAILURE $f $(head -c 200 $f | tr "\n" " ")"; done; find . -maxdepth 2 -name "round-*.json" -mmin -40 | while read f; do python3 -c "import json,sys; r=json.load(open(sys.argv[1])); cs=r.get(\"candidates\") or [{}]; print(\"ROUNDFILE\", sys.argv[1], \"accepted\", r.get(\"accepted\"), \"parent_gate\", r.get(\"parent_gate\"), \" \".join(\"%s:%s:gate=%s\" % (c.get(\"node\"), c.get(\"author\"), c.get(\"gate\")) for c in cs))" $f 2>&1 | tail -1; done; find . -maxdepth 2 \( -name report.json -o -name test_eval.json \) -mmin -40 | sed "s/^/NEWFILE /"; tail -n 8 ~/rsi/queue/runner.log | grep -E "finished|launched"' 2>/dev/null | sort -u)
  comm -13 "$seen" <(echo "$out") | grep -v '^$'
  echo "$out" > "$seen.new"; sort -u "$seen" "$seen.new" -o "$seen"
  sleep 300
done
