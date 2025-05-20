import streamlit as st
import pandas as pd

def render(df):
    st.header("🛑 Risk & Abuse Detection (Supabase 기반)")

    # ✅ 시간 파싱
    df["timestamp"] = pd.to_datetime(df["spend.authorizedAt"])

    # ✅ 사용자 기준 컬럼
    user_col = "spend.userId"

    # ✅ 상태 정리 (소문자, 공백 제거)
    df["spend.status"] = df["spend.status"].astype(str).str.strip().str.lower()

    # ✅ 1. 사용자별 취소율 (reversed 기준)
    cancel_rate = (
        df.groupby(user_col)
        .apply(lambda x: (x["spend.status"] == "reversed").sum() / len(x))
        .reset_index(name="cancel_rate")
    )

    # ✅ 2. 실패율 높은 사용자 (declined 기준)
    fail_rate = (
        df.groupby(user_col)
        .apply(lambda x: (x["spend.status"] == "declined").sum() / len(x))
        .reset_index(name="fail_rate")
    )

    # ✅ 3. 연속 취소 탐지
    df_sorted = df.sort_values([user_col, "timestamp"])
    df_sorted["is_cancel"] = df_sorted["spend.status"] == "reversed"
    df_sorted["cancel_streak"] = (
        df_sorted.groupby(user_col)["is_cancel"]
        .transform(lambda x: x.cumsum() - x.cumsum().where(~x).ffill().fillna(0))
    )

    # ✅ 📊 취소율/실패율 요약 테이블
    st.subheader("📊 사용자별 취소율 / 실패율")
    summary = cancel_rate.merge(fail_rate, on=user_col)
    st.dataframe(
        summary.sort_values(["cancel_rate", "fail_rate"], ascending=False).head(20)
    )

    # ✅ 📈 연속 취소 유저 예시
    st.subheader("📈 사용자별 연속 취소 횟수 예시")
    streak_df = df_sorted[df_sorted["cancel_streak"] > 1]
    st.dataframe(
        streak_df[[user_col, "timestamp", "spend.status", "cancel_streak"]].head(20)
    )
