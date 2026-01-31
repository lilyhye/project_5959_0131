import os
from datetime import datetime

def generate_report():
    """
    최종 통합 분석 보고서(generate_final_report.py)를 생성하는 함수입니다. (원복 버전)
    """
    report_path = "generate_final_report.py"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report_content = f"""# 데이터 분석 최종 통합 보고서 (Comprehensive Analysis Report)

**생성일시**: {current_time}  
**분석 대상**: `project1_5959.csv`

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
| **지역별 주문** | ![지역별 주문 건수]('01_region_counts.png') |
| **주문경로 비중** | ![주문경로별 비중]('02_order_channel.png') |
| **결제방법 분포** | ![결제방법 분포]('03_payment_method.png') |
| **품종별 판매** | ![품종별 판매 건수]('04_product_variety.png') |
| **가격대별 분포** | ![가격대별 주문 분포]('05_price_range.png') |

---

## 3. 시즌별 품목 선호도 분석
데이터 내 주문일자를 기반으로 한 사계절별 인기 품목 분석 결과입니다.

![시즌별 인기 품목]('seasonal_product_popularity.png')

### 시즌별 상위 주문 데이터
| 시즌 | 품종 | 주문건수 |
| :--- | :--- | ---: |
| **가을** | 감귤 | 4540 |
| **가을** | 감귤, 황금향 | 764 |
| **겨울** | 감귤 | 2416 |
| **겨울** | 한라봉 | 164 |

---

## 4. 심층 재구매율(Repurchase Rate) 분석

### 4.1 품목(품종)별 재구매율
![품종별 재구매율]('repurchase_by_product.png')

| 상위 품종 | 재구매율(%) | 전체주문건수 |
| :--- | ---: | ---: |
| **단감** | 100.00 | 6 |
| **딸기** | 86.44 | 59 |
| **한라봉** | 59.76 | 164 |
| **고구마** | 56.90 | 239 |
| **황금향** | 52.87 | 749 |

### 4.2 셀러별 고객 로열티 분석 (주문 10건 이상 대상)
![셀러별 재구매율]('repurchase_by_seller.png')
- **최우수 셀러**: 제주귤마켓 (96.4%), 규원이네 (95.3%), 황금노지 (94.7%) 등

### 4.3 회원구분 및 주문경로별 재구매율
- **회원구분**: 비회원(45.8%)의 재구매율이 회원(30.3%)보다 유의미하게 높게 나타남. ![회원별]('repurchase_by_membership.png')
- **주문경로**: TICTOK(66.7%), 인스타그램(39.2%), 카카오톡(48.2%) 순. ![경로별]('repurchase_by_channel.png')

---

## 5. RFM 기반 고객 세분화 분석
고객의 구매 행동(최근성, 빈도, 금액)을 기반으로 한 등급 분류 결과입니다.

![RFM 세그먼트]('rfm_customer_segments.png')

### 세그먼트별 평균 지표
| 등급 | Recency(일) | Frequency(건) | Monetary(원) |
| :--- | ---: | ---: | ---: |
| **VVIP (최상위)** | 38.4 | 159.9 | 4,981,440 |
| **VIP (우수)** | 42.0 | 65.3 | 2,343,740 |
| **Regular (일반)** | 57.7 | 8.5 | 332,161 |
| **At-risk (이탈우려)** | 86.3 | 2.3 | 58,729 |

---

## 6. 상세 교차 분석 데이터 (Cross-tabulation)

### 6.1 지역별 x 품종별 선호도 (상위 지역)
| 광역지역(정식) | 감귤 | 감귤, 황금향 | 고구마 | 황금향 |
| :--- | ---: | ---: | ---: | ---: |
| **경기도** | 2,099 | 220 | 84 | 226 |
| **서울특별시** | 931 | 133 | 28 | 149 |

---

## 8. 프로젝트 작업 결과물 구조 (File Tree)
```text
Project1_5959/
├── project1_5959.csv            # 원본 및 가공 데이터셋
├── eda_results/                 # 시각화 차트 이미지 (PNG)
├── eda_project1.py              # 기본 및 재구매율 분석 스크립트
├── eda_v2_advanced.py           # 시즌 및 RFM 고도화 분석 스크립트
├── dashboard_app.py             # Streamlit 통합 실시간 대시보드
└── generate_final_report.py # 최종 통합 분석 보고서 생성기
```
"""
    
    with open(report_path, "w", encoding="utf-8-sig") as f:
        f.write(report_content)
    
    print(f"보고서가 성공적으로 생성되었습니다: {os.path.abspath(report_path)}")

if __name__ == "__main__":
    generate_report()
