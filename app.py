import io
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from kpi_engine import export_to_excel, process_dataset, validate_schema

# Page Config
st.set_page_config(
    page_title="Pwani Teknowgalz - Impact Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Pwani Teknowgalz: Applicant Funnel & Impact Dashboard")
st.markdown(
    "Automated KPI tracking toward reaching the **50% reach goal by 2026**."
)

# Sidebar - File Upload & Validation
st.sidebar.header("📁 Data Ingestion")
uploaded_file = st.sidebar.file_uploader("Upload Applicant CSV", type=["csv"])

if uploaded_file is not None:
  try:
    raw_df = pd.read_csv(uploaded_file)
  except Exception as e:
    st.error(f"Error reading uploaded CSV: {e}")
    st.stop()
else:
  try:
    raw_df = pd.read_csv("data/pwani_teknowgalz_applicant_data_CORRECTED (1).csv")
    st.sidebar.info("Using default local dataset.")
  except Exception:
    st.warning("Please upload a valid CSV dataset to get started.")
    st.stop()

# Schema Check
is_valid, missing_columns = validate_schema(raw_df)
if not is_valid:
  st.error(
      "⚠️ **Invalid CSV Schema Detected!**\n\n"
      f"The uploaded file is missing required header(s): `{', '.join(missing_columns)}`.\n\n"
      "Please upload a standardized CSV dataset."
  )
  st.stop()

# Sidebar - Filters
st.sidebar.header("🔍 Filters")
years = sorted(raw_df["cohort_year"].unique())
selected_years = st.sidebar.multiselect("Cohort Year", years, default=years)

counties = sorted(raw_df["county"].unique())
selected_counties = st.sidebar.multiselect("County", counties, default=counties)

# Sidebar - Scenario Modeler
st.sidebar.header("⚙️ What-If Scenario Engine")
scenario_slider = st.sidebar.slider(
    "Reduce Interview Drop-off by (%)",
    min_value=0,
    max_value=100,
    value=0,
    step=5,
    help="Simulates saving candidates lost between interview and enrollment.",
)

# Filter Data
filtered_df = raw_df[
    (raw_df["cohort_year"].isin(selected_years))
    & (raw_df["county"].isin(selected_counties))
]

if filtered_df.empty:
  st.warning("No data matches the selected filter criteria.")
  st.stop()

# Process KPIs
kpi_data = process_dataset(filtered_df, scenario_reduction_pct=scenario_slider)

# Display Banner if Scenario Active
if scenario_slider > 0:
  st.info(
      f"⚡ **Scenario Active:** Reducing interview drop-off by **{scenario_slider}%** "
      f"adds **+{kpi_data['saved_candidates']:,} enrolled students**, boosting overall reach from "
      f"**{kpi_data['baseline_reach_rate']:.2f}%** to **{kpi_data['scenario_reach_rate']:.2f}%**."
  )

# Top KPI Metric Cards
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Applicants", f"{kpi_data['total_applicants']:,}")
col2.metric(
    "Enrolled Applicants",
    f"{kpi_data['scenario_enrolled']:,}",
    delta=(
        f"+{kpi_data['saved_candidates']:,} via Scenario"
        if scenario_slider > 0
        else None
    ),
)
col3.metric(
    "Overall Reach Rate",
    f"{kpi_data['scenario_reach_rate']:.2f}%",
    delta=f"-{kpi_data['target_gap']:.2f}% to 50% Goal",
)
col4.metric(
    "Capacity Rejections",
    f"{kpi_data['capacity_rejections']:,}",
    f"{kpi_data['capacity_pct']:.1f}% of Rejections",
)

st.divider()

# Core Visual: Plotly Interactive Funnel
st.subheader("🔽 Applicant Progression Funnel & Step Conversion Rates")

f_col1, f_col2 = st.columns([2, 1])

with f_col1:
  funnel_stages = ["Applied", "Screened", "Interviewed", "Enrolled"]
  funnel_values = [
      kpi_data["total_applicants"],
      kpi_data["screened"],
      kpi_data["interviewed"],
      kpi_data["scenario_enrolled"],
  ]

  fig_funnel = go.Figure(
      go.Funnel(
          y=funnel_stages,
          x=funnel_values,
          textinfo="value+percent initial",
          marker={
              "color": ["#0F172A", "#334155", "#0D9488", "#10B981"],
              "line": {"width": 2, "color": "#FFFFFF"},
          },
          connector={"line": {"color": "#CBD5E1", "width": 1}},
      )
  )
  fig_funnel.update_layout(height=380, margin=dict(l=20, r=20, t=20, b=20))
  st.plotly_chart(fig_funnel, use_container_width=True)

with f_col2:
  st.write("### Stage Yields")
  st.metric(
      "App → Screening Rate", f"{kpi_data['app_to_screening_rate']:.1f}%"
  )
  st.metric(
      "Screening → Interview Rate",
      f"{kpi_data['screening_to_interview_rate']:.1f}%",
  )
  st.metric(
      "Interview → Enrollment Rate",
      f"{kpi_data['interview_to_enrollment_rate']:.1f}%",
  )

st.divider()

# Diagnostic Tabs
tab1, tab2, tab3 = st.tabs(
    ["🌍 Regional Equity", "🎓 Program Yield", "⚠️ Rejection Reasons"]
)

with tab1:
  st.write("### County Breakdown & Share Analysis")
  fig_county = px.bar(
      kpi_data["county_df"],
      x="county",
      y=["Applied_Share_pct", "Enrolled_Share_pct"],
      barmode="group",
      title="Application Share (%) vs. Enrollment Share (%) by County",
      labels={"value": "Share (%)", "county": "County", "variable": "Metric"},
      color_discrete_sequence=["#1E293B", "#0D9488"],
  )
  st.plotly_chart(fig_county, use_container_width=True)
  st.dataframe(
      kpi_data["county_df"].style.format({
          "Reach_Rate_%": "{:.2f}%",
          "Applied_Share_pct": "{:.2f}%",
          "Enrolled_Share_pct": "{:.2f}%",
      }),
      use_container_width=True,
  )

with tab2:
  st.write("### Program Conversion Rate & Capacity Unmet Demand")
  fig_prog = px.bar(
      kpi_data["program_df"],
      x="program",
      y="Conversion_Rate_%",
      title="Program Conversion Rate (%)",
      labels={"Conversion_Rate_%": "Conversion Rate (%)", "program": "Program"},
      color="Conversion_Rate_%",
      color_continuous_scale="Viridis",
  )
  st.plotly_chart(fig_prog, use_container_width=True)
  st.dataframe(
      kpi_data["program_df"].style.format({"Conversion_Rate_%": "{:.2f}%"}),
      use_container_width=True,
  )

with tab3:
  st.write("### Primary Causes for Non-Enrollment")
  fig_reasons = px.pie(
      kpi_data["reasons_df"],
      values="Count",
      names="Reason",
      title="Rejection Reason Distribution",
      hole=0.4,
      color_discrete_sequence=px.colors.qualitative.Set3,
  )
  st.plotly_chart(fig_reasons, use_container_width=True)

# Export Summary Reports
st.divider()
st.subheader("📥 Export Summary Reports")
exp_col1, exp_col2 = st.columns(2)

csv_data = kpi_data["county_df"].to_csv(index=False).encode("utf-8")
exp_col1.download_button(
    label="📄 Download County Summary (CSV)",
    data=csv_data,
    file_name="pwani_county_summary.csv",
    mime="text/csv",
)

excel_data = export_to_excel(kpi_data["county_df"], kpi_data["program_df"])
exp_col2.download_button(
    label="📊 Download Full Summary (Excel)",
    data=excel_data,
    file_name="pwani_kpi_summary_report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)