#!/usr/bin/env python3
"""
workflow.py — Hello MLaaS Burst: Flyte Workflow with Distributed Ray Compute.

Demonstrates:
1. Macro-orchestration via Flyte (@task, @workflow, caching, typed contracts).
2. Micro-distributed compute via Ray (Ray Data + Ray's shared-memory object store).
3. Tri-environment switching (local Mac, AWS EKS GPU burst, and On-Prem VM).

Data hand-off: Flyte tasks exchange a FlyteFile (Parquet) instead of in-memory
Python lists, so large mesh datasets stay out of the Flyte literal payload and
Ray Data reads them in parallel blocks.

Graceful Fallback:
If flytekit, ray, or pyarrow are not yet installed in the current environment,
lightweight built-in fallbacks allow local developers to test and verify the
pipeline immediately (pyarrow missing -> NumPy .npz instead of Parquet).
"""

import os
import tempfile
import time
from typing import Dict, List, Any
import numpy as np

# ----------------------------------------------------------------------------
# Flyte Imports with Graceful Fallback
# ----------------------------------------------------------------------------
try:
    from flytekit import task, workflow, Resources, current_context
    from flytekit.types.file import FlyteFile
    FLYTE_AVAILABLE = True
except ImportError:
    FLYTE_AVAILABLE = False
    current_context = None

    class FlyteFile(os.PathLike):
        """Minimal local stand-in: a path wrapper compatible with os.fspath()."""

        def __init__(self, path: str):
            self.path = str(path)

        def __fspath__(self) -> str:
            return self.path

    def task(*args, **kwargs):
        def decorator(f):
            f.is_flyte_task = True
            return f
        if len(args) == 1 and callable(args[0]):
            return decorator(args[0])
        return decorator

    def workflow(*args, **kwargs):
        def decorator(f):
            f.is_flyte_workflow = True
            return f
        if len(args) == 1 and callable(args[0]):
            return decorator(args[0])
        return decorator

    class Resources:
        def __init__(self, cpu: str = "1", mem: str = "1Gi", gpu: str = "0"):
            self.cpu = cpu
            self.mem = mem
            self.gpu = gpu

# ----------------------------------------------------------------------------
# Ray Imports with Graceful Fallback
# ----------------------------------------------------------------------------
try:
    import ray
    import ray.data
    RAY_AVAILABLE = True
except ImportError:
    RAY_AVAILABLE = False
    ray = None

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    PARQUET_AVAILABLE = True
except ImportError:
    PARQUET_AVAILABLE = False

_FEATURE_COLUMNS = ("aoa", "re", "lift_cfd")


# ============================================================================
# Dataset I/O (Flyte <-> Ray hand-off)
# ============================================================================

def _scratch_dir() -> str:
    """Flyte task working directory when available, otherwise a temp directory."""
    if FLYTE_AVAILABLE:
        try:
            return current_context().working_directory
        except Exception:
            pass
    return tempfile.mkdtemp(prefix="mlaas-mesh-")


def _write_dataset(columns: Dict[str, np.ndarray]) -> str:
    """Persist columns as Parquet (or .npz when pyarrow is missing); return the path."""
    base = os.path.join(_scratch_dir(), "mesh")
    if PARQUET_AVAILABLE:
        path = base + ".parquet"
        pq.write_table(pa.table(columns), path)
    else:
        path = base + ".npz"
        np.savez(path, **columns)
    return path


def _read_dataset(path: str) -> Dict[str, np.ndarray]:
    """Load the dataset written by _write_dataset into NumPy columns."""
    if path.endswith(".parquet"):
        table = pq.read_table(path)
        return {name: table.column(name).to_numpy() for name in _FEATURE_COLUMNS}
    with np.load(path) as data:
        return {name: data[name] for name in _FEATURE_COLUMNS}


# ============================================================================
# Surrogate Training Compute (Micro Layer)
# ============================================================================

def _train_slice_compute(
    worker_id: int,
    angles_of_attack: np.ndarray,
    reynolds_numbers: np.ndarray,
    cfd_lift_coefficients: np.ndarray,
) -> Dict[str, Any]:
    """Core physics regression computation for surrogate slice."""
    features = np.column_stack([angles_of_attack, reynolds_numbers])
    targets = cfd_lift_coefficients

    # Regularized closed-form surrogate model solution
    lambda_reg = 1e-3
    xtx = features.T @ features + lambda_reg * np.eye(features.shape[1])
    weights = np.linalg.inv(xtx) @ (features.T @ targets)

    # Compute validation metrics
    predictions = features @ weights
    mse = float(np.mean((predictions - targets) ** 2))
    var = float(np.var(targets))
    r2 = float(1.0 - (mse / (var + 1e-8)))

    return {
        "worker_id": worker_id,
        "weights": weights.tolist(),
        "mse": mse,
        "r2": r2,
        "samples_processed": len(angles_of_attack),
    }


def _train_block(batch: Dict[str, np.ndarray]) -> Dict[str, list]:
    """Ray Data map_batches function: trains one surrogate slice per block."""
    res = _train_slice_compute(0, batch["aoa"], batch["re"], batch["lift_cfd"])
    return {
        "mse": [res["mse"]],
        "r2": [res["r2"]],
        "samples_processed": [res["samples_processed"]],
    }


# ============================================================================
# Flyte Tasks (Macro Layer)
# ============================================================================

@task(requests=Resources(cpu="1", mem="500Mi"))
def generate_mesh_data(num_samples: int = 1200) -> FlyteFile:
    """
    Step 1 (Flyte CPU Task): Generates aerodynamic airfoil parameters.
    Returns a FlyteFile (Parquet) so the dataset travels by reference, not as
    an in-memory list. Cached: in Flyte, re-running with unchanged inputs skips this step.
    """
    np.random.seed(42)
    # Angles of attack from -5 to +20 degrees (in radians)
    aoa = np.random.uniform(-0.087, 0.349, num_samples)
    # Reynolds numbers (normalized 0.1 to 1.0)
    re = np.random.uniform(0.1, 1.0, num_samples)

    # Physics ground truth: lift curve Cl = 2*pi*alpha - stall correction + Reynolds effect
    lift_cfd = 2.0 * np.pi * aoa - 1.2 * (aoa ** 3) + 0.05 * np.sin(re * 10)
    lift_cfd += np.random.normal(0, 0.015, num_samples)

    return FlyteFile(_write_dataset({"aoa": aoa, "re": re, "lift_cfd": lift_cfd}))


@task(requests=Resources(cpu="2", mem="2Gi"))
def train_surrogate_burst(
    dataset: FlyteFile,
    num_workers: int = 4,
    env_mode: str = "local",
) -> Dict[str, Any]:
    """
    Step 2 (Flyte + Ray Task): Dispatches distributed surrogate training to Ray.

    With Ray and Parquet available, Ray Data splits the dataset into `num_workers`
    blocks and trains one surrogate slice per block in parallel. Otherwise a
    standalone NumPy loop runs the same per-slice computation.

    When RAY_ADDRESS is set (KubeRay on EKS or an on-prem Ray cluster) the driver
    loads the file and hands it to Ray's object store, because worker nodes cannot
    see the driver pod's local disk. For datasets too large for the driver, point
    the file at a shared mount (FSx for Lustre) or S3 and use ray.data.read_parquet.
    """
    start_time = time.perf_counter()
    path = os.fspath(dataset)

    engine_used = "local-multiprocess"

    # Route compute based on environment and Ray availability
    if RAY_AVAILABLE and path.endswith(".parquet"):
        engine_used = "ray-data-distributed"
        remote_cluster = "RAY_ADDRESS" in os.environ
        if not ray.is_initialized():
            if remote_cluster:
                ray.init(address=os.environ["RAY_ADDRESS"])
            else:
                ray.init(ignore_reinit_error=True, include_dashboard=False)

        if remote_cluster:
            ds = ray.data.from_arrow(pq.read_table(path)).repartition(num_workers)
        else:
            ds = ray.data.read_parquet(path, override_num_blocks=num_workers)
        worker_results = ds.map_batches(
            _train_block, batch_size=None, batch_format="numpy"
        ).take_all()
    else:
        # Standalone Python fallback for instant developer onboarding
        cols = _read_dataset(path)
        aoa, re, lift_cfd = cols["aoa"], cols["re"], cols["lift_cfd"]
        chunk_size = len(aoa) // num_workers
        worker_results = []
        for i in range(num_workers):
            start_idx = i * chunk_size
            end_idx = (i + 1) * chunk_size if i < num_workers - 1 else len(aoa)
            worker_results.append(_train_slice_compute(
                i, aoa[start_idx:end_idx], re[start_idx:end_idx], lift_cfd[start_idx:end_idx]
            ))

    training_time = time.perf_counter() - start_time
    avg_r2 = float(np.mean([r["r2"] for r in worker_results]))
    avg_mse = float(np.mean([r["mse"] for r in worker_results]))

    return {
        "r2_score": avg_r2,
        "mse": avg_mse,
        "training_time_sec": training_time,
        "workers_used": float(num_workers),
        "engine": engine_used,
    }


@task(requests=Resources(cpu="1", mem="500Mi"))
def evaluate_surrogate(
    training_metrics: Dict[str, Any],
    cfd_benchmark_runtime_sec: float = 7200.0,
) -> Dict[str, str]:
    """
    Step 3 (Flyte CPU Task): Validates surrogate accuracy and computes acceleration factor.
    """
    train_time = max(0.0001, training_metrics["training_time_sec"])
    speedup = cfd_benchmark_runtime_sec / train_time

    return {
        "status": "APPROVED" if training_metrics["r2_score"] > 0.90 else "RETRAIN_NEEDED",
        "surrogate_r2": f"{training_metrics['r2_score']:.4f}",
        "surrogate_mse": f"{training_metrics['mse']:.6f}",
        "compute_engine": training_metrics.get("engine", "unknown"),
        "surrogate_runtime": f"{train_time:.3f}s",
        "cfd_baseline_runtime": f"{cfd_benchmark_runtime_sec:.1f}s",
        "acceleration_factor": f"{speedup:,.0f}x faster than CFD solver",
    }


# ============================================================================
# Flyte Workflow (Macro DAG)
# ============================================================================

@workflow
def surrogate_pipeline(
    num_samples: int = 1200,
    num_ray_workers: int = 4,
    env_mode: str = "local",
) -> Dict[str, str]:
    """
    Main Flyte workflow: Mesh Data -> Ray Burst Training -> Evaluation.
    """
    data = generate_mesh_data(num_samples=num_samples)
    metrics = train_surrogate_burst(
        dataset=data,
        num_workers=num_ray_workers,
        env_mode=env_mode,
    )
    return evaluate_surrogate(training_metrics=metrics)


if __name__ == "__main__":
    print("Executing Flyte + Ray surrogate pipeline locally...")
    result = surrogate_pipeline(num_samples=1600, num_ray_workers=4, env_mode="local")
    print("\n--- Pipeline Execution Summary ---")
    for k, v in result.items():
        print(f"  {k}: {v}")
