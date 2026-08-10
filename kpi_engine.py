import io
import numpy as np
import pandas as pd

# Mandatory columns required for KPI calculations
REQUIRED_COLUMNS = [
    'application_id',
    'county',
    'program',
    'cohort_year',
    'Screened',
    'Interviewed',
    'Enrolled',
    'reason_not_enrolled',
]


def clean_dataset(raw_df: pd.DataFrame) -> pd.DataFrame:
  """General data cleaning pipeline that standardizes unformatted CSV datasets

  before KPI processing.
  """
  df = raw_df.copy()

  # 1. Clean Column Headers (strip spaces)
  df.columns = [str(col).strip() for col in df.columns]

  # 2. Deduplication (drop rows with no application_id, exact row
  # duplicates, and duplicate application IDs)
  df = df.drop_duplicates()
  if 'application_id' in df.columns:
    df = df.dropna(subset=['application_id'])
    df['application_id'] = df['application_id'].astype(str).str.strip()
    df = df[df['application_id'].str.lower() != 'nan']
    df = df.drop_duplicates(subset=['application_id'], keep='first')

  # 3. Text & Categorical Cleaning
  text_cols = [
      'county',
      'program',
      'status',
      'completion_status',
      'reason_not_enrolled',
      'Drop-off Stage',
      'application_stage',
  ]
  for col in text_cols:
    if col in df.columns:
      df[col] = df[col].astype(str).str.strip()
      df[col] = df[col].replace({'nan': np.nan, 'None': np.nan, '': np.nan})

  # Title-case every categorical label column so casing variants
  # ("codehack" / "CODEHACK" / "Codehack") don't fragment into separate
  # groups downstream -- not just county, but program/status/stage too.
  for col in ['county', 'program', 'status', 'application_stage']:
    if col in df.columns:
      df[col] = df[col].str.title()

  if 'reason_not_enrolled' in df.columns:
    df['reason_not_enrolled'] = df['reason_not_enrolled'].fillna('Not Specified')

  # 4. Standardize Stage Flags ('Yes' / 'No')
  stage_cols = ['Applied', 'Screened', 'Interviewed', 'Enrolled']
  yes_values = {'yes', 'y', 'true', '1', 1, True}

  for col in stage_cols:
    if col in df.columns:
      df[col] = df[col].apply(
          lambda x: 'Yes' if str(x).strip().lower() in yes_values else 'No'
      )

  # 5. Coerce Data Types
  if 'cohort_year' in df.columns:
    df['cohort_year'] = (
        pd.to_numeric(df['cohort_year'], errors='coerce').fillna(0).astype(int)
    )

  if 'age' in df.columns:
    df['age'] = df['age'].astype(str).str.extract(r'(\d+)').astype(float)

  if 'application_date' in df.columns:
    df['application_date'] = pd.to_datetime(
        df['application_date'], errors='coerce'
    )

  return df


def validate_schema(df: pd.DataFrame):
  """Checks if the uploaded DataFrame contains all required columns."""
  cleaned_cols = [str(col).strip() for col in df.columns]
  missing_cols = [col for col in REQUIRED_COLUMNS if col not in cleaned_cols]
  if missing_cols:
    return False, missing_cols
  return True, []


def process_dataset(df: pd.DataFrame, scenario_reduction_pct: float = 0.0):
  """Cleans incoming dataset automatically then processes applicant KPIs."""
  # 1. Run Automated Data Cleaning
  df = clean_dataset(df)

  # 2. KPI Computations
  total_applicants = len(df)
  screened = len(df[df['Screened'] == 'Yes'])
  interviewed = len(df[df['Interviewed'] == 'Yes'])
  baseline_enrolled = len(df[df['Enrolled'] == 'Yes'])

  # What-If Scenario Calculation
  interview_dropoff = interviewed - baseline_enrolled
  saved_candidates = int(
      round(interview_dropoff * (scenario_reduction_pct / 100.0))
  )
  scenario_enrolled = baseline_enrolled + saved_candidates

  # Reach Rates
  baseline_reach_rate = (
      (baseline_enrolled / total_applicants * 100) if total_applicants > 0 else 0
  )
  scenario_reach_rate = (
      (scenario_enrolled / total_applicants * 100) if total_applicants > 0 else 0
  )
  target_reach_rate = 50.0  # 2026 Target Goal
  target_gap = target_reach_rate - scenario_reach_rate

  # Stage Conversion Yields
  app_to_screening_rate = (
      (screened / total_applicants * 100) if total_applicants > 0 else 0
  )
  screening_to_interview_rate = (
      (interviewed / screened * 100) if screened > 0 else 0
  )
  interview_to_enrollment_rate = (
      (scenario_enrolled / interviewed * 100) if interviewed > 0 else 0
  )

  # Capacity bottlenecks
  total_rejections = len(df[df['Enrolled'] == 'No'])
  capacity_reasons = [
      'Device unavailable',
      'Session full / capacity reached',
      'No trainer capacity',
  ]
  capacity_rejections = len(
      df[df['reason_not_enrolled'].isin(capacity_reasons)]
  )
  capacity_pct = (
      (capacity_rejections / total_rejections * 100)
      if total_rejections > 0
      else 0
  )
  device_shortages = len(df[df['reason_not_enrolled'] == 'Device unavailable'])

  # County summary
  county_df = (
      df.groupby('county')
      .agg(
          Applied=('application_id', 'count'),
          Enrolled=('Enrolled', lambda x: (x == 'Yes').sum()),
      )
      .reset_index()
  )
  county_df['Reach_Rate_%'] = (
      county_df['Enrolled'] / county_df['Applied']
  ) * 100
  county_df['Applied_Share_pct'] = (
      county_df['Applied'] / county_df['Applied'].sum() * 100
  )
  county_df['Enrolled_Share_pct'] = (
      county_df['Enrolled'] / county_df['Enrolled'].sum() * 100
      if county_df['Enrolled'].sum() > 0
      else 0
  )
  county_df = county_df.sort_values(by='Applied', ascending=False)

  # Program summary
  program_df = (
      df.groupby('program')
      .agg(
          Applied=('application_id', 'count'),
          Enrolled=('Enrolled', lambda x: (x == 'Yes').sum()),
      )
      .reset_index()
  )
  program_df['Conversion_Rate_%'] = (
      program_df['Enrolled'] / program_df['Applied']
  ) * 100

  capacity_by_program = (
      df[df['reason_not_enrolled'] == 'Session full / capacity reached']
      .groupby('program')
      .size()
  )
  program_df['Unmet_Demand_Volume'] = (
      program_df['program'].map(capacity_by_program).fillna(0).astype(int)
  )
  program_df = program_df.sort_values(
      by='Conversion_Rate_%', ascending=False
  )

  # Reasons summary
  reasons_df = (
      df[df['Enrolled'] == 'No']['reason_not_enrolled']
      .value_counts()
      .reset_index()
  )
  reasons_df.columns = ['Reason', 'Count']

  return {
      'cleaned_df': df,
      'total_applicants': total_applicants,
      'screened': screened,
      'interviewed': interviewed,
      'baseline_enrolled': baseline_enrolled,
      'scenario_enrolled': scenario_enrolled,
      'saved_candidates': saved_candidates,
      'baseline_reach_rate': baseline_reach_rate,
      'scenario_reach_rate': scenario_reach_rate,
      'target_gap': target_gap,
      'app_to_screening_rate': app_to_screening_rate,
      'screening_to_interview_rate': screening_to_interview_rate,
      'interview_to_enrollment_rate': interview_to_enrollment_rate,
      'capacity_rejections': capacity_rejections,
      'capacity_pct': capacity_pct,
      'device_shortages': device_shortages,
      'county_df': county_df,
      'program_df': program_df,
      'reasons_df': reasons_df,
  }


def export_to_excel(county_df: pd.DataFrame, program_df: pd.DataFrame) -> bytes:
  """Generates an Excel workbook containing summary tables in memory."""
  output = io.BytesIO()
  with pd.ExcelWriter(output, engine='openpyxl') as writer:
    county_df.to_excel(writer, sheet_name='County Breakdown', index=False)
    program_df.to_excel(writer, sheet_name='Program Breakdown', index=False)
  return output.getvalue()