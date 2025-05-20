import streamlit as st
import pandas as pd

def render(df):
    st.header("🛑 Risk & Abuse Detection")

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["cancelled_at"] = pd.to_datetime(df["cancelled_at"])

    # ✅ 1. 사용자별 취소율
    cancel_rate = (
        df.groupby('user_id')
        .apply(lambda x: (x['status'] == 'cancelled').sum() / len(x))
        .reset_index(name='cancel_rate')
    )

    # ✅ 2. 승인 후 몇 분 내 취소된 거래
    df["cancel_delay_min"] = (df["cancelled_at"] - df["timestamp"]).dt.total_seconds() / 60
    suspicious_cancel = df[(df["status"] == "cancelled") & (df["cancel_delay_min"] < 10)]

    # ✅ 3. 사용자별 연속 취소 횟수
    df_sorted = df.sort_values(['user_id', 'timestamp'])
    df_sorted["is_cancel"] = df_sorted["status"] == "cancelled"
    df_sorted["cancel_streak"] = (
        df_sorted.groupby("user_id")["is_cancel"]
        .apply(lambda x: x.cumsum() - x.cumsum().where(~x).ffill().fillna(0))
    )

    # ✅ 4. 실패율 높은 사용자
    fail_rate = (
        df.groupby('user_id')
        .apply(lambda x: (x['status'] == 'failed').sum() / len(x))
        .reset_index(name='fail_rate')
    )

    # ✅ 5. 다계정 탐지 (동일 IP+Device, 서로 다른 유저)
    multi_user = df.groupby(['ip', 'device_id'])["user_id"].nunique().reset_index()
    multi_user = multi_user[multi_user["user_id"] > 1]

    # ✅ 6. 이상 시간대 거래
    df["hour"] = df["timestamp"].dt.hour
    late_night_tx = df[df["hour"].isin(range(1, 5))]

    # ✅ 요약 테이블 표시
    st.subheader("📊 사용자별 취소율 / 실패율")
    summary = cancel_rate.merge(fail_rate, on="user_id")
    st.dataframe(summary.sort_values("cancel_rate", ascending=False).head(20))

    # ✅ 빠른 취소 의심 거래
    st.subheader("⚠️ 승인 후 10분 내 취소된 거래")
    st.dataframe(suspicious_cancel[["user_id", "timestamp", "cancelled_at", "cancel_delay_min"]].head(20))

    # ✅ 다계정 탐지 의심 IP/Device
    st.subheader("🔗 동일 IP/Device에서 여러 유저 사용")
    st.dataframe(multi_user)

    # ✅ 새벽시간대 거래
    st.subheader("🌙 새벽 시간대 거래 (1AM–4AM)")
    st.dataframe(late_night_tx[["user_id", "timestamp", "status", "spend.amount"]].head(20))
