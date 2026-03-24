import os
import argparse
import networkx as nx
import pandas as pd


# ===================== Graph =====================
def build_graph() -> nx.DiGraph:
    G = nx.DiGraph()

    resource_usage = {
        "main": 0.9732034542,
        "cart": 0.1711237533,
        "currency": 0.08523609192,
        "productcat": 0.1232599578,
        "recommendation": 0.03587265015,
        "ad": 0.07119954811,
        "shipping": 0.0480661623,
        "checkout": 0.06153931493,
        "email": 0.04393005371,
        "payment": 0.03774261475,
    }

    for node, resource in resource_usage.items():
        G.add_node(node, resource=resource)

    edges = [
        ("main", "recommendation", 0.89),
        ("main", "productcat", 6.05),
        ("main", "ad", 0.74),
        ("main", "currency", 2.26),
        ("main", "cart", 1.05),
        ("main", "checkout", 0.05),
        ("main", "shipping", 0.16),
        ("recommendation", "productcat", 0.21),
        ("checkout", "currency", 0.05),
        ("checkout", "cart", 0.11),
        ("checkout", "email", 0.05),
        ("checkout", "payment", 0.05),
        ("checkout", "shipping", 0.11),
    ]

    for source, target, weight in edges:
        G.add_edge(source, target, weight=weight)

    # Global denominators for normalization
    G.graph["W_total"] = sum(data["weight"] for _, _, data in G.edges(data=True)) or 1.0
    G.graph["R_total"] = sum(data["resource"] for _, data in G.nodes(data=True)) or 1.0

    return G


# ===================== Evaluation =====================
def evaluate_config(G: nx.DiGraph, config: dict, alpha: float = 0.5):
    """
    communication = sum of edge weights crossing groups / total edge weight
    contention = load of the heaviest group / total resource usage
    score = alpha * communication + (1 - alpha) * contention
    """
    beta = 1.0 - alpha

    communication_raw = 0.0
    for source, target, data in G.edges(data=True):
        if config[source] != config[target]:
            communication_raw += data.get("weight", 1.0)

    group_loads = {}
    for node, attrs in G.nodes(data=True):
        group_id = config[node]
        group_loads[group_id] = group_loads.get(group_id, 0.0) + attrs["resource"]

    contention_raw = max(group_loads.values()) if group_loads else 0.0

    communication = communication_raw / G.graph["W_total"]
    contention = contention_raw / G.graph["R_total"]
    score = alpha * communication + beta * contention

    return {
        "communication": communication,
        "contention": contention,
        "score": score,
        "groups": len(group_loads),
        "communication_raw": communication_raw,
        "contention_raw": contention_raw,
    }


# ===================== Partitions (Bell) =====================
def set_partitions(seq):
    """Generate all set partitions of a sequence using a recursive algorithm."""
    seq = list(seq)
    if not seq:
        yield []
        return

    first = seq[0]
    for rest in set_partitions(seq[1:]):
        for i in range(len(rest)):
            new_part = [group[:] for group in rest]
            new_part[i].append(first)
            yield new_part

        yield [[first]] + [group[:] for group in rest]


def partition_to_config_map(partition):
    config = {}
    for group_id, group in enumerate(partition):
        for service in group:
            config[service] = group_id
    return config


def partition_to_string(partition):
    """
    Format:
    - same execution unit: "-"
    - different execution units: "_"

    Example:
    ad-cart_main-productcat-payment
    """
    groups = [sorted(group) for group in partition]
    groups.sort(key=lambda group: tuple(group))
    return "_".join("-".join(group) for group in groups)


# ===================== Exhaustive Enumeration =====================
def exhaustive_to_csv(
    G: nx.DiGraph,
    services: list,
    out_csv: str,
    alpha: float = 0.5,
    min_groups: int = 1,
    max_groups: int = None,
    feasible=None,
):
    if max_groups is None:
        max_groups = len(services)

    rows = []

    for partition in set_partitions(services):
        num_groups = len(partition)

        if num_groups < min_groups or num_groups > max_groups:
            continue

        if feasible and not feasible(partition):
            continue

        config = partition_to_config_map(partition)
        metrics = evaluate_config(G, config, alpha=alpha)
        metrics["config_str"] = partition_to_string(partition)
        rows.append(metrics)

    df = pd.DataFrame(rows).sort_values("score", ascending=True).reset_index(drop=True)
    df["rank"] = df.index + 1
    cols = ["rank"] + [c for c in df.columns if c != "rank"]
    df = df[cols]
    df.to_csv(out_csv, index=False)
    return df


# ===================== CLI =====================
def parse_args():
    parser = argparse.ArgumentParser(
        description="Enumerate all deployment configurations and save a CSV with normalized communication, contention, and score."
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.5,
        help="Weight of communication in the score; contention weight is (1 - alpha). Default: 0.5",
    )
    parser.add_argument(
        "--min-groups",
        type=int,
        default=1,
        help="Minimum number of groups. Default: 1",
    )
    parser.add_argument(
        "--max-groups",
        type=int,
        default=0,
        help="Maximum number of groups. Use 0 for no upper bound. Default: 0",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if not 0.0 <= args.alpha <= 1.0:
        raise ValueError("--alpha must be between 0 and 1.")

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    OUTPUT_DIR = os.path.join(BASE_DIR, "data", "processed")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    alpha_str = str(args.alpha).replace(".", "")
    output_file = os.path.join(
        OUTPUT_DIR,
        f"exhaustive_configurations_alpha_{alpha_str}.csv"
    )

    G = build_graph()
    services = list(G.nodes())
    max_groups = args.max_groups if args.max_groups > 0 else len(services)

    feasible = None

    df = exhaustive_to_csv(
        G,
        services,
        out_csv=output_file,
        alpha=args.alpha,
        min_groups=args.min_groups,
        max_groups=max_groups,
        feasible=feasible,
    )

    print(f"Output file: {output_file}")
    print(f"Total configurations saved: {len(df)}")
    print("Top 10 configurations:")
    print(
        df.head(10)[
            [
                "config_str",
                "groups",
                "communication",
                "contention",
                "score",
                "communication_raw",
                "contention_raw",
            ]
        ]
    )