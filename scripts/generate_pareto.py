#!/usr/bin/env python3
# generate_pareto_2d.py
#
# Generates the 2D Pareto frontier using:
# - communication
# - contention
#
# Input:
#   data/processed/exhaustive_configurations_alpha_05.csv
#
# Output:
#   data/processed/pareto_2d_alpha_05.csv
#
# Output columns:
# - config_str
# - communication
# - contention
# - score
# - position
# - pareto_front

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a 2D Pareto frontier from exhaustive configuration data."
    )
    parser.add_argument(
        "--alpha",
        default="05",
        help="Alpha identifier used in filenames (default: 05)",
    )
    parser.add_argument(
        "--input",
        default=None,
        help="Optional input CSV path",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output CSV path",
    )
    return parser.parse_args()


def ensure_position_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensures a 'position' column exists (1-based index).
    """
    df = df.copy()

    if "position" not in df.columns:
        df["position"] = np.arange(1, len(df) + 1)

    return df


def validate_columns(df: pd.DataFrame):
    required = {"config_str", "communication", "contention", "score"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}. "
            f"Expected columns: {sorted(required)}"
        )


def compute_pareto_front(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the 2D Pareto frontier (minimization problem).
    """
    df = df.copy().reset_index(drop=True)

    comm = df["communication"].to_numpy()
    cont = df["contention"].to_numpy()
    n = len(df)

    is_pareto = np.ones(n, dtype=bool)

    for i in range(n):
        if not is_pareto[i]:
            continue

        dominated = (
            (comm <= comm[i]) &
            (cont <= cont[i]) &
            ((comm < comm[i]) | (cont < cont[i]))
        )
        dominated[i] = False

        if dominated.any():
            is_pareto[i] = False

    df["pareto_front"] = is_pareto
    return df


def build_default_paths(alpha: str):
    repo_root = Path(__file__).resolve().parent.parent

    input_path = repo_root / "data" / "processed" / f"exhaustive_configurations_alpha_{alpha}.csv"
    output_path = repo_root / "data" / "processed" / f"pareto_2d_alpha_{alpha}.csv"

    return input_path, output_path


def main():
    args = parse_args()

    default_input, default_output = build_default_paths(args.alpha)

    input_path = Path(args.input) if args.input else default_input
    output_path = Path(args.output) if args.output else default_output

    print(f"Reading input: {input_path}")
    df = pd.read_csv(input_path)

    validate_columns(df)
    df = ensure_position_column(df)

    print("Computing Pareto frontier...")
    df = compute_pareto_front(df)

    pareto_df = df[df["pareto_front"]].copy()

    # Ordena só pra ficar legível (não muda resultado)
    pareto_df = pareto_df.sort_values(
        by=["communication", "contention"]
    )

    columns = [
        "config_str",
        "communication",
        "contention",
        "score",
        "position",
        "pareto_front",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pareto_df.to_csv(output_path, index=False, columns=columns)

    print(f"Pareto frontier size: {len(pareto_df)}")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()