import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

def render(df, df_completed, df_pending):
    df_total = pd.concat([df_completed, df_pending], ignore_index=True)

    st.header("📊 Summary Statistics")
    st.markdown(f"🔄 **Raw rows loaded from Supabase:** `{len(df):,}` rows")

    # ✅ 핵심 요약 지표
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Transactions", len(df_total))
    col2.metric("Total Volume (USD)", f"${df_total['spend.amount_usd'].sum():,.2f}")
    col3.metric("Unique Users", df_total["spend.userID"].nunique())

    # ✅ 고급 지표 계산
    weekly_tx = df.groupby(["spend.userEmail", "week"]).size().reset_index(name="tx_count")
    latest_week = df["week"].max()
    latest_week_df = weekly_tx[weekly_tx["week"] == latest_week]

    recurring_users = latest_week_df[latest_week_df["tx_count"] >= 2]["spend.userEmail"].nunique()
    total_users = latest_week_df["spend.userEmail"].nunique()
    recurring_pct = (recurring_users / total_users) * 100 if total_users else 0

    country_counts = df["spend.merchantCountry"].value_counts()
    top3_concentration = (country_counts.head(3).sum() / country_counts.sum()) * 100 if not country_counts.empty else 0

    col1, col2 = st.columns(2)
    col1.metric("Recurring Users % (Last Week)", f"{recurring_pct:.1f}%")
    col2.metric("Top 3 Country Concentration", f"{top3_concentration:.1f}%")

    # ✅ 주간 신규 사용자 수
    user_min_week = df.groupby("spend.userEmail")["week"].min()
    weekly_new_users = user_min_week.value_counts().sort_index()

    # ✅ 주간 총 지출
    weekly_spend = df.groupby("week")["spend.amount_usd"].sum().sort_index()

    # ✅ 2열 배치로 주간 추세 시각화
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📅 Weekly New Users")
        fig, ax = plt.subplots(figsize=(6, 3))
        weekly_new_users.plot(ax=ax, marker='o', color='steelblue')
        ax.set_title("Weekly New Users")
        ax.set_xlabel("Week")
        ax.set_ylabel("Users")
        ax.tick_params(axis='x', labelrotation=30, labelsize=8)
        ax.grid(True, linestyle='--', alpha=0.4)
        st.pyplot(fig)

    with col2:
        st.subheader("💸 Weekly Spend (USD)")
        fig2, ax2 = plt.subplots(figsize=(6, 3))
        weekly_spend.plot(ax=ax2, marker='o', color='green')
        ax2.set_title("Weekly Spend")
        ax2.set_xlabel("Week")
        ax2.set_ylabel("USD")
        ax2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        ax2.tick_params(axis='x', labelrotation=30, labelsize=8)
        ax2.grid(True, linestyle='--', alpha=0.4)
        st.pyplot(fig2)
