import streamlit as st
import pandas as pd

def render(df_completed):
    st.header("🏪 Top Merchants & Users")

    # ✅ Top 20 Users by Total Spend
    top_users = df_completed.groupby("spend.userId")["spend.amount_usd"] \
        .sum().sort_values(ascending=False).head(20).reset_index()
    top_users.columns = ["User Email", "Total Spend (USD)"]

    # ✅ Top 10 Merchants by Spend
    top_merchants_by_spend = df_completed.groupby("spend.merchantName")["spend.amount_usd"] \
        .sum().sort_values(ascending=False).head(10).reset_index()
    top_merchants_by_spend.columns = ["Merchant", "Total Spend (USD)"]

    # ✅ Top 10 Merchants by Transaction Count
    top_merchants_by_count = df_completed["spend.merchantName"] \
        .value_counts().head(10).reset_index()
    top_merchants_by_count.columns = ["Merchant", "Transaction Count"]

    # ✅ Top 10 Merchants by Unique Users
    top_merchants_by_users = df_completed.groupby("spend.merchantName")["spend.userEmail"] \
        .nunique().sort_values(ascending=False).head(10).reset_index()
    top_merchants_by_users.columns = ["Merchant", "Unique User Count"]

    # ✅ 시각화
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
