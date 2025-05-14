import streamlit as st
from utils.supabase import load_data
from components import overview, time_analysis, country, retention, merchants

df = load_data()
df_completed = df[df["spend.status"] == "completed"]
df_pending = df[df["spend.status"] == "pending"]

tabs = st.tabs([
    "✅ Overview", "⏱ Time Analysis", "🌍 Country",
    "🧑 Retention", "🏪 Merchants & Users"
])

with tabs[0]: overview.render(df, df_completed, df_pending)
with tabs[1]: time_analysis.render(df_completed, df_pending)
with tabs[2]: country.render(df_completed, df_pending)
with tabs[3]: retention.render(df_completed)
with tabs[4]: merchants.render(df_completed)
