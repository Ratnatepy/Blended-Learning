from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


def prepare_kmodes_matrix(
    data: pd.DataFrame,
    columns: list[str],
    kmodes_config: dict,
) -> tuple[pd.DataFrame, np.ndarray]:
    """Prepare categorical/ordinal matrix for K-Modes using config-defined policy."""
    X = data[columns].copy()
    total_nulls = int(X.isna().sum().sum())
    print("K-Modes input shape:", X.shape)
    print("K-Modes total nulls:", total_nulls)
    if total_nulls > 0 and kmodes_config.get("missing_policy") == "raise":
        raise ValueError(
            "Configured cluster variables contain missing values. Clean or impute before K-Modes."
        )
    dtype = kmodes_config.get("input_dtype", "int")
    for col in X.columns:
        X[col] = X[col].astype(dtype).astype(str)
    return X, X.to_numpy()


def prepare_gmm_matrix(
    data: pd.DataFrame,
    columns: list[str],
) -> tuple[pd.DataFrame, np.ndarray, StandardScaler]:
    """Prepare numeric standardized matrix for comparison GMM experiments."""
    X = data[columns].copy()
    total_nulls = int(X.isna().sum().sum())
    print("GMM input shape:", X.shape)
    print("GMM total nulls:", total_nulls)
    if total_nulls > 0:
        raise ValueError("Configured cluster variables contain missing values. Clean or impute before GMM.")
    X = X.astype(float)
    scaler = StandardScaler()
    return X, scaler.fit_transform(X), scaler
