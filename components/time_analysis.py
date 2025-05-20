import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

def render(df_total):
    st.header("⏱ Time-based Analysis")

    # 거래 상태별 필터링
    df_completed = df_total[df_total["spend.status"] == "completed"]
    df_pending = df_total[df_total["spend.status"] == "pending"]
    df_all = df_total.copy()


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

    status_order = ["completed", "pending", "reversed", "declined"]

    daily_status_spend = df_all.groupby(["date_utc", "spend.status"])["spend.amount_usd"].sum().unstack(fill_value=0)
    for status in status_order:
        if status not in daily_status_spend.columns:
            daily_status_spend[status] = 0
    daily_status_spend = daily_status_spend[status_order]

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

    # ✅ 일자별 상태별 거래 수 집계 (표로 출력)
    st.subheader("📋 Daily Transaction Count by Status (UTC)")

    daily_status_count = df_all.groupby(["date_utc", "spend.status"]).size().unstack(fill_value=0)
    for status in status_order:
        if status not in daily_status_count.columns:
            daily_status_count[status] = 0
    daily_status_count = daily_status_count[status_order]
    daily_status_count = daily_status_count.reset_index()
    st.dataframe(daily_status_count.style.format(precision=0), use_container_width=True)

    
    st.write("🔍 Unique spend.status values in df_total:")
    st.write(df_total["spend.status"].dropna().unique())
