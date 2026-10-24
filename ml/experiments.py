"""
experiments.py  -  runs candidate algorithms on every public dataset and saves ONE ROW PER DATASET.

Colab usage (notebook 03a for classification, 03b for regression):

    import sys; sys.path.append(f"{BASE}/code")
    from experiments import run_experiments
    run_experiments("classification", BASE, max_minutes=90)     # stops by itself after 90 minutes
    # run the same cell again later: it continues where it stopped (resume)

Inputs  : {BASE}/datasets_list.csv  and  {BASE}/data/clf|reg/<did>.csv  (target column = "__target__")
Outputs : {BASE}/results/clf_experiments.csv | reg_experiments.csv   (the meta-table)
          {BASE}/results/failed_experiments.csv
"""
import os
import time
import warnings

os.environ.setdefault("PYTHONWARNINGS", "ignore")   # also silences joblib worker processes
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (HistGradientBoostingClassifier, HistGradientBoostingRegressor,
                              RandomForestClassifier, RandomForestRegressor)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import KFold, StratifiedKFold, cross_validate, train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC, SVR
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

from meta_features import extract_meta_features

RANDOM_STATE = 42
N_SPLITS = 5
MIN_CLASS_ROWS = 5          # classes with fewer rows are removed (needed for 5-fold stratified CV)
SLOW_ALGOS = {"SVM", "SVR"}  # these are subsampled to keep runtime reasonable
SLOW_MAX_ROWS = 3000

ALGOS_CLF = {
    "LogReg": LogisticRegression(max_iter=1000),
    "KNN": KNeighborsClassifier(),
    "DecisionTree": DecisionTreeClassifier(random_state=RANDOM_STATE),
    "RandomForest": RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE),
    "HistGB": HistGradientBoostingClassifier(random_state=RANDOM_STATE),
    "SVM": SVC(),
    "NaiveBayes": GaussianNB(),
}
ALGOS_REG = {
    "Ridge": Ridge(),
    "KNN": KNeighborsRegressor(),
    "DecisionTree": DecisionTreeRegressor(random_state=RANDOM_STATE),
    "RandomForest": RandomForestRegressor(n_estimators=100, random_state=RANDOM_STATE),
    "HistGB": HistGradientBoostingRegressor(random_state=RANDOM_STATE),
    "SVR": SVR(),
}


def prepare_X(X: pd.DataFrame):
    """Split columns into numeric / categorical; make categorical values plain strings (NaN stays NaN)."""
    X = X.copy()
    for c in X.columns:
        if X[c].dtype == "bool":
            X[c] = X[c].astype("object")
    num = X.select_dtypes(include=[np.number]).columns.tolist()
    cat = [c for c in X.columns if c not in num]
    for c in cat:
        s = X[c].astype("object")
        X[c] = s.where(s.isna(), s.astype(str))
    return X, num, cat


def build_pipeline(model, num, cat):
    """Preprocessing lives INSIDE the pipeline, so it is re-fitted on every training fold (no data leakage)."""
    parts = []
    if num:
        parts.append(("num", Pipeline([("imp", SimpleImputer(strategy="median")),
                                       ("sc", StandardScaler())]), num))
    if cat:
        parts.append(("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                                       ("oh", OneHotEncoder(handle_unknown="ignore", max_categories=20,
                                                            sparse_output=False))]), cat))
    return Pipeline([("pre", ColumnTransformer(parts, remainder="drop")), ("model", model)])


def _subsample(X, y, n, task):
    if len(X) <= n:
        return X, y
    try:
        strat = y if task == "classification" else None
        Xs, _, ys, _ = train_test_split(X, y, train_size=n, stratify=strat, random_state=RANDOM_STATE)
    except ValueError:
        idx = X.sample(n, random_state=RANDOM_STATE).index
        Xs, ys = X.loc[idx], y.loc[idx]
    return Xs, ys


def run_cv(name, model, X, y, task, num, cat):
    """5-fold cross-validation of one algorithm. Returns dict of scores (NaN if it failed)."""
    if name in SLOW_ALGOS:
        X, y = _subsample(X, y, SLOW_MAX_ROWS, task)
    if task == "classification":
        cv = StratifiedKFold(N_SPLITS, shuffle=True, random_state=RANDOM_STATE)
        scoring = {"f1": "f1_macro", "acc": "accuracy"}
    else:
        cv = KFold(N_SPLITS, shuffle=True, random_state=RANDOM_STATE)
        scoring = {"r2": "r2"}
    try:
        res = cross_validate(build_pipeline(clone(model), num, cat), X, y, cv=cv, scoring=scoring,
                             n_jobs=-1, error_score=np.nan)
        out = {k: float(np.nanmean(res[f"test_{k}"])) if not np.all(np.isnan(res[f"test_{k}"])) else np.nan
               for k in scoring}
        out["time"] = float(np.mean(res["fit_time"]))
    except Exception:
        out = {k: np.nan for k in scoring}
        out["time"] = np.nan
    if "r2" in out and not np.isnan(out["r2"]):
        out["r2"] = max(out["r2"], -1.0)      # a hopeless model should not ruin the table with -1000
    return out


def process_dataset(path, task):
    df = pd.read_csv(path)
    y = df.pop("__target__")
    X = df
    if task == "classification":
        y = y.astype(str)
        counts = y.value_counts()
        keep = counts[counts >= MIN_CLASS_ROWS].index
        mask = y.isin(keep)
        X, y = X[mask], y[mask]
        if y.nunique() < 2:
            raise ValueError("fewer than 2 usable classes")
    else:
        y = pd.to_numeric(y, errors="coerce")
        mask = y.notna()
        X, y = X[mask], y[mask]
        if len(y) < 50 or y.nunique() < 3:
            raise ValueError("regression target unusable")
    X = X.reset_index(drop=True)
    y = y.reset_index(drop=True)

    feats = extract_meta_features(X, y, task)          # computed on the data as it is
    Xp, num, cat = prepare_X(X)
    algos = ALGOS_CLF if task == "classification" else ALGOS_REG
    row = dict(feats)
    for name, model in algos.items():
        r = run_cv(name, model, Xp, y, task, num, cat)
        for k, v in r.items():
            row[f"{k}_{name}"] = v
    return row


def run_experiments(task, base, max_minutes=90, max_datasets=None, retry_failed=False):
    assert task in ("classification", "regression")
    folder, short = ("clf", "clf") if task == "classification" else ("reg", "reg")
    res_file = f"{base}/results/{short}_experiments.csv"
    fail_file = f"{base}/results/failed_experiments.csv"
    os.makedirs(f"{base}/results", exist_ok=True)

    lst = pd.read_csv(f"{base}/datasets_list.csv")
    lst = lst[lst.task == task].sort_values("n_rows")

    done = set(pd.read_csv(res_file)["did"]) if os.path.exists(res_file) else set()
    failed = set(pd.read_csv(fail_file)["did"]) if os.path.exists(fail_file) and not retry_failed else set()
    todo = [r for r in lst.itertuples()
            if r.did not in done and r.did not in failed and os.path.exists(f"{base}/data/{folder}/{r.did}.csv")]
    print(f"[{task}] {len(done)} ho chuke | {len(failed)} fail (skip) | {len(todo)} baqi | budget {max_minutes} min")

    start, n_now = time.time(), 0
    for i, r in enumerate(todo, 1):
        if (time.time() - start) > max_minutes * 60:
            print("Time budget khatam. Yehi cell dobara chalayein, wahin se shuru hoga.")
            break
        if max_datasets and n_now >= max_datasets:
            print(f"max_datasets={max_datasets} poore hue.")
            break
        t0 = time.time()
        try:
            row = {"did": r.did, "name": r.name, "split": r.split}
            row.update(process_dataset(f"{base}/data/{folder}/{r.did}.csv", task))
            pd.DataFrame([row]).to_csv(res_file, mode="a", header=not os.path.exists(res_file), index=False)
            n_now += 1
            print(f"[{i}/{len(todo)}] OK     did={r.did:<6} {r.name[:28]:<28} {time.time()-t0:5.0f}s", flush=True)
        except Exception as e:
            pd.DataFrame([{"did": r.did, "name": r.name, "task": task, "error": str(e)[:150]}]).to_csv(
                fail_file, mode="a", header=not os.path.exists(fail_file), index=False)
            print(f"[{i}/{len(todo)}] FAILED did={r.did:<6} {r.name[:28]:<28} {str(e)[:60]}", flush=True)
    total = len(pd.read_csv(res_file)) if os.path.exists(res_file) else 0
    print(f"Ab tak {total} / {len(lst)} datasets ka result save hai: {res_file}")
