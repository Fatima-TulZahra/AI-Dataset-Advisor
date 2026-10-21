---
title: "AI Dataset Advisor: Technical Requirements Document (TRD)"
---

| | |
|---|---|
| **Project** | AI Dataset Advisor |
| **Document version** | 1.0 (Draft) |
| **Related documents** | PRD, UI/UX Brief, App Flow, Brain.md |

# 1. Purpose

This document explains **how** the system is built: architecture, technologies, data handling, APIs, the cleaning engine, the meta-learning pipeline and the development workflow. Values marked *(default)* are starting points and can be tuned after testing.

# 2. System Architecture

```
 +-------------------+        HTTPS / JSON        +---------------------------+
 |  React Frontend   |  <----------------------> |  FastAPI Backend          |
 |  (Landing, Clean, |   cookie: session_id       |  - Session + ownership    |
 |   Models pages)   |                            |  - Profiling              |
 +-------------------+                            |  - Cleaning engine        |
                                                  |  - Meta-feature extractor |
                                                  |  - Recommender (meta-model)|
                                                  |  - Trainer / evaluator    |
                                                  +------------+--------------+
                                                               |
                                      +------------------------+---------------+
                                      |                                        |
                              storage/ (user files,                  artifacts/ (meta_model.joblib,
                              temporary, per session)                meta_table.csv; read-only)
```

Two separate parts exist:

1. **Offline part (Google Colab):** collects public datasets, extracts meta-features, runs experiments, trains the meta-model. Runs once; output is saved as files.
2. **Online part (website):** loads the saved meta-model at startup and serves users.

# 3. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React.js (Vite), JavaScript, HTML5, CSS3 | UI and components |
| Charts | Plotly (react-plotly.js) | Missing-value chart, model comparison charts |
| HTTP client | Fetch API or Axios (with credentials enabled) | Calls to the backend |
| Backend | Python 3.11, FastAPI, Uvicorn | REST API |
| Validation | Pydantic | Request/response schemas |
| Data | Pandas, NumPy, openpyxl | Reading and manipulating CSV/Excel |
| ML | scikit-learn | Models, pipelines, metrics |
| Model storage | Joblib | Save/load the meta-model |
| Optional storage | SQLite | Optional experiment history (not required) |
| Offline experiments | Google Colab, OpenML (`openml` package) | Dataset collection and experiments |
| Tools | Git/GitHub, VS Code, Postman or Swagger UI (`/docs`) | Development and testing |

**Rule:** the exact versions of `scikit-learn`, `pandas` and `numpy` must be identical in Colab and in the backend `requirements.txt`, because a Joblib file saved with one scikit-learn version may fail to load with another.

# 4. Repository Structure

```
ai-dataset-advisor/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app, startup (load meta-model), CORS
│   │   ├── config.py               # limits, thresholds, paths
│   │   ├── routers/
│   │   │   ├── session.py
│   │   │   ├── datasets.py         # upload, list, delete
│   │   │   ├── profiling.py
│   │   │   ├── cleaning.py
│   │   │   └── models.py           # recommend, train, results
│   │   ├── services/
│   │   │   ├── session_service.py
│   │   │   ├── storage_service.py  # file paths, ownership, cleanup
│   │   │   ├── profiler.py
│   │   │   ├── cleaner.py
│   │   │   ├── meta_features.py    # shared with ml/ scripts
│   │   │   ├── recommender.py
│   │   │   └── trainer.py
│   │   └── schemas/                # Pydantic models
│   ├── artifacts/                  # meta_model_clf.joblib, meta_model_reg.joblib, meta_table.csv
│   ├── tests/
│   └── requirements.txt
├── ml/                             # offline scripts and notebooks
│   ├── datasets_list.csv           # OpenML dataset IDs (train and held-out)
│   ├── build_meta_dataset.py
│   ├── train_meta_model.py
│   ├── evaluate_recommender.py
│   └── notebooks/*.ipynb
├── frontend/
│   ├── src/ (pages/, components/, api/, styles/)
│   └── package.json
├── data/                           # NOT pushed to GitHub (downloaded by script)
├── storage/                        # NOT pushed to GitHub (user files)
├── docs/                           # PRD, TRD, UI/UX Brief, App Flow
├── Brain.md
├── README.md
└── .gitignore
```

# 5. Data Storage Design

No database is required for the core system. Files are used.

## 5.1 Permanent files (development)

| File | Where | In GitHub? |
|---|---|---|
| Public datasets | `data/public_datasets/`, `data/heldout_datasets/` | No (re-downloaded using `datasets_list.csv`) |
| `meta_table.csv` | `backend/artifacts/` | Yes (small) |
| `meta_model_*.joblib` | `backend/artifacts/` | Yes if under about 100 MB (use `compress=3`) |
| Code, notebooks, docs | repo | Yes |

## 5.2 Temporary user files (runtime)

```
storage/
└── <session_id>/
    ├── session.json                 # created_at, last_active
    └── <dataset_id>/
        ├── original.csv             # never modified
        ├── cleaning_plan.json       # list of applied cleaning operations
        ├── cleaned.csv              # generated from original + plan
        ├── cleaning_report.json
        ├── results.json             # last training results
        └── info.json                # original filename, upload time, rows, cols
```

- Excel uploads are converted to `original.csv` after the user chooses a sheet.
- **Undo/Reset** deletes `cleaned.csv` and `cleaning_plan.json`; the cleaned file is always reproducible by replaying the plan on the original.
- Folders are nested by session so that deleting a session deletes all its files in one step.

# 6. Privacy and Session Design

1. On first visit the backend creates a random `session_id` (UUID4) and sends it as a cookie: `HttpOnly`, `SameSite=Lax`, `Secure` in production.
2. Every endpoint that touches a dataset resolves the path as `storage/<session_id_from_cookie>/<dataset_id>/`. A dataset that does not exist under the caller's session returns **404** (not 403), so its existence is not revealed.
3. There is **no endpoint that lists all datasets**; only "list my datasets" (current session).
4. `storage/` is never served as static files.
5. `dataset_id` values are random UUIDs.
6. Logs record only file name, size and status; never cell values.
7. `DELETE /api/session` removes the whole session folder immediately.
8. **Cleanup task:** a background task runs every 10 minutes and deletes sessions whose `last_active` is older than the retention period *(default 2 hours)*.
9. User data is never used to train the meta-model.

# 7. Configuration Constants *(defaults)*

| Constant | Value |
|---|---|
| `MAX_UPLOAD_MB` | 20 |
| `MAX_ROWS_FOR_TRAINING` | 50,000 (sample if larger; the user is told) |
| `SESSION_RETENTION_HOURS` | 2 (inactivity) |
| `CLEANUP_INTERVAL_MIN` | 10 |
| `MISSING_DROP_COLUMN_THRESHOLD` | 0.60 |
| `ID_LIKE_UNIQUE_RATIO` | 0.95 |
| `NUMERIC_PARSE_THRESHOLD` | 0.90 |
| `TASK_CLASSIFICATION_MAX_UNIQUE` | 20 |
| `TEST_SIZE` | 0.20 |
| `RANDOM_STATE` | 42 |
| `MODEL_TIME_LIMIT_SEC` | 60 per model |

# 8. API Specification

Base path: `/api`. All responses are JSON. Errors use the form `{"error": {"code": "...", "message": "..."}}`.

| Method | Endpoint | Description | Main response |
|---|---|---|---|
| GET | `/session` | Create or confirm the session | `{session_id_created: bool}` |
| DELETE | `/session` | Delete all my data | `{deleted: true}` |
| POST | `/datasets/upload` | Multipart file upload | `{dataset_id, filename, sheets?}` |
| POST | `/datasets/{id}/select-sheet` | Choose sheet for Excel | `{dataset_id}` |
| GET | `/datasets` | List my datasets | `[{dataset_id, filename, has_cleaned, uploaded_at}]` |
| DELETE | `/datasets/{id}` | Delete one dataset | `{deleted: true}` |
| GET | `/datasets/{id}/profile` | Profile of original data | rows, cols, duplicates, missing %, per-column info |
| GET | `/datasets/{id}/cleaning/suggestions` | Detected issues | list of suggestions (see 9.2) |
| POST | `/datasets/{id}/cleaning/auto` | Run Auto Clean | report + `needs_confirmation` list |
| POST | `/datasets/{id}/cleaning/apply` | Apply selected actions (Guided/Manual) | report |
| POST | `/datasets/{id}/cleaning/reset` | Undo all cleaning | `{reset: true}` |
| GET | `/datasets/{id}/download?version=cleaned` | Download file | CSV stream |
| GET | `/datasets/{id}/columns` | Columns and suggested task for a target | columns, types |
| POST | `/datasets/{id}/recommend` | `{target, task, use_version}` | top 3 algorithms + reasons |
| POST | `/datasets/{id}/train` | `{target, task, algorithms, use_version}` | metrics per model, best model |
| GET | `/datasets/{id}/results` | Last results | same as train |
| GET | `/datasets/{id}/results/download` | Results CSV | CSV stream |

`use_version` is `"cleaned"` or `"original"`; if omitted, the backend uses `cleaned.csv` when it exists, otherwise `original.csv`.

# 9. Data Processing Details

## 9.1 Profiling

Computed with Pandas: shape, memory usage, duplicate count, per-column dtype (inferred type: numeric / categorical / datetime / text / boolean), missing count and percentage, unique count, a few sample values, and basic statistics for numeric columns.

## 9.2 Cleaning Engine

Each detected issue becomes a **suggestion object**:

```json
{
  "id": "missing_age",
  "type": "missing_values",
  "column": "age",
  "severity": "medium",
  "safe_for_auto": true,
  "recommended_action": "impute_median",
  "alternatives": ["impute_mean", "drop_rows", "drop_column"],
  "reason": "12% of values are missing. The median is a safe choice."
}
```

| Issue | Detection rule | Recommended action | Safe for Auto? |
|---|---|---|---|
| Duplicate rows | exact duplicate rows | drop duplicates | Yes |
| Text inconsistency | leading/trailing spaces, mixed case in categorical columns | strip spaces, normalize case | Yes |
| Wrong data type | text column where at least 90% of values parse as numbers (or dates) | convert type | Yes |
| Constant column | one unique value | drop column | Yes |
| Very high missing | missing above 60% | drop column | Yes |
| Missing numeric | missing between 0% and 60% | impute median | Yes |
| Missing categorical | missing between 0% and 60% | impute mode | Yes |
| Missing target | target value missing (Models step) | drop those rows | Yes |
| ID-like column | unique ratio of at least 95% and name or type looks like an identifier | drop column | **No** (ask) |
| Outliers | outside 1.5 x IQR (numeric) | flag; option to clip (winsorize) | **No** (ask; default: keep) |

**Modes**

- **Auto Clean:** applies all "safe for auto" actions, then returns `needs_confirmation` for the rest. The frontend asks the user about each one.
- **Guided:** returns all suggestions; the frontend pre-ticks the recommended ones; user submits the selected list.
- **Manual:** same as Guided but nothing is pre-selected and alternatives can be chosen.

**Execution rules**

- Actions are executed in a fixed order: fix types, normalize text, drop duplicates, drop columns, handle missing values, handle outliers.
- The selected actions are saved to `cleaning_plan.json`; `cleaned.csv` is produced by applying the plan to `original.csv` (pure function, no hidden state).
- A report is returned: rows before/after, columns before/after, each action with counts.

## 9.3 Meta-Features

Computed by `meta_features.py` (the same file is used offline and online so values are consistent).

| Meta-feature | Description |
|---|---|
| `n_rows`, `n_cols` | Size (log-transformed when used by the model) |
| `numeric_ratio`, `categorical_ratio` | Share of numeric / categorical columns |
| `missing_pct` | Overall missing percentage |
| `n_classes` | Number of target classes (classification only) |
| `class_imbalance` | Majority class share minus minority class share, or ratio |
| `mean_abs_correlation` | Mean absolute pairwise correlation of numeric features |
| `target_skew`, `target_kurtosis` | Regression only |
| `mean_cardinality` | Average unique values of categorical columns |

# 10. Meta-Learning Pipeline (Offline, on Colab)

## 10.1 Steps

1. **Collect datasets:** at least 60 classification and 40 regression datasets from OpenML (IDs saved in `ml/datasets_list.csv`). Hold out about 15% as unseen test datasets.
2. **Standard preprocessing pipeline** (inside every model, fitted only on training folds):
   - numeric: median imputer, standard scaler
   - categorical: most-frequent imputer, `OneHotEncoder(handle_unknown="ignore", max_categories=20)`
3. **Extract meta-features** for each dataset.
4. **Run experiments:** 5-fold cross-validation for every candidate algorithm on every dataset; large datasets sampled to 5,000 rows; `random_state=42`.
5. **Save results** to `meta_table.csv` after each dataset (append mode, written to Google Drive) so a Colab disconnect does not lose progress.
6. **Train the meta-model:** a `RandomForestRegressor` with multi-output (one output per algorithm) predicts the cross-validation score of each algorithm from the meta-features. Separate meta-models for classification and regression.
7. **Evaluate on held-out datasets** (see 10.3).
8. **Save** `meta_model_clf.joblib` and `meta_model_reg.joblib` together with the list of feature names and algorithm names.

## 10.2 Candidate Algorithms

| Task | Algorithms | Baseline |
|---|---|---|
| Classification | Logistic Regression, KNN, Decision Tree, Random Forest, Gradient Boosting, SVM, Naive Bayes | `DummyClassifier(most_frequent)` |
| Regression | Linear/Ridge Regression, KNN, Decision Tree, Random Forest, Gradient Boosting, SVR | `DummyRegressor(mean)` |

Scoring: classification uses macro F1 (and accuracy as a secondary score); regression uses R² (or negative RMSE).

## 10.3 Recommender Evaluation

On held-out datasets, compute:

- **Top-3 hit rate:** how often the truly best algorithm is among the 3 recommended.
- **Mean regret:** best score minus the score of the top-1 recommendation.
- **Comparison with baselines:** "always Random Forest" and "random choice".

These numbers go into the final report.

# 11. Online Recommendation and Training

1. **Startup:** load both meta-models once into memory.
2. **Recommend:** extract meta-features of the selected data and target, predict a score per algorithm, sort, return the top 3. The *reason* text comes from simple rule templates based on meta-features and known algorithm traits (for example: "many categorical columns: tree-based models handle these well"); these are explanations, not outputs of the meta-model, and are described as such.
3. **Train:** for the top 3 algorithms plus the baseline:
   - split 80/20 (stratified for classification), `random_state=42`
   - build a pipeline (same preprocessing as in 10.1) so training works on cleaned **and** uncleaned data
   - fit and evaluate on the test split
   - compute metrics and training time; each model has a time limit; if exceeded, return "timed out" for that model
4. **Metrics:** classification: accuracy, precision, recall, F1 (macro), confusion matrix; regression: MAE, RMSE, R², predicted-vs-actual points.
5. **Task suggestion:** if the target has at most 20 unique values or is a non-numeric type, suggest classification; otherwise regression. The user can override.

# 12. Error Handling

| Situation | Response |
|---|---|
| Unsupported or corrupted file | 400, "Please upload a valid CSV or Excel file." |
| File too large | 413 with the limit in the message |
| Empty file or fewer than 10 rows | 400, explain minimum requirement |
| Dataset not found or not in session | 404 |
| Target has a single unique value | 422, "Target must have at least two different values." |
| Too many classes (above 50) or too few rows per class | 422 with advice |
| Training timeout | Partial results with "timed out" flagged |
| Unexpected error | 500 with a generic message; details only in server logs |

# 13. Security

- Validate file extension **and** content type; never execute uploaded content.
- Use `UploadFile` with a size check while streaming.
- Generate server-side file names; never use the user's filename in a path.
- CORS: allow only the frontend origin, with credentials.
- Do not log data values.
- Use HTTPS in deployment.

# 14. Testing Strategy

| Level | What | Tool |
|---|---|---|
| Unit | cleaner rules, meta-feature extraction, profiler | pytest |
| API | each endpoint, including ownership checks (user A cannot read user B's dataset) | pytest + FastAPI TestClient |
| ML | recommender returns 3 valid algorithms; training works on 10 diverse sample files | pytest and notebooks |
| Frontend | main flows manually; component checks | manual checklist |
| Privacy | two browser sessions cannot see each other's data; cleanup deletes expired sessions | manual + automated |
| End-to-end | Clean only; Clean then Models; Models only | manual checklist |

# 15. Development Workflow and Environments

- **Colab:** ML experiments only. Mount Google Drive, save progress after every dataset, fix library versions at the top of the notebook.
- **Local (VS Code):** backend and frontend.
- **GitHub:** branches `main` (stable), `dev` (integration), `feature/*` (individual work); pull requests need one review.
- **Commands (backend):** `pip install -r requirements.txt`, `uvicorn app.main:app --reload`.
- **Commands (frontend):** `npm install`, `npm run dev`.

# 16. Deployment (Optional)

For the demo, running locally is sufficient. If deployed publicly: backend on a small VM or a free tier host with persistent disk for `artifacts/`, frontend as static files, HTTPS enabled, same-site cookies configured.
