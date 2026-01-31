import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="주문 데이터 분석 대시보드", layout="wide")

# 한글 폰트 설정 (Plotly)
def set_korean_font():
    import plotly.io as pio
    pio.templates.default = "plotly_white"

set_korean_font()

# 데이터 로드 및 전처리 함수 (캐싱 적용)
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
    except:
        df = pd.read_csv(file_path, encoding='cp949')
    
    # 날짜 처리
    if '주문일' in df.columns:
        df['주문일'] = pd.to_datetime(df['주문일'], errors='coerce')
        df = df.dropna(subset=['주문일'])
    
    # 금액 처리 (쉼표 제거 및 숫자 변환)
    price_cols = ['결제금액', '실결제 금액', '판매단가', '공급단가']
    for col in price_cols:
        if col in df.columns and df[col].dtype == 'object':
            df[col] = df[col].str.replace(',', '').astype(float)
            
    return df

# 사이드바 구성
st.sidebar.header("📊 분석 필터")

# 데이터 파일 경로 설정 (상대 경로 사용으로 호환성 확보)
current_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(current_dir, 'project1_5959.csv')

if os.path.exists(data_path):
    df_raw = load_data(data_path)
    
    # 키워드 검색 필터
    all_products = sorted(df_raw['품종'].unique()) if '품종' in df_raw.columns else []
    search_keywords = st.sidebar.multiselect("🔍 품종 선택/검색", options=all_products, default=all_products[:2] if all_products else None)
    
    # 기간 필터
    min_date = df_raw['주문일'].min().date()
    max_date = df_raw['주문일'].max().date()
    date_range = st.sidebar.date_input("📅 주문 기간 선택", [min_date, max_date])
    
    # 데이터 필터링
    if search_keywords:
        df_filtered = df_raw[df_raw['품종'].isin(search_keywords)]
    else:
        df_filtered = df_raw.copy()
        
    if len(date_range) == 2:
        start_date, end_date = date_range
        df_filtered = df_filtered[(df_filtered['주문일'].dt.date >= start_date) & (df_filtered['주문일'].dt.date <= end_date)]

    # 메인 화면 제목
    st.title("🍎 주문 데이터 통합 분석 대시보드")
    st.markdown("---")

    # 상단 Metric 지표
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("총 주문 건수", f"{len(df_filtered):,} 건")
    with col2:
        total_payment = df_filtered['실결제 금액'].sum() if '실결제 금액' in df_filtered.columns else 0
        st.metric("총 결제 금액", f"{int(total_payment):,} 원")
    with col3:
        avg_payment = df_filtered['실결제 금액'].mean() if '실결제 금액' in df_filtered.columns else 0
        st.metric("평균 결제 금액", f"{int(avg_payment):,} 원")
    with col4:
        unique_users = df_filtered['UID'].nunique() if 'UID' in df_filtered.columns else 0
        st.metric("실구매 고객 수", f"{unique_users:,} 명")

    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["📈 트렌드 분석", "🔍 상세 EDA", "📋 상세 데이터"])

    # --- Tab 1: Trend Analysis ---
    with tab1:
        st.subheader("일자별 주문 건수 추이")
        if not df_filtered.empty:
            trend_df = df_filtered.groupby([df_filtered['주문일'].dt.date, '품종']).size().reset_index(name='주문건수')
            fig_trend = px.line(trend_df, x='주문일', y='주문건수', color='품종', title="키워드별 주문 트렌드 비교")
            fig_trend.update_layout(xaxis_title="주문일", yaxis_title="주문건수")
            st.plotly_chart(fig_trend, use_container_width=True)
            
            st.subheader("일자별 매출 추이")
            sales_df = df_filtered.groupby([df_filtered['주문일'].dt.date, '품종'])['실결제 금액'].sum().reset_index()
            fig_sales = px.area(sales_df, x='주문일', y='실결제 금액', color='품종', title="키워드별 매출 트렌드 (누적)")
            st.plotly_chart(fig_sales, use_container_width=True)

    # --- Tab 2: Detail EDA ---
    with tab2:
        eda_col1, eda_col2 = st.columns(2)
        
        with eda_col1:
            st.subheader("📍 지역별 주문 비중")
            if '광역지역(정식)' in df_filtered.columns:
                region_df = df_filtered['광역지역(정식)'].value_counts().reset_index()
                fig_region = px.pie(region_df, values='count', names='광역지역(정식)', hole=0.4, title="광역시도별 주문 분포")
                st.plotly_chart(fig_region, use_container_width=True)
        
        with eda_col2:
            st.subheader("🛍️ 주문경로별 비중")
            if '주문경로' in df_filtered.columns:
                path_df = df_filtered['주문경로'].value_counts().reset_index()
                fig_path = px.bar(path_df, x='count', y='주문경로', orientation='h', title="채널별 주문 유입")
                st.plotly_chart(fig_path, use_container_width=True)
                
        eda_col3, eda_col4 = st.columns(2)
        
        with eda_col3:
            st.subheader("⭐️ 셀러별 성과 (Top 10)")
            if '셀러명' in df_filtered.columns:
                seller_df = df_filtered.groupby('셀러명').size().reset_index(name='건수').sort_values('건수', ascending=False).head(10)
                fig_seller = px.bar(seller_df, x='건수', y='셀러명', color='건수', title="상위 셀러 판매 현황")
                st.plotly_chart(fig_seller, use_container_width=True)
                
        with eda_col4:
            st.subheader("💳 결제수단 비중")
            if '결제방법' in df_filtered.columns:
                pay_df = df_filtered['결제방법'].value_counts().reset_index()
                fig_pay = px.pie(pay_df, values='count', names='결제방법', title="결제 수단 선호도")
                st.plotly_chart(fig_pay, use_container_width=True)

    # --- Tab 3: Raw Data ---
    with tab3:
        st.subheader("상세 주문 데이터 (필터링됨)")
        st.dataframe(df_filtered, use_container_width=True)
        
        # 다운로드 버튼
        csv = df_filtered.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(
            label="📄 필터링된 데이터 다운로드 (CSV)",
            data=csv,
            file_name=f"filtered_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv',
        )

else:
    st.error(f"데이터 파일을 찾을 수 없습니다: {data_path}")
