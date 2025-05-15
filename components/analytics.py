import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

def render(df_total):
    st.header("📈 Analytics")
    df = df_total.copy()

    # ✅ 날짜 파싱
    df["date"] = pd.to_datetime(df["spend.authorizedAt"]).dt.date
    df["week"] = pd.to_datetime(df["date"]).dt.to_period("W").astype(str)

    # ✅ DAU (최근 30일)
    st.subheader("📊 Daily Active Users")
    dau = df.groupby("date")["spend.userEmail"].nunique()
    st.metric("Latest DAU", f"{dau.iloc[-1]:,}")

    fig1, ax1 = plt.subplots(figsize=(10, 3))
    dau.tail(30).plot(ax=ax1, marker='o', color='royalblue')
    ax1.set_title("DAU (Past 30 Days)")
    ax1.set_ylabel("Unique Users")
    ax1.grid(True, linestyle='--', alpha=0.4)
    plt.xticks(rotation=30)
    st.pyplot(fig1)

    # ✅ 누적 평균 지표
    st.subheader("💰 Spend Averages (Cumulative)")
    total_spend = df["spend.amount_usd"].sum()
    total_tx = len(df)
    total_users = df["spend.userEmail"].nunique()
    avg_per_tx = total_spend / total_tx if total_tx else 0
    avg_per_user = total_spend / total_users if total_users else 0

    col1, col2 = st.columns(2)
    col1.metric("Avg per Transaction", f"${avg_per_tx:,.2f}")
    col2.metric("Avg per User", f"${avg_per_user:,.2f}")

    st.markdown("##### ℹ️ Breakdown")
    st.caption(f"🔹 Total Spend: **${total_spend:,.2f}**")
    st.caption(f"🔹 Total Transactions: **{total_tx:,}**")
    st.caption(f"🔹 Unique Users: **{total_users:,}**")

    # ✅ 일간 트렌드
    st.subheader("📊 Daily Spend & Transactions")

    daily_stats = df.groupby("date").agg(
        total_spend=("spend.amount_usd", "sum"),
        tx_count=("spend.amount_usd", "count"),
        unique_users=("spend.userEmail", "nunique")
    ).reset_index()

    # 파생 지표
    daily_stats["avg_spend_per_user"] = daily_stats["total_spend"] / daily_stats["unique_users"]
    daily_stats["avg_tx_per_user"] = daily_stats["tx_count"] / daily_stats["unique_users"]

    # 💰 Daily Spend & Tx Count
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💰 Daily Total Spend")
        fig2, ax2 = plt.subplots(figsize=(7, 3))
        ax2.plot(daily_stats["date"], daily_stats["total_spend"], marker='o', color='blue')
        ax2.set_title("Daily Total Spend")
        ax2.set_ylabel("USD")
        ax2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        ax2.tick_params(axis='x', rotation=30)
        ax2.grid(True, linestyle="--", alpha=0.4)
        st.pyplot(fig2)

    with col2:
        st.subheader("🧾 Daily Transaction Count")
        fig3, ax3 = plt.subplots(figsize=(7, 3))
        ax3.plot(daily_stats["date"], daily_stats["tx_count"], marker='o', color='orange')
        ax3.set_title("Daily Transaction Count")
        ax3.set_ylabel("Tx Count")
        ax3.tick_params(axis='x', rotation=30)
        ax3.grid(True, linestyle="--", alpha=0.4)
        st.pyplot(fig3)

    # 💳 일간 유저당 평균 지표
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💳 Daily Avg Spend per Unique User")
        fig4, ax4 = plt.subplots(figsize=(7, 3))
        ax4.plot(daily_stats["date"], daily_stats["avg_spend_per_user"], marker='o', color='green')
        ax4.set_title("Avg Spend per User (Daily)")
        ax4.set_ylabel("USD")
        ax4.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        ax4.tick_params(axis='x', rotation=30)
        ax4.grid(True, linestyle="--", alpha=0.4)
        st.pyplot(fig4)

    with col2:
        st.subheader("🧾 Daily Avg Tx per Unique User")
        fig5, ax5 = plt.subplots(figsize=(7, 3))
        ax5.plot(daily_stats["date"], daily_stats["avg_tx_per_user"], marker='o', color='seagreen')
        ax5.set_title("Avg Tx per User (Daily)")
        ax5.set_ylabel("Tx Count")
        ax5.tick_params(axis='x', rotation=30)
        ax5.grid(True, linestyle="--", alpha=0.4)
        st.pyplot(fig5)

    # ✅ 주간 통계
    st.subheader("📆 Weekly Summary")

    weekly = df.groupby("week").agg(
        user_count=("spend.userEmail", "nunique"),
        total_tx=("spend.amount_usd", "count"),
        total_spend=("spend.amount_usd", "sum")
    ).reset_index()

    weekly["avg_spend_per_user"] = weekly["total_spend"] / weekly["user_count"]
    weekly["avg_spend_per_tx"] = weekly["total_spend"] / weekly["total_tx"]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("👥 Weekly Unique Users")
        fig6, ax6 = plt.subplots(figsize=(7, 3))
        ax6.plot(weekly["week"], weekly["user_count"], marker='o')
        ax6.set_title("Weekly Unique Users")
        ax6.set_ylabel("Users")
        ax6.tick_params(axis='x', rotation=30)
        ax6.grid(True, linestyle='--', alpha=0.4)
        st.pyplot(fig6)

        st.subheader("🧾 Weekly Transactions")
        fig7, ax7 = plt.subplots(figsize=(7, 3))
        ax7.plot(weekly["week"], weekly["total_tx"], marker='o', color='orange')
        ax7.set_title("Weekly Total Tx")
        ax7.set_ylabel("Tx Count")
        ax7.tick_params(axis='x', rotation=30)
        ax7.grid(True, linestyle='--', alpha=0.4)
        st.pyplot(fig7)

    with col2:
        st.subheader("💳 Weekly Avg Spend per Unique User")
        fig8, ax8 = plt.subplots(figsize=(7, 3))
        ax8.plot(weekly["week"], weekly["avg_spend_per_user"], marker='o', color='green')
        ax8.set_title("Weekly Avg Spend/User")
        ax8.set_ylabel("USD")
        ax8.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        ax8.tick_params(axis='x', rotation=30)
        ax8.grid(True, linestyle='--', alpha=0.4)
        st.pyplot(fig8)

        st.subheader("💸 Weekly Avg Spend per Transaction")
        fig9, ax9 = plt.subplots(figsize=(7, 3))
        ax9.plot(weekly["week"], weekly["avg_spend_per_tx"], marker='o', color='seagreen')
        ax9.set_title("Weekly Avg Spend/Tx")
        ax9.set_ylabel("USD")
        ax9.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        ax9.tick_params(axis='x', rotation=30)
        ax9.grid(True, linestyle='--', alpha=0.4)
        st.pyplot(fig9)
