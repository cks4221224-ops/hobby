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
    # 2. 커스텀 CSS (가독성 개선 & 3단계 구조)
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
        
        /* [타이틀] */
        h1, h2, h3 {
            font-family: 'Cinzel', serif !important;
            color: #ff4d4d !important;
            text-shadow: 0 0 10px rgba(184, 46, 46, 0.5);
            text-align: center;
        }
        
        /* [챕터 카드] */
        .chapter-card {
            background-color: #1f2833;
            border: 2px solid #45a29e;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            height: 100%;
        }
        .chapter-card:hover {
            transform: translateY(-5px);
            border-color: #66fcf1;
            background-color: #2b3645;
            box-shadow: 0 0 20px rgba(102, 252, 241, 0.3);
        }
        
        /* [버튼 스타일] */
        div.stButton > button {
            width: 100%;
            background-color: #1f2833;
            color: #66fcf1;
            border: 1px solid #45a29e;
            font-weight: bold;
            padding: 10px;
            transition: 0.2s;
        }
        div.stButton > button:hover {
            background-color: #66fcf1;
            color: #0b0c10;
            border-color: #66fcf1;
        }
        
        /* [메트릭 박스] */
        div[data-testid="metric-container"] {
            background-color: rgba(31, 40, 51, 0.9);
            border: 1px solid #45a29e;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        label[data-testid="stMetricLabel"] {
            color: #66fcf1 !important;
        }
        div[data-testid="stMetricValue"] {
            color: #ffffff !important;
        }

        /* [몬스터 카드] */
        .mob-card {
            background-color: #1a1a1a;
            border-left: 4px solid #b82e2e;
            border-bottom: 1px solid #333;
            padding: 15px;
            border-radius: 4px;
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
        }
        </style>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 3. 데이터 로드 및 전처리
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

    def get_img_path(name):
        if not os.path.exists("assets"): return None
        filename = f"{name.lower().replace(' ', '_')}.png"
        filepath = os.path.join("assets", filename)
        if os.path.exists(filepath): return filepath
        return None

    def plot_bar_dark(data, x, y, title, color_scale):
        fig = px.bar(data, x=x, y=y, orientation='h', text=x, title=title,
                     color=x, color_continuous_scale=color_scale)
        fig.update_layout(template="plotly_dark", 
                          plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                          font=dict(color='#e0e0e0', size=14),
                          yaxis=dict(autorange="reversed", title=""),
                          xaxis=dict(title="", showticklabels=False),
                          coloraxis_showscale=False, margin=dict(r=20))
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        return fig

    # -------------------------------------------------------------------------
    # 4. 화면 라우팅
    # -------------------------------------------------------------------------
    
    # [PAGE 1] 인트로
    if st.session_state.page == 'intro':
        _, col_center, _ = st.columns([1, 8, 1])
        with col_center:
            st.markdown("<h1 style='font-size: 3.5rem;'>🩸 DUNGEON CRAWL</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='color: #a0a0a0 !important;'>The Archive of Deaths and Glory</h3>", unsafe_allow_html=True)
            st.markdown("---")
            
            main_img = get_img_path("main_banner") 
            if main_img: st.image(main_img, use_container_width=True)
            else: st.info("assets 폴더에 이미지를 추가하면 더 멋진 화면이 됩니다.")

            st.markdown("---")

            total_games = len(df)
            total_wins = df['is_win'].sum()
            win_rate = (total_wins / total_games) * 100
            top_race = df['race_grouped'].mode()[0]
            top_killer = df_death['killer'].mode()[0]

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("총 원정", f"{total_games:,}")
            m2.metric("승률", f"{win_rate:.2f}%")
            m3.metric("최다 픽", top_race)
            m4.metric("최다 사망", top_killer)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("💀 NEXT CHAPTER (챕터 선택)", type="primary"):
                st.session_state.page = 'chapter_select'
                st.rerun()
            
            st.markdown("<div style='text-align:center; margin-top:20px;'><a href='https://crawl.nemelex.cards/#lobby' style='color:#66fcf1; text-decoration:none;'>🔗 한국 DCSS 웹서버 바로가기</a></div>", unsafe_allow_html=True)

    # [PAGE 2] 챕터 선택
    elif st.session_state.page == 'chapter_select':
        st.markdown("<h1>📜 ARCHIVES</h1>", unsafe_allow_html=True)
        st.markdown("<h3>분석하고 싶은 기록을 선택하십시오</h3>", unsafe_allow_html=True)
        st.markdown("---")
        
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.markdown("""
            <div class="chapter-card">
                <h2 style="color: #66fcf1 !important;">① 선호도 분석</h2>
                <p style="color: #ccc;">어떤 종족, 직업, 신앙이<br>가장 많은 사랑을 받았는가?</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Go to Chapter 1", key="btn_c1"):
                st.session_state.page = 'analysis'
                st.session_state.selected_chapter = 'ch1'
                st.rerun()

        with c2:
            st.markdown("""
            <div class="chapter-card" style="border-color: #ff4d4d;">
                <h2 style="color: #ff4d4d !important;">② 죽음의 기록</h2>
                <p style="color: #ccc;">어디서, 누구에게, 왜 죽었는가?<br>생존을 위한 필수 지침서</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Go to Chapter 2", key="btn_c2"):
                st.session_state.page = 'analysis'
                st.session_state.selected_chapter = 'ch2'
                st.rerun()

        with c3:
            st.markdown("""
            <div class="chapter-card" style="border-color: #ffd700;">
                <h2 style="color: #ffd700 !important;">③ 승률 분석</h2>
                <p style="color: #ccc;">가장 강력한 생존 조합은?<br>승리를 부르는 선택</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Go to Chapter 3", key="btn_c3"):
                st.session_state.page = 'analysis'
                st.session_state.selected_chapter = 'ch3'
                st.rerun()

        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("⬅️ 처음으로 돌아가기"):
            st.session_state.page = 'intro'
            st.rerun()

    # [PAGE 3] 상세 분석
    elif st.session_state.page == 'analysis':
        
        col_nav1, col_nav2 = st.columns([1, 8])
        with col_nav1:
            if st.button("🔙 뒤로"):
                st.session_state.page = 'chapter_select'
                st.rerun()
        
        # ---------------------------------------------------------------------
        # 챕터 1: 선호도
        # ---------------------------------------------------------------------
        if st.session_state.selected_chapter == 'ch1':
            st.header("📊 챕터 1: 모험가들의 취향")
            
            # 상단 그래프 3개 병렬 배치
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("#### 🧬 종족 선호도")
                cnt = df['race_grouped'].value_counts(normalize=True)*100
                top = cnt.head(10).reset_index()
                top.columns = ['Race', 'Ratio']
                st.plotly_chart(plot_bar_dark(top, 'Ratio', 'Race', "", 'Blues'), use_container_width=True)
            with col2:
                st.markdown("#### ⚔️ 직업 선호도")
                cnt = df['cls'].value_counts(normalize=True)*100
                top = cnt.head(10).reset_index()
                top.columns = ['Class', 'Ratio']
                st.plotly_chart(plot_bar_dark(top, 'Ratio', 'Class', "", 'Purples'), use_container_width=True)
            with col3:
                st.markdown("#### 🙏 신앙 선호도")
                df_god = df[df['god'] != 'No God']
                cnt = df_god['god'].value_counts(normalize=True)*100
                top = cnt.head(10).reset_index()
                top.columns = ['God', 'Ratio']
                st.plotly_chart(plot_bar_dark(top, 'Ratio', 'God', "", 'Greens'), use_container_width=True)

            # 히트맵 (하단 복구)
            st.markdown("---")
            st.subheader("🧩 종족별 신앙 성향 ")
            
            df_heat = df[(df['race'] != 'Minotaur') & (df['god'] != 'No God')]
            ct = pd.crosstab(df_heat['race_grouped'], df_heat['god'])
            ct_norm = ct.div(ct.sum(axis=1), axis=0) * 100
            valid = df_heat['race_grouped'].value_counts()[df_heat['race_grouped'].value_counts() >= 5].index
            ct_norm = ct_norm.loc[valid]
            
            fig = px.imshow(ct_norm, text_auto='.0f', aspect="auto", color_continuous_scale='Viridis',
                            labels=dict(x="신앙", y="종족", color="비율(%)"))
            fig.update_layout(template="plotly_dark", height=600, coloraxis_showscale=False,
                                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

        # ---------------------------------------------------------------------
        # 챕터 2: 죽음의 기록
        # ---------------------------------------------------------------------
        elif st.session_state.selected_chapter == 'ch2':
            st.header("💀 챕터 2: 죽음의 기록")
            
            tab1, tab2 = st.tabs(["📉 통계 요약", "👹 층별 위험 몬스터 (상세)"])
            
            with tab1:
                # 1열: 사망 원인 / 돌연사
                c1, c2 = st.columns(2)
                with c1:
                    cnt = df_death['killer'].value_counts(normalize=True)*100
                    top = cnt.head(10).reset_index()
                    top.columns = ['Killer', 'Ratio']
                    st.plotly_chart(plot_bar_dark(top, 'Ratio', 'Killer', "최다 사망 원인 Top 10", 'Reds'), use_container_width=True)
                with c2:
                    sudden = df_death[df_death['tdam'] >= df_death['mhp']]
                    if not sudden.empty:
                        cnt = sudden['killer'].value_counts().head(10).reset_index()
                        cnt.columns = ['Killer', 'Count']
                        fig = px.bar(cnt, x='Count', y='Killer', orientation='h', text='Count', 
                                     title="돌연사 원인 (One-shot)", color='Count', color_continuous_scale='Oranges')
                        fig.update_layout(template="plotly_dark", coloraxis_showscale=False, 
                                          plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                          font=dict(color='#e0e0e0'), yaxis=dict(autorange="reversed"), xaxis=dict(title="횟수"))
                        st.plotly_chart(fig, use_container_width=True)

                # 2열 (누락되었던 부분 복구): 사망 지역 / 사망 레벨
                c3, c4 = st.columns(2)
                with c3:
                    st.subheader("📍 사망 지역 분포")
                    place_cnt = df_death['formatted_place'].value_counts().reset_index()
                    place_cnt.columns = ['Place', 'Count']
                    fig_tree = px.treemap(place_cnt.head(30), path=['Place'], values='Count', 
                                          color='Count', color_continuous_scale='Reds')
                    fig_tree.update_layout(template="plotly_dark", margin=dict(t=0, l=0, r=0, b=0))
                    st.plotly_chart(fig_tree, use_container_width=True)
                
                with c4:
                    st.subheader("📉 사망 레벨(XL) 분포")
                    fig_xl = px.histogram(df_death, x="xl", nbins=27, 
                                          labels={'xl': '레벨 (XL)'}, color_discrete_sequence=['#ff4d4d'])
                    fig_xl.update_layout(template="plotly_dark", bargap=0.1, 
                                         plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                         yaxis_title="사망자 수")
                    st.plotly_chart(fig_xl, use_container_width=True)

            with tab2:
                st.subheader("👹 층별 지배자 (The Lords of Floors)")
                
                zone_tabs = st.tabs(["🌱 초반 (Early)", "⚔️ 중반 (Mid)", "🔥 후반 (Late)"])
                zones = {
                    "🌱 초반 (Early)": ["D:1", "D:2", "D:3", "D:4", "D:5", "D:6", "D:7", "D:8", "D:9", "D:10", "D:11", "D:12", "D:13", "D:14", "D:15", "Temple"],
                    "⚔️ 중반 (Mid)": ["Lair", "Orc", "Snake", "Spider", "Shoals", "Swamp"],
                    "🔥 후반 (Late)": ["Vaults", "Depths", "Elf", "Crypt", "Slime", "Zot", "Hell", "Pan", "Tomb", "Abyss"]
                }

                for tab, (zone_name, places) in zip(zone_tabs, zones.items()):
                    with tab:
                        target_places = []
                        for p in places:
                            found = df_death[df_death['formatted_place'].astype(str).str.contains(p, regex=False)]['formatted_place'].unique()
                            target_places.extend(found)
                        
                        target_places = sorted(list(set(target_places)), key=lambda s: (0, int(s.split(":")[1])) if "D:" in s else (1, s))

                        if not target_places:
                            st.info("데이터 없음")
                            continue

                        for place in target_places:
                            floor_data = df_death[df_death['formatted_place'] == place]
                            if floor_data.empty: continue
                            
                            killers = floor_data['killer'].value_counts()
                            top1 = killers.index[0]
                            count1 = killers.iloc[0]
                            subs = [f"{killers.index[i]}" for i in range(1, min(3, len(killers)))]
                            sub_text = ", ".join(subs) if subs else "없음"
                            img_path = get_img_path(top1)
                            danger_idx = "🩸" if count1 < 50 else ("🩸🩸" if count1 < 100 else "💀💀💀")

                            with st.container():
                                c_img, c_info, c_stat = st.columns([1, 4, 1.5])
                                with c_img:
                                    if img_path: st.image(img_path, width=50)
                                    else: st.markdown("<div style='font-size:25px;text-align:center'>👾</div>", unsafe_allow_html=True)
                                with c_info:
                                    st.markdown(f"""
                                        <div class="mob-card">
                                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                                <div>
                                                    <span class="floor-tag">{place}</span>
                                                    <span class="killer-name">{top1}</span>
                                                    <div class="sub-killers">Beware: {sub_text}</div>
                                                </div>
                                            </div>
                                        </div>
                                    """, unsafe_allow_html=True)
                                with c_stat:
                                    st.markdown(f"""
                                        <div style="text-align:right; margin-top:5px;">
                                            <div style="font-size:1.4rem; color:#ff4d4d; font-weight:bold;">{count1} Kills</div>
                                            <div style="font-size:0.8rem; color:#888;">{danger_idx}</div>
                                        </div>
                                    """, unsafe_allow_html=True)

        # ---------------------------------------------------------------------
        # 챕터 3: 승률 분석
        # ---------------------------------------------------------------------
        elif st.session_state.selected_chapter == 'ch3':
            st.header("🏆 챕터 3: 생존의 법칙 (승률)")
            st.info("")

            def get_win_stats(col):
                s = df.groupby(col).agg(Plays=('is_win','count'), Wins=('is_win','sum')).reset_index()
                s['WinRate'] = (s['Wins']/s['Plays'])*100
                return s[s['Plays']>=5].sort_values('WinRate', ascending=False).head(10)

            t1, t2, t3 = st.tabs(["🧬 종족별", "⚔️ 직업별", "🙏 신앙별"])
            
            with t1:
                st.plotly_chart(plot_bar_dark(get_win_stats('race_grouped'), 'WinRate', 'race_grouped', "", 'Teal'), use_container_width=True)
            with t2:
                st.plotly_chart(plot_bar_dark(get_win_stats('cls'), 'WinRate', 'cls', "", 'Magenta'), use_container_width=True)
            with t3:
                df_god_only = df[df['god'] != 'No God']
                s = df_god_only.groupby('god').agg(Plays=('is_win','count'), Wins=('is_win','sum')).reset_index()
                s['WinRate'] = (s['Wins']/s['Plays'])*100
                data = s[s['Plays']>=5].sort_values('WinRate', ascending=False).head(10)
                st.plotly_chart(plot_bar_dark(data, 'WinRate', 'god', "", 'YlOrBr'), use_container_width=True)

if __name__ == "__main__":
    run_dashboard()