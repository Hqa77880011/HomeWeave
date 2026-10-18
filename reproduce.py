"""Bidirectional three-node public DAG, one cell per node, EDF embedding, 8-second generated sessions, 256-byte cells. Independent train/validation/test episodes (seeds11/17/29) fit a held-out attacker for each registered defense."""

import argparse
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent


def build_steps(args):
    output = (ROOT / args.output).resolve()
    return [
        ["-m", "homeweave", "prepare", "--count", "400", "--seed", "11", "--output", str(output / "train.jsonl")],
        ["-m", "homeweave", "suite", "--data", str(output / "train.jsonl"), "--methods", "homeweave", "tunnel_only", "independent_nodes", "--output", str(output / "train")],
        ["-m", "homeweave", "prepare", "--count", "200", "--seed", "17", "--output", str(output / "validation.jsonl")],
        ["-m", "homeweave", "suite", "--data", str(output / "validation.jsonl"), "--methods", "homeweave", "tunnel_only", "independent_nodes", "--output", str(output / "validation")],
        ["-m", "homeweave", "prepare", "--count", "200", "--seed", "29", "--output", str(output / "test.jsonl")],
        ["-m", "homeweave", "suite", "--data", str(output / "test.jsonl"), "--methods", "homeweave", "tunnel_only", "independent_nodes", "--output", str(output / "test")],
        ["-m", "homeweave.attack", "--train", str(output / "train/homeweave/records.jsonl"), "--validation", str(output / "validation/homeweave/records.jsonl"), "--test", str(output / "test/homeweave/records.jsonl"), "--seed", "17", "--fpr", "0.01", "--output", str(output / "attacker_homeweave")],
        ["-m", "homeweave.attack", "--train", str(output / "train/tunnel_only/records.jsonl"), "--validation", str(output / "validation/tunnel_only/records.jsonl"), "--test", str(output / "test/tunnel_only/records.jsonl"), "--seed", "17", "--fpr", "0.01", "--output", str(output / "attacker_tunnel_only")],
        ["-m", "homeweave.attack", "--train", str(output / "train/independent_nodes/records.jsonl"), "--validation", str(output / "validation/independent_nodes/records.jsonl"), "--test", str(output / "test/independent_nodes/records.jsonl"), "--seed", "17", "--fpr", "0.01", "--output", str(output / "attacker_independent_nodes")],
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default='runs/fixed-setting')
    parser.add_argument("--plan", action="store_true", help="Print commands without creating data, fitting, inference or evaluation")

    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    if not args.plan and output.exists():
        parser.error("Choose a fresh --output directory")
    for step in build_steps(args):
        command = [sys.executable, *step]
        if args.plan:
            print(json.dumps(command))
        else:
            subprocess.run(command, cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
