# Brain.md: AI Dataset Advisor

> **What is this file?** The project's single source of truth and memory. Read it first before writing any code (humans and AI assistants). Keep it updated whenever a decision changes. Details live in `docs/PRD.md`, `docs/TRD.md`, `docs/UIUX_Brief.md` and `docs/App_Flow.md`.

## 1. Project Summary

**AI Dataset Advisor** is a beginner-friendly web app. A user uploads a CSV/Excel file, sees a data summary, cleans it (Auto / Guided / Manual), and gets the **top 3 recommended ML algorithms** (from a meta-learning model trained on public datasets). The recommended algorithms and a baseline are trained on the user's data and compared in a dashboard.

- University: Rachna College of Engineering and Technology (UET Lahore constituent college), Department of Computer Science
- Team: Mubashra Nadeem (2024-CS-404), Laiba Ilyas (2024-CS-410), Fatima Tul Zahra (2024-CS-420)
- Supervisor: Dr. Natasha Nigar
- Focus: combine profiling, guided cleaning, algorithm recommendation and comparison in **one simple tool**. We do **not** claim a new cleaning or algorithm-selection technique.

## 2. Roles

| Member | Area |
|---|---|
| Member 1 | Frontend (React) |
| Member 2 | Backend, data processing, cleaning |
| Member 3 | ML: datasets, meta-features, meta-model, evaluation |

## 3. Tech Stack

- Frontend: React (Vite), JavaScript, HTML5, CSS3, Plotly
- Backend: Python 3.11, FastAPI, Pydantic, Pandas, NumPy, openpyxl
- ML: scikit-learn, Joblib
- Offline experiments: Google Colab + OpenML + Google Drive
- Tools: Git/GitHub, VS Code
- SQLite: optional only; **not used** in the core system
- **Pin the same `scikit-learn`, `pandas`, `numpy` versions in Colab and `backend/requirements.txt`.**

## 4. Architecture in One Minute

- Two parts: **offline** (Colab: build `meta_table.csv`, train `meta_model_*.joblib`) and **online** (FastAPI loads the saved meta-models at startup; React talks to it via `/api`).
- No database. User files are temporary, in `storage/<session_id>/<dataset_id>/`.
- Per dataset: `original.csv` (never modified), `cleaning_plan.json`, `cleaned.csv` (regenerated from original + plan), `results.json`.
- Anonymous **session cookie** (HttpOnly) identifies each visitor. Every dataset access checks ownership; wrong session returns **404**. No "list all files" endpoint.
- Cleanup task deletes sessions after 2 hours of inactivity; users can also click **Delete my data**.

## 5. Key Decisions (and Why)

| # | Decision | Why |
|---|---|---|
| D1 | Cleaning has 3 modes: Auto, Guided, Manual | Beginners need automation; others want control |
| D2 | Auto Clean applies only *safe* actions; risky ones (ID-like columns, outliers) are asked | Cleaning can hurt models (Neutatz et al., 2022) |
| D3 | Original file is never modified; Undo = delete cleaned version | Safety and trust |
| D4 | Meta-model predicts the score of every algorithm; top 3 are recommended | Several algorithms often score almost the same; a single "best" label is unstable |
| D5 | Simple meta-features (rows, columns, missing %, class balance, etc.) | Lightweight and easy to explain (unlike graph-based deep models) |
| D6 | Encoding/imputation/scaling live inside the sklearn `Pipeline` | Avoids data leakage; lets the Models page work without prior cleaning |
| D7 | Always train a baseline (Dummy) model | Shows whether models learned anything |
| D8 | Files, not a database; user data temporary | Simplicity and privacy |
| D9 | User data is never used to train the meta-model | Privacy |
| D10 | Three flows supported: Clean only, Clean then Models, Models only | Different user needs |
| D11 | "Reason" texts for recommendations come from rule templates, not from the meta-model | Honest explainability |
| D12 | Colab for experiments, local VS Code for the website | Colab is good for long jobs, not for web servers |

## 6. Folder Map

```
backend/app/{main.py, config.py, routers/, services/, schemas/}
backend/artifacts/{meta_model_clf.joblib, meta_model_reg.joblib, meta_table.csv}
ml/{datasets_list.csv, build_meta_dataset.py, train_meta_model.py, evaluate_recommender.py, notebooks/}
frontend/src/{pages/, components/, api/, styles/}
docs/  data/ (not in git)  storage/ (not in git)
```

## 7. API Summary (base `/api`)

`GET /session`, `DELETE /session`, `POST /datasets/upload`, `POST /datasets/{id}/select-sheet`, `GET /datasets`, `DELETE /datasets/{id}`, `GET /datasets/{id}/profile`, `GET /datasets/{id}/cleaning/suggestions`, `POST /datasets/{id}/cleaning/auto`, `POST /datasets/{id}/cleaning/apply`, `POST /datasets/{id}/cleaning/reset`, `GET /datasets/{id}/download`, `GET /datasets/{id}/columns`, `POST /datasets/{id}/recommend`, `POST /datasets/{id}/train`, `GET /datasets/{id}/results`, `GET /datasets/{id}/results/download`. Full details in the TRD.

## 8. Defaults and Constants (change only in `config.py`)

Max upload 20 MB; training sample cap 50,000 rows; retention 2 h; cleanup every 10 min; drop column if missing above 60%; ID-like if unique ratio is at least 95%; classification if target has at most 20 unique values (or non-numeric); test size 0.2; random state 42; 60 s per model.

## 9. Coding Conventions

- Python: PEP 8, type hints, docstrings on public functions; one responsibility per service file; Pydantic schemas for all requests and responses.
- JavaScript: functional React components, one component per file, API calls only inside `src/api/`.
- Branching: `main` (stable), `dev` (integration), `feature/<name>`; pull request plus one review before merging to `dev`.
- Commit messages: short, present tense ("Add duplicate detection").
- Never commit: `.env`, `storage/`, `data/`, `node_modules/`, `venv/`.
- Every new feature: add a test, update the README or this file.

## 10. Rules for AI Assistants Working on This Project

**Do:**
- Follow the decisions in section 5 and the specs in `docs/`.
- Keep the original file untouched; build cleaning as a replayable plan.
- Put all preprocessing for models inside sklearn Pipelines fitted on training data only.
- Ask before changing an API contract, a folder structure or a decision.
- Write small, testable functions and include error handling with user-friendly messages.

**Do not:**
- Add a database, user accounts or permanent storage of user data.
- Log or print dataset contents.
- Serve `storage/` as static files or add a "list all datasets" endpoint.
- Use user data to train the meta-model.
- Claim the project invents a new technique.
- Upgrade library versions without updating Colab and `requirements.txt` together.

## 11. Current Status (update regularly)

| Phase | Status |
|---|---|
| 0. Planning documents | In progress |
| 1. Repo and setup | Not started |
| 2. Meta-dataset and meta-model (Colab) | Not started |
| 3. Upload, session, profiling | Not started |
| 4. Cleaning engine | Not started |
| 5. Frontend: Landing and Clean | Not started |
| 6. Recommend, train, Models page | Not started |
| 7. Integration, privacy, testing | Not started |
| 8. Documentation and demo | Not started |

**Next step:** approve the PRD/TRD, create the GitHub repository and folder structure.

## 12. Open Questions

- Final upload size and row limits.
- Deployed publicly or local demo?
- Final list of OpenML datasets (train vs held-out).

## 13. Glossary

| Term | Meaning |
|---|---|
| Meta-learning | Learning from past ML experiments on many datasets to predict what works on a new one |
| Meta-features | Numbers describing a dataset (rows, columns, missing %, class balance, ...) |
| Meta-table | Table of meta-features plus algorithm scores for each public dataset |
| Baseline | A trivial model (most common class or mean) used for comparison |
| Held-out datasets | Public datasets kept aside to test the recommender |
| Pipeline | sklearn object chaining preprocessing and a model |
| Data leakage | Information from test data leaking into training, causing fake high scores |
| Session | Anonymous visitor identity via cookie; owns its temporary files |
| Regret | Best possible score minus the score of the recommended algorithm |
