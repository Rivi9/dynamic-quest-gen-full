"""
Statistical analysis pipeline for the narrative personalization study.

Expected CSV columns:
    participant_id   : str
    condition        : "Experimental" | "Control"
    geq_flow         : float  (mean of GEQ Flow subscale items, reverse-scored)
    geq_immersion    : float  (mean of GEQ Immersion subscale items)
    geq_positive_affect : float
    personalization  : float  (mean of NPS-3 items)
    minipxi_total    : float  (mean of all 11 miniPXI items)
    voluntary_npc    : int    (from backend telemetry)
    dialogue_read_ratio : float  (1 - dialogue_skipped/dialogue_shown)
    exploration_coverage : float  (tiles_explored / total_tiles)
"""
from __future__ import annotations

import pandas as pd
from scipy import stats
import pingouin as pg


PRIMARY_DV   = "geq_flow"
SECONDARY_DVS = [
    "geq_immersion",
    "personalization",
    "minipxi_total",
    "voluntary_npc",
    "dialogue_read_ratio",
    "exploration_coverage",
]
ALL_DVS = [PRIMARY_DV] + SECONDARY_DVS


def reverse_score(series: pd.Series, max_val: float = 4.0) -> pd.Series:
    """Reverse-score a Likert item: new = max - old."""
    return max_val - series


def compute_geq_subscales(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Compute GEQ subscale means from raw item columns.

    Expects columns: geq_item_1 … geq_item_33
    Returns DataFrame with subscale columns appended.
    """
    df = raw.copy()
    df["geq_flow"] = (
        reverse_score(df["geq_item_5"])
        + reverse_score(df["geq_item_13"])
        + df["geq_item_25"]
        + df["geq_item_28"]
        + df["geq_item_31"]
    ) / 5.0

    df["geq_immersion"] = df[
        ["geq_item_3", "geq_item_12", "geq_item_18",
         "geq_item_19", "geq_item_27", "geq_item_30"]
    ].mean(axis=1)

    df["geq_positive_affect"] = (
        df["geq_item_1"]
        + df["geq_item_4"]
        + reverse_score(df["geq_item_8"])
        + df["geq_item_20"]
        + df["geq_item_29"]
    ) / 5.0

    return df


def run_t_tests(df: pd.DataFrame) -> dict[str, dict]:
    """
    Run independent-samples Welch t-tests (unequal variances) for each DV.

    Returns dict keyed by DV name with t, p, Cohen's d, and group means.
    """
    results: dict[str, dict] = {}
    for dv in ALL_DVS:
        if dv not in df.columns:
            continue
        exp  = df[df["condition"] == "Experimental"][dv].dropna()
        ctrl = df[df["condition"] == "Control"][dv].dropna()

        if len(exp) < 2 or len(ctrl) < 2:
            results[dv] = {"error": "insufficient data", "significant": False}
            continue

        t, p = stats.ttest_ind(exp, ctrl, equal_var=False)  # Welch's t-test
        d    = pg.compute_effsize(exp, ctrl, eftype="cohen")

        results[dv] = {
            "t":          round(float(t), 3),
            "p":          round(float(p), 4),
            "cohen_d":    round(float(d), 3),
            "exp_mean":   round(float(exp.mean()), 3),
            "ctrl_mean":  round(float(ctrl.mean()), 3),
            "exp_sd":     round(float(exp.std(ddof=1)), 3),
            "ctrl_sd":    round(float(ctrl.std(ddof=1)), 3),
            "exp_n":      int(exp.count()),
            "ctrl_n":     int(ctrl.count()),
            "significant": p < 0.05,
        }
    return results


def check_normality(df: pd.DataFrame) -> dict[str, dict]:
    """
    Shapiro-Wilk normality test per DV per condition.
    N=25 per group satisfies Shapiro-Wilk validity (n < 50).
    """
    normality: dict[str, dict] = {}
    for dv in ALL_DVS:
        if dv not in df.columns:
            continue
        normality[dv] = {}
        for cond in ("Experimental", "Control"):
            subset = df[df["condition"] == cond][dv].dropna()
            stat, p = stats.shapiro(subset)
            normality[dv][cond] = {
                "W": round(float(stat), 4),
                "p": round(float(p), 4),
                "normal": p > 0.05,
            }
    return normality


def compute_cronbach_alpha(df: pd.DataFrame, items: list[str]) -> float:
    """
    Cronbach's alpha via the standard formula:
        α = (k / (k-1)) * (1 - Σvar_i / var_total)
    """
    item_df = df[items].dropna()
    k       = len(items)
    if k < 2:
        return float("nan")
    item_vars  = item_df.var(axis=0, ddof=1).sum()
    total_var  = item_df.sum(axis=1).var(ddof=1)
    if total_var == 0.0:
        return float("nan")
    return round(float((k / (k - 1)) * (1 - item_vars / total_var)), 3)


def print_results_table(results: dict[str, dict]) -> None:
    """Print a formatted APA-style results table to stdout."""
    header = f"{'DV':<28} {'Exp M (SD)':<16} {'Ctrl M (SD)':<16} {'t':<8} {'p':<8} {'d':<8} {'sig':<5}"
    print(header)
    print("-" * len(header))
    for dv, r in results.items():
        exp_str  = f"{r['exp_mean']:.2f} ({r['exp_sd']:.2f})"
        ctrl_str = f"{r['ctrl_mean']:.2f} ({r['ctrl_sd']:.2f})"
        sig      = "*" if r["significant"] else ""
        print(
            f"{dv:<28} {exp_str:<16} {ctrl_str:<16} "
            f"{r['t']:<8.3f} {r['p']:<8.4f} {r['cohen_d']:<8.3f} {sig:<5}"
        )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python stats_analysis.py <data.csv>")
        sys.exit(1)

    df = pd.read_csv(sys.argv[1])
    print(f"Loaded {len(df)} participants from {sys.argv[1]}\n")

    print("=== Normality Tests (Shapiro-Wilk) ===")
    normality = check_normality(df)
    for dv, conds in normality.items():
        for cond, r in conds.items():
            flag = "" if r["normal"] else " ← non-normal (p < .05)"
            print(f"  {dv} [{cond}]: W={r['W']}, p={r['p']}{flag}")

    print("\n=== Independent Samples t-Tests (Welch) ===")
    results = run_t_tests(df)
    print_results_table(results)

    print("\n=== Cronbach's Alpha — GEQ Subscales ===")
    geq_flow_items = ["geq_item_5", "geq_item_13", "geq_item_25", "geq_item_28", "geq_item_31"]
    geq_imm_items  = ["geq_item_3", "geq_item_12", "geq_item_18", "geq_item_19", "geq_item_27", "geq_item_30"]
    if all(c in df.columns for c in geq_flow_items):
        df_scored = df.copy()
        df_scored["geq_item_5_r"]  = 4.0 - df_scored["geq_item_5"]
        df_scored["geq_item_13_r"] = 4.0 - df_scored["geq_item_13"]
        geq_flow_items_scored = ["geq_item_5_r", "geq_item_13_r",
                                 "geq_item_25", "geq_item_28", "geq_item_31"]
        alpha_flow = compute_cronbach_alpha(df_scored, geq_flow_items_scored)
        alpha_imm  = compute_cronbach_alpha(df, geq_imm_items)
        print(f"  GEQ Flow subscale:      α = {alpha_flow}")
        print(f"  GEQ Immersion subscale: α = {alpha_imm}")
    else:
        print("  (GEQ raw item columns not found in CSV — skipping)")
