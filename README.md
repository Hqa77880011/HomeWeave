# HomeWeave

Implementation of **Automation-consistent cover episodes for smart-home metadata privacy**.

## Installation

Requires Python `>=3.11`. Run from the repository root in an activated environment.

```bash
python -m pip install -e .
```

Inspection environment: Python 3.13.5; numpy 2.1.3, scipy 1.15.3, scikit-learn 1.6.1, matplotlib 3.10.0. Checks: Python syntax, configuration parsing and CLI/source argument matching. Training and full evaluation were not run.

## Data

Template nodes declare direction, capacity and parent minimum/maximum delays. Messages declare arrival, direction, bytes and deadline; public seed and epoch duration fix cover.

The bundled generator writes synthetic finite-model scenarios as JSONL. Fix the seed and keep the generated input for paired comparisons.

```bash
python -m homeweave prepare --count 200 --seed 17 --output data/generated.jsonl
```

## Execution and evaluation

```bash
python -m homeweave run --data data/generated.jsonl --output runs/main
```

## Comparisons and ablations

```bash
python -m homeweave suite --data data/generated.jsonl --output runs/comparison
```

Use `--methods` to select: `homeweave`, `tunnel_only`, `independent_nodes`, `shuffled_timing`, `one_end`, `no_real_embedding`.

For independent attack fitting, the existing pipeline prepares disjoint generated train/validation/test episodes with seeds 11/17/29 and fits one attacker per registered defense:

```bash
python reproduce.py --plan
python reproduce.py --output runs/fixed-setting
```

## Outputs

`runs/main/homeweave/records.jsonl` stores per-case results; `metrics.json` stores aggregate measurements. Comparison outputs use one directory per method.

```bash
python -m homeweave plot --inputs runs/comparison/homeweave --output figures
```

Plotting writes `figures/summary.csv` and metric PNGs. Statistical intervals can be computed from a retained record file:

```bash
python -m homeweave.statistics --records runs/main/homeweave/records.jsonl --output results/intervals.json
```
