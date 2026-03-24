# file: scripts/select_kmeans_representatives.py
# Requirements:
#   pip install pandas scikit-learn numpy

from pathlib import Path
import argparse
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans


REQUIRED_COLUMNS = ["communication", "contention"]
DEFAULT_CLUSTERS = 15

# Repository root = parent of /scripts
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = REPO_ROOT / "data/processed/communication_contention_dataset.csv"
DEFAULT_OUTPUT = REPO_ROOT / "data/processed/kmeans_representatives.csv"


def validate_columns(df: pd.DataFrame) -> None:
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required column(s) in input CSV: {', '.join(missing)}"
        )


def select_representatives(df: pd.DataFrame, n_clusters: int) -> pd.DataFrame:
    """
    Runs K-Means on the communication/contention space and returns
    only the representative rows, preserving the original cluster IDs.
    """
    X = df[REQUIRED_COLUMNS].to_numpy()

    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init="auto",
    )

    labels = kmeans.fit_predict(X)
    centroids = kmeans.cluster_centers_

    # Keep the logic close to the original script
    df = df.copy()
    df["cluster_kmeans"] = labels
    df["rep_kmeans"] = False

    for cluster_id in range(n_clusters):
        cluster_indices = np.where(labels == cluster_id)[0]

        if len(cluster_indices) == 0:
            continue

        cluster_points = X[cluster_indices]
        centroid = centroids[cluster_id]

        distances = np.linalg.norm(cluster_points - centroid, axis=1)
        representative_index = cluster_indices[np.argmin(distances)]

        df.loc[representative_index, "rep_kmeans"] = True

    df_representatives = df[df["rep_kmeans"]].copy()

    return df_representatives


def ensure_output_directory(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)


def main(input_csv: str, output_csv: str, n_clusters: int) -> None:
    input_path = Path(input_csv)
    output_path = Path(output_csv)

    df = pd.read_csv(input_path)
    validate_columns(df)

    df_representatives = select_representatives(df, n_clusters)

    ensure_output_directory(output_path)
    df_representatives.to_csv(output_path, index=False)

    print(f"Number of clusters: {n_clusters}")
    print(f"Input file: {input_path}")
    print(f"Output file: {output_path}")
    print(f"Representative rows written: {len(df_representatives)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Select one representative configuration per K-Means cluster "
            "based on communication and contention."
        )
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT),
        help=f"Input CSV file (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help=f"Output CSV file (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--clusters",
        type=int,
        default=DEFAULT_CLUSTERS,
        help=f"Number of clusters (default: {DEFAULT_CLUSTERS})",
    )

    args = parser.parse_args()
    main(args.input, args.output, args.clusters)