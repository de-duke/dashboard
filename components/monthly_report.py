import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pycountry

def render(df):
    st.header("📅 Monthly Report")

    # ✅ 월 파싱 & 정렬
    df["month"] = pd.to_datetime(df["spend.authorizedAt"], errors="coerce").dt.to_period("M").astype(str)
    available_months = sorted([m for m in df["month"].dropna().unique()], reverse=True)

    # ✅ 월 선택
    selected_month = st.selectbox("📆 Select Month", available_months)
    selected_idx = available_months.index(selected_month)
    prev_month = available_months[selected_idx + 1] if selected_idx + 1 < len(available_months) else None

    # ✅ 월별 필터링
    df_month = df[df["month"] == selected_month].copy()
    df_prev = df[df["month"] == prev_month].copy() if prev_month else pd.DataFrame(columns=df.columns)

    # ✅ KPI 계산 함수
    def calc_kpi(d):
        if d.empty or "spend.amount_usd" not in d.columns:
            return {"total_spend": 0, "tx_count": 0, "unique_users": 0}
        return {
            "total_spend": d["spend.amount_usd"].sum(),
            "tx_count": d["spend.amount_usd"].count(),
            "unique_users": d["spend.userEmail"].nunique()
        }

    kpi = calc_kpi(df_month)
    prev_kpi = calc_kpi(df_prev)

    def delta(current, prev):
        if prev == 0:
            return "N/A"
        change = (current - prev) / prev * 100
        sign = "🔺" if change >= 0 else "🔻"
        return f"{sign} {change:.1f}%"

    # ✅ KPI 카드
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Spend", f"${kpi['total_spend']:,.2f}", delta(kpi['total_spend'], prev_kpi['total_spend']))
    col2.metric("🧾 Transactions", f"{kpi['tx_count']:,}", delta(kpi['tx_count'], prev_kpi['tx_count']))
    col3.metric("👥 Unique Users", f"{kpi['unique_users']:,}", delta(kpi['unique_users'], prev_kpi['unique_users']))

    # ✅ 평균 계산
    avg_tx = kpi["total_spend"] / kpi["tx_count"] if kpi["tx_count"] else 0
    avg_user = kpi["total_spend"] / kpi["unique_users"] if kpi["unique_users"] else 0
    st.markdown("#### 💳 Monthly Spend Averages")
    col1, col2 = st.columns(2)
    col1.metric("Avg Spend per Tx", f"${avg_tx:,.2f}")
    col2.metric("Avg Spend per User", f"${avg_user:,.2f}")

    st.divider()

    # ✅ 일자별 지표
    st.markdown("### 📈 Daily Trends")
    df_month["date"] = pd.to_datetime(df_month["spend.authorizedAt"]).dt.date
    daily = df_month.groupby("date").agg(
        spend=("spend.amount_usd", "sum"),
        txs=("spend.amount_usd", "count"),
        users=("spend.userEmail", "nunique")
    ).reset_index()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📅 Daily Spend")
        fig, ax = plt.subplots(figsize=(7, 3))
        ax.plot(daily["date"], daily["spend"], marker='o', color='seagreen')
        ax.set_ylabel("USD")
        ax.grid(True, linestyle="--", alpha=0.4)
        st.pyplot(fig)

    with col2:
        st.subheader("📅 Daily Transactions")
        fig2, ax2 = plt.subplots(figsize=(7, 3))
        ax2.plot(daily["date"], daily["txs"], marker='o', color='orange')
        ax2.set_ylabel("Count")
        ax2.grid(True, linestyle="--", alpha=0.4)
        st.pyplot(fig2)

    # ✅ 신규 유저 (그 달에 처음 등장한 이메일 기준)
    df_all = df.copy()
    df_all["first_month"] = pd.to_datetime(df_all["spend.authorizedAt"], errors="coerce").dt.to_period("M").astype(str)
    user_first_month = df_all.groupby("spend.userEmail")["first_month"].min().reset_index()
    new_users = user_first_month[user_first_month["first_month"] == selected_month]
    st.subheader("📊 Monthly New Users")
    st.metric("New Users in Month", len(new_users))

    st.divider()

    # ✅ Top Merchants
    st.markdown("### 🏪 Top Merchants")
    top_merchants = df_month.groupby("spend.merchantName").agg(
        total_spend=("spend.amount_usd", "sum"),
        tx_count=("spend.amount_usd", "count"),
        user_count=("spend.userEmail", "nunique")
    ).sort_values("total_spend", ascending=False).head(10).reset_index()
    st.dataframe(top_merchants)

    # ✅ Country Spend
    st.markdown("### 🌍 Spend by Country")

    def get_country_name(code):
        try:
            return pycountry.countries.get(alpha_2=code).name
        except:
            return code

    df_month["country_name"] = df_month["spend.merchantCountry"].apply(get_country_name)
    country = df_month.groupby("country_name")["spend.amount_usd"].sum().sort_values(ascending=False).head(10)
    fig3, ax3 = plt.subplots(figsize=(10, 3))
    country.plot(kind="bar", ax=ax3, color='royalblue')
    ax3.set_ylabel("USD")
    ax3.set_title("Top 10 Countries by Spend")
    ax3.tick_params(axis='x', rotation=45)
    ax3.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    st.pyplot(fig3)

    st.divider()

    # ✅ Spend by Merchant Category
    st.markdown("### 🧾 Spend by Merchant Category")
    cat_df = df_month.groupby("spend.merchantCategory").agg(
        total_spend=("spend.amount_usd", "sum"),
        tx_count=("spend.amount_usd", "count"),
        user_count=("spend.userEmail", "nunique")
    ).sort_values("total_spend", ascending=False).head(10).reset_index()
    st.dataframe(cat_df)

    fig4, ax4 = plt.subplots(figsize=(10, 4))
    ax4.bar(cat_df["spend.merchantCategory"], cat_df["total_spend"], color="darkgreen")
    ax4.set_title("Top 10 Merchant Categories by Spend")
    ax4.set_ylabel("USD")
    ax4.set_xlabel("Category")
    ax4.tick_params(axis="x", rotation=45)
    ax4.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    st.pyplot(fig4)

    fig5, ax5 = plt.subplots(figsize=(10, 4))
    ax5.bar(cat_df["spend.merchantCategory"], cat_df["tx_count"], color="orange")
    ax5.set_title("Top 10 Merchant Categories by Transaction Count")
    ax5.set_ylabel("Transactions")
    ax5.set_xlabel("Category")
    ax5.tick_params(axis="x", rotation=45)
    st.pyplot(fig5)

    fig6, ax6 = plt.subplots(figsize=(10, 4))
    ax6.bar(cat_df["spend.merchantCategory"], cat_df["user_count"], color="royalblue")
    ax6.set_title("Top 10 Merchant Categories by Unique Users")
    ax6.set_ylabel("Users")
    ax6.set_xlabel("Category")
    ax6.tick_params(axis="x", rotation=45)
    st.pyplot(fig6)
