"""
master_daily.csv 생성 — KAU 영업일 축에 24개 final 소스를 left join.

- 월간/분기 파일은 date 키 단순 left join
- 결측 처리 일체 수행하지 않음
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
OUT = RAW / "master_daily.csv"


def _read(path: Path, cols: list[str] | None = None) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    if cols is not None:
        df = df[["date", *cols]]
    return df


def main() -> None:
    # 1) Y축 (KAU 영업일)
    kau = _read(
        RAW / "kau_front_daily.csv",
        ["front_vintage", "close", "open", "high", "low", "volume", "value",
         "is_traded", "vintage_transition"],
    ).rename(columns={"close": "KAU_CLOSE"})

    master = kau.copy()

    # 2) 일간 소스
    daily_sources: list[tuple[Path, list[str] | None]] = [
        (RAW / "oil_price_daily.csv",         ["Dubai", "Brent", "WTI", "Oman"]),
        (RAW / "gas_price_kau_daily.csv",     ["HH_GAS"]),
        (RAW / "coal_price_kau_daily.csv",    ["NEWCASTLE_COAL"]),
        (RAW / "smp_kau_daily.csv",           ["SMP_MEAN", "smp_window_mean", "smp_window_days"]),
        (RAW / "ecos_usd.csv",                 ["USD"]),
        (RAW / "ecos_usd_cny.csv",             None),
        (RAW / "ecos_call.csv",                None),
        (RAW / "ecos_bond_3y.csv",             None),
        (RAW / "ecos_bond_bbb.csv",            None),
        (RAW / "ecos_credit_spread.csv",       None),
        (RAW / "krx_indices.csv",              ["KOSPI", "VIX_KR"]),
        (RAW / "krx_sectors.csv",              None),
        (RAW / "weather_kau_daily.csv",       None),
    ]
    for path, cols in daily_sources:
        df = _read(path, cols)
        master = master.merge(df, on="date", how="left")

    # 3) 월간 소스 (단순 left join, 월초일에만 값)
    monthly_sources = [
        RAW / "ecos_cpi.csv",
        RAW / "ecos_ppi.csv",
        RAW / "ecos_cli.csv",
        RAW / "ecos_cci.csv",
        RAW / "ecos_bsi_p.csv",
        RAW / "ecos_bsi_e.csv",
        RAW / "ecos_export.csv",
        RAW / "ecos_import.csv",
        RAW / "kosis_iip.csv",
    ]
    for path in monthly_sources:
        df = _read(path)
        master = master.merge(df, on="date", how="left")

    # 4) 분기 소스 (단순 left join, 분기초일에만 값)
    q = _read(RAW / "gdp_growth.csv")
    master = master.merge(q, on="date", how="left")

    # 5) 결측 처리 없음 정렬 및 저장
    master = master.sort_values("date").reset_index(drop=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    master.to_csv(OUT, index=False, encoding="utf-8")


if __name__ == "__main__":
    main()
