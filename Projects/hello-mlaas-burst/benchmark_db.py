#!/usr/bin/env python3
"""
benchmark_db.py — SQLite Performance Database & Feature Attribution for Hello MLaaS.

Records empirical benchmark runs comparing the 'Old Way' (Monolithic / Serial /
Disk-Pickling / No-Cache) against the 'New Way' (Flyte Macro-Caching + Ray Distributed
In-Memory Shared-Memory Compute).

Tracks both quantitative metrics (latencies, I/O, throughput, accuracy) and qualitative
feature attributions linking performance improvements to specific Ray and Flyte features.
"""

import os
import sqlite3
import datetime
from typing import Dict, List, Any, Optional

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "benchmark_metrics.db")


def init_db(db_path: str = DEFAULT_DB_PATH) -> str:
    """Creates the SQLite benchmark schema if it does not already exist."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 1. Quantitative Benchmark Runs Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pipeline_benchmarks (
        run_id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL,
        pipeline_type TEXT NOT NULL,         -- 'old_way_serial_disk', 'new_way_flyte_ray_cold', 'new_way_flyte_ray_cached'
        pipeline_description TEXT NOT NULL,
        num_samples INTEGER NOT NULL,
        num_workers INTEGER NOT NULL,
        data_prep_ms REAL NOT NULL,
        disk_io_ms REAL NOT NULL,
        training_ms REAL NOT NULL,
        eval_ms REAL NOT NULL,
        total_wall_time_ms REAL NOT NULL,
        io_bytes_mb REAL NOT NULL,
        throughput_samples_sec REAL NOT NULL,
        cache_status TEXT NOT NULL,          -- 'MISS', 'HIT', 'NO_CACHE_SUPPORT'
        cache_time_saved_ms REAL NOT NULL,
        r2_score REAL NOT NULL,
        mse REAL NOT NULL,
        speedup_factor REAL NOT NULL,        -- Baseline = 1.0x (old way)
        gpu_waste_percent REAL NOT NULL      -- % of total wall time GPU is idle/wasted if run monolithically on GPU VM
    );
    """)

    # 2. Qualitative & Quantitative Feature Attribution Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS feature_attribution (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        framework TEXT NOT NULL,             -- 'Flyte', 'Ray', or 'Flyte+Ray'
        feature_name TEXT NOT NULL,
        feature_category TEXT NOT NULL,      -- 'caching', 'data_movement', 'parallelism', 'resource_lifecycle', 'type_safety'
        technical_mechanism TEXT NOT NULL,
        empirical_impact TEXT NOT NULL,
        metric_improvement TEXT NOT NULL,
        FOREIGN KEY (run_id) REFERENCES pipeline_benchmarks (run_id)
    );
    """)

    # 3. Create indices for fast query lookups
    cur.execute("CREATE INDEX IF NOT EXISTS idx_bench_type ON pipeline_benchmarks(pipeline_type);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_feat_run ON feature_attribution(run_id);")

    conn.commit()
    conn.close()
    return db_path


def record_benchmark_run(
    metrics: Dict[str, Any],
    features: Optional[List[Dict[str, str]]] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> str:
    """Inserts a benchmark run and its associated feature attributions into SQLite."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO pipeline_benchmarks (
        run_id, timestamp, pipeline_type, pipeline_description,
        num_samples, num_workers, data_prep_ms, disk_io_ms,
        training_ms, eval_ms, total_wall_time_ms, io_bytes_mb,
        throughput_samples_sec, cache_status, cache_time_saved_ms,
        r2_score, mse, speedup_factor, gpu_waste_percent
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        metrics["run_id"],
        metrics.get("timestamp", datetime.datetime.now().isoformat()),
        metrics["pipeline_type"],
        metrics["pipeline_description"],
        metrics["num_samples"],
        metrics["num_workers"],
        round(metrics["data_prep_ms"], 2),
        round(metrics["disk_io_ms"], 2),
        round(metrics["training_ms"], 2),
        round(metrics["eval_ms"], 2),
        round(metrics["total_wall_time_ms"], 2),
        round(metrics["io_bytes_mb"], 3),
        round(metrics["throughput_samples_sec"], 1),
        metrics["cache_status"],
        round(metrics.get("cache_time_saved_ms", 0.0), 2),
        round(metrics["r2_score"], 6),
        round(metrics["mse"], 6),
        round(metrics["speedup_factor"], 2),
        round(metrics["gpu_waste_percent"], 1),
    ))

    if features:
        for f in features:
            cur.execute("""
            INSERT INTO feature_attribution (
                run_id, framework, feature_name, feature_category,
                technical_mechanism, empirical_impact, metric_improvement
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics["run_id"],
                f["framework"],
                f["feature_name"],
                f["feature_category"],
                f["technical_mechanism"],
                f["empirical_impact"],
                f["metric_improvement"],
            ))

    conn.commit()
    conn.close()
    return metrics["run_id"]


def get_latest_comparison(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Returns the latest runs for each pipeline type."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute("""
    SELECT 
        pipeline_type,
        pipeline_description,
        num_samples,
        num_workers,
        total_wall_time_ms,
        data_prep_ms,
        disk_io_ms,
        training_ms,
        eval_ms,
        io_bytes_mb,
        throughput_samples_sec,
        cache_status,
        speedup_factor,
        gpu_waste_percent,
        r2_score
    FROM pipeline_benchmarks
    ORDER BY timestamp DESC
    LIMIT 10
    """).fetchall()

    result = [dict(r) for r in rows]
    conn.close()
    return result


def get_feature_attributions(run_id: str, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieves all feature attributions linked to a specific benchmark run."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute("""
    SELECT framework, feature_name, feature_category, technical_mechanism, empirical_impact, metric_improvement
    FROM feature_attribution
    WHERE run_id = ?
    """, (run_id,)).fetchall()

    result = [dict(r) for r in rows]
    conn.close()
    return result
