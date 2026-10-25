"""Paired statistics for initial-vs-final comparisons on identical test cases."""

import math
import random


def paired_bootstrap(a, b, direction=1, resamples=10000, seed=0):
    """95% CI of mean(direction*(b - a)) by resampling cases."""
    if len(a) != len(b) or not a:
        raise ValueError("paired_lengths")
    diffs = [direction * (y - x) for x, y in zip(a, b)]
    rng = random.Random(seed)
    n = len(diffs)
    means = sorted(sum(diffs[rng.randrange(n)] for _ in range(n)) / n
                   for _ in range(resamples))
    return means[int(0.025 * resamples)], means[int(0.975 * resamples) - 1]


def mcnemar_exact(a, b):
    """Two-sided exact McNemar p-value for binary paired outcomes."""
    gain = sum(1 for x, y in zip(a, b) if x < 0.5 <= y)
    loss = sum(1 for x, y in zip(a, b) if y < 0.5 <= x)
    n = gain + loss
    if n == 0:
        return 1.0, gain, loss
    k = min(gain, loss)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail), gain, loss


def paired_report(a, b, direction=1, seed=0):
    diff = sum(direction * (y - x) for x, y in zip(a, b)) / len(a)
    low, high = paired_bootstrap(a, b, direction, seed=seed)
    report = dict(n=len(a), mean_gain=diff, ci95=[low, high],
                  ci_excludes_zero=low > 0 or high < 0)
    if all(x in (0, 1, 0.0, 1.0) for x in list(a) + list(b)):
        p, gain, loss = mcnemar_exact(a, b)
        report.update(mcnemar_p=p, flipped_to_correct=gain, flipped_to_wrong=loss)
    return report
