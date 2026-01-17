import streamlit as st
import pandas as pd
import plotly.express as px
import os
import sys

# -----------------------------------------------------------------------------
# 1. 메인 대시보드 함수
# -----------------------------------------------------------------------------
def run_dashboard():
    st.set_page_config(
        page_title="Dungeon Crawl 통계",
        page_icon="🛡️",
        layout="wide"
    )

    st.markdown("""
        <style>
        .block-container { padding-top: 2rem; }
        </style>
    """, unsafe_allow_html=True)

    st.title("🛡️ Dungeon Crawl: 시즌 결산 대시보드")
    st.markdown("---")

    # 데이터 로드
    @st.cache_data
    def load_data():
        try:
            df = pd.read_csv('crawllog.csv')
            cols = ['race', 'cls', 'xl', 'god', 'killer', 'place']
            df = df[[c for c in cols if c in df.columns]]
            
            # 전처리
            if 'god' in df.columns:
                df['god'] = df['god'].fillna('No God')
            if 'killer' in df.columns:
                df['killer'] = df['killer'].fillna('Unknown')
                df = df[~df['killer'].isin(['Unknown', '알 수 없음'])]
            return df
        except Exception as e:
            return None

    df = load_data()

    if df is None:
        st.error("❌ 'crawllog.csv' 파일을 찾을 수 없습니다. 같은 폴더에 파일을 넣어주세요.")
        return

    # --- KPI 요약 ---
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("총 플레이", f"{len(df):,}회")
    k2.metric("평균 레벨", f"{df['xl'].mean():.1f} Lv")
    k3.metric("최다 픽 종족", df['race'].mode()[0])
    k4.metric("최다 사망 원인", df['killer'].value_counts().index[0])

    st.markdown("---")

    # --- 1. 종족 & 직업 (가로 막대) ---
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🧬 종족 선호도 Top 10")
        race_data = df['race'].value_counts().head(10).reset_index()
        race_data.columns = ['종족', '횟수']
        fig = px.bar(race_data, x='횟수', y='종족', orientation='h', text='횟수', color='횟수', color_continuous_scale='Teal')
        fig.update_layout(yaxis=dict(autorange="reversed"), xaxis_title="", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("⚔️ 직업 선호도 Top 10")
        cls_data = df['cls'].value_counts().head(10).reset_index()
        cls_data.columns = ['직업', '횟수']
        fig = px.bar(cls_data, x='횟수', y='직업', orientation='h', text='횟수', color='횟수', color_continuous_scale='Purples')
        fig.update_layout(yaxis=dict(autorange="reversed"), xaxis_title="", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    # --- 2. 신앙 & 레벨 (수정됨) ---
    c3, c4 = st.columns(2)
    with c3:
        st.subheader("🙏 신앙 분포 (No God 제외)")
        
        # 'No God' 제외 필터링
        god_filtered = df[df['god'] != 'No God']
        god_counts = god_filtered['god'].value_counts()
        
        # Top 9 + 기타 처리
        if len(god_counts) > 9:
            top_gods = god_counts[:9]
            others = pd.Series([god_counts[9:].sum()], index=['기타 (Others)'])
            god_counts = pd.concat([top_gods, others])
        
        god_df = god_counts.reset_index()
        god_df.columns = ['신앙', '신도 수']
        
        fig = px.pie(god_df, values='신도 수', names='신앙', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with c4:
        st.subheader("📈 사망 레벨 상세 분포 (1Lv 단위)")
        # nbins=28 (0~27레벨 커버)로 설정하여 막대 하나가 1레벨을 의미하도록 함
        fig = px.histogram(df, x='xl', nbins=28, title="사망 시점 레벨", color_discrete_sequence=['#FF7F50'])
        # X축 눈금을 1단위로 고정 (dtick=1)
        fig.update_xaxes(dtick=1, title_text='레벨 (Level)')
        fig.update_yaxes(title_text='사망자 수')
        fig.update_layout(bargap=0.2) # 막대 사이 간격 추가
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # --- 3. 사망 원인 & 장소 (장소 시각화 변경됨) ---
    c5, c6 = st.columns(2)
    with c5:
        st.subheader("💀 주요 사망 원인 Top 10")
        killer_data = df['killer'].value_counts().head(10).reset_index()
        killer_data.columns = ['사망 원인', '횟수']
        fig = px.bar(killer_data, x='횟수', y='사망 원인', orientation='h', text='횟수', color='횟수', color_continuous_scale='Reds')
        fig.update_layout(yaxis=dict(autorange="reversed"), xaxis_title="", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    with c6:
        st.subheader("🗺️ 위험 지역 비중 (Treemap)")
        # Treemap 데이터 준비
        place_counts = df['place'].value_counts().reset_index()
        place_counts.columns = ['장소', '사망 수']
        
        # 트리맵: 사각형의 크기로 비중을 보여줌
        fig = px.treemap(place_counts, path=['장소'], values='사망 수',
                         color='사망 수', color_continuous_scale='Oranges',
                         title="어디서 가장 많이 죽었을까?")
        fig.update_traces(textinfo="label+value+percent entry") # 이름+값+비율 표시
        st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# 2. 실행 로직 (안전한 자동 실행)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    is_streamlit_running = False
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        if get_script_run_ctx():
            is_streamlit_running = True
    except ImportError:
        pass

    if is_streamlit_running:
        run_dashboard()
    else:
        print("Streamlit 서버를 시작합니다... 브라우저가 자동으로 열립니다.")
        import subprocess
        cmd = [sys.executable, "-m", "streamlit", "run", __file__]
        subprocess.run(cmd)