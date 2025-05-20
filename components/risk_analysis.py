import streamlit as st
import pandas as pd

def render(df):
    st.header("🛑 Risk & Abuse Detection")

    # ✅ 시간 처리
    if "timestamp" not in df.columns:
        if "spend.authorizedAt" in df.columns:
            df["timestamp"] = pd.to_datetime(df["spend.authorizedAt"])
        else:
            st.error("❌ 'spend.authorizedAt' column not found.")
            return

    # ✅ 사용자 ID 고정
    user_col = "spend.userId"

    # ✅ amount_usd 생성
    if "amount_usd" not in df.columns:
        if "amount_cents" in df.columns:
            df["amount_usd"] = df["amount_cents"] / 100
        elif "spend.amount" in df.columns:
            df["amount_usd"] = df["spend.amount"] / 100
        else:
            st.error("❌ No amount field found.")
            return

    # ✅ 상태 정리
    df["status"] = df["status"].astype(str).str.strip().str.lower()

    # ✅ 취소율 / 실패율
    cancel_rate = (
        df.groupby(user_col)
        .apply(lambda x: (x["status"] == "reversed").sum() / len(x))
        .reset_index(name="cancel_rate")
    )
    fail_rate = (
        df.groupby(user_col)
        .apply(lambda x: (x["status"] == "declined").sum() / len(x))
        .reset_index(name="fail_rate")
    )

    # ✅ 취소 / 실패 금액 합계
    cancel_amount = df[df["status"] == "reversed"].groupby(user_col)["amount_usd"].sum().reset_index(name="cancel_amount_usd")
    fail_amount = df[df["status"] == "declined"].groupby(user_col)["amount_usd"].sum().reset_index(name="fail_amount_usd")

    # ✅ 취소 streak 계산
    df_sorted = df.sort_values([user_col, "timestamp"])
    df_sorted["is_cancel"] = df_sorted["status"] == "reversed"
    df_sorted["cancel_streak"] = (
        df_sorted.groupby(user_col)["is_cancel"]
        .transform(lambda x: x.cumsum() - x.cumsum().where(~x).ffill().fillna(0))
    )

    # ✅ 요약 테이블 병합
    summary = cancel_rate.merge(fail_rate, on=user_col)\
                         .merge(cancel_amount, on=user_col, how="left")\
                         .merge(fail_amount, on=user_col, how="left")\
                         .fillna(0)

    # ✅ 수상 사용자 기준 필터링
    suspicious = summary[(summary["cancel_rate"] > 0.3) | (summary["fail_rate"] > 0.2)]
    total_users = df[user_col].nunique()
    suspicious_users = suspicious[user_col].nunique()
    suspicious_pct = (suspicious_users / total_users) * 100 if total_users else 0

    st.subheader("📊 Cancel / Fail Rate Summary (Top 20)")
    st.caption(f"⚠️ Suspicious users: **{suspicious_users:,} / {total_users:,}** → **{suspicious_pct:.1f}%**")
    st.dataframe(
        summary.sort_values(["cancel_rate", "fail_rate"], ascending=False)
               .head(20)[[user_col, "cancel_rate", "fail_rate", "cancel_amount_usd", "fail_amount_usd"]]
    )

    # ✅ 연속 취소
    st.subheader("📈 Users with Consecutive Cancelled Transactions (≥2)")
    streak_df = df_sorted[df_sorted["cancel_streak"] >= 2]
    st.dataframe(
        streak_df[[user_col, "timestamp", "status", "cancel_streak"]]
        .sort_values(["cancel_streak", "timestamp"], ascending=[False, True])
        .head(30)
    )

    # ✅ 거래 패턴 탐지
    st.subheader("🔍 Suspicious Transaction Patterns")

    # Mirror pattern: + / − same amount
    df["abs_amount"] = df["amount_usd"].abs().round(2)
    mirror_flag = (
        df.groupby([user_col, "abs_amount"])["amount_usd"]
        .apply(lambda x: set(round(v, 2) for v in x) >= {x.max(), -x.max()})
        .reset_index(name="mirror_flag")
    )
    mirror_users = mirror_flag[mirror_flag["mirror_flag"] == True][user_col].unique()
    mirror_tx_df = df[df[user_col].isin(mirror_users)]

    st.markdown("**🔁 Mirror Transactions (same amount ±)**")
    st.dataframe(
        mirror_tx_df[[user_col, "amount_usd", "status", "timestamp"]]
        .sort_values(["timestamp"])
        .head(30)
    )

    # Same amount repeated ≥4 in one day
    df["date"] = df["timestamp"].dt.date
    repeated = (
        df.groupby([user_col, "amount_usd", "date"])
        .size().reset_index(name="count")
    )
    repeat_users = repeated[repeated["count"] >= 4][user_col].unique()
    repeat_tx_df = df[df[user_col].isin(repeat_users)]

    st.markdown("**🧾 Same Amount ≥ 4 Times per Day**")
    st.dataframe(
        repeat_tx_df[[user_col, "amount_usd", "status", "timestamp"]]
        .sort_values(["timestamp"])
        .head(30)
    )
