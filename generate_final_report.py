import os
from datetime import datetime

def generate_report():
    """
    최종 통합 분석 보고서를 생성하는 함수입니다. (재구매 기준 고도화 버전)
    """
    report_path = "final_comprehensive_report_v2.md"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report_content = f"""# 데이터 분석 최종 통합 보고서 (Comprehensive Analysis Report)

**생성일시**: {current_time}  
**분석 대상**: `project1_5959.csv`
**재구매 산정 기준**: 주문자연락처(또는 UID) 기준, **서로 다른 '주문날짜'**가 2회 이상인 경우 (동일 날짜 중복 주문 제외)

---

## 1. 데이터 개요 분석
- **전체 데이터 건수**: 9,144 건
- **칼럼 수**: 43 개

### 결측치 현황
| 주요 항목 | 결측치수 |
| :--- | ---: |
| 고객선택옵션 | 333 |
| 셀러명 | 153 |
| 배송준비 처리일 | 540 |
| 입금일 | 98 |
| 입금자명 | 8,048 |

---

## 2. 주요 시각화 기반 일반 분포 분석

### 2.1 핵심 지표 시각화 (5종)
| 항목 | 시각화 결과 |
| :--- | :--- |
| **지역별 주문** | ![지역별 주문 건수](./eda_results/01_region_counts.png) |
| **주문경로 비중** | ![주문경로별 비중](./eda_results/02_order_channel.png) |
| **결제방법 분포** | ![결제방법 분포](./eda_results/03_payment_method.png) |
| **품종별 판매** | ![품종별 판매 건수](./eda_results/04_product_variety.png) |
| **가격대별 분포** | ![가격대별 주문 분포](./eda_results/05_price_range.png) |

---

## 3. 시즌별 품목 선호도 분석
데이터 내 주문일자를 기반으로 한 사계절별 인기 품목 분석 결과입니다.

![시즌별 인기 품목](./eda_results/seasonal_product_popularity.png)

### 시즌별 상위 주문 데이터 (주문건수 기준)
| 시즌 | 품종 | 주문건수 |
| :--- | :--- | ---: |
| **가을** | 감귤 | 4540 |
| **가을** | 감귤, 황금향 | 764 |
| **겨울** | 감귤 | 2416 |
| **겨울** | 한라봉 | 164 |

---

## 4. 심층 재구매율(Repurchase Rate) 분석
*※ 본 지표는 '동일 날짜 중복 주문'을 제외한 순수 재방문 구매를 기준으로 합니다.*

### 4.1 품목(품종)별 재구매율 (TOP 5)
![품종별 재구매율](./eda_results/repurchase_by_product.png)

| 품종 | 재구매율(%) | 총 고객수 |
| :--- | ---: | ---: |
| **단감** | 20.0 | 5 |
| **딸기** | 18.6 | 43 |
| **감귤** | 17.3 | 4,589 |
| **한라봉** | 13.8 | 116 |
| **황금향** | 12.3 | 465 |

### 4.2 셀러별 고객 로열티 분석 (총 고객 10명 이상 대상)
![셀러별 재구매율](./eda_results/repurchase_by_seller.png)
- **최우수 로열티 셀러**: 신선농산 (54.5%), 윤아팜 (50.0%), 달콤 제주 귤내음 (46.2%)
- **대형 셀러 성과**: 킹댕즈 (18.2%, 고객 1,535명), 제주탐라마켓 (28.1%, 고객 64명)

### 4.3 회원구분 및 주문경로별 재구매율
- **회원구분**: 비회원(22.8%)의 재구매율이 회원(7.5%)보다 여전히 높게 나타남. ![회원별](./eda_results/repurchase_by_membership.png)
- **주문경로**: 카카오톡, TICTOK 등 메신저/SNS 채널 기반의 재구매 유합이 강세. ![경로별](./eda_results/repurchase_by_channel.png)

---

## 5. RFM 기반 고객 세분화 분석
*※ Frequency(빈도)를 '총 구매 일수'로 재정의하여 분석의 정교함을 높였습니다.*

![RFM 세그먼트](./eda_results/rfm_customer_segments.png)

### 세그먼트별 평균 지표 (날짜별 빈도 기준)
| 등급 | Recency(일) | Frequency(일) | Monetary(원) |
| :--- | ---: | ---: | ---: |
| **VVIP (최상위)** | 27.6 | 6.4 | 194,514 |
| **VIP (우수)** | 35.8 | 2.6 | 85,270 |
| **Regular (일반)** | 48.0 | 1.3 | 43,186 |
| **At-risk (이탈우려)** | 91.9 | 1.1 | 37,233 |

---

## 6. 상세 교차 분석 데이터 (Cross-tabulation)

### 6.1 지역별 x 품종별 선호도 (상위 지역)
| 광역지역(정식) | 감귤 | 감귤, 황금향 | 고구마 | 황금향 |
| :--- | ---: | ---: | ---: | ---: |
| **경기도** | 2,099 | 220 | 84 | 226 |
| **서울특별시** | 931 | 133 | 28 | 149 |

---

## 7. 프로젝트 작업 결과물 구조 (File Tree)
```text
Project1_5959/
├── project1_5959.csv            # 원본 및 가공 데이터셋
├── eda_results/                 # 시각화 차트 이미지 (PNG)
├── eda_project1.py              # 날짜 기반 재구매율 분석 스크립트
├── eda_v2_advanced.py           # 방문일수 기반 RFM 분석 스크립트
├── dashboard_app.py             # Streamlit 통합 실시간 대시보드
└── generate_final_report.py # 최종 통합 보고서 생성기 (현재 파일)
```

> [!IMPORTANT]
> 본 보고서의 모든 지표는 **주문자연락처**와 **고유 주문 날짜**를 기준으로 재산출되었습니다. 단순 주문 건수 기반의 분석보다 실제 고객의 재방문 및 충성도를 보다 정확하게 반영합니다.
"""
    
    # 보고서 파일 생성 (final_comprehensive_report_v2.md)
    with open(report_path, "w", encoding="utf-8-sig") as f:
        f.write(report_content)
    
    print(f"보고서가 성공적으로 생성되었습니다: {os.path.abspath(report_path)}")

if __name__ == "__main__":
    generate_report()
