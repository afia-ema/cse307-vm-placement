# Learning-Augmented OS Heuristics - Track 4: Predictive VM Placement

CSE-307 Operating Systems, Term Paper (Section B). Individual work.

Static bin-packing placement (first-fit, best-fit) decides where a VM goes using its load **at allocation time**.
This project adds a lightweight regression model that predicts each VM's near-future load, uses it to place VMs
proactively, and studies what happens when the workload **shifts partway through** the run.

## Setup and run

```bash
python -m venv .venv && source .venv/bin/activate     # optional
pip install -r requirements.txt
python run_experiments.py --seeds 30                  # takes ~15 seconds; writes everything in results/
```

Python 3.10+ (developed on 3.12; numpy 2.x, scikit-learn 1.8). All randomness is seeded: re-running reproduces the tables exactly.

## Repository layout

| Path | Contents |
|---|---|
| `src/traces.py` | Synthetic multi-VM load generator + the three shift scenarios (`none`, `ramp`, `spike`) |
| `src/predictor.py` | Ridge-regression load predictor (features: last 10 load samples; target: load 5 steps ahead) |
| `src/simulate.py` | Discrete-time simulator and the placement/migration policies |
| `run_experiments.py` | Runs 3 scenarios x 6 policies x 30 seeds, writes tables and figures |
| `results/` | `summary.md` (main table), `paired.md` (paired comparisons), `prediction_error.csv`, `raw.csv`, `fig1-3 *.png` |


## What is implemented

**Classical algorithms** (static, decide with the VM's current load):
* *First-fit* - lowest-index host that fits.
* *Best-fit* - fitting host with the least remaining capacity.

**Common to every policy:** if a host's load exceeds its capacity (an *overload* = SLA violation for that host-step),
one VM is migrated away (smallest VM that cures the overload, else the largest) to a host that fits.

**Learned / adaptive layer**
* *Predictive best-fit* - best-fit, but every VM is represented by `max(current, predicted load at t+5)`, so a host whose VMs are trending up looks fuller. Also used to choose migration targets.
* *Predictive + proactive* - additionally migrates a VM *before* overload when a host's predicted load exceeds 95% of capacity (destination must stay under 80%; 10-step cool-down per VM).
* *Best-fit + proactive (no ML)* - **ablation**: the same proactive rebalancing but driven by current load only. It isolates what the learned model contributes.
* *Predictive + proactive (shift-aware model)* - same policy, but the model was also trained on shifted traces. Tests whether the model's weakness under shift is a training-distribution problem.

The model is `sklearn.linear_model.Ridge` trained on 40 synthetic traces **without any shift** (seeds 10000+, disjoint from the test seeds 0-29), so the later shift is out-of-distribution for it.

## Experimental design

* 12 hosts x 100 CPU units; 100 VMs arrive/depart over 400 steps (40 present at t=0); baseline load 8-18 units + slow sinusoid + AR(1) noise.
* **Shift at t = 200** hits a random 40% of VMs, multiplying their demand by U(1.8, 2.6):
  * `ramp` - demand climbs linearly over 20 steps and **stays** high (persistent demand shift);
  * `spike` - demand jumps instantly and returns to normal after 60 steps (abrupt, transient);
  * `none` - control.
* For a given seed the three scenarios share all random draws except the shift, so policy comparisons are **paired**.
* Metrics (before / after t = 200): overloaded host-steps, number of migrations, utilization balance (std of host utilization over non-empty hosts), mean active hosts, and the predictor's MAE vs a "last value" baseline.

### Assumptions to be aware of
* **A1.** A newly arriving VM has 10 steps of earlier monitoring history available (e.g. from a profile or earlier deployment), so the predictor can be applied at placement time.
* **A2.** The predictive policies use `max(current, predicted)`. This is also a conservative safety margin, so part of their advantage over plain best-fit may come from headroom rather than from forecasting accuracy. The ablation controls for proactive migration but not for headroom - listed as a limitation in the report.
* **A3.** Migration is instantaneous and free except that it is counted; no migration-cost model.

## Headline results (ramp scenario, mean of 30 seeds, post-shift)

| Policy | Overloaded host-steps | Migrations | Active hosts |
|---|---|---|---|
| First-fit | 41.7 | 41.7 | 9.25 |
| Best-fit | 62.4 | 62.4 | 9.19 |
| Predictive best-fit | 51.6 | 51.6 | 9.10 |
| Best-fit + proactive (no ML) | 0.8 | 42.0 | 10.28 |
| Predictive + proactive | 0.6 | 39.9 | 10.32 |

Full tables for all scenarios: `results/summary.md`, `results/paired.md`. Discussion is in the report.

## AI-assistance disclosure

An AI assistant (Claude, Anthropic) was used to help write and debug the implementation code and to draft the report.

