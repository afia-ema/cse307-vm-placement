"""Run all experiments: 3 workload scenarios x 6 policies x N seeds.

Usage:  python run_experiments.py [--seeds 30]
Outputs (in results/): raw.csv, summary.csv, summary.md, paired.md, prediction_error.csv,
                       fig1_overloads.png, fig2_timeline_ramp.png, fig3_prediction_error.png
"""
import argparse, os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.traces import Config, generate_trace, SCENARIOS
from src.predictor import train_predictor, predict_all, persistence_all, target_all
from src.simulate import simulate, POLICIES

OUT = "results"
ALL = POLICIES + ("predictive_proactive_aug",)   # last one = same policy, shift-aware predictor
LABEL = {"first_fit": "First-fit", "best_fit": "Best-fit", "best_fit_proactive": "Best-fit + proactive (no ML)",
         "predictive": "Predictive best-fit", "predictive_proactive": "Predictive + proactive",
         "predictive_proactive_aug": "Predictive + proactive (shift-aware model)"}
COLOR = {"first_fit": "#9aa0a6", "best_fit": "#4c78a8", "best_fit_proactive": "#b279a2",
         "predictive": "#f58518", "predictive_proactive": "#54a24b", "predictive_proactive_aug": "#e45756"}


def phase_metrics(res, cfg, phase):
    sl = slice(0, cfg.shift_t) if phase == "pre" else slice(cfg.shift_t, cfg.T)
    return {
        f"overload_events_{phase}": res["over"][sl].sum(),
        f"unserved_{phase}": res["unserved"][sl].sum(),
        f"migrations_{phase}": res["migs"][sl].sum(),
        f"util_std_{phase}": res["ustd"][sl].mean(),
        f"active_hosts_{phase}": res["active"][sl].mean(),
    }


def pred_error(trace, preds, cfg):
    """MAE of the H-step-ahead prediction for VMs whose demand shifts (alive VMs only).
    preds: dict name -> P matrix (n_vms, T)."""
    y = target_all(trace["L"], cfg)
    t = np.arange(cfg.T)[None, :]
    alive = (trace["arrive"][:, None] <= t) & (t < trace["depart"][:, None])
    sel = alive & trace["shifted"][:, None]
    out = {}
    for ph, lo, hi in (("pre", cfg.shift_t - cfg.H - 40, cfg.shift_t - cfg.H), ("post", cfg.shift_t, cfg.shift_t + 40)):
        mask = sel.copy(); mask[:, :lo] = False; mask[:, hi:] = False
        if mask.sum() == 0:
            continue
        for name, P in preds.items():
            out[f"{name}_mae_{ph}"] = np.abs(P - y)[mask].mean()
        out[f"mean_load_{ph}"] = y[mask].mean()
    return out


def main(n_seeds):
    os.makedirs(OUT, exist_ok=True)
    cfg = Config()
    model = train_predictor(cfg)                                                   # no-shift training data
    model_aug = train_predictor(cfg, seed0=20_000, scenarios=("none", "ramp", "spike"))  # shift-aware (ablation)
    print("ridge coef (oldest->newest):", np.round(model.coef_, 3))

    rows, perr, timelines = [], [], {}
    for sc in SCENARIOS:
        for seed in range(n_seeds):
            tr = generate_trace(cfg, seed, sc)
            P = predict_all(model, tr["L"], cfg)
            P_aug = predict_all(model_aug, tr["L"], cfg)
            perr.append(dict(scenario=sc, seed=seed, **pred_error(
                tr, {"ridge": P, "ridgeaug": P_aug, "persist": persistence_all(tr["L"], cfg)}, cfg)))
            for pol in ALL:
                aug = pol.endswith("_aug")
                res = simulate(cfg, tr, P_aug if aug else P, pol[:-4] if aug else pol)
                rows.append(dict(scenario=sc, policy=pol, seed=seed,
                                 **phase_metrics(res, cfg, "pre"), **phase_metrics(res, cfg, "post")))
                timelines.setdefault((sc, pol), []).append(res["over"])

    raw = pd.DataFrame(rows); raw.to_csv(f"{OUT}/raw.csv", index=False)
    pe = pd.DataFrame(perr); g = pe.groupby("scenario").mean().drop(columns="seed"); g.to_csv(f"{OUT}/prediction_error.csv")

    metrics = ["overload_events", "unserved", "migrations", "util_std", "active_hosts"]
    cols = [f"{m}_{p}" for p in ("pre", "post") for m in metrics]
    raw.groupby(["scenario", "policy"])[cols].agg(["mean", "std"]).to_csv(f"{OUT}/summary.csv")

    lines = []
    for sc in SCENARIOS:
        lines.append(f"\n### Scenario: {sc}  (mean +/- std over {n_seeds} seeds)\n")
        lines.append("| Policy | Overload events (pre) | Overload events (post) | Migrations (pre) | Migrations (post) | Util. std (post) | Active hosts (post) |")
        lines.append("|---|---|---|---|---|---|---|")
        for pol in ALL:
            d = raw[(raw.scenario == sc) & (raw.policy == pol)]
            f = lambda c, k=1: f"{d[c].mean():.{k}f} +/- {d[c].std():.{k}f}"
            lines.append(f"| {LABEL[pol]} | {f('overload_events_pre')} | {f('overload_events_post')} | "
                         f"{f('migrations_pre')} | {f('migrations_post')} | {f('util_std_post',3)} | {d['active_hosts_post'].mean():.2f} |")
    open(f"{OUT}/summary.md", "w").write("\n".join(lines))

    pl = ["| Scenario | Comparison | Mean change in post-shift overload events | Seeds improved / worse / tied | Mean change in post-shift migrations |", "|---|---|---|---|---|"]
    pairs = [("predictive", "best_fit"), ("best_fit_proactive", "best_fit"), ("predictive_proactive", "best_fit"),
             ("predictive_proactive", "best_fit_proactive"), ("predictive_proactive_aug", "best_fit_proactive")]
    for sc in SCENARIOS:
        for a, b_ in pairs:
            A = raw[(raw.scenario == sc) & (raw.policy == a)].set_index("seed")
            B = raw[(raw.scenario == sc) & (raw.policy == b_)].set_index("seed")
            d = A["overload_events_post"] - B["overload_events_post"]
            dm = A["migrations_post"] - B["migrations_post"]
            pl.append(f"| {sc} | {LABEL[a]} vs {LABEL[b_]} | {d.mean():+.1f} | {(d<0).sum()} / {(d>0).sum()} / {(d==0).sum()} | {dm.mean():+.1f} |")
    open(f"{OUT}/paired.md", "w").write("\n".join(pl))

    # ---- Fig 1: post-shift overloads ----
    fig, ax = plt.subplots(figsize=(7.4, 3.4)); w = 0.135
    for i, pol in enumerate(ALL):
        sub = [raw[(raw.scenario == sc) & (raw.policy == pol)].overload_events_post for sc in SCENARIOS]
        ax.bar(np.arange(3) + (i - 2.5) * w, [s.mean() for s in sub], w, yerr=[s.std() / np.sqrt(n_seeds) for s in sub],
               label=LABEL[pol], color=COLOR[pol], capsize=2)
    ax.set_xticks(range(3)); ax.set_xticklabels(["No shift", "Gradual ramp (persistent)", "Abrupt spike (60 steps)"])
    ax.set_ylabel("Overloaded host-steps, t >= 200"); ax.legend(fontsize=6.5, frameon=False)
    ax.set_title("SLA-violation events after the shift point (mean; error bar = s.e. over %d seeds)" % n_seeds, fontsize=9)
    fig.tight_layout(); fig.savefig(f"{OUT}/fig1_overloads.png", dpi=200); plt.close(fig)

    # ---- Fig 2: timeline in ramp scenario ----
    fig, ax = plt.subplots(figsize=(7.4, 3.1)); k = 8
    for pol in ("first_fit", "best_fit", "predictive", "best_fit_proactive", "predictive_proactive_aug"):
        sm = np.convolve(np.mean(timelines[("ramp", pol)], axis=0), np.ones(k) / k, mode="same")
        ax.plot(sm, label=LABEL[pol], color=COLOR[pol], lw=1.5)
    ax.axvline(cfg.shift_t, color="k", ls="--", lw=1); ax.text(cfg.shift_t + 3, ax.get_ylim()[1] * 0.9, "shift begins", fontsize=8)
    ax.set_xlabel("time step"); ax.set_ylabel("overloaded hosts (8-step avg)")
    ax.set_title("Gradual-ramp scenario: overloaded hosts over time (mean of %d seeds)" % n_seeds, fontsize=9)
    ax.legend(fontsize=6.5, frameon=False); fig.tight_layout(); fig.savefig(f"{OUT}/fig2_timeline_ramp.png", dpi=200); plt.close(fig)

    # ---- Fig 3: prediction error ----
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 2.8), sharey=True)
    meths = [("persist", "Persistence (last value)", "#9aa0a6"), ("ridge", "Ridge (no-shift training)", "#f58518"),
             ("ridgeaug", "Ridge (shift-aware training)", "#e45756")]
    for ax, ph, title in zip(axes, ("pre", "post"), ("40 steps before shift (targets unshifted)", "40 steps after t=200")):
        for i, (key, lab, col) in enumerate(meths):
            ax.bar(np.arange(3) + (i - 1) * 0.26, [g.loc[s, f"{key}_mae_{ph}"] for s in SCENARIOS], 0.26, label=lab, color=col)
        ax.set_xticks(range(3)); ax.set_xticklabels(["No shift", "Ramp", "Spike"]); ax.set_title(title, fontsize=9)
    axes[0].set_ylabel("MAE, 5-step-ahead load"); axes[0].legend(fontsize=6.5, frameon=False)
    fig.suptitle("Prediction error on the VMs whose demand shifts", fontsize=9); fig.tight_layout()
    fig.savefig(f"{OUT}/fig3_prediction_error.png", dpi=200); plt.close(fig)

    print(open(f"{OUT}/summary.md").read()); print(); print(open(f"{OUT}/paired.md").read())
    print("\nPrediction error (mean over seeds):\n", g.round(3).to_string())


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seeds", type=int, default=30)
    main(ap.parse_args().seeds)
