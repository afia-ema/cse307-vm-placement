"""Synthetic multi-VM load traces with a deliberate demand shift partway through."""
from dataclasses import dataclass
import numpy as np


@dataclass
class Config:
    T: int = 400            # simulated time steps
    n_vms: int = 100        # total VMs that ever arrive
    n_init: int = 40        # VMs already present at t = 0
    n_hosts: int = 12
    capacity: float = 100.0 # CPU units per host
    W: int = 10             # history window fed to the predictor
    H: int = 5              # prediction horizon (steps ahead)
    shift_t: int = 200      # time at which the workload shifts
    shift_frac: float = 0.4 # fraction of VMs whose demand shifts
    ramp_len: int = 20      # 'ramp' scenario: steps to reach new demand level
    spike_len: int = 60     # 'spike' scenario: how long the spike lasts
    mult_lo: float = 1.8    # shifted VMs' demand multiplier ~ U(mult_lo, mult_hi)
    mult_hi: float = 2.6


SCENARIOS = ("none", "ramp", "spike")


def generate_trace(cfg: Config, seed: int, scenario: str = "ramp"):
    """Return a dict with the load matrix and VM lifetimes.

    L has shape (n_vms, W + T + H). Column j is the load at time t = j - W, so the
    first W columns are pre-arrival monitoring history (see README, assumption A1)
    and the last H columns let us score H-step-ahead predictions at t = T-1.

    All random draws are independent of `scenario`, so for a given seed the three
    scenarios differ ONLY in the shift -> paired comparisons are valid.
    """
    assert scenario in SCENARIOS
    rng = np.random.default_rng(seed)
    n, W, T, H = cfg.n_vms, cfg.W, cfg.T, cfg.H
    n_cols = W + T + H
    t = np.arange(n_cols) - W

    base = rng.uniform(8, 18, n)
    amp = 0.15 * base
    period = rng.uniform(60, 140, n)
    phase = rng.uniform(0, 2 * np.pi, n)

    # AR(1) noise
    eps = rng.normal(0, 0.05, (n, n_cols)) * base[:, None]
    noise = np.zeros((n, n_cols))
    for j in range(1, n_cols):
        noise[:, j] = 0.8 * noise[:, j - 1] + eps[:, j]

    load = base[:, None] + amp[:, None] * np.sin(2 * np.pi * t[None, :] / period[:, None] + phase[:, None]) + noise
    load = np.maximum(load, 0.5)

    # lifetimes
    arrive = np.zeros(n, dtype=int)
    arrive[cfg.n_init:] = rng.integers(1, 350, n - cfg.n_init)
    life = rng.integers(120, 260, n)
    depart = np.minimum(cfg.T, arrive + life)

    # shift definition (drawn always, applied depending on scenario)
    shifted = rng.random(n) < cfg.shift_frac
    mult = rng.uniform(cfg.mult_lo, cfg.mult_hi, n)

    m = np.ones((n, n_cols))
    if scenario == "ramp":      # persistent, gradual demand shift
        frac = np.clip((t - cfg.shift_t) / cfg.ramp_len, 0, 1)
        m = 1 + (mult[:, None] - 1) * frac[None, :]
    elif scenario == "spike":   # abrupt, temporary spike
        on = (t >= cfg.shift_t) & (t < cfg.shift_t + cfg.spike_len)
        m = np.where(on[None, :], mult[:, None], 1.0)
    m = np.where(shifted[:, None], m, 1.0)
    load = load * m

    return dict(L=load, arrive=arrive, depart=depart, shifted=shifted, scenario=scenario)
