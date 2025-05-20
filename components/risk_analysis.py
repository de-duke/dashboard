import streamlit as st
import pandas as pd

def render(df):
    st.header("🛑 Risk & Abuse Detection")

    # Parse timestamps
    df["timestamp"] = pd.to_datetime(df["spend.authorizedAt"])

    # Set user ID column
    user_col = "spend.userId"

    # Normalize status field
    df["spend.status"] = df["spend.status"].astype(str).str.strip().str.lower()

    # 1. Cancel rate (reversed)
    cancel_rate = (
        df.groupby(user_col)
        .apply(lambda x: (x["spend.status"] == "reversed").sum() / len(x))
        .reset_index(name="cancel_rate")
    )

    # 2. Fail rate (declined)
    fail_rate = (
        df.groupby(user_col)
        .apply(lambda x: (x["spend.status"] == "declined").sum() / len(x))
        .reset_index(name="fail_rate")
    )

    # 3. Consecutive cancel streak
    df_sorted = df.sort_values([user_col, "timestamp"])
    df_sorted["is_cancel"] = df_sorted["spend.status"] == "reversed"
    df_sorted["cancel_streak"] = (
        df_sorted.groupby(user_col)["is_cancel"]
        .transform(lambda x: x.cumsum() - x.cumsum().where(~x).ffill().fillna(0))
    )

    # 4. Cancel & fail amount per user
    cancel_amount = df[df["spend.status"] == "reversed"].groupby(user_col)["spend.amount_usd"].sum().reset_index(name="cancel_amount_usd")
    fail_amount = df[df["spend.status"] == "declined"].groupby(user_col)["spend.amount_usd"].sum().reset_index(name="fail_amount_usd")

    # 5. Merge all into summary
    summary = cancel_rate.merge(fail_rate, on=user_col)\
                         .merge(cancel_amount, on=user_col, how="left")\
                         .merge(fail_amount, on=user_col, how="left")\
                         .fillna(0)

    # 6. Identify suspicious users
    suspicious = summary[
        (summary["cancel_rate"] > 0.3) | (summary["fail_rate"] > 0.2)
    ]
    total_users = df[user_col].nunique()
    suspicious_users = suspicious[user_col].nunique()
    suspicious_pct = (suspicious_users / total_users) * 100 if total_users else 0

    # 📊 Cancel / Fail Rate Summary
    st.subheader("📊 Cancel / Fail Rate Summary (Top 20)")
    st.caption(f"⚠️ Suspicious users: **{suspicious_users:,} / {total_users:,}** → **{suspicious_pct:.1f}%**")

    st.dataframe(
        summary.sort_values(["cancel_rate", "fail_rate"], ascending=False)
               .head(20)[[user_col, "cancel_rate", "fail_rate", "cancel_amount_usd", "fail_amount_usd"]]
    )

    # 📈 Consecutive Cancel Streaks
    st.subheader("📈 Users with Consecutive Cancelled Transactions (≥2)")
    streak_df = df_sorted[df_sorted["cancel_streak"] >= 2]
    st.dataframe(
        streak_df[[user_col, "timestamp", "spend.status", "cancel_streak"]]
        .sort_values(["cancel_streak", "timestamp"], ascending=[False, True])
        .head(20)
    )


    st.subheader("🔍 Suspicious Transaction Patterns")
    
    # 1. Mirror transactions (same user, same abs amount, positive + negative)
    df["abs_amount"] = df["amount_usd"].abs().round(2)
    
    mirror_tx_flag = (
        df.groupby(["spend.userId", "abs_amount"])["amount_usd"]
        .apply(lambda x: set(round(v, 2) for v in x) >= {x.max(), -x.max()})
        .reset_index(name="mirror_flag")
    )
    
    mirror_users = mirror_tx_flag[mirror_tx_flag["mirror_flag"] == True]["spend.userId"].unique()
    mirror_tx_df = df[df["spend.userId"].isin(mirror_users)]
    
    st.markdown("**🔁 Users with matching positive & negative transactions (Mirror Tx)**")
    st.dataframe(
        mirror_tx_df[["spend.userId", "amount_usd", "status", "authorized_at"]]
        .sort_values(["spend.userId", "authorized_at"])
        .head(30)
    )
    
    # 2. Repeated same-amount transactions on the same day (≥4)
    df["date"] = pd.to_datetime(df["authorized_at"]).dt.date
    
    repeated_amount = (
        df.groupby(["spend.userId", "amount_usd", "date"])
        .size().reset_index(name="count")
    )
    
    repeat_users = repeated_amount[repeated_amount["count"] >= 4]["spend.userId"].unique()
    repeat_tx_df = df[df["spend.userId"].isin(repeat_users)]
    
    st.markdown("**🧾 Users with ≥4 repeated same-amount transactions per day**")
    st.dataframe(
        repeat_tx_df[["spend.userId", "amount_usd", "status", "authorized_at"]]
        .sort_values(["spend.userId", "authorized_at"])
        .head(30)
    )
