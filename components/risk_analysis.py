import streamlit as st
import pandas as pd

def render(df):
    st.header("🛑 Risk & Abuse Detection (Supabase 기반)")

    # ✅ timestamp 파싱
    df["timestamp"] = pd.to_datetime(df["spend.authorizedAt"])

    # ✅ 사용자 식별자 선택 (user_id 또는 spend.userEmail)
    user_col = "user_id" if "user_id" in df.columns else "spend.userEmail"

    # ✅ 1. 사용자별 취소율
    cancel_rate = (
        df.groupby(user_col)
        .apply(lambda x: (x["spend.status"] == "cancelled").sum() / len(x))
        .reset_index(name="cancel_rate")
    )

    # ✅ 2. 빠른 취소 감지는 불가능 (cancelled_at 필드 없음)
    st.info("🚫 'cancelled_at' 필드가 없어 빠른 취소 감지는 생략됩니다.")

    # ✅ 3. 연속 취소 횟수 계산 (cancel_streak)
    df_sorted = df.sort_values([user_col, "timestamp"])
    df_sorted["is_cancel"] = df_sorted["spend.status"] == "cancelled"
    df_sorted["cancel_streak"] = (
        df_sorted.groupby(user_col)["is_cancel"]
        .transform(lambda x: x.cumsum() - x.cumsum().where(~x).ffill().fillna(0))
    )

    # ✅ 4. 실패율 높은 사용자
    fail_rate = (
        df.groupby(user_col)
        .apply(lambda x: (x["spend.status"] == "failed").sum() / len(x))
        .reset_index(name="fail_rate")
    )

    # ✅ 5. 이상 시간대 거래 (새벽 1시~4시)
    df["hour"] = df["timestamp"].dt.hour
    late_night_tx = df[df["hour"].isin(range(1, 5))]

    # ✅ 사용자별 취소율 + 실패율 요약
    st.subheader("📊 사용자별 취소율 / 실패율")
    summary = cancel_rate.merge(fail_rate, on=user_col)
    st.dataframe(summary.sort_values("cancel_rate", ascending=False).head(20))

    # ✅ 새벽 시간대 거래
    st.subheader("🌙 새벽 시간대 거래 (1AM–4AM)")
    st.dataframe(
        late_night_tx[[user_col, "timestamp", "spend.status", "spend.amount_usd"]].head(20)
    )

    # ✅ 연속 취소 내역 (상위 유저만)
    st.subheader("📈 사용자별 연속 취소 횟수 예시")
    streak_df = df_sorted[df_sorted["cancel_streak"] > 1]
    st.dataframe(
        streak_df[[user_col, "timestamp", "spend.status", "cancel_streak"]].head(20)
    )
