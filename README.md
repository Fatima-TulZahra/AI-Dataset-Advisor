# AI Dataset Advisor

Web app that profiles and cleans tabular datasets and recommends ML algorithms using a meta-learning model.

See `Brain.md` (project memory) and `docs/` (PRD, TRD, UI/UX Brief, App Flow).

## Run the backend
```
cd backend
python -m venv venv
venv\Scripts\activate        # Windows  (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs

## Run the frontend
```
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 (backend must be running).

## Run backend tests
```
cd backend
pytest
```
