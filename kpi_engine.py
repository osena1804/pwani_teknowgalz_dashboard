import pandas as pd


def process_dataset(df):
    """Processes the applicant DataFrame and returns calculated KPIs,
    funnel metrics, county stats, and program stats.
    """
    total_applicants = len(df)
    screened = len(df[df['Screened'] == 'Yes'])
    interviewed = len(df[df['Interviewed'] == 'Yes'])
    enrolled = len(df[df['Enrolled'] == 'Yes'])

    overall_reach_rate = (
        (enrolled / total_applicants * 100) if total_applicants > 0 else 0
    )
    target_reach_rate = 50.0  # 2026 Target
    target_gap = target_reach_rate - overall_reach_rate

    # Stage-to-stage conversion rates -- shows WHERE in the funnel
    # candidates are being lost, not just the overall reach rate
    app_to_screening_rate = (
        (screened / total_applicants * 100) if total_applicants > 0 else 0
    )
    screening_to_interview_rate = (
        (interviewed / screened * 100) if screened > 0 else 0
    )
    interview_to_enrollment_rate = (
        (enrolled / interviewed * 100) if interviewed > 0 else 0
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
    county_df['Reach_Rate'] = (county_df['Enrolled'] / county_df['Applied']) * 100

    # County share of applications vs. enrollments -- separate KPI from
    # Reach Rate: shows whether intake itself is skewed toward one hub,
    # not just whether a county converts well
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
    program_df['Conversion_Rate'] = (
        program_df['Enrolled'] / program_df['Applied']
    ) * 100

    # Unmet Demand Volume -- specifically candidates turned away for lack
    # of seats (capacity-reached), NOT all non-enrollment. Using
    # Applied - Enrolled would conflate capacity losses with eligibility
    # failures and withdrawals, which misrepresents which programs
    # actually need more cohorts/seats vs. better screening.
    capacity_by_program = (
        df[df['reason_not_enrolled'] == 'Session full / capacity reached']
        .groupby('program')
        .size()
    )
    program_df['Unmet_Demand_Volume'] = (
        program_df['program'].map(capacity_by_program).fillna(0).astype(int)
    )

    program_df = program_df.sort_values(by='Conversion_Rate', ascending=False)

    # Reasons summary
    reasons_df = (
        df[df['Enrolled'] == 'No']['reason_not_enrolled']
        .value_counts()
        .reset_index()
    )
    reasons_df.columns = ['Reason', 'Count']

    return {
        'total_applicants': total_applicants,
        'screened': screened,
        'interviewed': interviewed,
        'enrolled': enrolled,
        'overall_reach_rate': overall_reach_rate,
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