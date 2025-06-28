import streamlit as st
import pandas as pd
from utils.supabase import load_data
from components import (
    overview,
    time_analysis,
    country,
    retention,
    merchants,
    analytics,
    monthly_report  # ✅ 월별 리포트 추가
)

# ✅ 데이터 로드 (Supabase에서 전처리 포함)
df = load_data()
df_completed = df[df["spend.status"] == "completed"]
df_pending = df[df["spend.status"] == "pending"]
df_total = pd.concat([df_completed, df_pending], ignore_index=True)

# ✅ 탭 구성
tabs = st.tabs([
    "✅ Overview",
    "⏱ Time Analysis",
    "🌍 Country",
    "🧑 Retention",
    "🏪 Merchants & Users",
    "📈 Analytics",
    "📅 Monthly Report"  
])

# ✅ 탭별 렌더링
with tabs[0]:
    overview.render(df, df_completed, df_pending)

with tabs[1]:
    time_analysis.render(df, df_total)

with tabs[2]:
    country.render(df_completed, df_pending)

with tabs[3]:
    retention.render(df_completed)

with tabs[4]:
    merchants.render(df_completed)

with tabs[5]: 
    analytics.render(df_total)

with tabs[6]: 
    monthly_report.render(df_total)  
