import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

def render(df_total):
    st.header("📈 Analytics (Completed + Pending)")

    df = df_total.copy()
    df["date"] = pd.to_datetime(df["spend.authorizedAt"]).dt.date

    # ✅ Daily Active Users (DAU)
    st.subheader("📊 Daily Active Users (DAU)")
    dau = df.groupby("date")["spend.userEmail"].nunique()
    st.metric("Latest DAU", f"{dau.iloc[-1]:,}")

    fig1, ax1 = plt.subplots(figsize=(10, 3))
    dau.tail(30).plot(ax=ax1, color="royalblue", marker="o")
    ax1.set_title("DAU (Past 30 Days)")
    ax1.set_ylabel("Unique Users")
    ax1.grid(True, linestyle="--", alpha=0.5)
    plt.xticks(rotation=30)
    st.pyplot(fig1)


    # ✅ Spend Averages
st.subheader("💰 Spend Averages")

# 총합 지표 계산
total_spend = df["spend.amount_usd"].sum()
total_tx = df.shape[0]
total_users = df["spend.userEmail"].nunique()

# 평균 계산
avg_per_tx = total_spend / total_tx if total_tx else 0
avg_per_user = total_spend / total_users if total_users else 0

# ✅ 주요 요약 카드 표시
col1, col2 = st.columns(2)
col1.metric("Average per Transaction", f"${avg_per_tx:,.2f}")
col2.metric("Average per User", f"${avg_per_user:,.2f}")

# ✅ 계산 근거 텍스트 표시
st.caption(f"🔹 Total Spend: **${total_spend:,.2f}**")
st.caption(f"🔹 Total Transactions: **{total_tx:,}**")
st.caption(f"🔹 Unique Users: **{total_users:,}**")

    # ✅ Spend Averages
    st.subheader("💰 Spend Averages")
    avg_per_tx = df["spend.amount_usd"].mean()
    avg_per_user = df.groupby("spend.userEmail")["spend.amount_usd"].sum().mean()

    col1, col2 = st.columns(2)
    col1.metric("Average per Transaction", f"${avg_per_tx:,.2f}")
    col2.metric("Average per User", f"${avg_per_user:,.2f}")

    # ✅ Weekly User & Spend Stats (호출)
    weekly_user_spend_stats(df)

# ✅ 주간 유저/지출 지표 함수
def weekly_user_spend_stats(df):
    st.header("📊 Weekly User & Spend Summary")

    # ✅ 주 단위 준비
    df["week"] = pd.to_datetime(df["date_utc"]).dt.to_period("W").astype(str)

    # ✅ 집계
    weekly_stats = df.groupby("week").agg(
        user_count=("spend.userEmail", "nunique"),
        total_tx=("spend.amount_usd", "count"),
        total_spend=("spend.amount_usd", "sum")
    ).reset_index()

    # ✅ 파생 지표
    weekly_stats["avg_per_user"] = weekly_stats["total_spend"] / weekly_stats["user_count"]
    weekly_stats["avg_per_tx"] = weekly_stats["total_spend"] / weekly_stats["total_tx"]

    # ✅ 시각화
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("👥 Weekly Unique Users")
        fig1, ax1 = plt.subplots(figsize=(7, 3))
        ax1.plot(weekly_stats["week"], weekly_stats["user_count"], marker='o')
        ax1.set_title("Unique Users per Week")
        ax1.set_ylabel("Users")
        ax1.tick_params(axis='x', rotation=30)
        ax1.grid(True, linestyle='--', alpha=0.4)
        st.pyplot(fig1)

        st.subheader("🧾 Weekly Tx Count")
        fig2, ax2 = plt.subplots(figsize=(7, 3))
        ax2.plot(weekly_stats["week"], weekly_stats["total_tx"], marker='o', color='darkorange')
        ax2.set_title("Total Transactions per Week")
        ax2.set_ylabel("Tx Count")
        ax2.tick_params(axis='x', rotation=30)
        ax2.grid(True, linestyle='--', alpha=0.4)
        st.pyplot(fig2)

    with col2:
        st.subheader("💳 Avg Spend per User")
        fig3, ax3 = plt.subplots(figsize=(7, 3))
        ax3.plot(weekly_stats["week"], weekly_stats["avg_per_user"], marker='o', color='green')
        ax3.set_title("Avg Spend/User")
        ax3.set_ylabel("USD")
        ax3.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        ax3.tick_params(axis='x', rotation=30)
        ax3.grid(True, linestyle='--', alpha=0.4)
        st.pyplot(fig3)

        st.subheader("💸 Avg Spend per Tx")
        fig4, ax4 = plt.subplots(figsize=(7, 3))
        ax4.plot(weekly_stats["week"], weekly_stats["avg_per_tx"], marker='o', color='seagreen')
        ax4.set_title("Avg Spend/Tx")
        ax4.set_ylabel("USD")
        ax4.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        ax4.tick_params(axis='x', rotation=30)
        ax4.grid(True, linestyle='--', alpha=0.4)
        st.pyplot(fig4)
