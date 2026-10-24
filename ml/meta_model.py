"""
meta_model.py  -  train, evaluate, save and use the META-MODEL (the "recommender brain").

Input  : meta-table made by experiments.py  (one row per dataset: meta-features + algorithm scores)
Output : a bundle file  meta_model_clf.joblib / meta_model_reg.joblib   (+ a small .json report)

Colab (notebook 04):
    import sys; sys.path.append(f"{BASE}/code")
    import meta_model as mm
    raw = mm.load_meta_table(f"{BASE}/results/clf_experiments.csv", "classification")
    mm.inspect_table(raw, "classification")
    bundle, report = mm.train_and_evaluate(raw, "classification")
    mm.save_bundle(bundle, f"{BASE}/artifacts/meta_model_clf.joblib", report)

Backend (later):
    bundle = mm.load_bundle(path);  mm.recommend(bundle, meta_features_dict, k=3)
"""
import datetime
import json
import os

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold

ID_COLS = ["did", "name", "split"]
SCORE_PREFIX = {"classification": "f1_", "regression": "r2_"}
OTHER_PREFIXES = ("f1_", "acc_", "r2_", "time_")
TOLERANCE = 0.01        # algorithms within 0.01 of the best score count as "best" (ties)
RANDOM_STATE = 42


# ---------------------------------------------------------------- table helpers
def load_meta_table(path, task):
    return pd.read_csv(path)


def get_columns(df, task):
    prefix = SCORE_PREFIX[task]
    score_cols = [c for c in df.columns if c.startswith(prefix)]
    algos = [c[len(prefix):] for c in score_cols]
    meta_cols = [c for c in df.columns if c not in ID_COLS and not c.startswith(OTHER_PREFIXES)]
    return meta_cols, algos, score_cols


def clean_table(df, task):
    """Drop rows without any score; replace missing scores by the row's worst score (a failed algorithm = bad choice)."""
    meta_cols, algos, score_cols = get_columns(df, task)
    df = df.dropna(subset=score_cols, how="all").copy()
    worst = df[score_cols].min(axis=1)
    for c in score_cols:
        df[c] = df[c].fillna(worst)
    df[meta_cols] = df[meta_cols].fillna(0)
    return df.reset_index(drop=True)


def inspect_table(df, task):
    meta_cols, algos, score_cols = get_columns(df, task)
    print(f"Datasets (rows): {len(df)}   | meta-features: {len(meta_cols)}   | algorithms: {len(algos)}")
    if "split" in df:
        print("Split counts:", df["split"].value_counts().to_dict())
    print("Missing scores per algorithm:", df[score_cols].isna().sum().rename(lambda c: c[len(SCORE_PREFIX[task]):]).to_dict())
    scores = df[score_cols].fillna(-9)
    wins = scores.idxmax(axis=1).str[len(SCORE_PREFIX[task]):].value_counts()
    print("\nHow often each algorithm was the best (number of datasets):")
    print(wins.to_string())
    share = wins.iloc[0] / wins.sum()
    if share > 0.7:
        print(f"\nWARNING: '{wins.index[0]}' wins {share:.0%} of datasets, so the meta-model will find it easy to look good. Mention this in the report.")
    print("\nMean score per algorithm:")
    print(df[score_cols].mean().rename(lambda c: c[len(SCORE_PREFIX[task]):]).sort_values(ascending=False).round(3).to_string())


# ---------------------------------------------------------------- model
def fit(df_train, task):
    meta_cols, algos, score_cols = get_columns(df_train, task)
    model = RandomForestRegressor(n_estimators=300, min_samples_leaf=2, random_state=RANDOM_STATE, n_jobs=-1)
    model.fit(df_train[meta_cols].to_numpy(), df_train[score_cols].to_numpy())
    return {"model": model, "task": task, "meta_cols": meta_cols, "algos": algos,
            "n_train_datasets": int(len(df_train)), "sklearn_version": sklearn.__version__,
            "created": str(datetime.date.today())}


def predict_scores(bundle, df):
    X = df.reindex(columns=bundle["meta_cols"], fill_value=0).fillna(0).to_numpy()
    return pd.DataFrame(bundle["model"].predict(X), columns=bundle["algos"], index=df.index)


# ---------------------------------------------------------------- evaluation
def evaluate(true, pred, baseline_order, seed=RANDOM_STATE, n_random=200):
    """true / pred: DataFrames (rows = datasets, columns = algorithms). Returns a comparison table."""
    algos = list(true.columns)
    best = true.max(axis=1)
    is_best = true.ge(best - TOLERANCE, axis=0)

    def metrics(top_lists):
        hit1 = np.mean([is_best.loc[i, t[0]] for i, t in zip(true.index, top_lists)])
        hit3 = np.mean([is_best.loc[i, t[:3]].any() for i, t in zip(true.index, top_lists)])
        reg1 = np.mean([best[i] - true.loc[i, t[0]] for i, t in zip(true.index, top_lists)])
        reg3 = np.mean([best[i] - true.loc[i, t[:3]].max() for i, t in zip(true.index, top_lists)])
        return [hit1, hit3, reg1, reg3]

    meta_top = [list(pred.loc[i].sort_values(ascending=False).index) for i in true.index]
    base_top = [list(baseline_order)] * len(true)
    rng = np.random.default_rng(seed)
    rand = np.mean([metrics([list(rng.permutation(algos)) for _ in true.index]) for _ in range(n_random)], axis=0)

    table = pd.DataFrame(
        [metrics(meta_top), metrics(base_top), rand],
        index=["Meta-model", f"Always {baseline_order[0]} (best on average)", "Random choice"],
        columns=["top1_hit", "top3_hit", "regret@1", "regret@3"])
    return table.round(3)


def cross_validate_meta(df_train, task, n_splits=5):
    """Honest estimate on the TRAIN datasets: each dataset is predicted by a model that never saw it."""
    _, algos, score_cols = get_columns(df_train, task)
    kf = KFold(n_splits=min(n_splits, len(df_train)), shuffle=True, random_state=RANDOM_STATE)
    oof = pd.DataFrame(index=df_train.index, columns=algos, dtype=float)
    for tr, te in kf.split(df_train):
        b = fit(df_train.iloc[tr], task)
        oof.iloc[te] = predict_scores(b, df_train.iloc[te]).to_numpy()
    true = df_train[score_cols].copy(); true.columns = algos
    order = list(true.mean().sort_values(ascending=False).index)
    return evaluate(true, oof, order)


def train_and_evaluate(raw, task):
    df = clean_table(raw, task)
    _, algos, score_cols = get_columns(df, task)
    train = df[df["split"] == "train"] if "split" in df else df
    held = df[df["split"] == "heldout"] if "split" in df else df.iloc[0:0]
    print(f"Train datasets: {len(train)} | Held-out datasets: {len(held)}")

    print("\n== (1) Cross-validation on TRAIN datasets (each dataset predicted by a model that did not see it) ==")
    cv_table = cross_validate_meta(train, task)
    print(cv_table.to_string())

    bundle = fit(train, task)
    report = {"cross_validation": cv_table}
    if len(held):
        true = held[score_cols].copy(); true.columns = algos
        order = list(train[score_cols].mean().sort_values(ascending=False).rename(lambda c: c[len(SCORE_PREFIX[task]):]).index)
        held_table = evaluate(true, predict_scores(bundle, held), order)
        print("\n== (2) HELD-OUT datasets (never used for training): the main result for the report ==")
        print(held_table.to_string())
        report["heldout"] = held_table
    print("\nHow to read: top1_hit/top3_hit = how often the truly best algorithm was our 1st choice / among our top 3 (higher is better).")
    print("regret = how much score we lose versus the best algorithm (lower is better).")
    return bundle, report


# ---------------------------------------------------------------- save / load / use
def save_bundle(bundle, path, report=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(bundle, path, compress=3)
    info = {k: v for k, v in bundle.items() if k != "model"}
    if report:
        info["metrics"] = {k: v.to_dict(orient="index") for k, v in report.items()}
    with open(path.replace(".joblib", "_info.json"), "w") as f:
        json.dump(info, f, indent=2)
    print("Saved:", path, f"({os.path.getsize(path)/1e6:.1f} MB)")


def load_bundle(path):
    bundle = joblib.load(path)
    if bundle["sklearn_version"] != sklearn.__version__:
        print(f"WARNING: model trained with scikit-learn {bundle['sklearn_version']}, installed {sklearn.__version__}")
    return bundle


def recommend(bundle, feats: dict, k=3):
    """feats = output of extract_meta_features(...). Returns the top-k algorithms with predicted scores."""
    pred = predict_scores(bundle, pd.DataFrame([feats])).iloc[0].sort_values(ascending=False)
    return [{"algorithm": a, "predicted_score": round(float(s), 3)} for a, s in pred.head(k).items()]


# ---------------------------------------------------------------- external test (Kaggle / UCI / your own file)
def make_external_csv(src_csv, target_col, dst_csv):
    df = pd.read_csv(src_csv)
    df = df.rename(columns={target_col: "__target__"})
    df.to_csv(dst_csv, index=False)


def external_check(bundle, csv_path, k=3):
    """csv_path: CSV whose target column is called __target__ (use make_external_csv).
    Runs the REAL algorithms on the file and compares with what the meta-model recommends."""
    from experiments import process_dataset      # lazy import: only needed in Colab
    task = bundle["task"]
    row = process_dataset(csv_path, task)
    rec = recommend(bundle, row, k)
    pre = SCORE_PREFIX[task]
    true = pd.Series({a: row[f"{pre}{a}"] for a in bundle["algos"]}).sort_values(ascending=False)
    top = [r["algorithm"] for r in rec]
    best = true.max()
    out = pd.DataFrame({"true_score": true.round(3),
                        "recommended": ["<-- recommended" if a in top else "" for a in true.index]})
    print(out.to_string())
    hit = any(true[a] >= best - TOLERANCE for a in top)
    print(f"\nTop-{k} recommended: {top}")
    print(f"Truly best: {true.index[0]} ({best:.3f}) -> best (or tied) inside our top {k}? {hit}")
    print(f"Regret (best minus our best pick): {best - max(true[a] for a in top):.3f}")
    return {"recommended": top, "true_ranking": true.to_dict(), "hit": bool(hit)}
