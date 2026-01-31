import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime
import numpy as np

# 페이지 설정
st.set_page_config(page_title="종합 주문 분석 대시보드 (V2)", layout="wide")

# Plotly 한글 깨짐 방지 템플릿 설정
import plotly.io as pio
pio.templates.default = "plotly_white"

# 데이터 로드 및 전처리 (캐싱)
@st.cache_data
def load_and_preprocess(file_path):
    if not os.path.exists(file_path):
        return None
    
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
    except:
        df = pd.read_csv(file_path, encoding='cp949')
    
    # 날짜 처리
    if '주문일' in df.columns:
        df['주문일'] = pd.to_datetime(df['주문일'], errors='coerce')
        df = df.dropna(subset=['주문일'])
    
    # 금액 처리
    price_cols = ['결제금액', '실결제 금액', '판매단가', '공급단가']
    for col in price_cols:
        if col in df.columns and df[col].dtype == 'object':
            df[col] = df[col].str.replace(',', '').astype(float)
    
    # 시즌 정보 추가
    def get_season(month):
        if month in [3, 4, 5]: return '봄'
        elif month in [6, 7, 8]: return '여름'
        elif month in [9, 10, 11]: return '가을'
        else: return '겨울'
    df['시즌'] = df['주문일'].dt.month.apply(get_season)
    
    return df

# RFM 분석 함수
def calculate_rfm(df):
    snapshot_date = df['주문일'].max() + pd.Timedelta(days=1)
    rfm = df.groupby('UID').agg({
        '주문일': lambda x: (snapshot_date - x.max()).days,
        'UID': 'count',
        '실결제 금액': 'sum'
    })
    rfm.columns = ['Recency', 'Frequency', 'Monetary']
    
    # 5점 척도 스코어링 (데이터 분포 고려)
    for col, labels in [('Recency', [5,4,3,2,1]), ('Frequency', [1,2,3,4,5]), ('Monetary', [1,2,3,4,5])]:
        try:
            rfm[f'{col[0]}_Score'] = pd.qcut(rfm[col].rank(method='first'), 5, labels=labels)
        except:
            rfm[f'{col[0]}_Score'] = pd.cut(rfm[col], 5, labels=labels)
            
    rfm['Total_Score'] = rfm['R_Score'].astype(int) + rfm['F_Score'].astype(int) + rfm['M_Score'].astype(int)
    
    def segment_customer(score):
        if score >= 13: return 'VVIP (최상위)'
        elif score >= 10: return 'VIP (우수)'
        elif score >= 7: return 'Regular (일반)'
        else: return 'At-risk (이탈우려)'
    rfm['Segment'] = rfm['Total_Score'].apply(segment_customer)
    return rfm

# 앱 시작
data_path ='project1_5959.csv'
df_raw = load_and_preprocess(data_path)

if df_raw is not None:
    # --- 사이드바 필터 ---
    st.sidebar.title("🌲 분석 필터")
    
    # 품종 검색 (복수 선택)
    all_varieties = sorted(df_raw['품종'].unique().tolist())
    selected_varieties = st.sidebar.multiselect(
        "🏷️ 분석할 품종 선택 (검색 가능)",
        options=all_varieties,
        default=['감귤', '황금향'] if '감귤' in all_varieties else all_varieties[:2]
    )
    
    # 날짜 범위
    min_d, max_d = df_raw['주문일'].min().date(), df_raw['주문일'].max().date()
    date_input = st.sidebar.date_input("📅 기간 선택", [min_d, max_d])
    
    # 데이터 필터링 적용
    mask = df_raw['품종'].isin(selected_varieties) if selected_varieties else df_raw['품종'].notnull()
    if len(date_input) == 2:
        mask &= (df_raw['주문일'].dt.date >= date_input[0]) & (df_raw['주문일'].dt.date <= date_input[1])
    df = df_raw[mask]

    # --- 메인 대시보드 UI ---
    st.title("📊 통합 데이터 분석 대시보드")
    st.info("`final_comprehensive_report.md`의 분석 항목을 실시간으로 시각화합니다.")

    # KPI Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("총 주문 건수", f"{len(df):,}건")
    m2.metric("총 매출액", f"₩{int(df['실결제 금액'].sum()):,}원")
    m3.metric("평균 객단가", f"₩{int(df['실결제 금액'].mean()):,}원" if len(df)>0 else "0")
    m4.metric("재구매율(전체)", f"{(df['재구매 횟수'] > 0).mean()*100:.1f}%" if '재구매 횟수' in df.columns else "N/A")

    # 탭 구성
    t1, t2, t3, t4, t5, t6 = st.tabs(["📈 트렌드 비교", "🍂 시즌 & 재구매", "👥 RFM 고객 분석", "📍 기초 EDA", "🛍️ 셀러별 채널 분석", "📋 상세 데이터"])

    with t1:
        st.subheader("키워드 기반 주문/매출 트렌드")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            trend_count = df.groupby([df['주문일'].dt.date, '품종']).size().reset_index(name='주문건수')
            fig1 = px.line(trend_count, x='주문일', y='주문건수', color='품종', title="일자별 주문 건수 추이")
            st.plotly_chart(fig1, use_container_width=True)
        with col_t2:
            trend_sales = df.groupby([df['주문일'].dt.date, '품종'])['실결제 금액'].sum().reset_index()
            fig2 = px.area(trend_sales, x='주문일', y='실결제 금액', color='품종', title="일자별 매출액 추이")
            st.plotly_chart(fig2, use_container_width=True)

    with t2:
        st.subheader("시즌별 판매 및 재구매율 분석")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            season_counts = df['시즌'].value_counts().reset_index()
            fig_s = px.bar(season_counts, x='시즌', y='count', color='시즌', title="시즌별 주문 비중", 
                           category_orders={"시즌": ["봄", "여름", "가을", "겨울"]})
            st.plotly_chart(fig_s, use_container_width=True)
        with col_s2:
            if '재구매 횟수' in df.columns:
                re_rate = df.groupby('품종').apply(lambda x: (x['재구매 횟수'] > 0).mean() * 100).reset_index(name='재구매율(%)')
                fig_re = px.bar(re_rate.sort_values('재구매율(%)', ascending=False).head(10), 
                                x='재구매율(%)', y='품종', orientation='h', title="품종별 재구매율 Top 10", color='재구매율(%)')
                st.plotly_chart(fig_re, use_container_width=True)

    with t3:
        st.subheader("RFM 고객 세분화 분석")
        rfm_data = calculate_rfm(df)
        col_r1, col_r2 = st.columns([1, 2])
        with col_r1:
            seg_counts = rfm_data['Segment'].value_counts().reset_index()
            fig_pie = px.pie(seg_counts, values='count', names='Segment', title="고객 세그먼트 비중",
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_r2:
            seg_stats = rfm_data.groupby('Segment')[['Recency', 'Frequency', 'Monetary']].mean().reset_index()
            # 포맷팅용 가공
            seg_stats_display = seg_stats.copy()
            seg_stats_display['Monetary'] = seg_stats_display['Monetary'].apply(lambda x: f"₩{int(x):,}")
            st.dataframe(seg_stats_display, use_container_width=True)
            
            fig_scatter = px.scatter(rfm_data.sample(min(len(rfm_data), 1000)), x='Frequency', y='Monetary', color='Segment', 
                                    size='Recency', log_x=True, title="고객 세그먼트 산점도 (샘플링)")
            st.plotly_chart(fig_scatter, use_container_width=True)

    with t4:
        st.subheader("지역 및 채널 분석")
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            if '광역지역(정식)' in df.columns:
                reg_df = df['광역지역(정식)'].value_counts().reset_index().head(10)
                fig_reg = px.bar(reg_df, x='count', y='광역지역(정식)', orientation='h', title="지역별 주문 Top 10")
                st.plotly_chart(fig_reg, use_container_width=True)
        with col_e2:
            if '주문경로' in df.columns:
                ch_df = df['주문경로'].value_counts().reset_index()
                fig_ch = px.pie(ch_df, values='count', names='주문경로', title="주문 채널 비중")
                st.plotly_chart(fig_ch, use_container_width=True)

    with t5:
        st.subheader("상위 15개 셀러별 주문경로 분석")
        if '셀러명' in df.columns and '주문경로' in df.columns:
            # 상위 15개 셀러 추출
            top_15_sellers = df['셀러명'].value_counts().head(15).index.tolist()
            df_top_sellers = df[df['셀러명'].isin(top_15_sellers)]
            
            # 셀러별 주문경로 집계
            seller_channel = df_top_sellers.groupby(['셀러명', '주문경로']).size().reset_index(name='주문건수')
            
            # 시각화 (누적 막대 그래프)
            fig_seller_ch = px.bar(seller_channel, x='주문건수', y='셀러명', color='주문경로', 
                                   title="상위 15개 셀러의 주문 유입 채널", orientation='h',
                                   category_orders={"셀러명": top_15_sellers})
            st.plotly_chart(fig_seller_ch, use_container_width=True)
            
            # 데이터 표 (Pivot Table)
            st.markdown("#### 셀러별 채널별 주문 건수 상세")
            pivot_seller_ch = df_top_sellers.pivot_table(index='셀러명', columns='주문경로', 
                                                         values='UID', aggfunc='count', fill_value=0)
            # 합계 추가 및 상위 순서 유지
            pivot_seller_ch['합계'] = pivot_seller_ch.sum(axis=1)
            pivot_seller_ch = pivot_seller_ch.loc[top_15_sellers]
            st.dataframe(pivot_seller_ch, use_container_width=True)
        else:
            st.warning("'셀러명' 또는 '주문경로' 칼럼이 데이터에 존재하지 않습니다.")

    with t6:
        st.subheader("데이터 필터 결과")
        st.write(f"현재 조건에 해당하는 데이터: {len(df):,}건")
        st.dataframe(df.head(500), use_container_width=True)
        csv_data = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button("📥 필터링된 데이터 다운로드 (CSV)", csv_data, "filtered_data.csv", "text/csv")

else:
    st.error(f"데이터 파일을 찾을 수 없습니다: {data_path}")
    st.info("파일 경로를 확인하거나 데이터 파일이 해당 위치에 있는지 업무 담당자에게 문의하세요.")
