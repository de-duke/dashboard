import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

def render(df_total):
    st.header("📈 Analytics (Completed + Pending)")
    df = df_total.copy()

    # ✅ 날짜 전처리
    df["date"] = pd.to_datetime(df["spend.authorizedAt"]).dt.date
    df["week"] = pd.to_datetime(df["date"]).dt.to_period("W").astype(str)

    # ✅ DAU
    st.subheader("📊 Daily Active Users")
    dau = df.groupby("date")["spend.userEmail"].nunique()
    st.metric("Latest DAU", f"{dau.iloc[-1]:,}")
    fig1, ax1 = plt.subplots(figsize=(10, 3))
    dau.tail(30).plot(ax=ax1, marker='o', color='royalblue')
    ax1.set_title("DAU (Past 30 Days)")
    ax1.set_ylabel("Users")
    ax1.grid(True, linestyle='--', alpha=0.4)
    st.pyplot(fig1)

    # ✅ Spend Averages
    st.subheader("💰 Spend Averages")
    total_spend = df["spend.amount_usd"].sum()
    total_tx = len(df)
    total_users = df["spend.userEmail"].nunique()
    avg_per_tx = total_spend / total_tx if total_tx else 0
    avg_per_user = total_spend / total_users if total_users else 0

    col1, col2 = st.columns(2)
    col1.metric("Avg per Tx", f"${avg_per_tx:,.2f}")
    col2.metric("Avg per User", f"${avg_per_user:,.2f}")
    st.caption(f"🔹 Total Spend: ${total_spend:,.2f}")
    st.caption(f"🔹 Total Tx: {total_tx:,}")
    st.caption(f"🔹 Unique Users: {total_users:,}")

    # ✅ 주간 요약 계산
    st.subheader("📊 Weekly Summary")
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
        fig2, ax2 = plt.subplots(figsize=(7, 3))
        ax2.plot(weekly["week"], weekly["user_count"], marker='o')
        ax2.set_title("Weekly Unique Users")
        ax2.set_ylabel("Users")
        ax2.tick_params(axis='x', rotation=30)
        ax2.grid(True, linestyle='--', alpha=0.4)
        st.pyplot(fig2)

        st.subheader("🧾 Weekly Transactions")
        fig3, ax3 = plt.subplots(figsize=(7, 3))
        ax3.plot(weekly["week"], weekly["total_tx"], marker='o', color='orange')
        ax3.set_title("Weekly Total Tx")
        ax3.set_ylabel("Tx Count")
        ax3.tick_params(axis='x', rotation=30)
        ax3.grid(True, linestyle='--', alpha=0.4)
        st.pyplot(fig3)

    with col2:
        st.subheader("💳 Avg Spend per User")
        fig4, ax4 = plt.subplots(figsize=(7, 3))
        ax4.plot(weekly["week"], weekly["avg_spend_per_user"], marker='o', color='green')
        ax4.set_title("Weekly Avg/User")
        ax4.set_ylabel("USD")
        ax4.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        ax4.tick_params(axis='x', rotation=30)
        ax4.grid(True, linestyle='--', alpha=0.4)
        st.pyplot(fig4)

        st.subheader("💸 Avg Spend per Tx")
        fig5, ax5 = plt.subplots(figsize=(7, 3))
        ax5.plot(weekly["week"], weekly["avg_spend_per_tx"], marker='o', color='seagreen')
        ax5.set_title("Weekly Avg/Tx")
        ax5.set_ylabel("USD")
        ax5.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        ax5.tick_params(axis='x', rotation=30)
        ax5.grid(True, linestyle='--', alpha=0.4)
        st.pyplot(fig5)
