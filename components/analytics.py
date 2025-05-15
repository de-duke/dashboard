import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

def render(df):
    st.header("📈 Analytics")

    st.subheader("📊 Daily Active Users (DAU)")
    df["date"] = pd.to_datetime(df["spend.authorizedAt"]).dt.date
    dau = df.groupby("date")["spend.userEmail"].nunique()

    st.metric("Latest DAU", f"{dau.iloc[-1]:,}")
    fig1, ax1 = plt.subplots(figsize=(10, 3))
    dau.tail(30).plot(ax=ax1, color="royalblue", marker="o")
    ax1.set_title("DAU (Past 30 Days)")
    ax1.set_ylabel("Unique Users")
    ax1.grid(True, linestyle="--", alpha=0.5)
    plt.xticks(rotation=30)
    st.pyplot(fig1)

    st.subheader("💰 Spend Averages")
    avg_per_tx = df["spend.amount_usd"].mean()
    avg_per_user = df.groupby("spend.userEmail")["spend.amount_usd"].sum().mean()

    col1, col2 = st.columns(2)
    col1.metric("Average per Transaction", f"${avg_per_tx:,.2f}")
    col2.metric("Average per User", f"${avg_per_user:,.2f}")

    st.subheader("📦 Sample: Points Conversion Rate (if data available)")

    if "type" in df.columns:
        total_point_earners = df[df["type"] == "points_earned"]["spend.userEmail"].nunique()
        total_point_users = df[df["type"] == "points_redeemed"]["spend.userEmail"].nunique()
        if total_point_earners:
            point_conversion_rate = (total_point_users / total_point_earners) * 100
            st.metric("Points Conversion Rate", f"{point_conversion_rate:.1f}%")
        else:
            st.info("No point earning records found.")
    else:
        st.warning("No 'type' column in data. Skipping points analysis.")

    st.subheader("🌍 Country Concentration")

    country_counts = df["spend.merchantCountry"].value_counts()
    top3_share = (country_counts.head(3).sum() / country_counts.sum()) * 100
    st.metric("Top 3 Countries Concentration", f"{top3_share:.1f}%")

    st.bar_chart(country_counts.head(10))
