# 📊 Pwani Teknowgalz: Applicant Funnel & Impact Dashboard

An interactive Streamlit dashboard that automatically cleans applicant data and calculates KPIs tracking Pwani Teknowgalz's progress toward their **2026 goal of reaching 50% of program applicants** (up from ~15% today).

🚀 **Live Dashboard:** https://pwaniteknowgalzdashboard-pxewkjvurzdzojuw5jxq3w.streamlit.app/

🚀 **Watch Demo** https://drive.google.com/file/d/1dzkVeeAqRFYsa7pJg2kl4lQeY1R7fK0j/view?usp=drivesdk

---

## What this does

Upload any applicant CSV with the expected schema, and the dashboard:
1. Validates the file has the right columns and tells you exactly which ones are missing if not.
2. Automatically cleans it, fixes inconsistent casing, stray whitespace, duplicate rows, mixed Yes/No formats, and messy dates
3. Calculates every KPI live and renders an interactive funnel KPI cards, regional and program breakdowns,and rejection-reasons chart.
4. Lets you run a "what-if" scenario (e.g. "what if interview drop-off were cut in half?") with a slider
5. Exports summary tables as CSV or Excel

---

## Project structure

```
pwani_teknowgalz_dashboard/
├── app.py                  # Streamlit UI: layout, charts, filters
├── kpi_engine.py            # Data cleaning + KPI calculations (no UI code)
├── data/
│   └── pwani_teknowgalz_applicant_data_CORRECTED(1).csv   # Default dataset, loads if nothing is uploaded
├── requirements.txt
├── .gitignore
└── README.md
```

---

## KPIs covered

**Goal Tracking & Overall Conversion**
- Overall Reach Rate vs. 2026 target, and the gap to close
- Applied → Screened, Screened → Interviewed, Interviewed → Enrolled rates

**Resource & Capacity Bottlenecks**
- Capacity Rejection % (capacity/trainer/device vs. eligibility)
- Device Shortage Count

**Regional Inclusion & Equity**
- County Reach Rate
- Applied Share % vs. Enrolled Share % by county (is intake skewed toward
  one hub?)

**Program Performance & Demand**
- Program Conversion Rate
- Unmet Demand Volume per program (candidates turned away specifically
  for lack of seats)

**Known data limitations:** no gender or mentorship-exposure fields exist in this dataset.

---

## Local setup

```bash
git clone <your-repo-url>
cd pwani_teknowgalz_dashboard

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

streamlit run app.py
```

Opens automatically at `http://localhost:8501`.

To test with a different dataset, use the file uploader in the sidebar, no code changes needed as long as the CSV has these columns:

```
application_id, county, program, application_date, age, application_stage,
status, completion_status, reason_not_enrolled, cohort_year,
Applied, Screened, Interviewed, Enrolled, Drop-off Stage
```

---

## Deploying to Streamlit Community Cloud (free, public URL)

### 1. Push the project to GitHub
```bash
git add .
git commit -m "Ready for deployment"
git push -u origin main
```

### 2. Deploy
1. Go to **[streamlit.io/cloud](https://streamlit.io/cloud)** (also called Streamlit Community Cloud) and sign in with GitHub.
2. Click **New app**.
3. Choose:
   - **Repository:** your `pwani_teknowgalz_dashboard` repo
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. Click **Deploy**.

The first deploy takes a few minutes while it installs everything from`requirements.txt`. You'll get a public URL like:
```
https://<your-app-name>.streamlit.app
```

### 3. Updating after deployment
Any time you push a new commit to `main`, the deployed app **auto-updates**
within a minute or two — no redeploy step needed:
```bash
git add .
git commit -m "Fix county filter bug"
git push
```

### 4. Common deployment issues

| Problem | Cause | Fix |
|---|---|---|
| App shows "ModuleNotFoundError" | A package used in `app.py`/`kpi_engine.py` isn't in `requirements.txt` | Add it, commit, push |
| App can't find the default CSV | `data/` folder wasn't committed, or is in `.gitignore` | Check `git status`, make sure the CSV is tracked |
| App works locally but not deployed | Local `venv` has packages installed that aren't pinned in `requirements.txt` | Run `pip freeze > requirements.txt` locally, commit it |
| Deployed app is stuck on an old version | Streamlit Cloud caches by branch/commit | Push a new commit, or use "Reboot app" from the Streamlit Cloud dashboard |

### 5. Managing the app after deploy
From (https://share.streamlit.io) you can:
- View logs if something breaks in production
- Reboot the app manually
- Change which branch/file it deploys from
- Delete the app

---

## requirements.txt

```
streamlit>=1.38
pandas>=2.0
numpy>=1.26
plotly>=5.20
openpyxl>=3.1
```

`openpyxl` is required for the Excel export feature (`export_to_excel` in
`kpi_engine.py`) even though it's never imported directly in `app.py` —
pandas needs it as the Excel engine under the hood.

---

## Data note

The dataset is simulated, not Pwani Teknowgalz's real applicant data, per the organization's data-privacy decision (documented in the Project Proposal, Section 3.1). It blends a public education dataset with synthetic records grounded in Pwani Teknowgalz's real public figures (~20,000 cumulative applicants, ~15% current reach, actual program and county names) so the KPIs and funnel shape are realistic even though no real individual-level records are used.

🛠️ Technology Stack
Frontend & Framework: Streamlit

Data Processing & Manipulation: Pandas, NumPy

Data Visualization: Plotly Express & Graph Objects

Spreadsheet Export Engine: openpyxl

Version Control: Git & GitHub