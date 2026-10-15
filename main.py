import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 제목 구성
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="동네별 인구 피라미드",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide"
)

# 따뜻하고 친근한 분위기를 위한 대시보드 헤더
st.title("🏡 동네별 인구 피라미드")
st.caption("우리 동네의 최신 연도 연령별·성별 인구 구조를 확인해 보세요.")

# -----------------------------------------------------------------------------
# 2. 데이터 불러오기 (캐싱 적용)
# -----------------------------------------------------------------------------
# st.cache_data를 사용하면 데이터를 매번 다시 다운로드하지 않고 메모리에 보관하여 앱 속도가 향상됩니다.
@st.cache_data
def load_population_data():
    url = "https://raw.githubusercontent.com/joon7810/bp/main/population_ts_yearly_gender.zip"
    # pandas는 zip 압축 파일의 URL을 직접 읽어서 CSV 데이터를 파싱할 수 있습니다.
    df = pd.read_csv(url)
    return df

with st.spinner("최신 인구 데이터를 불러오는 중입니다..."):
    df_raw = load_population_data()

# -----------------------------------------------------------------------------
# 3. 최신 연도 데이터 추출
# -----------------------------------------------------------------------------
# 데이터셋에 포함된 연도 중 가장 최신 연도를 자동으로 파악하여 필터링합니다.
latest_year = int(df_raw['연도'].max())
df_latest = df_raw[df_raw['연도'] == latest_year].copy()

st.info(f"💡 현재 화면은 가장 최신 연도인 **{latest_year}년** 기준 인구 데이터입니다.")

# -----------------------------------------------------------------------------
# 4. 시도 ➔ 시군구 ➔ 동 드롭다운 선택 (연쇄 필터링)
# -----------------------------------------------------------------------------
# 화면 상단에 3개의 컬럼을 생성하여 드롭다운을 나란히 배치합니다.
col_sido, col_sigungu, col_dong = st.columns(3)

# 1) 시/도 선택
with col_sido:
    sido_options = sorted(df_latest['시도'].dropna().unique())
    selected_sido = st.selectbox("1️⃣ 시/도 선택", sido_options)

# 2) 시/군/구 선택 (선택한 시/도에 속한 지역만 추출)
with col_sigungu:
    sigungu_options = sorted(
        df_latest[df_latest['시도'] == selected_sido]['시군구'].dropna().unique()
    )
    selected_sigungu = st.selectbox("2️⃣ 시/군/구 선택", sigungu_options)

# 3) 읍/면/동 선택 (선택한 시/도 및 시/군/구에 속한 동네만 추출)
with col_dong:
    dong_options = sorted(
        df_latest[
            (df_latest['시도'] == selected_sido) & 
            (df_latest['시군구'] == selected_sigungu)
        ]['동'].dropna().unique()
    )
    selected_dong = st.selectbox("3️⃣ 읍/면/동 선택", dong_options)

# -----------------------------------------------------------------------------
# 5. 선택된 동네 데이터 전처리 및 나이 라벨 생성
# -----------------------------------------------------------------------------
# 0세부터 99세, 그리고 100세 이상 순서대로 나이 라벨 리스트를 만듭니다.
age_categories = [f"{i}세" for i in range(100)] + ["100세 이상"]

# 데이터프레임의 열 이름과 일치하도록 '남_0세', '여_0세' 형태의 칼럼 목록 생성
male_cols = [f"남_{age}" for age in age_categories]
female_cols = [f"여_{age}" for age in age_categories]

# 사용자가 선택한 동네 1행 추출
target_row = df_latest[
    (df_latest['시도'] == selected_sido) & 
    (df_latest['시군구'] == selected_sigungu) & 
    (df_latest['동'] == selected_dong)
]

if not target_row.empty:
    row_data = target_row.iloc[0]
    
    # 남성 및 여성 나이별 인구 수 추출
    male_values = [int(row_data.get(col, 0)) for col in male_cols]
    female_values = [int(row_data.get(col, 0)) for col in female_cols]

    # 인구 피라미드 작성을 위해 남성 데이터는 음수(-)로 변환하여 왼쪽에 배치합니다.
    male_values_neg = [-val for val in male_values]

    # 총인구 요약 카드 정보
    total_male = sum(male_values)
    total_female = sum(female_values)
    total_population = total_male + total_female

    # -------------------------------------------------------------------------
    # 6. 상단 요약지표(Metric) 표시
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader(f"📍 {selected_sido} {selected_sigungu} {selected_dong} 현황")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("총인구수", f"{total_population:,} 명")
    m2.metric("남성 인구", f"{total_male:,} 명")
    m3.metric("여성 인구", f"{total_female:,} 명")

    # -------------------------------------------------------------------------
    # 7. Plotly 인구 피라미드 막대그래프 생성
    # -------------------------------------------------------------------------
    fig = go.Figure()

    # 따뜻하고 편안한 톤의 색상 (남성: 딥 블루/소프트 인디고, 여성: 따뜻한 코랄 핑크)
    color_male = "#4A7BB0"
    color_female = "#E86F68"

    # 남성 막대 그래프 (왼쪽)
    fig.add_trace(go.Bar(
        y=age_categories,
        x=male_values_neg,
        name="남성",
        orientation="h",
        marker_color=color_male,
        customdata=male_values,  # 툴팁에 양수 인구수를 보여주기 위한 실제 값
        hovertemplate="<b>%{y}</b> 남성: %{customdata:,}명<extra></extra>"
    ))

    # 여성 막대 그래프 (오른쪽)
    fig.add_trace(go.Bar(
        y=age_categories,
        x=female_values,
        name="여성",
        orientation="h",
        marker_color=color_female,
        customdata=female_values,
        hovertemplate="<b>%{y}</b> 여성: %{customdata:,}명<extra></extra>"
    ))

    # X축 눈금을 좌우 대칭 형태의 양수로 보기 좋게 표시하기 위한 설정
    max_val = max(max(male_values, default=1), max(female_values, default=1))
    step = max(1, max_val // 4)
    tick_vals = list(range(-step * 4, step * 5, step))
    tick_texts = [f"{abs(val):,}" for val in tick_vals]

    # 그래프 레이아웃 및 축 설정
    fig.update_layout(
        title=dict(
            text=f"<b>{selected_dong}</b> 연령별 인구 피라미드 ({latest_year}년)",
            font=dict(size=18)
        ),
        barmode="overlay",  # 두 성별 막대가 중앙선 기준으로 겹쳐지지 않고 좌우 배치
        bargap=0.1,
        xaxis=dict(
            title="인구 수 (명)",
            tickvals=tick_vals,
            ticktext=tick_texts,
            range=[-max_val * 1.1, max_val * 1.1]
        ),
        yaxis=dict(
            title="나이",
            type="category",
            # [핵심 요구사항] 세로축 순서 고정:
            # categoryorder='array' 옵션과 함께 categoryarray에 ['0세', '1세', ..., '100세 이상'] 순서대로 넣어주면
            # Plotly 기본 동작에 의해 배열의 첫 번째('0세')가 맨 아래에, 마지막('100세 이상')이 맨 위 눈금에 고정됩니다.
            categoryorder="array",
            categoryarray=age_categories
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=800,
        margin=dict(l=60, r=40, t=80, b=50),
        template="plotly_white"
    )

    # 시각화 그래프 차트 출력
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("선택하신 동네의 인구 데이터가 존재하지 않습니다.")
