import streamlit as st
import pandas as pd
import plotly.express as px
import os

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 상태 관리
# -----------------------------------------------------------------------------
def run_dashboard():
    st.set_page_config(page_title="DCSS: 죽음의 기록", page_icon="🩸", layout="wide")
    
    # 상태 초기화
    if 'page' not in st.session_state:
        st.session_state.page = 'intro'
    if 'selected_chapter' not in st.session_state:
        st.session_state.selected_chapter = None

    # -------------------------------------------------------------------------
    # 2. 커스텀 CSS (심미성 및 가독성 강화)
    # -------------------------------------------------------------------------
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Roboto:wght@300;400;700&display=swap');
        
        /* [전체 테마] */
        .stApp {
            background-color: #0b0c10;
            color: #e0e0e0;
            font-family: 'Roboto', sans-serif;
        }
        
        /* [헤더 폰트] */
        h1, h2, h3 {
            font-family: 'Cinzel', serif !important;
            color: #ff4d4d !important;
            text-shadow: 0 0 10px rgba(184, 46, 46, 0.5);
            text-align: center;
        }
        
        /* [버튼 스타일링] */
        div.stButton > button {
            background-color: #1f2833;
            color: #66fcf1;
            border: 2px solid #45a29e;
            font-weight: bold;
            font-size: 1.1rem;
            padding: 12px 0px;
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        div.stButton > button:hover {
            background-color: #66fcf1;
            color: #0b0c10;
            border-color: #66fcf1;
            box-shadow: 0 0 20px rgba(102, 252, 241, 0.6);
            transform: translateY(-2px);
        }

        /* [Metric 스타일링 (통계 요약)] */
        div[data-testid="stMetric"] {
            background-color: #1a1a1a;
            border: 1px solid #333;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        div[data-testid="stMetricLabel"] {
            color: #a0a0a0 !important;
            font-size: 0.9rem !important;
        }
        div[data-testid="stMetricValue"] {
            color: #ff4d4d !important;
            font-family: 'Cinzel', serif;
            font-size: 1.8rem !important;
        }

        /* [이미지 컨테이너] */
        div[data-testid="stImage"] {
            display: flex;
            justify-content: center;
        }
        div[data-testid="stImage"] > img {
            border-radius: 10px;
            border: 2px solid #333;
        }

        /* [카드 스타일] */
        .chapter-desc {
            text-align: center; 
            color: #ccc; 
            font-size: 0.9rem; 
            margin-bottom: 15px;
            min-height: 50px;
        }
        .mob-card {
            background-color: #1a1a1a;
            border-left: 4px solid #b82e2e;
            border-bottom: 1px solid #333;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 10px;
        }
        .floor-tag {
            font-family: 'Cinzel', serif;
            font-weight: bold;
            color: #66fcf1;
            font-size: 1.2rem;
            margin-right: 10px;
        }
        .killer-name {
            font-size: 1.3rem;
            color: #ffcccc;
            font-weight: bold;
        }
        .sub-killers {
            font-size: 0.9rem;
            color: #a0a0a0;
            margin-top: 4px;
        }
        </style>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 3. 데이터 및 에셋 로드
    # -------------------------------------------------------------------------
    @st.cache_data
    def load_data():
        try:
            if not os.path.exists('crawllog.csv'): return None, None
            df = pd.read_csv('crawllog.csv')
            
            if 'god' in df.columns: df['god'] = df['god'].fillna('No God')
            if 'killer' in df.columns: df['killer'] = df['killer'].fillna('Unknown')
            
            cond1 = df['ktyp'].astype(str) == 'winning'
            cond2 = df['tmsg'].astype(str).str.lower().str.contains('escaped', na=False)
            df['is_win'] = cond1 | cond2
            
            df['race_grouped'] = df['race'].apply(lambda x: 'Draconian' if 'Draconian' in str(x) else x)

            def format_place(row):
                place = row['place']
                lvl = row['lvl']
                if place == 'D' and pd.notnull(lvl): return f"D:{int(lvl)}"
                return str(place)
            df['formatted_place'] = df.apply(format_place, axis=1)
            
            exclude = ['winning', 'quit', 'user', 'leaving', 'wizmode', 'starvation', 'Unknown', 'miscast']
            df_death = df[~df['killer'].isin(exclude)].copy()
            
            return df, df_death
        except: return None, None

    df, df_death = load_data()
    
    if df is None:
        st.error("❌ 'crawllog.csv' 파일이 없습니다.")
        return

    # 이미지 로드 함수
    def get_img_path(name):
        if os.path.exists("assets"):
            filename = f"{str(name).lower().replace(' ', '_')}.png"
            filepath = os.path.join("assets", filename)
            if os.path.exists(filepath): return filepath
        if "minotaur" in str(name).lower():
            return "https://raw.githubusercontent.com/crawl/crawl/master/crawl-ref/source/rltiles/mon/minotaur.png"
        return "https://raw.githubusercontent.com/crawl/crawl/master/crawl-ref/source/rltiles/mon/demon_spawn.png"

    # [UX 개선] Plotly 차트 설정 함수 (Modebar 제거 및 깔끔한 툴팁)
    def plot_bar_dark(data, x, y, title_text, color_scale):
        fig = px.bar(data, x=x, y=y, orientation='h', text=x, 
                     color=x, color_continuous_scale=color_scale)
        fig.update_layout(
            template="plotly_dark", 
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#ffffff', size=14),
            title=dict(text=title_text, font=dict(color='#ff4d4d', size=18)),
            yaxis=dict(autorange="reversed", title="", tickfont=dict(color='#e0e0e0')),
            xaxis=dict(title="", showticklabels=False),
            coloraxis_showscale=False, 
            margin=dict(r=20, t=30 if title_text else 0),
            hovermode="y unified" # [추가] 툴팁 가독성 향상
        )
        fig.update_traces(
            texttemplate='%{text:.1f}%', 
            textposition='outside', 
            textfont=dict(color='white'),
            hovertemplate='%{y}: %{x:.1f}%<extra></extra>' # [추가] 깔끔한 호버 텍스트
        )
        return fig

    # -------------------------------------------------------------------------
    # 4. 화면 라우팅
    # -------------------------------------------------------------------------
    
    # [PAGE 1] 인트로
    if st.session_state.page == 'intro':
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h1 style='font-size: 3.5rem;'>🩸 DUNGEON CRAWL</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #a0a0a0 !important;'>The Archive of Deaths and Glory</h3>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        col_l, col_c, col_r = st.columns([1, 0.8, 1]) 
        
        with col_c:
            banner_path = os.path.join("assets", "main_banner.png")
            if os.path.exists(banner_path):
                st.image(banner_path, use_container_width=True)
            else:
                 st.image(get_img_path("minotaur"), width=200)

            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("- 다음장 -", use_container_width=True): # 버튼 텍스트 영문으로 변경 (통일감)
                st.session_state.page = 'chapter_select'
                st.rerun()
            
            st.markdown("<div style='text-align:center; margin-top:20px;'><a href='https://crawl.nemelex.cards/#lobby' style='color:#66fcf1; text-decoration:none; font-size:0.8rem;'>🔗 Play DCSS Online</a></div>", unsafe_allow_html=True)

    # [PAGE 2] 챕터 선택
    elif st.session_state.page == 'chapter_select':
        st.markdown("<h1>📜 ARCHIVES</h1>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.markdown("<h3 style='color: #66fcf1 !important;'>선호도 분석</h3>", unsafe_allow_html=True)
            st.markdown("<div class='chapter-desc'>어떤 종족, 직업, 신앙이<br>가장 많은 사랑을 받았는가?</div>", unsafe_allow_html=True)
            if st.button("선호도 분석 확인", key="btn_c1", use_container_width=True):
                st.session_state.page = 'analysis'
                st.session_state.selected_chapter = 'ch1'
                st.rerun()

        with c2:
            st.markdown("<h3 style='color: #ff4d4d !important;'>죽음의 기록</h3>", unsafe_allow_html=True)
            st.markdown("<div class='chapter-desc'>생존을 위한 필수 지침서<br>주요 사망 원인과 위험 지역</div>", unsafe_allow_html=True)
            if st.button("죽음의 기록 확인", key="btn_c2", use_container_width=True):
                st.session_state.page = 'analysis'
                st.session_state.selected_chapter = 'ch2'
                st.rerun()

        with c3:
            st.markdown("<h3 style='color: #ffd700 !important;'>메타 빌드 분석</h3>", unsafe_allow_html=True)
            st.markdown("<div class='chapter-desc'>가장 강력한 생존 조합<br>승리를 부르는 선택</div>", unsafe_allow_html=True)
            if st.button("메타 빌드 확인", key="btn_c3", use_container_width=True):
                st.session_state.page = 'analysis'
                st.session_state.selected_chapter = 'ch3'
                st.rerun()

        st.markdown("<br><br>", unsafe_allow_html=True)
        
        _, c_back, _ = st.columns([1.5, 1, 1.5])
        with c_back:
            if st.button("⬅️ 처음으로 돌아가기", use_container_width=True):
                st.session_state.page = 'intro'
                st.rerun()

    # [PAGE 3] 상세 분석
    elif st.session_state.page == 'analysis':
        
        # 상단 네비게이션바 (간격 조정)
        col_nav1, col_nav2 = st.columns([1, 8])
        with col_nav1:
            if st.button("🔙 목록", use_container_width=True):
                st.session_state.page = 'chapter_select'
                st.rerun()
        
        # ---------------------------------------------------------------------
        # Ch1: 선호도 분석 (Insight-First 적용)
        # ---------------------------------------------------------------------
        if st.session_state.selected_chapter == 'ch1':
            st.header("📊 선호도 분석")
            
            # [UX 개선] 핵심 지표(Metrics) 상단 노출
            m1, m2, m3 = st.columns(3)
            with m1: st.metric("가장 사랑받는 종족", df['race_grouped'].mode()[0])
            with m2: st.metric("가장 사랑받는 직업", df['cls'].mode()[0])
            with m3: st.metric("가장 사랑받는 신", df[df['god']!='No God']['god'].mode()[0])
            st.markdown("---")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("#### 🧬 종족 Top 10")
                cnt = df['race_grouped'].value_counts(normalize=True)*100
                top = cnt.head(10).reset_index()
                top.columns = ['Race', 'Ratio']
                # config={'displayModeBar': False} 추가로 차트 깔끔하게
                st.plotly_chart(plot_bar_dark(top, 'Ratio', 'Race', "", 'Blues'), use_container_width=True, config={'displayModeBar': False})
            with col2:
                st.markdown("#### ⚔️ 직업 Top 10")
                cnt = df['cls'].value_counts(normalize=True)*100
                top = cnt.head(10).reset_index()
                top.columns = ['Class', 'Ratio']
                st.plotly_chart(plot_bar_dark(top, 'Ratio', 'Class', "", 'Purples'), use_container_width=True, config={'displayModeBar': False})
            with col3:
                st.markdown("#### 🙏 신앙 Top 10")
                df_god = df[df['god'] != 'No God']
                cnt = df_god['god'].value_counts(normalize=True)*100
                top = cnt.head(10).reset_index()
                top.columns = ['God', 'Ratio']
                st.plotly_chart(plot_bar_dark(top, 'Ratio', 'God', "", 'Greens'), use_container_width=True, config={'displayModeBar': False})

            st.markdown("---")
            st.subheader("🧩 종족별 신앙 선택")
            df_heat = df[(df['race'] != 'Minotaur') & (df['god'] != 'No God')]
            ct = pd.crosstab(df_heat['race_grouped'], df_heat['god'])
            ct_norm = ct.div(ct.sum(axis=1), axis=0) * 100
            valid = df_heat['race_grouped'].value_counts()[df_heat['race_grouped'].value_counts() >= 5].index
            ct_norm = ct_norm.loc[valid]
            fig = px.imshow(ct_norm, text_auto='.0f', aspect="auto", color_continuous_scale='Viridis',
                            labels=dict(x="신앙", y="종족", color="비율(%)"))
            fig.update_layout(template="plotly_dark", height=600, coloraxis_showscale=False,
                              plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        # ---------------------------------------------------------------------
        # Ch2: 죽음의 기록 (Insight-First 적용)
        # ---------------------------------------------------------------------
        elif st.session_state.selected_chapter == 'ch2':
            st.header("💀 죽음의 기록")
            
            # [UX 개선] 사망 관련 핵심 지표
            m1, m2, m3 = st.columns(3)
            with m1: st.metric("총 사망 기록", f"{len(df_death):,} 회")
            with m2: st.metric("최대 사망 원인", df_death['killer'].mode()[0])
            with m3: st.metric("가장 위험한 층", df_death['formatted_place'].mode()[0])
            st.markdown("---")

            tab1, tab2 = st.tabs(["📉 통계 요약", "👹 층별 위험 몬스터"])
            with tab1:
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("#### 🩸 최다 사망 원인")
                    cnt = df_death['killer'].value_counts(normalize=True)*100
                    top = cnt.head(10).reset_index()
                    top.columns = ['Killer', 'Ratio']
                    st.plotly_chart(plot_bar_dark(top, 'Ratio', 'Killer', "", 'Reds'), use_container_width=True, config={'displayModeBar': False})
                with c2:
                    st.markdown("#### ⚡ 돌연사 (One-shot)")
                    sudden = df_death[df_death['tdam'] >= df_death['mhp']]
                    if not sudden.empty:
                        cnt = sudden['killer'].value_counts().head(10).reset_index()
                        cnt.columns = ['Killer', 'Count']
                        fig = px.bar(cnt, x='Count', y='Killer', orientation='h', text='Count', 
                                     color='Count', color_continuous_scale='Oranges')
                        fig.update_layout(template="plotly_dark", coloraxis_showscale=False, 
                                          plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                          font=dict(color='#ffffff', size=14), yaxis=dict(autorange="reversed"), xaxis=dict(title="횟수"))
                        fig.update_traces(texttemplate='%{text}회', textposition='outside', textfont=dict(color='white'))
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

                c3, c4 = st.columns(2)
                with c3:
                    st.subheader("📍 사망 지역 분포")
                    place_cnt = df_death['formatted_place'].value_counts().reset_index()
                    place_cnt.columns = ['Place', 'Count']
                    fig_tree = px.treemap(place_cnt.head(30), path=['Place'], values='Count', color='Count', color_continuous_scale='Reds')
                    fig_tree.update_layout(template="plotly_dark", margin=dict(t=0, l=0, r=0, b=0), font=dict(color='white'))
                    st.plotly_chart(fig_tree, use_container_width=True, config={'displayModeBar': False})
                with c4:
                    st.subheader("📉 사망 레벨(XL) 분포")
                    fig_xl = px.histogram(df_death, x="xl", nbins=27, labels={'xl': '레벨 (XL)'}, color_discrete_sequence=['#ff4d4d'])
                    fig_xl.update_layout(template="plotly_dark", bargap=0.1, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'), yaxis_title="사망자 수")
                    st.plotly_chart(fig_xl, use_container_width=True, config={'displayModeBar': False})

            with tab2:
                st.subheader("👹 층별 지배자")
                zone_tabs = st.tabs(["🌱 초반", "⚔️ 중반", "🔥 후반"])
                zones = {"🌱 초반": ["D:1", "D:2", "D:3", "D:4", "D:5", "D:6", "D:7", "D:8", "D:9", "D:10", "D:11", "D:12", "D:13", "D:14", "D:15", "Temple"], "⚔️ 중반": ["Lair", "Orc", "Snake", "Spider", "Shoals", "Swamp"], "🔥 후반": ["Vaults", "Depths", "Elf", "Crypt", "Slime", "Zot", "Hell", "Pan", "Tomb", "Abyss"]}
                for tab, (zone_name, places) in zip(zone_tabs, zones.items()):
                    with tab:
                        target_places = []
                        for p in places:
                            found = df_death[df_death['formatted_place'].astype(str).str.contains(p, regex=False)]['formatted_place'].unique()
                            target_places.extend(found)
                        target_places = sorted(list(set(target_places)), key=lambda s: (0, int(s.split(":")[1])) if "D:" in s else (1, s))
                        if not target_places: st.info("데이터 없음"); continue

                        for place in target_places:
                            floor_data = df_death[df_death['formatted_place'] == place]
                            if floor_data.empty: continue
                            killers = floor_data['killer'].value_counts()
                            top1 = killers.index[0]
                            count1 = killers.iloc[0]
                            subs = [f"{killers.index[i]}" for i in range(1, min(3, len(killers)))]
                            sub_text = ", ".join(subs) if subs else "없음"
                            danger_idx = "🩸" if count1 < 20 else ("🩸🩸" if count1 < 50 else "💀💀💀")
                            
                            with st.container():
                                c_info, c_stat = st.columns([5.5, 1.5])
                                with c_info: st.markdown(f"<div class='mob-card'><div><span class='floor-tag'>{place}</span><span class='killer-name'>{top1}</span><div class='sub-killers'>Beware: {sub_text}</div></div></div>", unsafe_allow_html=True)
                                with c_stat: st.markdown(f"<div style='text-align:right; margin-top:10px;'><div style='font-size:1.4rem; color:#ff4d4d; font-weight:bold;'>{count1} Kills</div><div style='font-size:0.8rem; color:#888;'>{danger_idx}</div></div>", unsafe_allow_html=True)

        # ---------------------------------------------------------------------
        # Ch3: 메타 빌드 분석 (Insight-First 적용)
        # ---------------------------------------------------------------------
        elif st.session_state.selected_chapter == 'ch3':
            st.header("🏆 메타 빌드 분석")
            st.info("썩은물들의 기록이 반영된 데이터입니다. 승률은 성능을 보장하지 않습니다.")

            def get_win_stats(col):
                s = df.groupby(col).agg(Plays=('is_win','count'), Wins=('is_win','sum')).reset_index()
                s['WinRate'] = (s['Wins']/s['Plays'])*100
                return s[s['Plays']>=5].sort_values('WinRate', ascending=False).head(10)
            
            # [UX 개선] 승률 데이터 미리 계산
            race_win = get_win_stats('race_grouped')
            best_race = race_win.iloc[0]['race_grouped'] if not race_win.empty else "-"
            best_rate = race_win.iloc[0]['WinRate'] if not race_win.empty else 0

            # 상단 메트릭 표시
            m1, m2 = st.columns(2)
            with m1: st.metric("최고 승률 종족", best_race)
            with m2: st.metric("해당 승률", f"{best_rate:.1f}%")
            st.markdown("---")

            t1, t2, t3 = st.tabs(["🧬 종족", "⚔️ 직업", "🙏 신앙"])
            with t1: st.plotly_chart(plot_bar_dark(race_win, 'WinRate', 'race_grouped', "", 'Teal'), use_container_width=True, config={'displayModeBar': False})
            with t2: st.plotly_chart(plot_bar_dark(get_win_stats('cls'), 'WinRate', 'cls', "", 'Magenta'), use_container_width=True, config={'displayModeBar': False})
            with t3:
                df_god_only = df[df['god'] != 'No God']
                s = df_god_only.groupby('god').agg(Plays=('is_win','count'), Wins=('is_win','sum')).reset_index()
                s['WinRate'] = (s['Wins']/s['Plays'])*100
                data = s[s['Plays']>=5].sort_values('WinRate', ascending=False).head(10)
                st.plotly_chart(plot_bar_dark(data, 'WinRate', 'god', "", 'YlOrBr'), use_container_width=True, config={'displayModeBar': False})

if __name__ == "__main__":
    run_dashboard()