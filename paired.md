| Scenario | Comparison | Mean change in post-shift overload events | Seeds improved / worse / tied | Mean change in post-shift migrations |
|---|---|---|---|---|
| none | Predictive best-fit vs Best-fit | -4.5 | 23 / 4 / 3 | -4.5 |
| none | Best-fit + proactive (no ML) vs Best-fit | -16.9 | 30 / 0 / 0 | +5.0 |
| none | Predictive + proactive vs Best-fit | -16.9 | 30 / 0 / 0 | +4.7 |
| none | Predictive + proactive vs Best-fit + proactive (no ML) | +0.0 | 0 / 0 / 30 | -0.3 |
| none | Predictive + proactive (shift-aware model) vs Best-fit + proactive (no ML) | +0.0 | 0 / 0 / 30 | +0.4 |
| ramp | Predictive best-fit vs Best-fit | -10.8 | 25 / 3 / 2 | -10.8 |
| ramp | Best-fit + proactive (no ML) vs Best-fit | -61.6 | 30 / 0 / 0 | -20.4 |
| ramp | Predictive + proactive vs Best-fit | -61.8 | 30 / 0 / 0 | -22.5 |
| ramp | Predictive + proactive vs Best-fit + proactive (no ML) | -0.2 | 9 / 7 / 14 | -2.1 |
| ramp | Predictive + proactive (shift-aware model) vs Best-fit + proactive (no ML) | -0.3 | 10 / 5 / 15 | -2.5 |
| spike | Predictive best-fit vs Best-fit | -5.0 | 23 / 5 / 2 | -5.6 |
| spike | Best-fit + proactive (no ML) vs Best-fit | -24.8 | 30 / 0 / 0 | +1.1 |
| spike | Predictive + proactive vs Best-fit | -25.1 | 30 / 0 / 0 | +1.8 |
| spike | Predictive + proactive vs Best-fit + proactive (no ML) | -0.3 | 12 / 6 / 12 | +0.6 |
| spike | Predictive + proactive (shift-aware model) vs Best-fit + proactive (no ML) | -0.6 | 14 / 7 / 9 | -0.1 |