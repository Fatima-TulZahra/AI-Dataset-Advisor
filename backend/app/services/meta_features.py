"""
Meta-feature extraction for AI Dataset Advisor.

ONE shared file: used offline (Colab experiments) and online (FastAPI backend)
so that the numbers describing a dataset are computed in exactly the same way.

Usage:
    feats = extract_meta_features(X, y, "classification")   # or "regression"
    # X: pandas DataFrame (features only), y: pandas Series (target)
"""
import numpy as np
import pandas as pd

MAX_CORR_COLUMNS = 50  # keep correlation fast on wide datasets


def _split_columns(X: pd.DataFrame):
    numeric = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical = X.select_dtypes(include=["object", "category", "bool", "string"]).columns.tolist()
    return numeric, categorical


def _mean_abs_correlation(X: pd.DataFrame, numeric_cols: list) -> float:
    cols = [c for c in numeric_cols if X[c].nunique(dropna=True) > 1]
    if len(cols) < 2:
        return 0.0
    if len(cols) > MAX_CORR_COLUMNS:
        cols = list(pd.Series(cols).sample(MAX_CORR_COLUMNS, random_state=42))
    corr = X[cols].corr().abs().to_numpy()
    upper = corr[np.triu_indices_from(corr, k=1)]
    upper = upper[~np.isnan(upper)]
    return float(upper.mean()) if upper.size else 0.0


def extract_meta_features(X: pd.DataFrame, y: pd.Series, task: str) -> dict:
    """Return a flat dict of numbers describing the dataset."""
    if task not in ("classification", "regression"):
        raise ValueError("task must be 'classification' or 'regression'")

    n_rows, n_cols = X.shape
    numeric, categorical = _split_columns(X)

    feats = {
        "n_rows": int(n_rows),
        "n_cols": int(n_cols),
        "log_n_rows": float(np.log10(max(n_rows, 1))),
        "rows_per_col": float(n_rows / max(n_cols, 1)),
        "numeric_ratio": len(numeric) / max(n_cols, 1),
        "categorical_ratio": len(categorical) / max(n_cols, 1),
        "missing_pct": float(X.isna().to_numpy().mean() * 100) if X.size else 0.0,
        "mean_abs_correlation": _mean_abs_correlation(X, numeric),
        "mean_cardinality": float(np.mean([X[c].nunique(dropna=True) for c in categorical])) if categorical else 0.0,
    }

    if task == "classification":
        shares = y.value_counts(normalize=True)
        feats["n_classes"] = int(len(shares))
        feats["class_imbalance"] = float(shares.max() - shares.min()) if len(shares) > 1 else 1.0
    else:
        yn = pd.to_numeric(y, errors="coerce").dropna()
        feats["target_skew"] = float(yn.skew()) if len(yn) > 2 else 0.0
        feats["target_kurtosis"] = float(yn.kurtosis()) if len(yn) > 3 else 0.0

    # replace any NaN/inf with 0 so the meta-model never receives invalid numbers
    for k, v in feats.items():
        if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
            feats[k] = 0.0
    return feats


if __name__ == "__main__":
    from sklearn.datasets import load_iris, load_diabetes
    d = load_iris(as_frame=True)
    print(extract_meta_features(d.data, d.target, "classification"))
    d = load_diabetes(as_frame=True)
    print(extract_meta_features(d.data, d.target, "regression"))
