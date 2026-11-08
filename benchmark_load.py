"""Run one isolated public_03 controller benchmark; refuse to overwrite evidence."""
import argparse
import ctypes
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import httpx


class MemoryCounters(ctypes.Structure):
    _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                ("PrivateUsage", ctypes.c_size_t)]


def memory_bytes(process):
    if os.name != "nt":
        return None
    counters = MemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    if ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.c_void_p(process._handle),
                                                ctypes.byref(counters), counters.cb):
        return counters.PeakWorkingSetSize
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", default="runs/mine03")
    parser.add_argument("--db", default="state/mine03.sqlite3")
    parser.add_argument("--port", type=int, default=8702)
    args = parser.parse_args()
    run_dir, db_path = Path(args.run_dir), Path(args.db)
    if run_dir.exists() or db_path.exists():
        raise SystemExit("Refusing to overwrite a run or database; choose fresh paths")
    run_dir.parent.mkdir(parents=True, exist_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    url = f"http://127.0.0.1:{args.port}"
    client = httpx.Client(base_url=url, timeout=10)
    start = time.monotonic()
    server = subprocess.Popen([sys.executable, "-m", "sim", "serve", "--scenario",
                               "scenarios/public_03_load.yaml", "--run-dir", str(run_dir),
                               "--port", str(args.port)], stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)
    controller = None
    server_peak = controller_peak = 0
    try:
        deadline = start + 1200
        while time.monotonic() < deadline:
            if server.poll() is not None:
                raise RuntimeError(f"simulator exited {server.returncode} during startup")
            try:
                if client.get("/health").status_code == 200:
                    break
            except httpx.TransportError:
                pass
            server_peak = max(server_peak, memory_bytes(server) or 0)
            time.sleep(0.25)
        else:
            raise TimeoutError("simulator startup exceeded 20 minutes")
        ready = time.monotonic()
        controller = subprocess.Popen([sys.executable, "controller.py", url, "--db", str(db_path)],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        while controller.poll() is None:
            server_peak = max(server_peak, memory_bytes(server) or 0)
            controller_peak = max(controller_peak, memory_bytes(controller) or 0)
            time.sleep(0.25)
        _, stderr = controller.communicate()
        done = time.monotonic()
        server_peak = max(server_peak, memory_bytes(server) or 0)
        state = client.get("/sim/state").json()
        with sqlite3.connect(db_path) as db:
            chunks, calls, ingest_s = db.execute(
                "SELECT COUNT(*), COALESCE(SUM(calls),0), COALESCE(SUM(elapsed_s),0) FROM ingest_metrics"
            ).fetchone()
            checkpoint = db.execute("SELECT v FROM checkpoint WHERE k='chunk'").fetchone()
        result = {"cpu_count_host": os.cpu_count(), "startup_wall_s": round(ready-start, 2),
                  "controller_wall_s": round(done-ready, 2), "total_wall_s": round(done-start, 2),
                  "simulated_days": state["sim_minute"]/1440,
                  "controller_s_per_simulated_day": round((done-ready)/(state["sim_minute"]/1440), 2),
                  "peak_server_working_set_bytes": server_peak or None,
                  "peak_controller_working_set_bytes": controller_peak or None,
                  "ingested_chunks": chunks, "ingested_calls": calls,
                  "ingest_only_calls_per_s": round(calls/ingest_s, 2) if ingest_s else None,
                  "checkpoint": checkpoint[0] if checkpoint else None,
                  "finished": state["finished"], "controller_exit": controller.returncode,
                  "stderr_tail": stderr[-1000:]}
        print(json.dumps(result, indent=2), flush=True)
        if controller.returncode or not state["finished"]:
            raise SystemExit(1)
    finally:
        if controller and controller.poll() is None:
            controller.kill()
            controller.wait()
        server.terminate()
        server.wait(timeout=30)


if __name__ == "__main__":
    main()
