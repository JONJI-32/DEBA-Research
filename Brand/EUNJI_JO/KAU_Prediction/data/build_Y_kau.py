"""KAU 제1배출권(front-vintage) 종속변수 시계열 구축 스크립트.

김유곤(2021) 선행연구의 front-vintage 체이닝 규칙을 KAU15~KAU25(2015-01-12 ~ 
2026-04-17)에 확장 적용해 단일 시계열 `data/processed/kau_front_daily.csv`를 생성한다.
"""

import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"

RAW_FILE = "kau_daily_kau_only.csv"
OUT_FILE = "kau_front_daily.csv"

# 마스터 전환 일정 — 선행연구 + 사용자 입력. (vintage, start, end(inclusive))
# end=None 은 "현재 거래중 → 데이터 최신일까지" 의미.
TRANSITION_MAP = [
    ("KAU15", "2015-01-12", "2016-06-30"),
    ("KAU16", "2016-07-01", "2017-06-30"),
    ("KAU17", "2017-07-03", "2018-08-09"),
    ("KAU18", "2018-08-10", "2019-09-30"),
    ("KAU19", "2019-10-01", "2020-09-11"),
    ("KAU20", "2020-09-14", "2021-08-10"),
    ("KAU21", "2021-08-11", "2022-08-08"),
    ("KAU22", "2022-08-09", "2023-08-31"),
    ("KAU23", "2023-09-01", "2024-08-30"),
    ("KAU24", "2024-09-02", "2025-08-29"),
    ("KAU25", "2025-09-01", None),
]

OHLC_COLS = ["open", "high", "low"]


def load_raw() -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / RAW_FILE, encoding="utf-8-sig")
    df["BAS_DD"] = pd.to_datetime(df["BAS_DD"])
    rename = {
        "BAS_DD": "date",
        "ISU_NM": "front_vintage",
        "TDD_CLSPRC": "close",
        "TDD_OPNPRC": "open",
        "TDD_HGPRC": "high",
        "TDD_LWPRC": "low",
        "ACC_TRDVOL": "volume",
        "ACC_TRDVAL": "value",
    }
    return df.rename(columns=rename)[list(rename.values())]


def build_segments(df: pd.DataFrame) -> pd.DataFrame:
    """TRANSITION_MAP에 따라 빈티지별 구간을 슬라이싱."""
    data_max = df["date"].max()
    segments = []

    for vintage, start, end in TRANSITION_MAP:
        start_ts = pd.Timestamp(start)
        end_ts = pd.Timestamp(end) if end is not None else data_max

        seg = df[
            (df["front_vintage"] == vintage)
            & (df["date"] >= start_ts)
            & (df["date"] <= end_ts)
        ].copy()

        segments.append(seg)

    result = pd.concat(segments, ignore_index=True).sort_values("date").reset_index(drop=True)
    return result


def handle_gaps(df: pd.DataFrame) -> pd.DataFrame:
    """무거래일 OHLC sentinel(0) → NaN, is_traded / vintage_transition 플래그 추가."""
    df = df.copy()
    zero_vol_mask = df["volume"] == 0
    for col in OHLC_COLS:
        df.loc[zero_vol_mask, col] = pd.NA
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["is_traded"] = df["volume"] > 0
    df["vintage_transition"] = df["front_vintage"] != df["front_vintage"].shift(1)
    # 첫 행은 전환이 아님
    df.loc[df.index[0], "vintage_transition"] = False
    return df


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    raw = load_raw()
    segmented = build_segments(raw)
    processed = handle_gaps(segmented)

    out_cols = [
        "date",
        "front_vintage",
        "close",
        "open",
        "high",
        "low",
        "volume",
        "value",
        "is_traded",
        "vintage_transition",
    ]
    out = processed[out_cols]

    out_path = PROCESSED_DIR / OUT_FILE
    out.to_csv(out_path, index=False)


if __name__ == "__main__":
    main()
