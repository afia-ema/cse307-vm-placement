
### Scenario: none  (mean +/- std over 30 seeds)

| Policy | Overload events (pre) | Overload events (post) | Migrations (pre) | Migrations (post) | Util. std (post) | Active hosts (post) |
|---|---|---|---|---|---|---|
| First-fit | 48.7 +/- 7.8 | 14.0 +/- 5.4 | 48.7 +/- 7.8 | 14.0 +/- 5.4 | 0.254 +/- 0.026 | 7.25 |
| Best-fit | 59.9 +/- 10.2 | 16.9 +/- 6.1 | 59.9 +/- 10.2 | 16.9 +/- 6.1 | 0.271 +/- 0.026 | 7.26 |
| Best-fit + proactive (no ML) | 0.3 +/- 0.5 | 0.0 +/- 0.0 | 46.4 +/- 5.9 | 22.0 +/- 4.3 | 0.249 +/- 0.022 | 8.20 |
| Predictive best-fit | 40.8 +/- 7.2 | 12.4 +/- 4.7 | 40.8 +/- 7.2 | 12.4 +/- 4.7 | 0.279 +/- 0.029 | 7.39 |
| Predictive + proactive | 0.1 +/- 0.3 | 0.0 +/- 0.0 | 44.3 +/- 5.1 | 21.7 +/- 4.0 | 0.246 +/- 0.019 | 8.25 |
| Predictive + proactive (shift-aware model) | 0.1 +/- 0.3 | 0.0 +/- 0.0 | 45.1 +/- 4.8 | 22.4 +/- 4.2 | 0.245 +/- 0.024 | 8.10 |

### Scenario: ramp  (mean +/- std over 30 seeds)

| Policy | Overload events (pre) | Overload events (post) | Migrations (pre) | Migrations (post) | Util. std (post) | Active hosts (post) |
|---|---|---|---|---|---|---|
| First-fit | 48.7 +/- 7.8 | 41.7 +/- 10.5 | 48.7 +/- 7.8 | 41.7 +/- 10.5 | 0.214 +/- 0.034 | 9.25 |
| Best-fit | 59.9 +/- 10.2 | 62.4 +/- 15.1 | 59.9 +/- 10.2 | 62.4 +/- 15.1 | 0.229 +/- 0.031 | 9.19 |
| Best-fit + proactive (no ML) | 0.3 +/- 0.5 | 0.8 +/- 1.2 | 46.4 +/- 5.9 | 42.0 +/- 6.8 | 0.214 +/- 0.023 | 10.28 |
| Predictive best-fit | 40.8 +/- 7.2 | 51.6 +/- 12.9 | 40.8 +/- 7.2 | 51.6 +/- 12.9 | 0.219 +/- 0.031 | 9.10 |
| Predictive + proactive | 0.1 +/- 0.3 | 0.6 +/- 0.9 | 44.3 +/- 5.1 | 39.9 +/- 7.5 | 0.208 +/- 0.021 | 10.32 |
| Predictive + proactive (shift-aware model) | 0.1 +/- 0.3 | 0.5 +/- 1.1 | 45.1 +/- 4.8 | 39.4 +/- 6.2 | 0.204 +/- 0.026 | 10.22 |

### Scenario: spike  (mean +/- std over 30 seeds)

| Policy | Overload events (pre) | Overload events (post) | Migrations (pre) | Migrations (post) | Util. std (post) | Active hosts (post) |
|---|---|---|---|---|---|---|
| First-fit | 48.7 +/- 7.8 | 24.0 +/- 8.7 | 48.7 +/- 7.8 | 25.5 +/- 8.3 | 0.259 +/- 0.023 | 8.76 |
| Best-fit | 59.9 +/- 10.2 | 31.0 +/- 9.2 | 59.9 +/- 10.2 | 32.7 +/- 8.8 | 0.266 +/- 0.019 | 9.12 |
| Best-fit + proactive (no ML) | 0.3 +/- 0.5 | 6.2 +/- 7.4 | 46.4 +/- 5.9 | 33.8 +/- 6.0 | 0.235 +/- 0.023 | 9.98 |
| Predictive best-fit | 40.8 +/- 7.2 | 26.0 +/- 9.4 | 40.8 +/- 7.2 | 27.1 +/- 8.2 | 0.266 +/- 0.021 | 9.16 |
| Predictive + proactive | 0.1 +/- 0.3 | 5.9 +/- 7.4 | 44.3 +/- 5.1 | 34.4 +/- 7.0 | 0.234 +/- 0.019 | 9.98 |
| Predictive + proactive (shift-aware model) | 0.1 +/- 0.3 | 5.6 +/- 6.3 | 45.1 +/- 4.8 | 33.7 +/- 5.8 | 0.236 +/- 0.018 | 10.14 |