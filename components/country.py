import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import pycountry
import plotly.express as px

def render(df_completed, df_pending):
    st.header("🌍 Country-Based Analysis")

    # ✅ 국가코드 → 국가명 / ISO3 변환 함수
    def get_country_name(code):
        try:
            return pycountry.countries.get(alpha_2=code).name
        except:
            return code

    def get_iso3(code):
        try:
            return pycountry.countries.get(alpha_2=code).alpha_3
        except:
            return None

    # ✅ 국가별 지출 합계
    spend_completed = df_completed.groupby("spend.merchantCountry")["spend.amount_usd"].sum()
    spend_pending = df_pending.groupby("spend.merchantCountry")["spend.amount_usd"].sum()

    country_df = pd.DataFrame({
        "Completed": spend_completed,
        "Pending": spend_pending
    }).fillna(0)

    country_df.index = country_df.index.map(get_country_name)
    country_df["Total"] = country_df["Completed"] + country_df["Pending"]
    top10_df = country_df.sort_values("Total", ascending=False).head(10)[["Completed", "Pending"]]

    # ✅ 상위 10개 국가 스택형 바차트
    st.subheader("📊 Top 10 Countries by Spend")
    fig, ax = plt.subplots(figsize=(10, 4))
    top10_df.plot(kind="bar", stacked=True, color=["green", "orange"], ax=ax)
    ax.set_title("Top 10 Countries by Total Spend")
    ax.set_ylabel("Spend (USD)")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
    ax.grid(True, linestyle='--', alpha=0.3)
    st.pyplot(fig)

    # ✅ Choropleth 지도 시각화
    st.subheader("🗺️ Global Distribution of Completed Transactions")
    country_counts = df_completed["spend.merchantCountry"].value_counts().reset_index()
    country_counts.columns = ["country_code", "appeared"]
    country_counts["iso3"] = country_counts["country_code"].apply(get_iso3)
    country_counts["country_name"] = country_counts["country_code"].apply(get_country_name)
    map_df = country_counts.dropna(subset=["iso3"])

    fig_map = px.choropleth(
        map_df,
        locations="iso3",
        color="appeared",
        hover_name="country_name",
        color_continuous_scale=["#d0f0c0", "#2e8b57", "#006400"],
        title="🌍 Completed Transactions by Country",
        projection="robinson"
    )
    fig_map.update_layout(
        margin=dict(r=0, t=50, l=0, b=0),
        height=500
    )
    st.plotly_chart(fig_map, use_container_width=True)
