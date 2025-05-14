import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def render(df_completed):
    st.header("🧑 User Retention (Cohort Analysis)")

    # ✅ 날짜 처리
    df_cohort = df_completed.copy()
    df_cohort["authorized_date"] = pd.to_datetime(df_cohort["spend.authorizedAt"]).dt.normalize()

    # ✅ Cohort 기준일 = 사용자 첫 거래일
    df_cohort["cohort_day0"] = df_cohort.groupby("spend.userEmail")["authorized_date"].transform("min")

    # ✅ Day 기준 차이 계산
    df_cohort["cohort_day"] = (df_cohort["authorized_date"] - df_cohort["cohort_day0"]).dt.days
    df_cohort["cohort_day0_str"] = df_cohort["cohort_day0"].dt.strftime("%Y-%m-%d")

    # ✅ 리텐션 분석 대상 기간 필터링
    df_cohort = df_cohort[df_cohort["cohort_day0"] >= pd.to_datetime("2025-04-15").tz_localize("UTC")]

    # ✅ Pivot Table 생성 (Day 0 대비 N일 후에 재방문한 유저 수)
    retention_table = df_cohort.pivot_table(
        index="cohort_day0_str",
        columns="cohort_day",
        values="spend.userEmail",
        aggfunc="nunique"
    )

    # ✅ 백분율로 변환
    retention_pct = retention_table.divide(retention_table[0], axis=0) * 100

    # ✅ 히트맵 시각화
    st.subheader("📊 Cohort Retention Heatmap")
    plt.figure(figsize=(14, 6))
    sns.heatmap(
        retention_pct,
        annot=True,
        fmt=".1f",
        cmap="YlGnBu",
        linewidths=0.5,
        linecolor="gray",
        cbar=True,
        annot_kws={"size": 8}
    )
    plt.title("User Retention by Cohort (Completed Only)", fontsize=14, weight="bold")
    plt.xlabel("Day Since First Transaction")
    plt.ylabel("Cohort Start Date")
    plt.xticks(rotation=0)
    plt.tight_layout()
    st.pyplot(plt.gcf())
