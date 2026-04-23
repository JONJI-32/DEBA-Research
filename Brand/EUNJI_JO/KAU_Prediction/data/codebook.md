# master_daily.csv 코드북

> 작성일: 2026-04-23
> 대상 파일: [data/processed/master_daily.csv](../data/processed/master_daily.csv)
> Shape: **2,766행 × 57컬럼**
> 날짜 범위: 2015-01-12 ~ 2026-04-17 (KAU 영업일 축)
> 생성 스크립트: [src/processing/merge_master_daily.py](../src/processing/merge_master_daily.py)

카테고리 태그: `시장내부`(10) / `에너지`(9) / `경제지표`(27) / `기후`(11) = 57

## 주의사항

- **월간·분기 변수 (44~57)**: 브로드캐스트·forward-fill 미적용. 월초/분기초 KAU 영업일에만 값, 그 외는 NaN. Publication lag shift(CPI 익월 초 발표 등)는 본 파일에 미반영 — 모델링 단계에서 별도 시프트 필요.
- **`vintage_transition=True`인 날**: 동일 자산이 아닌 빈티지 교체 구간이므로 수익률/차분 계산 시 마스킹 권장.
- **`is_traded=False`인 날**: `KAU_CLOSE`는 체이닝된 이월가지만 `open/high/low`는 NaN — OHLC 기반 피처 사용 시 주의.
- **Window 변수 (`smp_*_window_*`, `weather_*_window_*`)**: 주말·휴일 신호를 다음 KAU 영업일에 흡수하는 설계. Look-ahead bias 없음 (과거 방향 window).
- **해외 에너지 (`HH_GAS`, `NEWCASTLE_COAL`)**: ffill 정합 후 NaN 0. 레벨은 직전 영업일 값 유지 — 변동률 계산 시 0 일이 다수 발생.



| # | column | category | meaning_ko | unit | freq | source | nan_pct | notes |
|--:|---|---|---|---|---|---|---:|---|
| 1 | `date` | 시장내부 | 날짜 (KAU 영업일) | - | 일 | `processed/kau_front_daily.csv` (KRX ets) | 0.00% | 2,766 유일·정렬. 인덱스 키 |
| 2 | `front_vintage` | 시장내부 | 당일 제1배출권 빈티지 태그 | - | 일 | `processed/kau_front_daily.csv` (선행연구 기반) | 0.00% | 문자열 `KAU15`~`KAU25` |
| 3 | `KAU_CLOSE` | 시장내부 | KAU 종가 **Y변수** | 원 | 일 | `processed/kau_front_daily.csv` ← `raw/kau_daily_kau_only.csv` | 0.00% | 무거래일은 직전 체결가 유지 |
| 4 | `open` | 시장내부 | 시가 | 원 | 일 | `processed/kau_front_daily.csv` | 23.39% | 무거래일 sentinel(0)→NaN |
| 5 | `high` | 시장내부 | 고가 | 원 | 일 | `processed/kau_front_daily.csv` | 23.39% | 무거래일 NaN |
| 6 | `low` | 시장내부 | 저가 | 원 | 일 | `processed/kau_front_daily.csv` | 23.39% | 무거래일 NaN |
| 7 | `volume` | 시장내부 | 거래량 | tCO2eq | 일 | `processed/kau_front_daily.csv` | 0.00% | 무거래일 0 |
| 8 | `value` | 시장내부 | 거래대금 | 원 | 일 | `processed/kau_front_daily.csv` | 0.00% | 무거래일 0 |
| 9 | `is_traded` | 시장내부 | 당일 실거래 여부 플래그 | bool | 일 | `processed/kau_front_daily.csv` | 0.00% | 2,119 True / 647 False |
| 10 | `vintage_transition` | 시장내부 | 빈티지 전환일 여부 플래그 | bool | 일 | `processed/kau_front_daily.csv` (TRANSITION_MAP) | 0.00% | 수익률 계산 시 마스킹 필요 |
| 11 | `Dubai` | 에너지 | 두바이유 현물가 | USD/bbl | 일 | `processed/oil_price_daily.csv` ← `raw/일일국제원유가격(*).csv` | 2.75% | 국내 영업일 기준 |
| 12 | `Brent` | 에너지 | 브렌트유 현물가 | USD/bbl | 일 | `processed/oil_price_daily.csv` | 0.58% | 국내 영업일 기준 |
| 13 | `WTI` | 에너지 | WTI 현물가 | USD/bbl | 일 | `processed/oil_price_daily.csv` | 3.11% | 국내 영업일 기준 |
| 14 | `Oman` | 에너지 | 오만유 현물가 | USD/bbl | 일 | `processed/oil_price_daily.csv` | 2.75% | 국내 영업일 기준 |
| 15 | `HH_GAS` | 에너지 | Henry Hub 천연가스 현물가 | USD/MMBtu | 일(KAU ffill) | `processed/gas_price_kau_daily.csv` ← FRED DHHNGSP | 0.00% | 미국 휴장일 83건 forward-fill |
| 16 | `NEWCASTLE_COAL` | 에너지 | Newcastle 석탄 선물가 | USD/ton | 일(KAU ffill) | `processed/coal_price_kau_daily.csv` ← Investing.com | 0.00% | ICE 휴장일 19건 forward-fill |
| 17 | `SMP_MEAN` | 에너지 | KPX 거래량 가중평균 SMP (당일) | KRW/kWh | 일 | `processed/smp_kau_daily.csv` ← `raw/HOME_전력거래_계통한계가격_시간별SMP.csv` | 0.00% | 시간별 → 일간 가중평균 |
| 18 | `smp_window_mean` | 에너지 | 직전 KAU 영업일~당일 window SMP 단순평균 | KRW/kWh | 일(KAU window) | `processed/smp_kau_daily.csv` | 0.00% | 주말·휴일 수요 신호 흡수 |
| 19 | `smp_window_days` | 에너지 | window 길이 (일) | 일 | 일(KAU window) | `processed/smp_kau_daily.csv` | 0.00% | 1~11 정수. 월요일 보통 3 |
| 20 | `USD` | 경제지표 | 원/달러 환율 종가 (15:30) | KRW/USD | 일 | `raw/ecos_usd.csv` (ECOS 731Y003/0000003) | 0.00% | |
| 21 | `USD_CNY` | 경제지표 | 원/위안 환율 종가 | KRW/CNY | 일 | `raw/ecos_usd_cny.csv` (ECOS 731Y003/0000010) | 0.00% | |
| 22 | `CALL` | 경제지표 | 콜금리 | % | 일 | `raw/ecos_call.csv` (ECOS) | 0.00% | |
| 23 | `BOND_3Y` | 경제지표 | 국고채 3년 수익률 | % | 일 | `raw/ecos_bond_3y.csv` (ECOS) | 0.00% | |
| 24 | `BOND_BBB` | 경제지표 | 회사채 BBB 수익률 | % | 일 | `raw/ecos_bond_bbb.csv` (ECOS) | 0.00% | |
| 25 | `CREDIT_SPREAD` | 경제지표 | 크레딧 스프레드 (BBB − 국고3Y) | %p | 일 | `raw/ecos_credit_spread.csv` (ECOS) | 0.00% | |
| 26 | `KOSPI` | 경제지표 | 코스피 종가 | index | 일 | `raw/krx_indices.csv` (KRX idx/kospi_dd_trd) | 0.00% | |
| 27 | `VIX_KR` | 경제지표 | 코스피200 변동성지수 (VKOSPI) | index | 일 | `raw/krx_indices.csv` (KRX idx/drvprod_dd_trd) | 0.00% |  |
| 28 | `KRX_IRON` | 경제지표 | KRX 철강 섹터지수 종가 | index | 일 | `raw/krx_sectors.csv` | 0.00% | |
| 29 | `KRX_ENG` | 경제지표 | KRX 에너지화학 섹터지수 종가 | index | 일 | `raw/krx_sectors.csv` | 0.00% | |
| 30 | `KRX_ENERGY` | 경제지표 | KRX 유틸리티 섹터지수 종가 | index | 일 | `raw/krx_sectors.csv` | 0.00% | 원래 전력/가스 유틸 |
| 31 | `KRX_CEMENT` | 경제지표 | KRX 건설 섹터지수 종가 | index | 일 | `raw/krx_sectors.csv` | 0.00% | |
| 32 | `KRX_SEMICON` | 경제지표 | KRX 반도체 섹터지수 종가 | index | 일 | `raw/krx_sectors.csv` | 0.00% | |
| 33 | `ta_avg` | 기후 | 서울 일평균기온 | °C | 일(KAU) | `processed/weather_kau_daily.csv` ← 기상청 API허브 stn=108 | 0.04% | 원본 1건 결측(2015-01-02) |
| 34 | `ta_avg_window_mean` | 기후 | window 기간 일평균기온의 평균 | °C | 일(KAU window) | `processed/weather_kau_daily.csv` | 0.04% | 주말 기온 흡수 |
| 35 | `ta_avg_dev` | 기후 | 평년(91~20, 12.9045°C) 대비 편차 | °C | 일(KAU) | `processed/weather_kau_daily.csv` | 0.04% | `ta_avg − 12.9045` |
| 36 | `ta_avg_dev_window_mean` | 기후 | window 편차 평균 | °C | 일(KAU window) | `processed/weather_kau_daily.csv` | 0.04% | |
| 37 | `ta_avg_dev_abs` | 기후 | 평년 대비 절대편차 \|ta_avg − 12.9045\| | °C | 일(KAU) | `processed/weather_kau_daily.csv` | 0.04% | 박경근(2019)·Christiansen(2005) |
| 38 | `ta_avg_dev_abs_window_mean` | 기후 | window 절대편차 평균 | °C | 일(KAU window) | `processed/weather_kau_daily.csv` | 0.04% | |
| 39 | `ta_avg_dev_abs_window_max` | 기후 | window 절대편차 최댓값 (극단 보존) | °C | 일(KAU window) | `processed/weather_kau_daily.csv` | 0.04% | 극한기상일 포착 |
| 40 | `rn_day` | 기후 | 서울 일강수량 | mm | 일(KAU) | `processed/weather_kau_daily.csv` | 0.00% | -9.0(무강수) → 0 치환 |
| 41 | `rn_day_window_mean` | 기후 | window 일강수량 평균 | mm | 일(KAU window) | `processed/weather_kau_daily.csv` | 0.00% | |
| 42 | `rn_day_window_sum` | 기후 | window 누적 강수량 | mm | 일(KAU window) | `processed/weather_kau_daily.csv` | 0.00% | 연휴 누적 강수 포착 |
| 43 | `weather_window_days` | 기후 | weather window 길이 | 일 | 일(KAU window) | `processed/weather_kau_daily.csv` | 0.00% | smp_window_days와 동일 로직 |
| 44 | `CPI` | 경제지표 | 소비자물가지수 총지수 | index (2020=100) | 월 | `raw/ecos_cpi.csv` (ECOS 901Y009/0) | 97.58% | 월초일만 값, 그 외 NaN |
| 45 | `PPI` | 경제지표 | 생산자물가지수 총지수 | index (2015=100) | 월 | `raw/ecos_ppi.csv` (ECOS 404Y014/*AA) | 97.58% | 월초일만 값 |
| 46 | `CLI` | 경제지표 | 선행종합지수 | index | 월 | `raw/ecos_cli.csv` (ECOS 901Y067/I16A) | 97.58% | 월초일만 값 |
| 47 | `CCI` | 경제지표 | 동행종합지수 | index | 월 | `raw/ecos_cci.csv` (ECOS 901Y067/I16B) | 97.58% | 월초일만 값 |
| 48 | `BSI_P` | 경제지표 | BSI 업황실적 — 제조업 | index (기준 100) | 월 | `raw/ecos_bsi_p.csv` (ECOS 512Y007/AA/C0000) | 97.58% | 월초일만 값 |
| 49 | `BSI_E` | 경제지표 | BSI 업황실적 — 비제조업 | index (기준 100) | 월 | `raw/ecos_bsi_e.csv` (ECOS 512Y007/AA/Y9900) | 97.58% | 월초일만 값 |
| 50 | `EXPORT` | 경제지표 | 통관 수출금액 | 천불 | 월 | `raw/ecos_export.csv` (ECOS 901Y118/T002) | 97.58% | 월초일만 값 |
| 51 | `IMPORT` | 경제지표 | 통관 수입금액 | 천불 | 월 | `raw/ecos_import.csv` (ECOS 901Y118/T004) | 97.58% | 월초일만 값 |
| 52 | `IIP_MFG` | 경제지표 | 광공업생산지수 — 제조업(원지수) | index (2020=100) | 월 | `raw/kosis_iip.csv` (KOSIS DT_1F02001 C/T10) | 97.58% | 월초일만 값 |
| 53 | `IIP_STEEL` | 경제지표 | 광공업생산지수 — 1차철강(원지수) | index (2020=100) | 월 | `raw/kosis_iip.csv` (KOSIS DT_1F02001 C241/T10) | 97.58% | 월초일만 값 |
| 54 | `IIP_CHEM` | 경제지표 | 광공업생산지수 — 화학물질(원지수) | index (2020=100) | 월 | `raw/kosis_iip.csv` (KOSIS DT_1F02001 C20/T10) | 97.58% | 월초일만 값 |
| 55 | `CAP_UTIL` | 경제지표 | 제조업 평균가동률 | % | 월 | `raw/kosis_iip.csv` (KOSIS DT_1F32002 C/T50) | 97.58% | 월초일만 값 |
| 56 | `IND_ORDER` | 경제지표 | 국내 기계수주 (선박제외, 계) | 백만원 | 월 | `raw/kosis_iip.csv` (KOSIS DT_1F48005 1/0/T4) | 97.58% | 월초일만 값 |
| 57 | `GDP_GROWTH` | 경제지표 | GDP 성장률 (전년동기비) | % | 분기 | `processed/gdp_growth.csv` ← ECOS 200Y106/1400 | 99.35% | 분기초일만 값. 2015년 전 구간 NaN (lag) |

---

