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

    predicted_cluster = int(kmodes_model.predict(row.to_numpy())[0]) + 1
    cluster_label = CLUSTER_LABEL_MAP[str(predicted_cluster)]

    return predicted_cluster, cluster_label