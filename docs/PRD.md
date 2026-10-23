---
title: "AI Dataset Advisor: Product Requirements Document (PRD)"
---

| | |
|---|---|
| **Project** | AI Dataset Advisor |
| **Institution** | Department of Computer Science, Rachna College of Engineering and Technology (A Constituent College of UET Lahore) |
| **Team** | Mubashra Nadeem (2024-CS-404), Laiba Ilyas (2024-CS-410), Fatima Tul Zahra (2024-CS-420) |
| **Supervisor** | Dr. Natasha Nigar |
| **Document version** | 1.0 (Draft) |

# 1. Purpose of this Document

This document describes **what** the AI Dataset Advisor must do and **who** it is for. It does not describe how it is built (see the TRD) or how it looks (see the UI/UX Brief). Every feature in the project should trace back to a requirement in this document.

# 2. Problem Statement

Students and beginners who work with datasets for machine learning struggle to:

- Find data quality problems (missing values, duplicate rows, wrong data types, outliers).
- Decide which cleaning steps are safe and which are harmful.
- Choose a suitable machine learning algorithm for their dataset.
- Compare several models fairly and understand the results.

Existing tools cover parts of this (YData Profiling for profiling, H2O AutoML, PyCaret and auto-sklearn for model search), but they are mostly code-based, and no single beginner-friendly tool combines profiling, guided cleaning, algorithm recommendation and model comparison.

# 3. Product Vision

A simple web application where a beginner can upload a CSV or Excel file, understand its quality, clean it with guidance (or automatically), and receive a small set of recommended algorithms that are trained and compared on their own data, without writing any code.

# 4. Goals and Non-Goals

## 4.1 Goals

1. Let users upload CSV/Excel files and see an easy-to-read summary of their data.
2. Detect common data quality issues and explain them in plain language.
3. Offer three cleaning modes: **Auto Clean**, **Guided**, and **Manual**.
4. Never modify the user's original file; allow undo/reset at any time.
5. Recommend the top 3 suitable algorithms using a **meta-learning model** trained on public datasets.
6. Train the recommended algorithms plus a **baseline** on the user's data and compare them with appropriate metrics.
7. Support users who only want cleaning, users who only want model recommendations, and users who want both.
8. Protect user privacy: each user sees only their own files, and files are deleted automatically.

## 4.2 Non-Goals (Out of Scope)

- Inventing a new cleaning or algorithm-selection technique (the aim is to make the process easy, not to claim novelty).
- Deep learning, image, text or time-series data (tabular data only).
- User accounts, passwords, or permanent storage of user data.
- Hyperparameter tuning or full AutoML pipeline search.
- Using user-uploaded data to train or improve the meta-model.
- Mobile app (a responsive website is enough).

# 5. Target Users

| Persona | Description | Main need |
|---|---|---|
| **Beginner Student** | Learning ML, does not know what cleaning is needed | Auto Clean and simple explanations |
| **Intermediate Student** | Knows basics, wants control | Guided mode and algorithm comparison |
| **Quick Checker** | Already has clean data | Go directly to the Models page, upload and compare |
| **Evaluator / Supervisor** | Reviews the project | Clear flow, sensible results, evaluation of the recommender |

# 6. User Stories

| ID | As a... | I want to... | So that... |
|---|---|---|---|
| US-01 | user | upload a CSV or Excel file | I can analyze my own data |
| US-02 | user | see a summary of rows, columns, types, missing values and duplicates | I understand my dataset |
| US-03 | beginner | click one button to clean my data safely | I do not need cleaning knowledge |
| US-04 | user | see a list of suggested fixes with a plain-language reason | I can decide what to apply |
| US-05 | user | see a report of what changed and a before/after summary | I trust the result |
| US-06 | user | undo all cleaning and go back to the original | I can try again without risk |
| US-07 | user | download the cleaned file | I can use it elsewhere |
| US-08 | user | continue to the Models page with my cleaned file selected | I do not upload again |
| US-09 | user | upload a file directly on the Models page | I can skip cleaning |
| US-10 | user | choose the target column and task (with an automatic suggestion) | the system trains the right type of model |
| US-11 | user | get 3 recommended algorithms with a short reason | I know where to start |
| US-12 | user | see models and a baseline compared in a table and charts | I can pick the best one |
| US-13 | user | download the results as CSV | I can include them in my report |
| US-14 | user | delete my data immediately | my privacy is protected |
| US-15 | user | never see other users' files | my data stays private |

# 7. Functional Requirements

## 7.1 Upload and Session

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Accept `.csv`, `.xlsx`, `.xls` files up to the configured size limit (default 20 MB). | Must |
| FR-02 | If an Excel file has several sheets, let the user choose the sheet. | Should |
| FR-03 | Reject unsupported or corrupted files with a clear message. | Must |
| FR-04 | Create an anonymous session for each visitor; tie every uploaded file to that session. | Must |

## 7.2 Profiling

| ID | Requirement | Priority |
|---|---|---|
| FR-05 | Show rows, columns, memory size, duplicate row count, total missing percentage. | Must |
| FR-06 | Per column: detected type, missing count/percentage, unique count, sample values. | Must |
| FR-07 | Show a missing-values chart. | Should |

## 7.3 Cleaning

| ID | Requirement | Priority |
|---|---|---|
| FR-08 | Detect: missing values, duplicate rows, wrong data types, constant columns, ID-like columns, text inconsistencies, outliers. | Must |
| FR-09 | Provide each suggestion with a severity, a recommended action and a plain-language reason. | Must |
| FR-10 | **Auto Clean mode:** apply only safe actions automatically and ask the user about risky actions. | Must |
| FR-11 | **Guided mode:** show all suggestions, with recommended ones pre-selected; the user confirms. | Must |
| FR-12 | **Manual mode:** the user chooses each action and its method. | Should |
| FR-13 | Never overwrite the original file; produce a separate cleaned file. | Must |
| FR-14 | Produce a cleaning report (what was changed, how many rows/columns/values). | Must |
| FR-15 | Provide Reset/Undo to return to the original. | Must |
| FR-16 | Allow download of the cleaned file (CSV). | Must |

## 7.4 Algorithm Recommendations

| ID | Requirement | Priority |
|---|---|---|
| FR-17 | The user selects the target column; the system suggests classification or regression and the user can override. | Must |
| FR-18 | Extract meta-features from the user's dataset. | Must |
| FR-19 | Use the trained meta-model to rank algorithms and return the top 3. | Must |
| FR-20 | Show a short reason for each recommendation. | Should |
| FR-21 | Work on both cleaned and uncleaned files (preprocessing is part of the training pipeline). | Must |

## 7.5 Training and Comparison

| ID | Requirement | Priority |
|---|---|---|
| FR-22 | Train the 3 recommended algorithms plus a baseline model on the user's data. | Must |
| FR-23 | Classification metrics: accuracy, precision, recall, F1. Regression metrics: MAE, RMSE, R². | Must |
| FR-24 | Show a comparison table and charts; highlight the best model. | Must |
| FR-25 | Allow download of results as CSV. | Should |
| FR-26 | Enforce time and size limits so training cannot hang the server. | Must |

## 7.6 Privacy and Data Lifecycle

| ID | Requirement | Priority |
|---|---|---|
| FR-27 | A user can access only files belonging to their own session. | Must |
| FR-28 | Delete files automatically after the retention period (default 2 hours of inactivity). | Must |
| FR-29 | "Delete my data now" button. | Must |
| FR-30 | Display a short privacy notice. | Must |

# 8. Non-Functional Requirements

| ID | Category | Requirement |
|---|---|---|
| NFR-01 | Usability | A first-time user can finish upload, cleaning and download without help. |
| NFR-02 | Performance | Profiling of a 20 MB file completes in under 15 seconds; training completes within the time limit (default 2 minutes total). |
| NFR-03 | Reliability | Errors return a clear message; the app never shows a raw stack trace. |
| NFR-04 | Privacy/Security | No user data in logs; files not publicly accessible; HTTPS on deployment. |
| NFR-05 | Explainability | Every suggestion and recommendation has an understandable reason. |
| NFR-06 | Reproducibility | Experiments use fixed random seeds and pinned library versions. |
| NFR-07 | Compatibility | Works on the latest Chrome, Edge and Firefox; usable on a tablet-size screen. |
| NFR-08 | Maintainability | Code in modules with a README; consistent code style. |

# 9. Success Metrics

| Metric | Target |
|---|---|
| Recommender **top-3 hit rate** on held-out datasets (the best algorithm appears in the top 3) | Higher than the "always recommend Random Forest" baseline |
| Mean **regret** (best score minus score of the top-1 recommended algorithm) | Lower than the baseline |
| End-to-end flow success in testing (upload to results on 10 different datasets) | 100% |
| Cleaning never modifies the original file | 100% |
| User testing with 5 classmates: task completion without help | At least 80% |

# 10. Assumptions and Constraints

- The project is a semester project; deployment is a demo (local or a free host).
- Meta-model training happens offline on Google Colab; the website only loads the saved model.
- Only tabular data with a single target column is supported.
- Limits (file size, rows, time) are configurable and can be adjusted after testing.

# 11. Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| Too few public datasets, so the meta-model is weak | Poor recommendations | Collect at least 60 classification and 40 regression datasets; use OpenML |
| Experiments take too long | Delay | Run on Colab; sample large datasets to 5,000 rows; save progress to Drive regularly |
| Library version mismatch between Colab and backend | Model fails to load | Pin the same `scikit-learn` version everywhere |
| Cleaning harms model quality | Misleading results | Suggest, don't force; keep the original; allow undo |
| Privacy leak between users | Serious | Session ownership check on every request; auto-delete |
| Scope too large | Unfinished project | Prioritize Must items first; Should items only if time remains |

# 12. Milestones

| Phase | Deliverable |
|---|---|
| 0 | Planning documents approved |
| 1 | Repository and project setup |
| 2 | Meta-dataset built and meta-model trained (parallel with 3-5) |
| 3 | Upload, session and profiling working |
| 4 | Cleaning engine with three modes |
| 5 | Frontend: Landing and Clean wizard |
| 6 | Recommendation, training and Models wizard |
| 7 | Integration, privacy cleanup, testing |
| 8 | Documentation, report and demo |

# 13. Team Responsibilities

| Member | Area |
|---|---|
| Member 1 | Frontend (React interface, upload page, dataset summary, charts, results dashboard) |
| Member 2 | Backend and data processing (FastAPI, file handling, data-quality checks, cleaning functions) |
| Member 3 | Machine learning (public datasets, meta-features, recommendation model, evaluation of candidate algorithms) |

All members contribute to integration, testing, documentation and the final presentation.

# 14. Open Questions

1. Final maximum file size and row limit for uploads.
2. Whether to deploy publicly or demo locally.
3. Whether SQLite is used for optional experiment history (currently not required).
