import streamlit as st
import pandas as pd

# ✅ secrets.toml 에 저장된 관리자 비밀번호
ADMIN_PASSWORD = st.secrets["admin"]["password"]

def render(df_completed):
    st.header("🏪 Top Merchants & Users")

    # ✅ 비밀번호 입력받기
    pw_input = st.text_input("🔐 관리자 비밀번호를 입력하면 실제 User ID가 표시됩니다", type="password")

    # ✅ 유저 ID 익명화 매핑
    unique_users = df_completed["spend.userId"].unique()
    anon_map = {uid: f"User {i+1:03d}" for i, uid in enumerate(unique_users)}
    df_completed["anon_user_id"] = df_completed["spend.userId"].map(anon_map)

    # ✅ 표시할 유저 ID 컬럼 결정
    if pw_input == ADMIN_PASSWORD:
        st.success("✅ 관리자 인증 완료: 실제 유저 ID 표시 중")
        user_col = "spend.userId"
    else:
        st.info("🕶️ 익명 유저 ID 표시 중")
        user_col = "anon_user_id"

    # ✅ Top 20 Users by Spend
    top_users = df_completed.groupby(user_col)["spend.amount_usd"] \
        .sum().sort_values(ascending=False).head(20).reset_index()
    top_users.columns = ["User", "Total Spend (USD)"]

    
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
