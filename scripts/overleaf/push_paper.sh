#!/bin/bash
# Push paper files from paper/cvpr2027 to the Overleaf project and verify.
# usage: push_paper.sh <label> <files relative to paper/cvpr2027 ...>   e.g. sec/5_results.tex fig/fig_cost.pdf refs.bib
# sec/N_x.tex is pushed as sec_N_x.tex (Overleaf keeps the sections flat); fig/*.pdf and refs.bib keep their names.
# Refuses colleague files; stops if a file it would push was edited on Overleaf (pre-download differs from git HEAD).
set -u
label=$1; shift
H=$(dirname "$(realpath "$0")"); REPO=$(realpath "$H/../.."); R=$REPO/paper/cvpr2027; PRA=6aeb77eb783f7886443848c4
W=${OL_WORK:-/tmp/claude-1000/ol_push}/$label; mkdir -p "$W/pre" "$W/post" "$W/stage"
ol_name() { case $1 in sec/*) echo "sec_$(basename "$1")";; *) basename "$1";; esac; }
timeout 150 node "$H/ol_zip.js" $PRA "$W/pre.zip" > /dev/null 2>&1 && (cd "$W/pre" && unzip -o -q ../pre.zip) || { echo "pre download failed"; exit 1; }
# main.tex on Overleaf inputs sec_N.tex (flat), the repo's inputs sec/N.tex: compare and stage it in Overleaf form
to_ol() { if [ "$1" = main.tex ]; then sed 's#\\input{sec/#\\input{sec_#g'; else cat; fi; }
for f in "$@"; do
  n=$(ol_name "$f")
  case $n in fig_framework*|main.bib|rebuttal.tex|README.md) echo "REFUSED colleague file $n"; exit 1;; esac
  # the Overleaf copy must equal what git had before this change (i.e. nobody edited it there)
  if [ -e "$W/pre/$n" ] && ! cmp -s "$W/pre/$n" <(cd "$REPO" && git show "$(git log -n1 --format=%H -- paper/cvpr2027/$f)~1:paper/cvpr2027/$f" 2>/dev/null | to_ol "$f") \
       && ! cmp -s "$W/pre/$n" <(to_ol "$f" < "$R/$f"); then
    prev_ok=0; for c in $(cd "$REPO" && git log -n5 --format=%H -- "paper/cvpr2027/$f"); do cmp -s "$W/pre/$n" <(cd "$REPO" && git show "$c:paper/cvpr2027/$f" | to_ol "$f") && prev_ok=1; done
    [ $prev_ok = 1 ] || { echo "STOP: $n on Overleaf matches none of the last 5 git versions (edited there?)"; exit 2; }
  fi
  to_ol "$f" < "$R/$f" > "$W/stage/$n"
done
timeout 600 node "$H/ol_push.js" $PRA "$W/after.pdf" "$W"/stage/* 2>&1 | grep -E "overwrites|in tree|compile|saved|ERR|pdf" | cut -c1-160
timeout 150 node "$H/ol_zip.js" $PRA "$W/post.zip" > /dev/null 2>&1 && (cd "$W/post" && unzip -o -q ../post.zip) || { echo "post download failed"; exit 1; }
bad=0; for n in $(ls "$W/stage"); do cmp -s "$W/stage/$n" "$W/post/$n" && echo "$n pushed == repo" || { echo "$n MISMATCH"; bad=1; }; done
for n in 0_abstract 1_intro 2_related 3_method 4_setup 5_results 6_discussion 7_conclusion; do cmp -s "$R/sec/$n.tex" "$W/post/sec_$n.tex" || echo "sec_$n differs from repo"; done
ok=1; for n in fig_framework.pdf fig_framework_old.pdf fig_framework_old2.pdf main.bib rebuttal.tex README.md; do cmp -s "$W/pre/$n" "$W/post/$n" || { echo "COLLEAGUE FILE CHANGED: $n"; ok=0; }; done
diff -rq "$W/pre/sec" "$W/post/sec" > /dev/null || { echo "COLLEAGUE sec/ CHANGED"; ok=0; }; [ $ok = 1 ] && echo colleague-ok
for p in 8 9; do echo "overleaf page $p: $(pdftotext -f $p -l $p "$W/after.pdf" - 2>/dev/null | grep -n -m3 -E '^([0-9]\. (Future work|Conclusion)|References)' | tr '\n' ' ')"; done
first9=$(pdftotext -f 9 -l 9 "$W/after.pdf" - 2>/dev/null | grep -v -E '^[0-9]+$|^$|CVPR' | head -1)
echo "overleaf page 9 starts: $first9"
echo "$first9" | grep -qE '^(LLM Usage Statement|References)' || { echo "MAIN TEXT SPILLS ONTO PAGE 9"; exit 4; }
[ $bad = 0 ] && [ $ok = 1 ] || { echo "PUSH NOT VERIFIED"; exit 3; }
