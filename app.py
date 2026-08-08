import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
from kpi_engine import process_dataset

# Page configuration
st.set_page_config(
    page_title="Pwani Teknowgalz - Funnel Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Pwani Teknowgalz: Applicant Funnel & Impact Dashboard")
st.markdown(
    "Automated KPI tracking toward reaching the **50% reach goal by 2026**."
)

# Sidebar: File Uploader & Dynamic Filters
st.sidebar.header("📁 Data Source & Filters")
uploaded_file = st.sidebar.file_uploader("Upload Applicant CSV", type=["csv"])

# Load dataset (from upload or fallback default file)
if uploaded_file is not None:
  raw_df = pd.read_csv(uploaded_file)
else:
  try:
    raw_df = pd.read_csv("data/pwani_teknowgalz_applicant_data_CORRECTED (1).csv")
    st.sidebar.info("Using default local dataset.")
  except Exception:
    st.warning("Please upload a valid CSV dataset to get started.")
    st.stop()

# Apply Sidebar Filters
years = sorted(raw_df["cohort_year"].unique())
selected_years = st.sidebar.multiselect("Cohort Year", years, default=years)

counties = sorted(raw_df["county"].unique())
selected_counties = st.sidebar.multiselect("County", counties, default=counties)

filtered_df = raw_df[
    (raw_df["cohort_year"].isin(selected_years))
    & (raw_df["county"].isin(selected_counties))
]

if filtered_df.empty:
  st.warning("No data available for the selected filters.")
  st.stop()

# Process KPIs
kpi_data = process_dataset(filtered_df)

# Top KPI Metric Cards
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Applicants", f"{kpi_data['total_applicants']:,}")
col2.metric("Total Enrolled", f"{kpi_data['enrolled']:,}")
col3.metric(
    "Overall Reach Rate",
    f"{kpi_data['overall_reach_rate']:.2f}%",
    delta=f"-{kpi_data['target_gap']:.2f}% to 50% Goal",
)
col4.metric(
    "Capacity Rejections",
    f"{kpi_data['capacity_rejections']:,}",
    f"{kpi_data['capacity_pct']:.1f}% of Rejections",
)

st.divider()

# Core Visual: Plotly Interactive Funnel
st.subheader("🔽 Applicant Progression Funnel")

funnel_stages = ["Applied", "Screened", "Interviewed", "Enrolled"]
funnel_values = [
    kpi_data["total_applicants"],
    kpi_data["screened"],
    kpi_data["interviewed"],
    kpi_data["enrolled"],
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
fig_funnel.update_layout(height=420, margin=dict(l=20, r=20, t=30, b=20))
st.plotly_chart(fig_funnel, use_container_width=True)

st.divider()

# Diagnostic Tabs
tab1, tab2, tab3 = st.tabs(
    ["🌍 Regional Equity", "🎓 Program Yield", "⚠️ Rejection Reasons"]
)

with tab1:
  st.write("### County Breakdown")
  fig_county = px.bar(
      kpi_data["county_df"],
      x="county",
      y=["Applied", "Enrolled"],
      barmode="group",
      title="Applications vs. Enrollments by County",
      labels={"value": "Count", "county": "County"},
      color_discrete_sequence=["#1E293B", "#0D9488"],
  )
  st.plotly_chart(fig_county, use_container_width=True)

with tab2:
  st.write("### Program Yield & Unmet Demand")
  fig_prog = px.bar(
      kpi_data["program_df"],
      x="program",
      y="Conversion_Rate",
      title="Program Conversion Rate (%)",
      labels={"Conversion_Rate": "Conversion Rate (%)", "program": "Program"},
      color="Conversion_Rate",
      color_continuous_scale="Viridis",
  )
  st.plotly_chart(fig_prog, use_container_width=True)

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