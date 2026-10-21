---
title: "AI Dataset Advisor: App Flow"
---

# 1. Purpose

This document describes **how a user moves through the application** and how the frontend and backend talk to each other at each step. It covers the main journeys, decisions, error flows and the data lifecycle.

# 2. Overall Flow

```
                               [ Landing Page ]
                              /                \
                 "Clean my data"              "Find best models"
                         |                            |
                    [ Upload ]                 [ Choose data source ]
                         |                     /        |         \
                   [ Overview ]        cleaned file  earlier file  upload new
                         |                     \        |         /
                    [ Clean ]                       [ Setup: target + task ]
                         |                                  |
                    [ Result ]                       [ Recommendations ]
                    /    |     \                            |
          Download   Undo   Continue to Models ------->  [ Train + Compare ]
          (end)      (back                                  |
                    to Clean)                          [ Results Dashboard ]
                                                        /        |        \
                                                 Download   Change target   Back to
                                                 results    (to Setup)      cleaning
```

# 3. User Journeys

## Journey A: Clean Only

| Step | User action | System action |
|---|---|---|
| 1 | Opens Landing, clicks **Clean my data** | Frontend calls `GET /session`; backend creates a session cookie if none exists |
| 2 | Uploads a file | `POST /datasets/upload`; file saved as `original.csv` (or sheet list returned for Excel) |
| 3 | (Excel only) picks a sheet | `POST /select-sheet` |
| 4 | Sees overview | `GET /profile` returns summary and column details |
| 5 | Chooses a mode | Frontend shows the matching UI |
| 6a | **Auto:** clicks "Clean my data" | `POST /cleaning/auto` applies safe actions; returns report and risky items |
| 6b | **Auto:** answers risky questions | `POST /cleaning/apply` with the user's choices |
| 6c | **Guided/Manual:** reviews and applies | `GET /cleaning/suggestions` then `POST /cleaning/apply` |
| 7 | Sees result | Backend returns the report, before/after summary; `cleaned.csv` exists |
| 8 | Clicks **Download** | `GET /download?version=cleaned` |
| 9 | Optionally **Undo** | `POST /cleaning/reset` deletes the cleaned version |

## Journey B: Clean, then Models

Same as Journey A up to step 7, then:

| Step | User action | System action |
|---|---|---|
| 8 | Clicks **Continue to Models** | Frontend navigates to `/models` with `dataset_id` in state; "Use cleaned file" is pre-selected |
| 9 | Selects target (task auto-suggested) | `GET /columns` returns columns and suggested task |
| 10 | Clicks **Get recommendations** | `POST /recommend` extracts meta-features, runs the meta-model, returns top 3 with reasons |
| 11 | Clicks **Train and compare** | `POST /train` trains 3 models plus baseline, returns metrics |
| 12 | Views dashboard, downloads CSV | `GET /results/download` |

## Journey C: Models Only

| Step | User action | System action |
|---|---|---|
| 1 | Clicks **Find best models** | Session created if needed |
| 2 | Selects **Upload a new file** (or an earlier file) | Upload as in Journey A; no cleaning step required |
| 3 to 6 | Same as Journey B steps 9 to 12 | Training uses `original.csv` because no cleaned file exists; the training pipeline imputes missing values and encodes categories itself |

# 4. Decision Points

| Where | Decision | Result |
|---|---|---|
| Upload | File valid? | No: show error, stay on Upload |
| Upload | Excel with several sheets? | Yes: show sheet picker |
| Clean | Which mode? | Auto, Guided or Manual flow |
| Auto Clean | Any risky items? | Yes: ask the user; No: go straight to Result |
| Models, Data step | Which source? | Cleaned file, earlier file or new upload |
| Models, Setup | Suggested task correct? | User accepts or overrides |
| Train | Dataset too large? | Sample to the row limit and tell the user |
| Train | A model exceeds the time limit? | Mark "timed out", continue with others |

# 5. Data Version Logic (Which file is used?)

```
 Is there a cleaned.csv for this dataset?
     |-- yes --> default = cleaned.csv   (user may switch to original)
     |-- no  --> default = original.csv
```

- Cleaning never modifies `original.csv`.
- `cleaned.csv` is regenerated from `original.csv` plus `cleaning_plan.json`.
- Reset removes `cleaned.csv` and `cleaning_plan.json`.

# 6. Session and Data Lifecycle

```
 First visit
    |
    v
 Backend creates session_id (cookie) --> storage/<session_id>/
    |
    v
 User uploads files --> storage/<session_id>/<dataset_id>/...
    |
    v
 Every request: check cookie -> check dataset belongs to this session
    |                              |
    |                              +-- not found --> 404
    v
 User is inactive for 2 hours  OR  user clicks "Delete my data"
    |
    v
 Cleanup task / DELETE /session  --> entire session folder removed
```

- A background task checks every 10 minutes for expired sessions.
- User A can never see User B's files because the path is built from A's own cookie.

# 7. Error and Edge-Case Flows

| Situation | Flow |
|---|---|
| Invalid file type | Show message, keep the user on Upload |
| File too large | Show the limit, keep the user on Upload |
| Empty file or fewer than 10 rows | Show message, keep the user on Upload |
| Session expired (cookie missing or session deleted) | Show "Session ended, files deleted", redirect to Upload; remove stale entries from "Recent files" |
| Target has one unique value | Show message on Setup and block "Get recommendations" |
| Too many classes | Show warning and advice (choose another target or regression) |
| Training timeout | Show partial results with "timed out" next to the model |
| Network or server error | Error banner with a **Retry** button; no data lost |
| User refreshes the page | Dataset list restored from the session (server) and `localStorage`; wizard returns to the first step of the current page with the file selected |

# 8. Frontend Navigation Rules

- The step bar allows going **back** freely; going **forward** only when the current step is complete.
- Changing the data source or target on the Models page clears old recommendations and results.
- Applying new cleaning actions after results exist marks existing results as "outdated".
- The header always shows **Delete my data**, which asks for confirmation, then returns to Landing.

# 9. Sequence Summary (Backend Calls)

```
 Clean flow:     GET /session -> POST /upload -> GET /profile -> GET /cleaning/suggestions
                 -> POST /cleaning/auto | /cleaning/apply -> GET /download

 Models flow:    GET /columns -> POST /recommend -> POST /train -> GET /results/download

 Housekeeping:   POST /cleaning/reset, DELETE /datasets/{id}, DELETE /session
```
