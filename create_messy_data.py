import random
import numpy as np
import pandas as pd

# Load original clean dataset
df_orig = pd.read_csv("pwani_teknowgalz_applicant_data_CORRECTED (1).csv")
df_messy = df_orig.copy()

# Set seed for reproducible test results
np.random.seed(42)
random.seed(42)

# 1. Untrimmed Column Headers (leading/trailing whitespace)
header_map = {
    "county": "  county ",
    "program": "program  ",
    "Screened": " Screened",
    "Interviewed": "Interviewed ",
    "Enrolled": " Enrolled ",
    "reason_not_enrolled": " reason_not_enrolled ",
    "cohort_year": "cohort_year  ",
}
df_messy.rename(columns=header_map, inplace=True)

# 2. Add 150 Exact Duplicate Rows
dup_rows = df_messy.sample(n=150, random_state=42)
df_messy = pd.concat([df_messy, dup_rows], ignore_index=True)

# 3. Add 50 Duplicate application_id Entries with padded spaces and inconsistent casing
dup_id_rows = df_messy.sample(n=50, random_state=123).copy()
county_col = [c for c in df_messy.columns if "county" in c][0]
dup_id_rows[county_col] = "   mombasa   "
df_messy = pd.concat([df_messy, dup_id_rows], ignore_index=True)

# 4. Inconsistent Text Casing and Untrimmed Whitespace in String Columns
county_col = [c for c in df_messy.columns if "county" in c][0]
df_messy[county_col] = df_messy[county_col].apply(
    lambda x: (
        f"  {str(x).lower()}  "
        if random.random() < 0.4
        else f"{str(x).upper()}"
        if random.random() < 0.3
        else f"{x}  "
    )
)

program_col = [c for c in df_messy.columns if "program" in c][0]
df_messy[program_col] = df_messy[program_col].apply(
    lambda x: f" {str(x)}  " if random.random() < 0.3 else x
)

# 5. Missing / Null Values in reason_not_enrolled
reason_col = [c for c in df_messy.columns if "reason_not_enrolled" in c][0]


def mess_reason(val):
  r = random.random()
  if r < 0.05:
    return np.nan
  elif r < 0.10:
    return "nan"
  elif r < 0.15:
    return "None"
  elif r < 0.20:
    return "   "
  else:
    return f"  {val}  " if random.random() < 0.3 else val


df_messy[reason_col] = df_messy[reason_col].apply(mess_reason)

# 6. Unstandardized Stage Flags ('Yes'/'No' -> 'true', '1', 'y', 'YES', 'false', '0', 'n', 'NO')
flag_cols = [
    c
    for c in df_messy.columns
    if c.strip() in ["Applied", "Screened", "Interviewed", "Enrolled"]
]
yes_variations = ["yes", "Y", "true", "1", "YES", " Yes ", "True"]
no_variations = ["no", "N", "false", "0", "NO", " No ", "False"]

for col in flag_cols:
  df_messy[col] = df_messy[col].apply(
      lambda val: (
          random.choice(yes_variations)
          if str(val).strip().lower() in ["yes", "true", "1"]
          else random.choice(no_variations)
      )
  )

# 7. Uncoerced Numeric Types (float-strings and spaces in numbers)
year_col = [c for c in df_messy.columns if "cohort_year" in c][0]
df_messy[year_col] = df_messy[year_col].apply(
    lambda x: (
        f"{x}.0"
        if random.random() < 0.3
        else f" {x} "
        if random.random() < 0.3
        else str(x)
    )
)

if "age" in df_messy.columns:
  df_messy["age"] = df_messy["age"].apply(
      lambda x: f" {x} " if random.random() < 0.3 else str(x)
  )

# Save messy dataset
output_filename = "pwani_teknowgalz_MESSY_TEST_DATA.csv"
df_messy.to_csv(output_filename, index=False)
print(
    f"Successfully generated '{output_filename}' with {len(df_messy):,} rows."
)