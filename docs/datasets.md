# Datasets

> Filled in Step 2. Every dataset will list: provider, access method, field list, geographic
> resolution, update cycle, latest period, licence terms, and redistribution / commercial-use
> limits — each verified against the dataset page, or marked **needs verification**.

Planned for v1 (Mapo-gu, cafe):

| Key | Dataset | Resolution | Status |
|---|---|---|---|
| `semas_stores` | 소상공인시장진흥공단 상가(상권)정보 (data.go.kr 15012005 / 15083033) | point | needs verification |
| `seoul_trade_areas` | 서울시 상권분석서비스 영역 (골목·발달·전통시장·관광특구) | trade_area | needs verification |
| `seoul_ta_population` | 상권 길단위·상주·직장 인구 | trade_area | needs verification |
| `seoul_ta_sales` | 상권 추정매출 (서비스업종별) | trade_area | needs verification |
| `seoul_ta_stores` | 상권 점포 (개업·폐업·점포 수) | trade_area | needs verification |
| `seoul_living_pop` | 생활인구 (250 m 국가기준격자 전환 여부 확인 필요) | grid_250m | needs verification |
| `transit_pois` | 지하철역·버스정류소 위치 | point | needs verification |
| `school_pois` | 학교·대학 위치 | point | needs verification |
| — | 임대료 | — | 필지 단위 공개 데이터 없음으로 가정 (MVP: 결측) |

Kakao Local API results are proxied at request time and never stored.
