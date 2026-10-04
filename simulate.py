"""Discrete-time VM placement simulator and the four placement policies."""
import numpy as np
from .traces import Config

POLICIES = ("first_fit", "best_fit", "best_fit_proactive", "predictive", "predictive_proactive")

PROACTIVE_TRIGGER = 0.95   # predicted host load (fraction of capacity) that triggers a proactive move
PROACTIVE_TARGET = 0.80    # destination must stay below this predicted fraction after the move
COOLDOWN = 10              # steps a VM is left alone after being proactively migrated


def _choose(policy, vm_m, host_m, limit, exclude=None, require_fit=False):
    """Pick a host for a VM whose decision-metric load is vm_m.

    first_fit : lowest-index host that fits
    best_fit* / predictive* : fitting host with the least remaining capacity
    Fallback (new VM only): the least loaded host, even if it cannot fit.
    """
    fits = host_m + vm_m <= limit
    if exclude is not None:
        fits[exclude] = False
    idx = np.flatnonzero(fits)
    if idx.size:
        if policy == "first_fit":
            return int(idx[0])
        return int(idx[np.argmax(host_m[idx])])
    if require_fit:
        return None
    m = host_m.copy()
    if exclude is not None:
        m[exclude] = np.inf
    return int(np.argmin(m))


def simulate(cfg: Config, trace: dict, P: np.ndarray, policy: str):
    """Run one policy on one trace.

    static policies decide with the CURRENT load of each VM (value at allocation time);
    predictive policies decide with max(current, predicted load at t+H) so they can
    anticipate growth.  Every policy also reacts to overload by migrating a VM away.
    """
    assert policy in POLICIES
    L, arrive, depart = trace["L"], trace["arrive"], trace["depart"]
    n, Hn, W, T, cap = cfg.n_vms, cfg.n_hosts, cfg.W, cfg.T, cfg.capacity
    predictive = policy in ("predictive", "predictive_proactive")
    # best_fit_proactive is an ablation: same proactive rebalancing, but driven by CURRENT load only
    proactive = policy in ("best_fit_proactive", "predictive_proactive")

    host_of = -np.ones(n, dtype=int)
    last_mig = np.full(n, -10**9)
    over = np.zeros(T); unserved = np.zeros(T); migs = np.zeros(T)
    proactive_migs = np.zeros(T); active = np.zeros(T); ustd = np.zeros(T)

    for t in range(T):
        cur = L[:, t + W]
        m = np.maximum(P[:, t], cur) if predictive else cur
        host_of[depart <= t] = -1                      # departures
        placed = host_of >= 0
        host_cur = np.bincount(host_of[placed], weights=cur[placed], minlength=Hn)
        host_m = np.bincount(host_of[placed], weights=m[placed], minlength=Hn)

        for v in np.flatnonzero(arrive == t):          # arrivals
            h = _choose(policy, m[v], host_m, cap)
            host_of[v] = h
            host_cur[h] += cur[v]; host_m[h] += m[v]

        # ---- measurement (before any migration at this step) ----
        placed = host_of >= 0
        counts = np.bincount(host_of[placed], minlength=Hn)
        occ = counts > 0
        util = host_cur / cap
        over[t] = (host_cur > cap).sum()
        unserved[t] = np.maximum(host_cur - cap, 0).sum()
        active[t] = occ.sum()
        ustd[t] = util[occ].std() if occ.sum() > 1 else 0.0

        # ---- reactive migration (all policies) ----
        for h in np.flatnonzero(host_cur > cap):
            for _ in range(n):
                if host_cur[h] <= cap:
                    break
                members = np.flatnonzero(host_of == h)
                excess = host_cur[h] - cap
                big = members[cur[members] >= excess]
                v = big[np.argmin(cur[big])] if big.size else members[np.argmax(cur[members])]
                d = _choose(policy, m[v], host_m, cap, exclude=h, require_fit=True)
                if d is None:
                    break
                host_of[v] = d
                host_cur[h] -= cur[v]; host_m[h] -= m[v]
                host_cur[d] += cur[v]; host_m[d] += m[v]
                migs[t] += 1; last_mig[v] = t

        # ---- proactive migration (predictive_proactive only) ----
        if proactive:
            for h in range(Hn):
                if host_cur[h] > cap or host_m[h] <= PROACTIVE_TRIGGER * cap:
                    continue
                members = np.flatnonzero((host_of == h) & (t - last_mig >= COOLDOWN))
                if members.size == 0:
                    continue
                need = host_m[h] - PROACTIVE_TRIGGER * cap
                big = members[m[members] >= need]
                v = big[np.argmin(m[big])] if big.size else members[np.argmax(m[members])]
                d = _choose(policy, m[v], host_m, PROACTIVE_TARGET * cap, exclude=h, require_fit=True)
                if d is None:
                    continue
                host_of[v] = d
                host_cur[h] -= cur[v]; host_m[h] -= m[v]
                host_cur[d] += cur[v]; host_m[d] += m[v]
                migs[t] += 1; proactive_migs[t] += 1; last_mig[v] = t

    return dict(over=over, unserved=unserved, migs=migs, proactive_migs=proactive_migs,
                active=active, ustd=ustd)
