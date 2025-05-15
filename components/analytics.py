import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

def render(df_total):
    st.header("📈 Analytics Overview")

    df = df_total.copy()
    df["date"] = pd.to_datetime(df["spend.authorizedAt"]).dt.date
    df["week"] = pd.to_datetime(df["date"]).dt.to_period("W").astype(str)

    # ✅ KPI: 최상단 카드
    total_spend = df["spend.amount_usd"].sum()
    total_tx = len(df)
    total_users = df["spend.userEmail"].nunique()

    col1, col2, col3 = st.columns(3)
    col1.metric("🔹 Total Spend", f"${total_spend:,.2f}")
    col2.metric("🔹 Total Transactions", f"{total_tx:,}")
    col3.metric("🔹 Unique Users", f"{total_users:,}")

    st.divider()

    # ✅ 누적 평균 지표
    st.subheader("💰 Spend Averages (Cumulative)")

    avg_per_tx = total_spend / total_tx if total_tx else 0
    avg_per_user = total_spend / total_users if total_users else 0

    col1, col2 = st.columns(2)
    col1.metric("Avg per Transaction", f"${avg_per_tx:,.2f}")
    col2.metric("Avg per User", f"${avg_per_user:,.2f}")

    st.divider()

    # ✅ 📆 Daily Data Section
    st.subheader("📆 Daily Data")

    daily_stats = df.groupby("date").agg(
        total_spend=("spend.amount_usd", "sum"),
        tx_count=("spend.amount_usd", "count"),
        unique_users=("spend.userEmail", "nunique")
    ).reset_index()

    # 🧑‍💻 신규 유저 계산
    user_min_date = df.groupby("spend.userEmail")["date"].min()
    new_user_daily = user_min_date.value_counts().sort_index().rename_axis("date").reset_index(name="new_users")
    daily_stats = pd.merge(daily_stats, new_user_daily, on="date", how="left").fillna(0)

    daily_stats["avg_spend_per_user"] = daily_stats["total_spend"] / daily_stats["unique_users"]
    daily_stats["avg_tx_per_user"] = daily_stats["tx_count"] / daily_stats["unique_users"]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Daily Active Users (DAU)")
        dau = daily_stats.set_index("date")["unique_users"]
        fig, ax = plt.subplots(figsize=(7, 3))
        dau.tail(30).plot(ax=ax, marker='o', color='royalblue')
        ax.set_title("DAU (Past 30 Days)")
        ax.set_ylabel("Users")
        ax.tick_params(axis='x', rotation=30)
        ax.grid(True, linestyle='--', alpha=0.4)
        st.pyplot(fig)

    with col2:
        st.subheader("🧑‍💼 Daily New Users")
        fig2, ax2 = plt.subplots(figsize=(7, 3))
        ax2.plot(daily_stats["date"], daily_stats["new_users"], marker='o', color='mediumseagreen')
        ax2.set_title("New Users per Day")
        ax2.set_ylabel("Users")
        ax2.tick_params(axis='x', rotation=30)
        ax2.grid(True, linestyle='--', alpha=0.4)
        st.pyplot(fig2)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💰 Daily Total Spend")
        fig3, ax3 = plt.subplots(figsize=(7, 3))
        ax3.plot(daily_stats["date"], daily_stats["total_spend"], marker='o', color='blue')
        ax3.set_title("Daily Spend")
        ax3.set_ylabel("USD")
        ax3.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        ax3.tick_params(axis='x', rotation=30)
        ax3.grid(True, linestyle='--', alpha=0.4)
        st.pyplot(fig3)

    with col2:
        st.subheader("🧾 Daily Transactions")
        fig4, ax4 = plt.subplots(figsize=(7, 3))
        ax4.plot(daily_stats["date"], daily_stats["tx_count"], marker='o', color='orange')
        ax4.set_title("Transaction Count")
        ax4.set_ylabel("Tx Count")
        ax4.tick_params(axis='x', rotation=30)
        ax4.grid(True, linestyle='--', alpha=0.4)
        st.pyplot(fig4)


        # 유저별 일일 지출 합계
    daily_user_spend = df.groupby(["date", "spend.userEmail"])["spend.amount_usd"].sum().reset_index()
    pivot_spend = daily_user_spend.pivot(columns="date", values="spend.amount_usd")
    
    # 유저별 일일 tx 횟수
    daily_user_tx = df.groupby(["date", "spend.userEmail"]).size().reset_index(name="tx_count")
    pivot_tx = daily_user_tx.pivot(columns="date", values="tx_count")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💳 Daily Spend per User (Boxplot)")
        fig_spend, ax_spend = plt.subplots(figsize=(7, 3))
        pivot_spend.plot.box(ax=ax_spend, rot=30)
        ax_spend.set_ylabel("USD")
        ax_spend.set_title("Spend Distribution per Day")
        st.pyplot(fig_spend)
    
    with col2:
        st.subheader("🧾 Daily Tx Count per User (Boxplot)")
        fig_tx, ax_tx = plt.subplots(figsize=(7, 3))
        pivot_tx.plot.box(ax=ax_tx, rot=30)
        ax_tx.set_ylabel("Tx Count")
        ax_tx.set_title("Tx Count Distribution per Day")
        st.pyplot(fig_tx)

    st.divider()

    # ✅ 📅 Weekly Summary Section
    st.subheader("📅 Weekly Data")

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
        fig5, ax5 = plt.subplots(figsize=(7, 3))
        ax5.plot(weekly["week"], weekly["user_count"], marker='o')
        ax5.set_title("Weekly Unique Users")
        ax5.set_ylabel("Users")
        ax5.tick_params(axis='x', rotation=30)
        ax5.grid(True, linestyle='--', alpha=0.4)
        st.pyplot(fig5)

        st.subheader("🧾 Weekly Transactions")
        fig6, ax6 = plt.subplots(figsize=(7, 3))
        ax6.plot(weekly["week"], weekly["total_tx"], marker='o', color='orange')
        ax6.set_title("Weekly Transactions")
        ax6.set_ylabel("Tx Count")
        ax6.tick_params(axis='x', rotation=30)
        ax6.grid(True, linestyle='--', alpha=0.4)
        st.pyplot(fig6)

    with col2:
        st.subheader("💳 Weekly Avg Spend per Unique User")
        fig7, ax7 = plt.subplots(figsize=(7, 3))
        ax7.plot(weekly["week"], weekly["avg_spend_per_user"], marker='o', color='green')
        ax7.set_title("Weekly Avg/User")
        ax7.set_ylabel("USD")
        ax7.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        ax7.tick_params(axis='x', rotation=30)
        ax7.grid(True, linestyle='--', alpha=0.4)
        st.pyplot(fig7)

        st.subheader("💸 Weekly Avg Spend per Transaction")
        fig8, ax8 = plt.subplots(figsize=(7, 3))
        ax8.plot(weekly["week"], weekly["avg_spend_per_tx"], marker='o', color='seagreen')
        ax8.set_title("Weekly Avg/Tx")
        ax8.set_ylabel("USD")
        ax8.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        ax8.tick_params(axis='x', rotation=30)
        ax8.grid(True, linestyle='--', alpha=0.4)
        st.pyplot(fig8)
