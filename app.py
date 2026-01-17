import streamlit as st
import pandas as pd
import plotly.express as px
import sys

# -----------------------------------------------------------------------------
# 1. 메인 대시보드 설정 및 스타일
# -----------------------------------------------------------------------------
def run_dashboard():
    st.set_page_config(page_title="DCSS 시즌 결산 (Final Ver.)", page_icon="🛡️", layout="wide")

    st.markdown("""
        <style>
        .block-container { padding-top: 1rem; }
        div[data-testid="metric-container"] {
            background-color: #f0f2f6;
            border: 1px solid #d6d9df;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        @media (prefers-color-scheme: dark) {
            div[data-testid="metric-container"] {
                background-color: #262730;
                border: 1px solid #41444b;
            }
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("🛡️ Dungeon Crawl: 종합 분석 리포트")
    st.markdown("---")

    # -------------------------------------------------------------------------
    # 2. 데이터 로드 및 전처리
    # -------------------------------------------------------------------------
    @st.cache_data
    def load_data():
        try:
            df = pd.read_csv('crawllog.csv')
            
            # 1. 결측치 처리
            if 'god' in df.columns: 
                df['god'] = df['god'].fillna('No God')
            if 'killer' in df.columns: 
                df['killer'] = df['killer'].fillna('Unknown')
                
            # 2. 승리 여부 판단
            cond1 = df['ktyp'].astype(str) == 'winning'
            cond2 = df['tmsg'].astype(str).str.lower().str.contains('escaped', na=False)
            df['is_win'] = cond1 | cond2

            # 3. 드라코니언 통합
            df['race_grouped'] = df['race'].apply(lambda x: 'Draconian (All)' if 'Draconian' in str(x) else x)

            # 4. 사망 지역 표기 정리 (D만 층수 표기, 나머지는 지역명만)
            def format_place(row):
                place = row['place']
                lvl = row['lvl']
                if place == 'D' and pd.notnull(lvl):
                    return f"D:{int(lvl)}"
                return place
            
            df['formatted_place'] = df.apply(format_place, axis=1)

            # 5. 순수 사망 데이터 (분석용)
            exclude_killers = ['winning', 'quit', 'user', 'leaving', 'wizmode', 'starvation', 'Unknown', 'miscast']
            df_death = df[~df['killer'].isin(exclude_killers)].copy()

            return df, df_death
        except Exception as e:
            st.error(f"데이터 로드 중 오류 발생: {e}")
            return None, None

    df, df_death = load_data()
    if df is None: return

    # -------------------------------------------------------------------------
    # 3. 상단 핵심 지표 (Metrics)
    # -------------------------------------------------------------------------
    total_games = len(df)
    total_wins = df['is_win'].sum()
    win_rate = (total_wins / total_games) * 100
    
    top_race = df['race_grouped'].mode()[0]
    top_race_count = df['race_grouped'].value_counts().iloc[0]
    
    top_killer = df_death['killer'].mode()[0]
    top_killer_count = df_death['killer'].value_counts().iloc[0]

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("총 플레이 수", f"{total_games:,}회")
    col_m2.metric("총 클리어 (승률)", f"{total_wins:,}회", f"{win_rate:.2f}%")
    col_m3.metric("최다 픽 종족", f"{top_race}", f"{top_race_count}회 선택")
    col_m4.metric("최다 사망 원인", f"{top_killer}", f"{top_killer_count}회 발생")

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 4. 공통 차트 함수 (컬러바 숨김 & 텍스트 잘림 방지)
    # -------------------------------------------------------------------------
    def plot_bar_chart(data, x_col, y_col, title, color_scale, top_n=10):
        counts = data[y_col].value_counts(normalize=True) * 100
        top_data = counts.head(top_n).reset_index()
        top_data.columns = [y_col, x_col]
        
        fig = px.bar(top_data, x=x_col, y=y_col, orientation='h', text=x_col,
                     title=title, color=x_col, color_continuous_scale=color_scale)
        
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        
        max_val = top_data[x_col].max()
        fig.update_layout(
            yaxis=dict(autorange="reversed", title=""),
            xaxis=dict(title="비율 (%)", range=[0, max_val * 1.3]), # 여유 공간 30%
            margin=dict(r=20),
            coloraxis_showscale=False
        )
        return fig

    # -------------------------------------------------------------------------
    # 5. 선호도 분석 (Preferences)
    # -------------------------------------------------------------------------
    st.header("📊 1. 선호도 분석 (Preferences)")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.plotly_chart(plot_bar_chart(df, 'Ratio', 'race_grouped', "🧬 종족 선호도", 'Blues'), use_container_width=True)

    with c2:
        st.plotly_chart(plot_bar_chart(df, 'Ratio', 'cls', "⚔️ 직업 선호도", 'Purples'), use_container_width=True)

    with c3:
        df_god_filtered = df[df['god'] != 'No God']
        st.plotly_chart(plot_bar_chart(df_god_filtered, 'Ratio', 'god', "🙏 신앙 선호도 (무교 제외)", 'Greens'), use_container_width=True)

    # -------------------------------------------------------------------------
    # [NEW] 1.5. 종족별 신앙 선택 (Heatmap)
    # -------------------------------------------------------------------------
    st.subheader("🧩 종족별 신앙 선택 비율 (미노타우르스 제외)")
    st.caption("각 종족이 어떤 신을 주로 선택하는지 비율(%)로 보여줍니다. (표본 과다인 미노타우르스 및 무교 제외)")

    # 데이터 필터링 (미노타우르스 제외, 무교 제외)
    df_heatmap = df[(df['race'] != 'Minotaur') & (df['god'] != 'No God')]
    
    # 1. 교차표 생성 (Count)
    ct = pd.crosstab(df_heatmap['race_grouped'], df_heatmap['god'])
    
    # 2. 비율 변환 (각 종족 내에서 해당 신앙 선택 비율, row 기준 합 100%)
    ct_norm = ct.div(ct.sum(axis=1), axis=0) * 100
    
    # 3. 데이터가 너무 적은 종족 제거 (노이즈 방지, 최소 5회 이상 플레이된 종족만)
    race_counts = df_heatmap['race_grouped'].value_counts()
    valid_races = race_counts[race_counts >= 5].index
    ct_norm = ct_norm.loc[valid_races]

    # 4. 히트맵 시각화
    if not ct_norm.empty:
        fig_heat = px.imshow(ct_norm, text_auto='.0f', aspect="auto",
                             labels=dict(x="신앙", y="종족", color="비율(%)"),
                             color_continuous_scale='Viridis')
        
        fig_heat.update_layout(
            height=600, 
            coloraxis_showscale=False, # 컬러바 숨김
            xaxis_title="", 
            yaxis_title=""
        )
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info("조건에 맞는 데이터가 부족합니다.")

    # -------------------------------------------------------------------------
    # 6. 사망 분석 (Deep Dive)
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.header("💀 2. 죽음의 기록 (Death Analysis)")
    
    # 6-1. 사망 원인 및 돌연사
    col_d1, col_d2 = st.columns(2)

    with col_d1:
        st.subheader("주요 사망 원인 Top 10")
        st.plotly_chart(plot_bar_chart(df_death, 'Ratio', 'killer', "", 'Reds'), use_container_width=True)

    with col_d2:
        st.subheader("💥 돌연사(One-shot) 유발 원인")
        st.caption("사망 턴 데미지(tdam)가 최대 체력(mhp) 이상인 경우")
        
        sudden_death = df_death[df_death['tdam'] >= df_death['mhp']]
        if not sudden_death.empty:
            sd_counts = sudden_death['killer'].value_counts().head(10).reset_index()
            sd_counts.columns = ['유발 원인', '횟수']
            
            fig_sd = px.bar(sd_counts, x='횟수', y='유발 원인', orientation='h', text='횟수',
                            color='횟수', color_continuous_scale='Oranges')
            fig_sd.update_traces(textposition='outside')
            fig_sd.update_layout(
                yaxis=dict(autorange="reversed", title=""),
                xaxis=dict(title="발생 횟수", range=[0, sd_counts['횟수'].max() * 1.2]),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_sd, use_container_width=True)
        else:
            st.info("돌연사 데이터가 충분하지 않습니다.")

    # 6-2. 지역 및 레벨 분포
    col_d3, col_d4 = st.columns(2)
    
    with col_d3:
        st.subheader("📍 사망 지역 분포 (Treemap)")
        place_counts = df_death['formatted_place'].value_counts().reset_index()
        place_counts.columns = ['Place', 'Count']
        top_places = place_counts.head(40) 
        
        fig_tree = px.treemap(top_places, path=['Place'], values='Count',
                              color='Count', color_continuous_scale='Oranges')
        fig_tree.update_traces(textinfo="label+value+percent entry")
        fig_tree.update_layout(margin=dict(t=30, l=0, r=0, b=0), coloraxis_showscale=False)
        st.plotly_chart(fig_tree, use_container_width=True)

    with col_d4:
        st.subheader("📉 사망 레벨(XL) 분포")
        fig_xl = px.histogram(df_death, x="xl", nbins=27, 
                              labels={'xl': '레벨 (XL)'}, color_discrete_sequence=['#FF5733'])
        fig_xl.update_layout(bargap=0.1, xaxis_title="캐릭터 레벨", yaxis_title="사망자 수")
        st.plotly_chart(fig_xl, use_container_width=True)

    # 6-3. 층별 지배자 (테이블)
    st.subheader("👹 층별 최다 사망 원인 (Most Dangerous Mobs)")
    with st.expander("층별 데이터 열기/닫기", expanded=False):
        def get_sort_key(place_str):
            if place_str.startswith("D:"):
                return (0, int(place_str.split(":")[1]))
            elif place_str == "D": return (0, 0)
            elif "Lair" in place_str: return (1, 0)
            elif "Orc" in place_str: return (2, 0)
            elif "Elf" in place_str: return (3, 0)
            elif "Snake" in place_str: return (4, 0)
            elif "Spider" in place_str: return (5, 0)
            elif "Shoals" in place_str: return (6, 0)
            elif "Swamp" in place_str: return (7, 0)
            elif "Slime" in place_str: return (8, 0)
            elif "Vaults" in place_str: return (9, 0)
            elif "Crypt" in place_str: return (10, 0)
            elif "Depths" in place_str: return (11, 0)
            elif "Zot" in place_str: return (12, 0)
            else: return (99, 0)

        floor_killer = df_death.groupby('formatted_place')['killer'].agg(
            lambda x: x.value_counts().index[0] if len(x) > 0 else "None"
        ).reset_index()
        floor_count = df_death.groupby('formatted_place')['killer'].agg(
            lambda x: x.value_counts().iloc[0] if len(x) > 0 else 0
        ).reset_index(name='Count')
        
        result = pd.merge(floor_killer, floor_count, on='formatted_place')
        result.columns = ['장소', '최다 사망 원인', '해당 원인 사망수']
        
        result['sort_key'] = result['장소'].apply(get_sort_key)
        result = result.sort_values('sort_key').drop('sort_key', axis=1)
        
        st.dataframe(result, use_container_width=True, hide_index=True)

    # -------------------------------------------------------------------------
    # 7. 승률 분석
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.header("🏆 3. 승률 (Win Rate) Top 10")

    tab1, tab2 = st.tabs(["🧬 종족별 승률", "⚔️ 직업별 승률"])

    def plot_win_rate(group_col, title, color_scale, min_games=5):
        stats = df.groupby(group_col).agg(
            Plays=('is_win', 'count'),
            Wins=('is_win', 'sum')
        ).reset_index()
        stats['WinRate'] = (stats['Wins'] / stats['Plays']) * 100
        
        top_stats = stats[stats['Plays'] >= min_games].sort_values('WinRate', ascending=False).head(10)
        
        fig = px.bar(top_stats, x='WinRate', y=group_col, orientation='h', text='WinRate',
                     title=title, color='WinRate', color_continuous_scale=color_scale)
        
        fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        
        max_val = top_stats['WinRate'].max() if not top_stats.empty else 10
        fig.update_layout(
            yaxis=dict(autorange="reversed", title=""),
            xaxis=dict(title="승률 (%)", range=[0, max_val * 1.25]),
            margin=dict(r=20),
            coloraxis_showscale=False
        )
        return fig

    with tab1:
        st.plotly_chart(plot_win_rate('race_grouped', "종족별 승률 (최소 5판)", 'Teal'), use_container_width=True)

    with tab2:
        st.plotly_chart(plot_win_rate('cls', "직업별 승률 (최소 5판)", 'Magenta'), use_container_width=True)


if __name__ == "__main__":
    is_streamlit_running = False
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        if get_script_run_ctx(): is_streamlit_running = True
    except ImportError: pass

    if is_streamlit_running:
        run_dashboard()
    else:
        print("Streamlit 서버를 시작합니다...")
        import subprocess
        cmd = [sys.executable, "-m", "streamlit", "run", __file__]
        subprocess.run(cmd)