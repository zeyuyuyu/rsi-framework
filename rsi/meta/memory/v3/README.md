Memory of the meta level: records of finished runs of the same self-improvement loop.

prior/INDEX.tsv  one line per finished run: suite, who proposed procedures (fixed = nobody, replica = two copies of
                 the same procedure, numeric = blind search, llm = an earlier LLM meta level), the procedure the run
                 started from, rounds, candidates trained, candidates kept, the sum of the gate changes of the kept
                 candidates, the lowest gate of the run, and how the last kept procedure differs from the start.
prior/<run>.tsv  one line per candidate. gate: greedy success on that round's unseen gate scenes. parent_gate: the
                 parent policy on the same scenes. gate_change: gate - parent_gate. sampled_success_per_step: success
                 rate of the practice tries in each inner step (hundreds of tries each). mixed_share_per_step: share
                 of practice scenes with both outcomes. loss_first / loss_last: training loss at the first and last
                 step of the last update. changes_vs_parent: fields that differ from the parent's procedure.
Runs whose proposer is fixed and that kept every round are always-accept curves (no gate decision).
A kept candidate was the best child of its round and scored at least its parent; with gate noise of about 3 points
that happens by luck about half the time, so sum_gate_change_of_kept overstates the real gain of a run.
Nothing here holds a test result.
