from pathlib import Path
import json
import joblib
import pandas as pd

# Project root = one folder above /api
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models"

KMODES_MODEL_PATH = MODEL_DIR / "kmodes_model.pkl"
FEATURE_COLUMNS_PATH = MODEL_DIR / "kmodes_feature_columns.json"
CLUSTER_LABEL_MAP_PATH = MODEL_DIR / "kmodes_cluster_label_map.json"


def check_model_files():
    missing_files = []

    for path in [
        KMODES_MODEL_PATH,
        FEATURE_COLUMNS_PATH,
        CLUSTER_LABEL_MAP_PATH,
    ]:
        if not path.exists():
            missing_files.append(str(path))

    if missing_files:
        raise FileNotFoundError(
            "Missing K-Modes model files. Please place these files inside the project models/ folder: "
            + ", ".join(missing_files)
        )


check_model_files()

kmodes_model = joblib.load(KMODES_MODEL_PATH)

with open(FEATURE_COLUMNS_PATH, "r", encoding="utf-8") as f:
    FEATURE_COLUMNS = json.load(f)

with open(CLUSTER_LABEL_MAP_PATH, "r", encoding="utf-8") as f:
    CLUSTER_LABEL_MAP = json.load(f)



def assign_kmodes_cluster(responses: dict):
    missing_features = [
        feature for feature in FEATURE_COLUMNS
        if feature not in responses
    ]

    if missing_features:
        raise ValueError(
            f"Missing {len(missing_features)} required clustering features: {missing_features}"
        )

    row = pd.DataFrame([responses])
    row = row[FEATURE_COLUMNS].copy()

    for col in FEATURE_COLUMNS:
        row[col] = pd.to_numeric(row[col], errors="raise").astype("Int64").astype(str)

    input_array = row.to_numpy()

    raw_predicted_cluster = int(kmodes_model.predict(input_array)[0])

    # -----------------------------
    # Tie-safe correction
    # -----------------------------
    # K-Modes uses categorical matching.
    # Extreme inputs such as all 5s can tie between clusters.
    # In that case, choose the cluster with the higher centroid average.
    centroids = kmodes_model.cluster_centroids_

    distances = []
    for centroid in centroids:
        distance = sum(input_array[0][i] != centroid[i] for i in range(len(FEATURE_COLUMNS)))
        distances.append(distance)

    min_distance = min(distances)
    tied_clusters = [
        index for index, distance in enumerate(distances)
        if distance == min_distance
    ]

    if len(tied_clusters) > 1:
        centroid_scores = []

        for cluster_index in tied_clusters:
            centroid_values = [
                int(value)
                for value in centroids[cluster_index]
            ]

            centroid_average = sum(centroid_values) / len(centroid_values)
            centroid_scores.append((cluster_index, centroid_average))

        raw_predicted_cluster = max(
            centroid_scores,
            key=lambda item: item[1]
        )[0]

    predicted_cluster = raw_predicted_cluster + 1
    cluster_label = CLUSTER_LABEL_MAP[str(predicted_cluster)]

    return predicted_cluster, cluster_label
       