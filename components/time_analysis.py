import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

def render(df_completed, df_pending):
    st.header("⏱ Time-based Analysis")

    # ✅ 시간대별 소비 합계
    st.subheader("⏰ Hourly Spend (UTC)")
    hourly_spend_completed = df_completed.groupby("hour_utc")["spend.amount_usd"].sum()
    hourly_spend_pending = df_pending.groupby("hour_utc")["spend.amount_usd"].sum()

    hourly_df = pd.DataFrame({
        "Completed": hourly_spend_completed,
        "Pending": hourly_spend_pending
    }).fillna(0)

    fig, ax = plt.subplots(figsize=(10, 4))
    hourly_df.plot(kind="bar", stacked=True, color=["green", "orange"], ax=ax)
    ax.set_title("Hourly Spend by Status")
    ax.set_xlabel("Hour (UTC)")
    ax.set_ylabel("Total Spend (USD)")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.grid(True, linestyle="--", alpha=0.4)
    st.pyplot(fig)

    # ✅ 일자별 거래 수 및 금액
    st.subheader("📅 Daily Transaction Count & Volume")
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
    ax2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax2.grid(True, linestyle="--", alpha=0.5)

    plt.xticks(rotation=45)
    fig.tight_layout()
    st.pyplot(fig)


    # ✅ 일자별 거래 상태별 금액 (stacked bar)
    st.subheader("📊 Daily Spend by Status (UTC)")

    # 필요한 상태 목록 정의
    df_all = pd.concat([df_completed, df_pending])
    status_order = ["completed", "pending", "reversed", "declined"]

    # 일자별 상태별 금액 합계
    daily_status_spend = df_all.groupby(["date_utc", "spend.status"])["spend.amount_usd"].sum().unstack(fill_value=0)

    # 모든 상태 컬럼이 보장되도록 정렬
    for status in status_order:
        if status not in daily_status_spend.columns:
            daily_status_spend[status] = 0
    daily_status_spend = daily_status_spend[status_order]  # 컬럼 순서 고정

    fig, ax = plt.subplots(figsize=(10, 5))
    daily_status_spend.plot(kind="bar", stacked=True, ax=ax,
                            color=["green", "orange", "gray", "red"])
    ax.set_title("Daily Spend by Status")
    ax.set_xlabel("Date (UTC)")
    ax.set_ylabel("Spend (USD)")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, linestyle='--', alpha=0.4)
    st.pyplot(fig)
