# public_03_load benchmark

Status: **not run**. No throughput, peak memory, decision lag, simulated-day wall-clock time, or official grading metric is available. The current terminal resolves neither `python` nor an installed runtime through `py -0p`; access to the Python executable under the user's AppData directory is denied. The 4-vCPU/8-GB and ten-minutes-per-simulated-day targets are therefore unverified.

The controller records per-chunk call counts and ingest time in `ingest_metrics` when run. The reproducible sequence, once Python is available, is:

```bash
python -m sim baseline --scenario scenarios/public_03_load.yaml --run-dir runs/base03
python -m sim serve --scenario scenarios/public_03_load.yaml --run-dir runs/mine03
FORMI_DB=state/mine03.sqlite3 /usr/bin/time -v ./run.sh http://127.0.0.1:8700
python -m sim grade --run runs/mine03 --baseline runs/base03 --out reports/public_03_grade.md
```

Use a clean run directory and database. Do not start the benchmark until smaller tests pass; run it only once. On Linux, record `/usr/bin/time -v` maximum resident set and wall time, the simulator's `end_minute`, and `SELECT SUM(calls)/SUM(elapsed_s) FROM ingest_metrics` for ingest-only throughput. End-to-end time includes simulator generation and HTTP transfer. Record actual CPU count and memory limit alongside the result before comparing against the target.
