import os
import pandas as pd
from supabase import create_client

# ✅ Supabase에서 페이징으로 모든 트랜잭션 수집
def fetch_all_rows(batch_size=1000000, max_pages=50):
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    all_data = []
    offset = 0

    for _ in range(max_pages):
        res = (
            supabase.table("transactions")
            .select("*")
            .order('"spend.authorizedAt"', desc=False)
            .range(offset, offset + batch_size - 1)
            .execute()
        )
        batch = res.data
        if not batch:
            break
        all_data.extend(batch)
        offset += batch_size

    return pd.DataFrame(all_data)

# ✅ 전체 수집 + 전처리
def load_data():
    df = fetch_all_rows()

    # 전처리
    df["spend.status"] = df["spend.status"].astype(str).str.lower()

    # 센트 → 달러
    df["spend.amount_usd"] = df["spend.amount"].apply(lambda x: int(x) / 100 if x else 0)

    # 날짜 파싱
    df["spend.authorizedAt"] = pd.to_datetime(df["spend.authorizedAt"], format="mixed", errors="coerce")
    df["date_utc"] = df["spend.authorizedAt"].dt.date
    df["hour_utc"] = df["spend.authorizedAt"].dt.hour
    df["week"] = pd.to_datetime(df["date_utc"]).dt.to_period("W").astype(str)

    return df
