import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import pycountry
import plotly.express as px
from supabase import create_client
import math
import numpy as np
import os

st.set_page_config(layout="wide")

SUPABASE_URL = os.getenv("SUPABASE_URL") or "https://yadsjoudwijtqnyfasat.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlhZHNqb3Vkd2lqdHFueWZhc2F0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDcxMzkzNjQsImV4cCI6MjA2MjcxNTM2NH0.DnLQo1bXrGQOsdUc_km3zKL5KXRXQxxzpRIfQbVhqVk"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ✅ 모든 데이터 페이징 방식으로 수집
def fetch_all_rows(batch_size=5000, max_pages=20):
    all_data = []
    offset = 0
    for _ in range(max_pages):
        res = (
            supabase.table("transactions")
            .select("*")
            .order('"spend.authorizedAt"', desc=False)
            .range(offset, offset + batch_size - 1)
            .execute()
        )
        batch = res.data
        if not batch:
            break
        all_data.extend(batch)
        offset += batch_size
    return pd.DataFrame(all_data)

@st.cache_data(ttl=300)
def load_data():
    df = fetch_all_rows(batch_size=5000, max_pages=50)  # 최대 250,000건 수집

    df["spend.status"] = df["spend.status"].astype(str).str.lower()

    def safe_amount_to_usd(x):
        try:
            return int(x) / 100
        except:
            return 0
    df["spend.amount_usd"] = df["spend.amount"].apply(safe_amount_to_usd)

    df["spend.authorizedAt"] = pd.to_datetime(df["spend.authorizedAt"], format="mixed", errors="coerce")
    df["hour_utc"] = df["spend.authorizedAt"].dt.hour
    df["date_utc"] = df["spend.authorizedAt"].dt.date

    return df

# ✅ 데이터 로딩
df = load_data()
df_completed = df[df["spend.status"] == "completed"]
df_pending = df[df["spend.status"] == "pending"]
df_total = pd.concat([df_completed, df_pending], ignore_index=True)

# ✅ 대시보드 탭 구성
tab1, tab2, tab3, tab4, tab5 = st.tabs(["✅ Overview", "⏱ Time Analysis", "🌍 Country", "🧑 Retention", "🏪 Merchants & Users"])

# ✅ Overview
with tab1:
    st.header("📊 Summary Statistics")

    # ✅ 전체 로드된 Supabase 원본 데이터 수
    st.markdown(f"🔄 **Raw rows loaded from Supabase:** `{len(df):,}` rows")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Processed Transactions", len(df_total))
    col2.metric("Total Volume (USD)", f"${df_total['spend.amount_usd'].sum():,.2f}")
    col3.metric("Unique Users", df_total["spend.userEmail"].nunique())

    st.subheader("✅ Completed Transactions")
    col1, col2, col3 = st.columns(3)
    col1.metric("Transactions", len(df_completed))
    col2.metric("Volume (USD)", f"${df_completed['spend.amount_usd'].sum():,.2f}")
    col3.metric("Users", df_completed["spend.userEmail"].nunique())

    st.subheader("🕓 Pending Transactions")
    col1, col2, col3 = st.columns(3)
    col1.metric("Transactions", len(df_pending))
    col2.metric("Volume (USD)", f"${df_pending['spend.amount_usd'].sum():,.2f}")
    col3.metric("Users", df_pending["spend.userEmail"].nunique())

    # ✅ 상태 분포 확인
    st.write("✅ status:")
    st.dataframe(df["spend.status"].value_counts())

    # ✅ 고급 지표 계산
    st.subheader("📈 Advanced Summary")

    df["week"] = pd.to_datetime(df["date_utc"]).dt.to_period("W").astype(str)
    weekly_tx_count = df.groupby(["spend.userEmail", "week"]).size().reset_index(name="tx_count")

    # 가장 최근 주만 추출
    latest_week = df["week"].max()
    latest_week_df = weekly_tx_count[weekly_tx_count["week"] == latest_week]

    # 2회 이상 사용한 유저 수
    recurring_users = latest_week_df[latest_week_df["tx_count"] >= 2]["spend.userEmail"].nunique()
    total_users = latest_week_df["spend.userEmail"].nunique()

    recurring_pct = (recurring_users / total_users) * 100 if total_users else 0

    # 지역 집중도 (Top 3 국가 트랜잭션 비율)
    country_counts = df["spend.merchantCountry"].value_counts()
    top3_concentration = (country_counts.head(3).sum() / country_counts.sum()) * 100 if not country_counts.empty else 0

    col1, col2 = st.columns(2)
    col1.metric("Recurring Users % (≥2 tx/week)", f"{recurring_pct:.1f}%")
    col2.metric("Top 3 Country Concentration", f"{top3_concentration:.1f}%")

    # 주차 컬럼 생성 (week)
    df["week"] = pd.to_datetime(df["date_utc"]).dt.to_period("W").astype(str)

    # 주간 신규 사용자 수 계산
    user_min_week = df.groupby("spend.userEmail")["week"].min()
    weekly_new_users = user_min_week.value_counts().sort_index()

    # 💸 주간 총 지출
    weekly_spend = df.groupby("week")["spend.amount_usd"].sum().sort_index()

    col1, col2 = st.columns(2)

with col1:
    st.subheader("📅 Weekly New Users")
    fig, ax = plt.subplots(figsize=(6, 3))
    weekly_new_users.plot(ax=ax, marker='o', color='steelblue')
    ax.set_title("Weekly New Users", fontsize=14)
    ax.set_xlabel("Week", fontsize=10)
    ax.set_ylabel("Users", fontsize=10)
    ax.tick_params(axis='x', labelrotation=30, labelsize=8)
    ax.grid(True, linestyle='--', alpha=0.4)
    st.pyplot(fig)

with col2:
    st.subheader("💸 Weekly Spend (USD)")
    fig2, ax2 = plt.subplots(figsize=(6, 3))
    weekly_spend.plot(ax=ax2, marker='o', color='green')
    ax2.set_title("Weekly Spend (USD)", fontsize=14)
    ax2.set_xlabel("Week", fontsize=10)
    ax2.set_ylabel("USD", fontsize=10)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax2.tick_params(axis='x', labelrotation=30, labelsize=8)
    ax2.grid(True, linestyle='--', alpha=0.4)
    st.pyplot(fig2)

# ⏱ Time Analysis
with tab2:
    st.header("⏱ Time-based Analysis")

    st.subheader("Hourly Spend (UTC)")
    hourly_spend_completed = df_completed.groupby("hour_utc")["spend.amount_usd"].sum()
    hourly_spend_pending = df_pending.groupby("hour_utc")["spend.amount_usd"].sum()
    hourly_df = pd.DataFrame({
        "Completed": hourly_spend_completed,
        "Pending": hourly_spend_pending
    }).fillna(0)

    fig, ax = plt.subplots(figsize=(10,4))
    hourly_df.plot(kind="bar", stacked=True, color=["green", "orange"], ax=ax)
    ax.set_title("Hourly Spend by Status")
    ax.set_xlabel("Hour (UTC)")
    ax.set_ylabel("Total Spend (USD)")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    st.pyplot(fig)

    st.subheader("Daily Transaction Count & Volume")
    daily_stats = df_completed.groupby("date_utc").agg(
        tx_count=("spend.amount_usd", "count"),
        total_volume_usd=("spend.amount_usd", "sum")
    ).reset_index()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    ax1.plot(daily_stats["date_utc"], daily_stats["tx_count"], marker='o', color='steelblue')
    ax1.set_ylabel("Transactions")
    ax1.grid(True, linestyle="--", alpha=0.5)

    ax2.plot(daily_stats["date_utc"], daily_stats["total_volume_usd"], marker='o', color='green')
    ax2.set_ylabel("Volume (USD)")
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax2.grid(True, linestyle="--", alpha=0.5)

    plt.xticks(rotation=45)
    fig.tight_layout()
    st.pyplot(fig)


# 🌍 Country Analysis
with tab3:
    st.header("🌍 Country-Based Analysis")

    def get_country_name(code):
        try:
            return pycountry.countries.get(alpha_2=code).name
        except:
            return code

    def get_iso3(code):
        try:
            return pycountry.countries.get(alpha_2=code).alpha_3
        except:
            return None

    country_spend_completed = df_completed.groupby("spend.merchantCountry")["spend.amount_usd"].sum()
    country_spend_pending = df_pending.groupby("spend.merchantCountry")["spend.amount_usd"].sum()
    country_df = pd.DataFrame({
        "Completed": country_spend_completed,
        "Pending": country_spend_pending
    }).fillna(0)
    country_df.index = country_df.index.map(get_country_name)
    country_df["Total"] = country_df["Completed"] + country_df["Pending"]
    top10_df = country_df.sort_values("Total", ascending=False).head(10)[["Completed", "Pending"]]

    fig, ax = plt.subplots(figsize=(10, 4))
    top10_df.plot(kind="bar", stacked=True, color=["green", "orange"], ax=ax)
    ax.set_title("Top 10 Countries by Spend")
    ax.set_ylabel("Total Spend (USD)")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
    st.pyplot(fig)

    st.subheader("🌐 Completed Transactions by Country (Map)")
    country_counts = df_completed["spend.merchantCountry"].value_counts().reset_index()
    country_counts.columns = ["country_code", "appeared"]
    country_counts["iso3"] = country_counts["country_code"].apply(get_iso3)
    country_counts["country_name"] = country_counts["country_code"].apply(get_country_name)
    country_flag_df = country_counts.dropna(subset=["iso3"])

    fig = px.choropleth(
        country_flag_df,
        locations="iso3",
        color="appeared",
        hover_name="country_name",
        color_continuous_scale=["#d0f0c0", "#2e8b57", "#006400"],
        title="🌐 Completed Transactions by Country",
        projection="robinson",
    )
    fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0}, height=500)
    st.plotly_chart(fig)


# 🧑 Retention
with tab4:
    st.header("🧑 User Retention (Cohort Analysis)")
    df_cohort = df_completed.copy()
    df_cohort["authorized_date"] = pd.to_datetime(df_cohort["spend.authorizedAt"]).dt.normalize()
    df_cohort["cohort_day0"] = df_cohort.groupby("spend.userEmail")["authorized_date"].transform("min")
    df_cohort["cohort_day"] = (df_cohort["authorized_date"] - df_cohort["cohort_day0"]).dt.days
    df_cohort["cohort_day0_str"] = df_cohort["cohort_day0"].dt.strftime("%Y-%m-%d")
    df_cohort = df_cohort[df_cohort["cohort_day0"] >= pd.to_datetime("2025-04-15").tz_localize("UTC")]

    retention_table = df_cohort.pivot_table(
        index="cohort_day0_str",
        columns="cohort_day",
        values="spend.userEmail",
        aggfunc="nunique"
    )
    retention_pct = retention_table.divide(retention_table[0], axis=0) * 100

    plt.figure(figsize=(14, 6))
    sns.heatmap(
        retention_pct,
        annot=True,
        fmt=".1f",
        cmap="YlGnBu",
        linewidths=0.5,
        linecolor="gray",
        cbar=True,
        annot_kws={"size": 8}
    )
    plt.title("User Retention Heatmap by Cohort (Completed Only)", fontsize=14, weight="bold")
    plt.xlabel("Day Since First Transaction")
    plt.ylabel("Cohort Start Date")
    plt.xticks(rotation=0)
    plt.tight_layout()
    st.pyplot(plt.gcf())

# 🏪 Top Merchants & Users
with tab5:
    st.header("🏪 Top Merchants & Users")

    top_users = df_completed.groupby("spend.userEmail")["spend.amount_usd"] \
        .sum().sort_values(ascending=False).head(20).reset_index()
    top_users.columns = ["User Email", "Total Spend (USD)"]

    top_merchants_by_spend = df_completed.groupby("spend.merchantName")["spend.amount_usd"] \
        .sum().sort_values(ascending=False).head(10).reset_index()
    top_merchants_by_spend.columns = ["Merchant", "Total Spend (USD)"]

    top_merchants_by_count = df_completed["spend.merchantName"] \
        .value_counts().head(10).reset_index()
    top_merchants_by_count.columns = ["Merchant", "Transaction Count"]

    top_merchants_by_users = df_completed.groupby("spend.merchantName")["spend.userEmail"] \
        .nunique().sort_values(ascending=False).head(10).reset_index()
    top_merchants_by_users.columns = ["Merchant", "Unique User Count"]

    st.subheader("🔝 Top 20 Users by Total Spend")
    st.dataframe(top_users)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💳 Top 10 Merchants by Total Spend")
        st.dataframe(top_merchants_by_spend)
    with col2:
        st.subheader("🧾 Top 10 Merchants by Transaction Count")
        st.dataframe(top_merchants_by_count)

    st.subheader("👥 Top 10 Merchants by Unique User Count")
    st.dataframe(top_merchants_by_users)
