# public_03_load: measured benchmark

One baseline and one controller run were completed on Python 3.12.10 / Windows. Commands were `python -m sim baseline --scenario scenarios/public_03_load.yaml --run-dir runs/base03`, then `python benchmark_load.py --port 8702`, followed by `python -m sim grade --run runs/mine03 --baseline runs/base03 --out reports/public_03_grade.md`. All run data and the controller database are ignored by Git. No repeated load run was used to tune outcomes.

| Measure | Observed |
|---|---:|
| Baseline generation wall time | 546.25 s |
| Controller-run simulator startup/history generation | 255.27 s |
| Controller wall time, including history ingestion and five live days | 1,135.78 s |
| Total controller-run wall time | 1,391.05 s |
| Controller wall time per simulated day (five-day amortized) | 227.16 s (3.79 min) |
| Total run wall time per simulated day (including startup) | 278.21 s (4.64 min) |
| Ingested calls / chunks | 7,433,295 / 88 |
| Ingest-only throughput, sum of chunk calls / sum of ingestion seconds | 13,958.47 calls/s |
| Final checkpoint / simulator | 87 / finished at five days |
| Peak simulator / controller process working set | 685,420,544 B / 37,896,192 B |
| Persisted controller SQLite database | 241,664 B |
| Simulator run directories, baseline / controller | 4,451,810,014 B / 4,451,877,539 B |

The host has **12 logical processors and 16,849,256,448 bytes physical RAM**. The process working-set peaks are separately sampled process values, not a container/cgroup maximum or a proof of total-system peak memory. The measured five-day average is below ten minutes per simulated day on this host, but **the 4-vCPU/8-GB target was not directly verified** because no such resource limit was imposed. Startup/history ingestion and individual late days were not timed separately, so the average cannot prove that *every* simulated day met the target. The baseline generation time is separate from the controller-run timing.

Official grading in `reports/public_03_grade.md`: aggregate conclusion rate 0.368, **+0.9%** relative to baseline; pickup +0.0%, engagement +0.8%; 16 applied changes, all neutral, **zero harmful**. Governance recorded 20 requests, 16 approvals, four ordinary approver declines, no auto applies, apply conflicts, lapses, or expiry. No incident was injected. This is a scale and hygiene result, not strong evidence of outcome lift; the current conservative experiment gate did not promote a winner in five days.

At larger scale, event transfer/JSON parsing and simulator generation dominate wall time, while SQLite stores only aggregate rows. The controller's single-process HTTP polling and SQLite single writer remain likely bottlenecks at substantially higher load. A production benchmark should constrain CPU/RAM, report per-day latency and backlog, and instrument both simulator and controller separately.
