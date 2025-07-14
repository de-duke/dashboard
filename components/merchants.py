import streamlit as st
import pandas as pd
import pycountry
from supabase import create_client
import os

# Supabase 연결
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

ADMIN_PASSWORD = st.secrets["admin"]["password"]

# ✅ 국가코드 → 국가명
def get_country_name(code):
    try:
        return pycountry.countries.get(alpha_2=code.upper()).name
    except:
        return code

def render(df_completed):
    st.header("🏪 Top Merchants & Users")

    # ✅ 비밀번호 입력
    pw_input = st.text_input("Enter the admin password to view full user IDs", type="password")

    # ✅ 익명화 처리
    unique_users = df_completed["spend.userId"].unique()
    anon_map = {uid: f"User {i+1:03d}" for i, uid in enumerate(unique_users)}
    df_completed["anon_user_id"] = df_completed["spend.userId"].map(anon_map)

    user_col = "spend.userId" if pw_input == ADMIN_PASSWORD else "anon_user_id"
    if pw_input == ADMIN_PASSWORD:
        st.success("✅ Admin access granted: showing full user IDs")
    else:
        st.info("🕶️ Showing anonymized user IDs")

    # ✅ 유저 테이블에서 countryCode 가져오기
    users_data = supabase.table("users").select("id, address").execute().data
    users_df = pd.DataFrame(users_data)
    users_df["country_code"] = users_df["address"].apply(
        lambda x: x.get("countryCode") if isinstance(x, dict) and "countryCode" in x else None
    )
    users_df["user_country"] = users_df["country_code"].apply(get_country_name)

    # ✅ 유저 country 병합
    df_completed = df_completed.merge(
        users_df[["id", "user_country"]],
        left_on="spend.userId",
        right_on="id",
        how="left"
    )

    # ✅ 각 유저가 가장 많이 지출한 2개 국가 계산
    user_country_spend = df_completed.groupby(["spend.userId", "spend.merchantCountry"])["spend.amount_usd"].sum().reset_index()
    user_country_spend["rank"] = user_country_spend.groupby("spend.userId")["spend.amount_usd"].rank(method="first", ascending=False)
    top2_countries = user_country_spend[user_country_spend["rank"] <= 2].sort_values(["spend.userId", "rank"])

    # ✅ Top 2 국가를 병합 (→ 국가 이름 변환 포함)
    def map_codes_to_names(code_list):
        return ", ".join([get_country_name(code) for code in code_list])

    country_list = (
        top2_countries.groupby("spend.userId")["spend.merchantCountry"]
        .apply(lambda x: map_codes_to_names(x.tolist()))
        .reset_index()
    )
    country_list.columns = ["spend.userId", "top_countries_spent"]

    # ✅ Top 20 유저 집계
    top_users = df_completed.groupby("spend.userId")["spend.amount_usd"].sum().sort_values(ascending=False).head(20).reset_index()
    top_users = top_users.merge(
        df_completed[["spend.userId", "anon_user_id", "user_country"]].drop_duplicates("spend.userId"),
        on="spend.userId", how="left"
    ).merge(country_list, on="spend.userId", how="left")

    # ✅ 컬럼 구성
    top_users["User"] = top_users[user_col]
    top_users = top_users[["User", "spend.amount_usd", "user_country", "top_countries_spent"]]
    top_users.columns = ["User", "Total Spend (USD)", "User Country", "Top 2 Spend Countries"]

    st.subheader("🔝 Top 20 Users by Total Spend")
    st.dataframe(top_users)

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

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💳 Top 10 Merchants by Total Spend")
        st.dataframe(top_merchants_by_spend)

    with col2:
        st.subheader("🧾 Top 10 Merchants by Transaction Count")
        st.dataframe(top_merchants_by_count)

    st.subheader("👥 Top 10 Merchants by Unique User Count")
    st.dataframe(top_merchants_by_users)
