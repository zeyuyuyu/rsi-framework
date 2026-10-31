"""Turning verified attempts into training items, and the feedback-removal control.

``exclude_flag`` (optional) drops cases whose ``inputs[flag]`` is true before
any rule applies, e.g. answers that are cheap to guess.

Rules (chosen by the improvement program):
  * ``verified``     - keep verified attempts only, <= ``per_case`` per case,
                       hardest still-solvable cases first (ReST-EM / expert iteration);
  * ``mixed_groups`` - keep every attempt of cases whose verified rate lies strictly
                       inside ``band``; each item carries a group-relative advantage
                       (reward minus case mean; divided by the case std when ``adv`` is
                       "zscore"). Uniform groups carry no signal.
The control ``feedback="shuffled"`` permutes rewards/verification *within each
case* before curation: same counts, same structure, no information from the
oracle. It applies to every rule, so "does external feedback matter" is tested
identically for every update operator.
"""

import random
from dataclasses import replace


def shuffle_feedback(attempts, rng: random.Random):
    out = []
    for tries in attempts:
        labels = [(a.reward, a.verified) for a in tries]
        rng.shuffle(labels)
        out.append([replace(a, reward=r, verified=v) for a, (r, v) in zip(tries, labels)])
    return out


def curate(cases, attempts, rule: dict, rng: random.Random):
    if len(cases) != len(attempts):
        raise ValueError("attempt_denominator_mismatch")
    for case, tries in zip(cases, attempts):
        if not tries or any(a.case_id != case.id for a in tries):
            raise ValueError("attempt_case_mismatch")
    name = rule.get("rule", "verified")
    budget = int(rule.get("budget", 2000))
    lo, hi = rule.get("band", [0.0, 1.0])
    flag = rule.get("exclude_flag")
    if flag:
        keep = [i for i, c in enumerate(cases)
                if not (isinstance(c.inputs, dict) and c.inputs.get(flag))]
        excluded = len(cases) - len(keep)
        cases = [cases[i] for i in keep]
        attempts = [attempts[i] for i in keep]
    rates = [sum(a.verified for a in tries) / len(tries) for tries in attempts]
    stats = dict(rule=name, cases=len(cases), attempts=sum(len(t) for t in attempts),
                 verified_attempts=sum(a.verified for t in attempts for a in t),
                 mixed_cases=sum(0 < r < 1 for r in rates),
                 solved_cases=sum(r > 0 for r in rates))
    items, item_cases = [], []
    if name == "verified":
        per_case = int(rule.get("per_case", 2))
        order = sorted(range(len(cases)), key=lambda i: (rates[i], cases[i].id))
        for i in order:
            if rates[i] <= 0 or not lo <= rates[i] <= hi:
                continue
            for a in [a for a in attempts[i] if a.verified][:per_case]:
                if len(items) < budget:
                    items.append(a.experience)
                    item_cases.append(cases[i].id)
    elif name == "mixed_groups":
        eligible = [i for i in range(len(cases)) if lo < rates[i] < hi]
        rng.shuffle(eligible)
        zscore = rule.get("adv", "center") == "zscore"     # addendum 16 harness component
        for i in eligible[:budget]:
            rewards = [a.reward for a in attempts[i]]
            mean = sum(rewards) / len(rewards)
            sd = (sum((r - mean) ** 2 for r in rewards) / len(rewards)) ** 0.5
            for a in attempts[i]:
                adv = (a.reward - mean) / (sd + 1e-6) if zscore else a.reward - mean
                items.append(dict(experience=a.experience, advantage=adv))
                item_cases.append(cases[i].id)
    else:
        raise ValueError(f"unknown_curation_rule:{name}")
    stats.update(items=len(items), item_cases=len(set(item_cases)),
                 excluded_by_flag=excluded if flag else 0)
    return items, item_cases, stats
