import streamlit as st
import pandas as pd

def render(df):
    st.header("🛑 Risk & Abuse Detection (Supabase 기반)")

    # ✅ timestamp 대체 필드 정의
    df["timestamp"] = pd.to_datetime(df["spend.authorizedAt"])

    # ✅ 사용자 식별자: user_id가 없다면 이메일로 대체
    if "user_id" in df.columns:
        user_col = "user_id"
    else:
        user_col = "spend.userEmail"

    # ✅ 1. 사용자별 취소율
    cancel_rate = (
        df.groupby(user_col)
        .apply(lambda x: (x["spend.status"] == "cancelled").sum() / len(x))
        .reset_index(name="cancel_rate")
    )

    # ✅ 2. 취소 시각이 없기 때문에 빠른 취소 감지는 생략 (또는 임시 처리)
    st.info("🚫 'cancelled_at' 필드가 없어 빠른 취소 감지는 생략됩니다.")

    # ✅ 3. 연속 취소 횟수
    df_sorted = df.sort_values([user_col, "timestamp"])
    df_sorted["is_cancel"] = df_sorted["spend.status"] == "cancelled"
    df_sorted["cancel_streak"] = (
        df_sorted.groupby(user_col)["is_cancel"]
        .apply(lambda x: x.cumsum() - x.cumsum().where(~x).ffill().fillna(0))
    )

    # ✅ 4. 실패율 높은 사용자
    fail_rate = (
        df.groupby(user_col)
        .apply(lambda x: (x["spend.status"] == "failed").sum() / len(x))
        .reset_index(name="fail_rate")
    )

    # ✅ 5. 새벽 시간대 거래 (1AM–4AM)
    df["hour"] = df["timestamp"].dt.hour
    late_night_tx = df[df["hour"].isin(range(1, 5))]

    # ✅ 시각화
    st.subheader("📊 사용자별 취소율 / 실패율")
    summary = cancel_rate.merge(fail_rate, on=user_col)
    st.dataframe(summary.sort_values("cancel_rate", ascending=False).head(20))

    st.subheader("🌙 새벽 시간대 거래 (1AM–4AM)")
    st.dataframe(
        late_night_tx[[user_col, "timestamp", "spend.status", "spend.amount_usd"]].head(20)
    )

    # ✅ streak 정보도 필요하다면 추후 출력 가능
