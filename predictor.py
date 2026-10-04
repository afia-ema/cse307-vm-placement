"""Lightweight learned component: ridge regression on a VM's recent load history."""
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from sklearn.linear_model import Ridge

from .traces import Config, generate_trace


def _windows(L, cfg: Config):
    """Windows ending at t = 0..T-1 and their H-step-ahead targets.

    Returns X (n, T, W), y (n, T). Column j of L is time j - W, so the window that
    ends at time t covers columns t+1 .. t+W.
    """
    W, T, H = cfg.W, cfg.T, cfg.H
    win = sliding_window_view(L, W, axis=1)          # (n, n_cols - W + 1, W)
    X = win[:, 1:T + 1, :]                           # window ending at t = 0..T-1
    y = L[:, W + H: W + H + T]                       # load at t + H
    return X, y


def train_predictor(cfg: Config, n_train_traces: int = 40, seed0: int = 10_000, scenarios=("none",)):
    """Train a ridge model on synthetic traces (seeds disjoint from the test seeds 0..N).

    Default: traces WITHOUT any demand shift, so a later shift is out-of-distribution.
    Pass scenarios=("none","ramp","spike") for the shift-aware variant used in the ablation.
    """
    Xs, ys = [], []
    for k in range(n_train_traces):
        tr = generate_trace(cfg, seed0 + k, scenarios[k % len(scenarios)])
        X, y = _windows(tr["L"], cfg)
        mu = X.mean(axis=2, keepdims=True)
        Xs.append((X / mu).reshape(-1, cfg.W))       # scale-free features
        ys.append((y / mu[..., 0]).reshape(-1))
    model = Ridge(alpha=1.0)
    model.fit(np.vstack(Xs), np.concatenate(ys))
    return model


def predict_all(model, L, cfg: Config):
    """P[v, t] = predicted load of VM v at time t + H, using only data up to time t."""
    X, _ = _windows(L, cfg)
    mu = X.mean(axis=2, keepdims=True)
    ratio = model.predict((X / mu).reshape(-1, cfg.W)).reshape(X.shape[0], X.shape[1])
    return np.maximum(ratio * mu[..., 0], 0.0)


def persistence_all(L, cfg: Config):
    """Naive baseline: predict that the load stays at its latest value."""
    X, _ = _windows(L, cfg)
    return X[:, :, -1]


def target_all(L, cfg: Config):
    return _windows(L, cfg)[1]
