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
    if df.empty:
        return pd.DataFrame(columns=['Recency', 'Frequency', 'Monetary', 'R_Score', 'F_Score', 'M_Score', 'Total_Score', 'Segment'])
        
    # 날짜 시간 분리 (날짜만 기준으로 재구매 판단)
    df_rfm = df.copy()
    df_rfm['주문날짜'] = df_rfm['주문일'].dt.date
    
    snapshot_date = df['주문일'].max() + pd.Timedelta(days=1)
    
    # 식별자: 주문자연락처 (없으면 UID 사용)
    id_col = '주문자연락처' if '주문자연락처' in df.columns else 'UID'
    
    # 집계: Frequency는 서로 다른 주문날짜의 수
    rfm = df_rfm.groupby(id_col).agg({
        '주문일': lambda x: (snapshot_date - x.max()).days,
        '주문날짜': 'nunique',
        '실결제 금액': 'sum'
    })
    rfm.columns = ['Recency', 'Frequency', 'Monetary']
    
    # 5점 척도 스코어링
    for col, labels in [('Recency', [5,4,3,2,1]), ('Frequency', [1,2,3,4,5]), ('Monetary', [1,2,3,4,5])]:
        try:
            rfm[f'{col[0]}_Score'] = pd.qcut(rfm[col].rank(method='first'), 5, labels=labels)
        except:
            try:
                rfm[f'{col[0]}_Score'] = pd.cut(rfm[col], 5, labels=labels)
            except:
                rfm[f'{col[0]}_Score'] = 3
            
    for score_col in ['R_Score', 'F_Score', 'M_Score']:
        rfm[score_col] = pd.to_numeric(rfm[score_col], errors='coerce').fillna(3).astype(int)
        
    rfm['Total_Score'] = rfm['R_Score'] + rfm['F_Score'] + rfm['M_Score']
    
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
    st.info("`generate_final_report.py`의 분석 항목을 실시간으로 시각화합니다.")

    # 재구매 지표 계산을 위한 기초 데이터 준비 (날짜 기준)
    id_col_kpi = '주문자연락처' if '주문자연락처' in df_raw.columns else 'UID'
    df_unique_day_kpi = df.groupby([id_col_kpi, df['주문일'].dt.date]).size().reset_index(name='order_day_count')
    user_day_counts_kpi = df_unique_day_kpi.groupby(id_col_kpi).size()
    repeat_users_count_kpi = (user_day_counts_kpi >= 2).sum()
    total_users_count_kpi = len(user_day_counts_kpi)

    # 상단 지표 레이아웃
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("총 주문 건수", f"{len(df):,}건")
    m2.metric("총 매출액", f"₩{int(df['실결제 금액'].sum()):,}원")
    m3.metric("평균 객단가", f"₩{int(df['실결제 금액'].mean()):,}원" if len(df)>0 else "0")
    m4.metric("재구매율(날짜기준)", f"{(repeat_users_count_kpi / total_users_count_kpi * 100):.1f}%" if total_users_count_kpi > 0 else "N/A")

    # 탭 구성
    t1, t2, t3, t4, t5, t6, t7 = st.tabs(["📈 트렌드 비교", "🍂 시즌 & 재구매", "👥 RFM 고객 분석", "📍 기초 EDA", "🛍️ 셀러별 채널 분석", "🔍 키워드 매출 분석", "📋 상세 데이터"])

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
            season_counts = df['시즌'].value_counts().reset_index(name='order_count')
            season_counts.columns = ['시즌', 'count']
            fig_s = px.bar(season_counts, x='시즌', y='count', color='시즌', title="시즌별 주문 비중", 
                           category_orders={"시즌": ["봄", "여름", "가을", "겨울"]})
            st.plotly_chart(fig_s, use_container_width=True)
        with col_s2:
            # 품종별 재구매율 (다른 날 주문한 경우만)
            item_day_counts = df.groupby(['품종', id_col, df['주문일'].dt.date]).size().reset_index()
            item_user_counts = item_day_counts.groupby(['품종', id_col]).size().reset_index(name='day_count')
            
            re_rate_logic = item_user_counts.groupby('품종').apply(
                lambda x: (x['day_count'] >= 2).mean() * 100
            ).reset_index(name='재구매율(%)')
            
            fig_re = px.bar(re_rate_logic.sort_values('재구매율(%)', ascending=False).head(10), 
                            x='재구매율(%)', y='품종', orientation='h', title="품종별 재구매율 Top 10 (날짜기준)", color='재구매율(%)')
            st.plotly_chart(fig_re, use_container_width=True)

        st.divider()
        st.subheader("🔁 재구매 고객 구매 패턴 상세 분석")
        
        # 재구매 데이터 필터링 (아이디별 서로 다른 주문 일수 2일 이상)
        user_day_counts_repeat = df.groupby(id_col)[['주문일']].agg(lambda x: x.dt.date.nunique())
        repeat_ids = user_day_counts_repeat[user_day_counts_repeat.iloc[:, 0] >= 2].index
        
        # 실제 재구매가 일어난 날들만 추출 (동일 날짜 주문은 1건으로 처리하기 위해 unique date로 접근)
        df_target = df[df[id_col].isin(repeat_ids)].copy()
        df_target['주문날짜'] = df_target['주문일'].dt.date
        df_repeat = df_target.drop_duplicates(subset=[id_col, '주문날짜']).sort_values([id_col, '주문일'])
        
        if not df_repeat.empty:
            col_p1, col_p2 = st.columns(2)
            
            with col_p1:
                # 1. 재구매 빈도 분포 (구매 일수별 고객 수)
                freq_dist = user_day_counts_repeat.value_counts().reset_index(name='customer_count')
                freq_dist.columns = ['구매일수', '고객수']
                freq_dist['구분'] = freq_dist['구매일수'].apply(lambda x: f"{x}일" if x < 5 else "5일 이상")
                freq_summary = freq_dist.groupby('구분')['고객수'].sum().reset_index()
                
                if not freq_summary.empty and freq_summary['고객수'].sum() > 0:
                    fig_freq = px.pie(freq_summary, values='고객수', names='구분', title="고객별 총 구매 일수 비중",
                                      hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
                    st.plotly_chart(fig_freq, use_container_width=True)
                else:
                    st.info("빈도 분포를 표시할 데이터가 없습니다.")
                
            with col_p2:
                # 2. 구매 주기 분석 (연속 주문 일자 간의 일수 차이)
                df_repeat['prev_date'] = df_repeat.groupby(id_col)['주문날짜'].shift(1)
                df_repeat['interval'] = (df_repeat['주문날짜'] - df_repeat['prev_date']).apply(lambda x: x.days if pd.notnull(x) else np.nan)
                intervals = df_repeat['interval'].dropna()
                
                if not intervals.empty:
                    fig_dist = px.histogram(intervals, x='interval', nbins=50, 
                                            title="재구매 고객의 방문 간격 분포 (Days)",
                                            labels={'interval': '구매 간격 (일)', 'count': '방문 횟수'},
                                            color_discrete_sequence=['indianred'])
                    st.plotly_chart(fig_dist, use_container_width=True)
                    st.info(f"💡 재구매 고객의 평균 구매 주기는 약 **{intervals.mean():.1f}일**입니다.")
            
            # 3. 재구매 고객이 선호하는 품종 Top 10
            st.markdown("#### ⭐ 재구매 고객의 주요 구매 품종")
            # 재구매 발생 시점(2회차 이상)의 품종 집계
            df_re_items = df_target.sort_values([id_col, '주문일'])
            df_re_items['order_rank'] = df_re_items.groupby(id_col)['주문날짜'].transform(lambda x: pd.factorize(x)[0] + 1)
            df_repeat_only = df_re_items[df_re_items['order_rank'] >= 2]
            
            df_repeat_items_stats = df_repeat_only.groupby('품종').size().reset_index(name='재구매주문건수')
            if not df_repeat_items_stats.empty:
                fig_rep_items = px.bar(df_repeat_items_stats.sort_values('재구매주문건수', ascending=False).head(10),
                                       x='재구매주문건수', y='품종', orientation='h', color='재구매주문건수',
                                       title="재구매 고객이 다시 찾은 품종 Top 10")
                st.plotly_chart(fig_rep_items, use_container_width=True)
            else:
                st.info("재구매 발생 품종을 분석할 데이터가 부족합니다.")

            # 데이터 표
            st.markdown("#### 재구매 행동 지표 요약 (날짜기준)")
            summary_stats = pd.DataFrame({
                '지표': ['총 재구매 고객 수', '평균 구매 일수', '최대 구매 일수', '평균 구매 주기'],
                '수치': [
                    f"{len(repeat_ids):,}명",
                    f"{user_day_counts_repeat.loc[repeat_ids].mean().iloc[0]:.2f}일",
                    f"{user_day_counts_repeat.max().iloc[0]:,}일",
                    f"{intervals.mean():.1f}일" if not intervals.empty else "N/A"
                ]
            })
            st.table(summary_stats)
        else:
            st.info("재구매 고객 데이터가 충분하지 않습니다.")

    with t3:
        st.subheader("RFM 고객 세분화 분석")
        rfm_data = calculate_rfm(df)
        col_r1, col_r2 = st.columns([1, 2])
        with col_r1:
            seg_counts = rfm_data['Segment'].value_counts().reset_index(name='customer_count')
            if not seg_counts.empty and seg_counts['customer_count'].sum() > 0:
                fig_pie = px.pie(seg_counts, values='customer_count', names='Segment', title="고객 세그먼트 비중",
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("세그먼트 비중을 표시할 데이터가 없습니다.")
        with col_r2:
            seg_stats = rfm_data.groupby('Segment')[['Recency', 'Frequency', 'Monetary']].mean().reset_index()
            # 포맷팅용 가공
            seg_stats_display = seg_stats.copy()
            seg_stats_display['Monetary'] = seg_stats_display['Monetary'].apply(lambda x: f"₩{int(x):,}")
            st.dataframe(seg_stats_display, use_container_width=True)
            
            if not rfm_data.empty:
                fig_scatter = px.scatter(rfm_data.sample(min(len(rfm_data), 1000)), x='Frequency', y='Monetary', color='Segment', 
                                        size='Recency', log_x=True, title="고객 세그먼트 산점도 (샘플링)")
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.info("산점도를 표시할 고객 데이터가 없습니다.")

        st.divider()
        st.subheader("👨‍🌾 셀러별 재구매율 현황")
        if '셀러명' in df.columns and '재구매 횟수' in df.columns:
            # 셀러별 재구매율 계산 (주문 10건 이상 셀러 대상)
            seller_counts = df['셀러명'].value_counts()
            valid_sellers = seller_counts[seller_counts >= 10].index
            df_valid_sellers = df[df['셀러명'].isin(valid_sellers)]
            
            seller_re_rate = df_valid_sellers.groupby('셀러명').apply(
                lambda x: (x['재구매 횟수'] > 0).mean() * 100
            ).reset_index(name='재구매율(%)')
            
            fig_seller_re = px.bar(seller_re_rate.sort_values('재구매율(%)', ascending=False).head(20),
                                   x='재구매율(%)', y='셀러명', orientation='h', 
                                   title="셀러별 재구매율 Top 20 (주문 10건 이상)",
                                   color='재구매율(%)', color_continuous_scale='Viridis')
            st.plotly_chart(fig_seller_re, use_container_width=True)
        else:
            st.warning("'셀러명' 또는 '재구매 횟수' 데이터가 부족합니다.")

    with t4:
        st.subheader("지역 및 채널 분석")
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            if '광역지역(정식)' in df.columns:
                reg_df = df['광역지역(정식)'].value_counts().reset_index(name='order_count')
                reg_df.columns = ['광역지역(정식)', 'count']
                fig_reg = px.bar(reg_df.head(10), x='count', y='광역지역(정식)', orientation='h', title="지역별 주문 Top 10")
                st.plotly_chart(fig_reg, use_container_width=True)
        with col_e2:
            if '주문경로' in df.columns:
                ch_df = df['주문경로'].value_counts().reset_index(name='order_count')
                ch_df.columns = ['주문경로', 'count']
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
            pivot_seller_ch['합계'] = pivot_seller_ch.sum(axis=1)
            # KeyError 방지: 인덱스에 있는 셀러만 loc 시도
            pivot_seller_ch = pivot_seller_ch.reindex(top_15_sellers).fillna(0)
            st.dataframe(pivot_seller_ch, use_container_width=True)

            # --- 셀러 월별 활동/유입/이탈 분석 추가 ---
            st.divider()
            st.subheader("📅 셀러 월별 활동 및 유입/이탈 현황")
            
            # 월별 데이터 준비 (결측치 제거하여 KeyError 방지)
            df_seller_active = df.dropna(subset=['셀러명', '주문일']).copy()
            if not df_seller_active.empty:
                df_seller_active['연월'] = df_seller_active['주문일'].dt.to_period('M').astype(str)
                
                # 월별 활동 셀러 리스트 생성
                monthly_sellers = df_seller_active.groupby('연월')['셀러명'].unique().to_dict()
                months = sorted(monthly_sellers.keys())
                
                activity_stats = []
                first_seen = df_seller_active.groupby('셀러명')['연월'].min().to_dict()
                
                for i, month in enumerate(months):
                    current_sellers = set(monthly_sellers[month])
                    # 유입: 이번 달에 처음 본 셀러 수
                    new_sellers = sum(1 for s in current_sellers if s in first_seen and first_seen[s] == month)
                    
                    # 이탈율 계산: 지난달엔 있었는데 이번달엔 없는 셀러 (첫 달 제외)
                    churn_rate = 0
                    if i > 0:
                        prev_sellers = set(monthly_sellers[months[i-1]])
                        churned_sellers = prev_sellers - current_sellers
                        churn_rate = (len(churned_sellers) / len(prev_sellers)) * 100
                    
                    inflow_rate = (new_sellers / len(current_sellers)) * 100
                    
                    activity_stats.append({
                        '연월': month,
                        '활동셀러수': len(current_sellers),
                        '신규모집셀러': new_sellers,
                        '유입율(%)': inflow_rate,
                        '이탈율(%)': churn_rate
                    })
                
                df_activity = pd.DataFrame(activity_stats)
                
                if not df_activity.empty:
                    # 시각화 1: 활동 셀러 및 신규 셀러 추이
                    fig_act = go.Figure()
                    fig_act.add_trace(go.Bar(x=df_activity['연월'], y=df_activity['활동셀러수'], name='전체 활동 셀러', marker_color='skyblue'))
                    fig_act.add_trace(go.Bar(x=df_activity['연월'], y=df_activity['신규모집셀러'], name='신규 유입 셀러', marker_color='orange'))
                    fig_act.update_layout(title="월별 활동 및 신규 셀러 수 추이", barmode='group')
                    st.plotly_chart(fig_act, use_container_width=True)
                    
                    # 시각화 2: 유입율 및 이탈율 추이
                    fig_rate = px.line(df_activity, x='연월', y=['유입율(%)', '이탈율(%)'], 
                                       markers=True, title="월별 셀러 유입율 및 이탈율 변화")
                    st.plotly_chart(fig_rate, use_container_width=True)
                    
                    # 요약 지표
                    st.markdown("#### 셀러 활동 지표 요약 (월별)")
                    st.dataframe(df_activity.style.format({
                        '유입율(%)': '{:.1f}%',
                        '이탈율(%)': '{:.1f}%'
                    }), use_container_width=True)

                    # --- 상위 30개 셀러 키워드 전략 분석 추가 ---
                    st.divider()
                    st.subheader("🎯 상위 30개 셀러의 키워드 활용 전략")
                    
                    if '상품명' in df.columns:
                        # 상위 30개 셀러 추출
                        top_30_sellers = df['셀러명'].value_counts().head(30).index.tolist()
                        df_top_30 = df[df['셀러명'].isin(top_30_sellers)].copy()
                        df_top_30['상품명_clean'] = df_top_30['상품명'].fillna('')
                        
                        kw_categories = {
                            '이벤트': ['1\+1', '사전예약'],
                            '맛강조': ['과즙폭발', '꿀', '당도'],
                            '가성비': ['실속'],
                            '품종': ['타이벡', '조생'],
                            '원산지': ['제주', '해남']
                        }
                        
                        seller_kw_list = []
                        for seller in top_30_sellers:
                            df_s = df_top_30[df_top_30['셀러명'] == seller]
                            total_s = len(df_s)
                            
                            row = {'셀러명': seller, '총주문건수': total_s}
                            for cat, keywords in kw_categories.items():
                                pattern = '|'.join(keywords)
                                count = df_s['상품명_clean'].str.contains(pattern, case=False, regex=True).sum()
                                row[cat] = (count / total_s * 100) if total_s > 0 else 0
                            
                            seller_kw_list.append(row)
                        
                        df_seller_kw = pd.DataFrame(seller_kw_list)
                        
                        if not df_seller_kw.empty and len(df_seller_kw.columns) > 1:
                            # 시각화: 히트맵 (셀러별 키워드 활용 비중)
                            fig_hm = px.imshow(df_seller_kw.set_index('셀러명').drop(columns=['총주문건수']),
                                               labels=dict(x="키워드 카테고리", y="셀러명", color="사용 비중(%)"),
                                               x=['이벤트', '맛강조', '가성비', '품종', '원산지'],
                                               title="상위 30개 셀러의 키워드 활용 패턴 (Heatmap)",
                                               color_continuous_scale='YlGnBu', text_auto='.1f')
                            fig_hm.update_layout(height=800)
                            st.plotly_chart(fig_hm, use_container_width=True)
                        else:
                            st.info("히트맵을 생성할 셀러/키워드 데이터가 부족합니다.")
                        
                        # 데이터 표
                        st.markdown("#### 셀러별 키워드 활용 상세 (비중 %)")
                        st.dataframe(df_seller_kw.style.format({
                            '이벤트': '{:.1f}%', '맛강조': '{:.1f}%', '가성비': '{:.1f}%', '품종': '{:.1f}%', '원산지': '{:.1f}%'
                        }), use_container_width=True)
                    else:
                        st.warning("'상품명' 칼럼이 없어 키워드 분석을 진행할 수 없습니다.")

                    # --- 셀러 성장성 분석 및 마케팅 제언 추가 ---
                    st.divider()
                    st.subheader("🚀 셀러 성장성 분석 및 마케팅 제언")

                    # 최근 2개월 비교 데이터 준비
                    months_sorted = sorted(df_seller_active['연월'].unique(), reverse=True)
                    if len(months_sorted) >= 2:
                        current_m = months_sorted[0]
                        prev_m = months_sorted[1]
                        
                        st.info(f"분석 기간: {prev_m} (전월) vs {current_m} (당월)")
                        
                        # 월별 셀러 판매량 집계
                        m_counts = df_seller_active[df_seller_active['연월'].isin([current_m, prev_m])]
                        seller_growth = m_counts.groupby(['셀러명', '연월']).size().unstack(fill_value=0)
                        
                        # 증감량 계산
                        if current_m in seller_growth.columns and prev_m in seller_growth.columns:
                            seller_growth['증감량'] = seller_growth[current_m] - seller_growth[prev_m]
                            seller_growth['증감율(%)'] = (seller_growth['증감량'] / seller_growth[prev_m] * 100).replace([np.inf, -np.inf], 100).fillna(100)
                            
                            col_g1, col_g2 = st.columns(2)
                            
                            def get_marketing_advice(change, is_surge=True):
                                if is_surge:
                                    return "성공 채널 예산 확대, 충성 고객 전용 감사 쿠폰, 리뷰 이벤트 강화, 연관 상품 큐레이션"
                                else:
                                    return "이탈 방지 리마인드 알림, 단기 할인 프로모션, 인기 품목 재입고 안내, 유입 채널 광고 소재 교체"

                            with col_g1:
                                st.success(f"🔥 판매량 급증 셀러 Top 10 ({current_m} 기준)")
                                surge_top10 = seller_growth.sort_values('증감량', ascending=False).head(10).reset_index()
                                surge_top10['마케팅 추천 전략'] = surge_top10['증감량'].apply(lambda x: get_marketing_advice(x, True))
                                st.dataframe(surge_top10[['셀러명', prev_m, current_m, '증감량', '마케팅 추천 전략']], use_container_width=True)
                                
                            with col_g2:
                                st.error(f"⚠️ 판매량 급감 셀러 Top 10 ({current_m} 기준)")
                                decline_top10 = seller_growth.sort_values('증감량', ascending=True).head(10).reset_index()
                                decline_top10['마케팅 추천 전략'] = decline_top10['증감량'].apply(lambda x: get_marketing_advice(x, False))
                                st.dataframe(decline_top10[['셀러명', prev_m, current_m, '증감량', '마케팅 추천 전략']], use_container_width=True)
                                
                            # 시각화: 증감량 분포
                            fig_growth = px.bar(pd.concat([surge_top10, decline_top10]), 
                                                x='증감량', y='셀러명', color='증감량',
                                                title="셀러별 판매량 변화 폭 (Top 10 급증/급감)",
                                                color_continuous_scale='RdYlGn', orientation='h')
                            st.plotly_chart(fig_growth, use_container_width=True)
                        else:
                            st.warning("비교할 수 있는 월별 데이터가 부족합니다.")
                    else:
                        st.info("성장성 분석을 위해서는 최소 2개월 이상의 데이터가 필요합니다.")
                else:
                    st.info("활동 지표를 계산할 수 있는 충분한 데이터가 없습니다.")
            else:
                st.info("셀러 활동 분석을 위한 유효한 데이터(셀러명, 주문일)가 없습니다.")
        else:
            st.warning("'셀러명' 또는 '주문일' 칼럼이 데이터에 존재하지 않습니다.")

    with t6:
        st.subheader("🔍 상품 키워드별 매출 기여도 분석")
        
        if '상품명' in df.columns:
            # 키워드 카테고리 정의
            kw_categories = {
                '이벤트': ['1\+1', '사전예약'],
                '맛강조': ['과즙폭발', '꿀', '당도'],
                '가성비': ['실속'],
                '품종': ['타이벡', '조생'],
                '원산지': ['제주', '해남']
            }
            
            # 검색을 위해 미리 처리
            df_kw = df.copy()
            df_kw['상품명_clean'] = df_kw['상품명'].fillna('')
            df_kw['연월'] = df_kw['주문일'].dt.to_period('M').astype(str)
            
            monthly_total_sales = df_kw.groupby('연월')['실결제 금액'].sum()
            
            kw_results = []
            
            for cat, keywords in kw_categories.items():
                # 해당 카테고리의 어떤 키워드라도 포함된 주문 필터링
                pattern = '|'.join(keywords)
                mask_cat = df_kw['상품명_clean'].str.contains(pattern, case=False, regex=True)
                df_cat = df_kw[mask_cat]
                
                # 월별 매출 합계
                cat_monthly_sales = df_cat.groupby('연월')['실결제 금액'].sum()
                
                for month in monthly_total_sales.index:
                    sales_val = cat_monthly_sales.get(month, 0)
                    total_val = monthly_total_sales[month]
                    ratio = (sales_val / total_val * 100) if total_val > 0 else 0
                    
                    kw_results.append({
                        '연월': month,
                        '카테고리': cat,
                        '매출액': sales_val,
                        '비중(%)': ratio
                    })
            
            df_kw_final = pd.DataFrame(kw_results)
            
            if not df_kw_final.empty:
                # 시각화 1: 카테고리별 월별 매출 비중 추이
                fig_kw_line = px.line(df_kw_final, x='연월', y='비중(%)', color='카테고리', markers=True,
                                      title="월별 상품 키워드 카테고리 매출 비중 (%)")
                st.plotly_chart(fig_kw_line, use_container_width=True)
                
                # 시각화 2: 누적 매출 비중 (Stack Bar)
                fig_kw_stack = px.bar(df_kw_final, x='연월', y='비중(%)', color='카테고리',
                                      title="월별 키워드 매출 기여도 누적 분포", barmode='relative')
                st.plotly_chart(fig_kw_stack, use_container_width=True)
            else:
                st.info("키워드 기여도를 분석할 데이터가 부족합니다.")
            
            # 데이터 표
            if not df_kw_final.empty:
                st.markdown("#### 키워드 카테고리별 월 매출 비중 상세")
                pivot_kw = df_kw_final.pivot(index='연월', columns='카테고리', values='비중(%)').fillna(0)
                st.dataframe(pivot_kw.style.format("{:.1f}%"), use_container_width=True)
        else:
            st.warning("'상품명' 칼럼이 데이터에 존재하지 않아 키워드 분석이 불가능합니다.")

    with t7:
        st.subheader("데이터 필터 결과")
        st.write(f"현재 조건에 해당하는 데이터: {len(df):,}건")
        st.dataframe(df.head(500), use_container_width=True)
        csv_data = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button("📥 필터링된 데이터 다운로드 (CSV)", csv_data, "filtered_data.csv", "text/csv")

else:
    st.error(f"데이터 파일을 찾을 수 없습니다: {data_path}")
    st.info("파일 경로를 확인하거나 데이터 파일이 해당 위치에 있는지 업무 담당자에게 문의하세요.")
