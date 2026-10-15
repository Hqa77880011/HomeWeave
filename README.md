# HomeWeave

Implementation of **Automation-consistent cover episodes for smart-home metadata privacy**.

Compiles automation DAGs by intersecting all parent timing intervals. Direction-specific slots embed real fragments before deadlines and retain cover capacity when empty.

## Install

Use Python 3.11 or newer.

```bash
git clone https://github.com/Hqa77880011/HomeWeave.git
cd HomeWeave
python -m venv .venv
```

Activate with `source .venv/bin/activate` on Linux/macOS or `.venv\Scripts\Activate.ps1` in PowerShell, then install.

```bash
python -m pip install -e .
```

## Data preparation

Template nodes declare direction, capacity and parent minimum/maximum delays. Messages declare arrival, direction, bytes and deadline; public seed and epoch duration fix cover.

```bash
python -m homeweave prepare --count 200 --seed 17 --output data/workload.jsonl
```

The generator creates finite workloads from the formal model. Each JSONL row is one scenario. `--count` controls corpus size and `--seed` controls generation. Imported cases use the same schema. Generate calibration and test scenarios independently.

## Execute and compare

```bash
python -m homeweave run --data data/workload.jsonl --output runs/main
python -m homeweave suite --data data/workload.jsonl --output runs/comparison
```

Select methods with `--methods`. homeweave retains DAG timing and both ends; tunnel_only forwards real traffic; independent_nodes and shuffled_timing break episode structure; one_end removes reverse cover; no_real_embedding separates real traffic.

## Evaluation and visualization

Command success within deadline, bytes and amplification, overflow, mean/P95 delay, runtime and trained chain inference AUC.

Each method writes `records.jsonl` and `metrics.json` with means, sample standard deviations, usable counts and P50/P95/P99. Rates are fractions. Undefined conditional metrics remain unavailable. Method timers exclude reference scoring. RSS includes the Python runtime; serialized sizes measure JSON bytes.

```bash
python -m homeweave plot --inputs runs/comparison/homeweave --output figures
```

Pass multiple method directories to compare them. Plotting writes `summary.csv` and metric PNGs.

## Implementation conventions

The driver schedules byte metadata without issuing device commands. Cover only adds tunnel capacity. Immediate deadline escape remains visible in the trace. Production endpoints must authenticate and discard dummy payloads and capture both directions including ACK/recovery.

## Independent attacker training

Prepare and execute independent train, validation and test corpora with different seeds, then run:

```bash
python -m homeweave.attack --train runs/train/homeweave/records.jsonl --validation runs/validation/homeweave/records.jsonl --test runs/test/homeweave/records.jsonl --output runs/attacker
```

The attacker selects logistic regression or ExtraTrees using validation AUC and reports held-out Top-1, balanced accuracy, AUC and validation-threshold TPR/FPR. Recorded data must use disjoint households/sessions. The fitted attacker is saved to `attacker.joblib`.


## Uncertainty and paired comparisons

```bash
python -m homeweave.statistics --records runs/main/homeweave/records.jsonl --output results/intervals.json
```

Supply --reference with a matched record file for paired differences. Resampling uses independent case IDs, or explicit cluster IDs when provided. Repeated observations from one source unit must share cluster. Zero-event bounds refer to an event in an independent cluster.
