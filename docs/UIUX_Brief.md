---
title: "AI Dataset Advisor: UI/UX Brief"
---

# 1. Purpose

This brief tells the frontend developer (and anyone designing screens) **what the interface should look like and how it should behave**. It is a guide, not a pixel-perfect design; wireframes below are simplified sketches.

# 2. Design Principles

1. **Beginner-first:** plain language, no jargon without a short explanation.
2. **One thing at a time:** both tool pages are step-by-step wizards.
3. **Explain every suggestion:** every cleaning suggestion and recommendation has a one-line reason.
4. **Safe by default:** the original file is never changed; Undo/Reset is always visible.
5. **Transparent:** always show what changed (before/after) and which file is being used.
6. **Calm and clean:** lots of white space, few colors, no clutter.
7. **Private:** a visible privacy note and a "Delete my data" button.

# 3. Visual Direction

| Item | Guidance |
|---|---|
| Overall style | Clean, modern, light background, rounded cards |
| Color use | Match the proposal diagrams: **purple** = data input, **pink** = data preparation (cleaning), **teal** = machine learning, **blue** = results. Use these as accent colors on the matching steps and pages. |
| Neutral colors | White/off-white background, dark grey text, light grey borders |
| Status colors | Green = success/recommended, amber = warning, red = error/danger |
| Typography | One sans-serif family (for example Inter or system font); headings bold, body 16 px |
| Icons | One icon set (for example Lucide or Material) |
| Charts | Plotly with the same accent colors; always include axis titles and a short caption |
| Buttons | One primary style (filled) per screen; secondary style outlined; destructive actions in red |

# 4. Site Map

```
/                 Landing page
/clean            Clean wizard  (Upload -> Overview -> Clean -> Result)
/models           Models wizard (Data -> Setup -> Recommend -> Results)
/privacy          Short privacy information (can be a modal)
```

Global header on all pages: logo/name (links to Home), links **Clean**, **Models**, and a small **Delete my data** action.

# 5. Page Specifications

## 5.1 Landing Page

**Goal:** explain the tool in 10 seconds and send the user to the correct tool.

```
+----------------------------------------------------------------+
| AI Dataset Advisor                    [Clean]  [Models]  [Delete my data] |
+----------------------------------------------------------------+
|                                                                |
|   Understand, clean and model your dataset                     |
|   Upload a CSV or Excel file and get guided help, no code.     |
|                                                                |
|   +----------------------+      +----------------------+       |
|   |  Clean my data       |      |  Find the best models|       |
|   |  Find problems, fix  |      |  Pick a target, get  |       |
|   |  them, download.     |      |  recommended         |       |
|   |      [Start]         |      |  algorithms, compare.|       |
|   +----------------------+      |      [Start]         |       |
|                                 +----------------------+       |
|                                                                |
|   How it works:  1 Upload > 2 Clean > 3 Recommend > 4 Compare  |
|                                                                |
|   Privacy: your file is kept only for this session and is      |
|   deleted automatically.                                       |
+----------------------------------------------------------------+
```

## 5.2 Clean Page (Wizard)

A **step bar** is shown at the top: *Upload > Overview > Clean > Result*. The current step is highlighted. The user may go back to a previous step.

### Step 1: Upload

- Large drag-and-drop area with "Browse file" button.
- Accepted formats and size limit shown under the box.
- For Excel with several sheets: a dropdown "Choose sheet".
- States: *empty*, *uploading (progress)*, *error (message with reason)*, *success (file name and size)*.
- If the user has earlier files in this session: a small "Use a previous file" list.

### Step 2: Overview

```
 sales.csv      1,200 rows | 14 columns | 3 duplicates | 8% missing

 [ Missing values chart ]

 Column    Type        Missing   Unique   Sample values
 age       numeric     12%       58       23, 41, 35
 city      text        0%        7        Lahore, Multan
 ...
 [ Continue to cleaning ]
```

- Table is sortable and scrolls inside its own container.
- Columns with problems show a small warning icon with tooltip.

### Step 3: Clean

Mode selector (radio cards) with one-line descriptions:

- **Auto Clean:** "We fix the safe problems for you." (recommended default for beginners)
- **Guided:** "Review suggestions and choose."
- **Manual:** "You decide every step."

```
 Mode: (o) Auto Clean   ( ) Guided   ( ) Manual

 [Auto]    [ Clean my data ]
           After running: "We need your decision on 2 items" -> asks only risky items:
              "Column 'id' looks like an ID (every value is unique). Remove it?  [Yes] [No]"
              "Column 'salary' has outliers. [Keep] [Limit extreme values]"

 [Guided]  [x] Remove 3 duplicate rows             Recommended
           [x] Fill 'age' (12% missing) with median Recommended
           [ ] Remove column 'id'                  Why? Every value is unique
           [ Apply selected ]
```

- Every suggestion row has: checkbox, short title, severity chip, "Why?" expandable text.
- Manual mode adds a dropdown for the method (for example mean/median/drop rows).

### Step 4: Result

```
 Before: 1,200 rows, 14 columns        After: 1,187 rows, 12 columns

 What changed:
   - Removed 3 duplicate rows
   - Filled 144 missing values in 'age' (median)
   - Removed column 'id'

 [Download cleaned file]  [Undo all changes]  [Continue to Models >]
```

- "Continue to Models" opens `/models` with the cleaned file pre-selected.
- Undo asks for a quick confirmation.

## 5.3 Models Page (Wizard)

Step bar: *Data > Setup > Recommend > Results*.

### Step 1: Data

Three options (radio cards):

1. **Use cleaned file:** "sales_cleaned.csv" (pre-selected if the user arrived from Clean).
2. **Choose from my earlier files** (this session only).
3. **Upload a new file** (same upload component as the Clean page).

A note: "Cleaning is optional. Missing values and categories are handled automatically during training."

### Step 2: Setup

- **Target column** dropdown (searchable).
- **Task** selector: Classification / Regression with the suggested one pre-selected and a short explanation ("Your target has 3 unique values, so this looks like classification").
- Small preview of the target distribution (bar chart or histogram).

### Step 3: Recommend

```
 Recommended algorithms for your data

 1. Random Forest        Why: many categorical columns; handles mixed data well
 2. Gradient Boosting    Why: dataset size is suitable for boosting
 3. Logistic Regression  Why: a simple, easy-to-explain baseline for comparison

 A baseline model (always predicts the most common class) will also be trained.
 [ Train and compare ]
```

- Short note: "Recommendations come from a model trained on public datasets."
- Optional "Show dataset characteristics" expandable section showing the meta-features in plain language.

### Step 4: Results

- Loading state with a progress message ("Training model 2 of 4...").
- **Comparison table:** Model, Accuracy, Precision, Recall, F1, Training time (regression: MAE, RMSE, R², time). Baseline row visually distinct. Best model highlighted with a star.
- **Charts:** bar chart comparing the main metric; confusion matrix for the best classifier, or predicted-vs-actual scatter for regression.
- Plain-language summary: "Random Forest performed best (F1 0.90), much better than the baseline (0.52)."
- Actions: **Download results (CSV)**, **Train again with different target**, **Back to cleaning**.

# 6. Reusable Components

| Component | Used on |
|---|---|
| `Header`, `Footer`, `PrivacyNote` | All pages |
| `StepBar` | Clean, Models |
| `FileUpload` | Clean, Models |
| `DataSummaryCards` | Clean overview |
| `ColumnTable` | Clean overview |
| `MissingChart` | Clean overview |
| `ModeSelector` | Clean |
| `SuggestionList` / `SuggestionItem` | Clean |
| `BeforeAfterCard`, `ChangeReport` | Clean result |
| `DataSourcePicker` | Models |
| `TargetSelector`, `TaskSelector` | Models |
| `RecommendationCard` | Models |
| `ResultsTable`, `MetricChart`, `ConfusionMatrix` | Models |
| `Toast`, `ErrorBanner`, `LoadingSpinner`, `ConfirmDialog` | All |

# 7. States and Feedback

Every screen must define these states:

| State | Behaviour |
|---|---|
| Empty | Friendly message and the next action ("Upload a file to begin") |
| Loading | Spinner or progress text; buttons disabled to prevent double submission |
| Success | Short confirmation (toast) and the next step enabled |
| Error | Clear message in plain language, what to do next, and a retry option |
| Session expired | "Your session ended and your files were deleted. Please upload again." |

# 8. Content and Tone

- Friendly, short sentences, no technical jargon where avoidable.
- Where a technical term is needed, add a tooltip (for example "Outlier: a value far away from the rest").
- Error messages say what happened and what to do: "We could not read this file. Please upload a CSV or Excel file."

# 9. Responsiveness

- Desktop first (1024 px and above), usable on tablet (768 px).
- On narrow screens, tables scroll horizontally inside their own container and cards stack vertically.

# 10. Accessibility

- Text contrast at least 4.5:1.
- Every input has a label; all actions reachable by keyboard; visible focus outline.
- Do not rely on color alone (use icons or text next to color chips).
- Charts have a text summary or a data table alternative.

# 11. Persistence in the Browser

- The browser stores only the **list of dataset IDs and file names** of the current session (for "Recent files") in `localStorage`.
- The real access control is the server session; if the server says "not found", the frontend removes the entry from the list.

# 12. Acceptance Criteria for the UI

1. A first-time user can complete Upload, Auto Clean and Download without instructions.
2. The Models page opens with the cleaned file already selected when arriving from Clean.
3. A user can reach Models, upload a file directly and get results without visiting Clean.
4. Every suggestion has a visible "Why?".
5. Undo/Reset restores the original data and the UI reflects it.
6. All error and loading states are implemented.
