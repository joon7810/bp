
# main.py
# 동네별 인구 피라미드
# 초보자도 이해하기 쉽도록 한국어 주석을 달았습니다.

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go


# --------------------------------------------------
# 1. 페이지 설정
# --------------------------------------------------
st.set_page_config(
    page_title="동네별 인구 피라미드",
    page_icon="🏘️",
    layout="wide",
)

# 따뜻한 색감의 화면 스타일
st.markdown(
    """
    <style>
    .stApp {
        background-color: #FFF9F2;
    }
    h1, h2, h3 {
        color: #70452E;
    }
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #F0DCC9;
        border-radius: 12px;
        padding: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🏘️ 동네별 인구 피라미드")
st.markdown(
    "우리 동네의 연령별 인구를 살펴보세요. "
    "남성은 왼쪽, 여성은 오른쪽에 표시됩니다."
)


# --------------------------------------------------
# 2. 데이터 불러오기
# --------------------------------------------------
DATA_URL = (
    "https://raw.githubusercontent.com/joon7810/bp/main/"
    "population_ts_yearly_gender.zip"
)

# 0세부터 100세 이상까지 총 101개 연령대
AGES = [f"{age}세" for age in range(101)]
AGES[-1] = "100세 이상"

# CSV에서 실제로 사용할 인구 열 이름을 만듭니다.
MALE_COLS = [
    f"남_{age}세" for age in range(100)
] + ["남_100세 이상"]

FEMALE_COLS = [
    f"여_{age}세" for age in range(100)
] + ["여_100세 이상"]

POPULATION_COLS = MALE_COLS + FEMALE_COLS


@st.cache_data(show_spinner="인구 데이터를 불러오는 중입니다...")
def load_data():
    """압축 CSV를 읽고 가장 최신 연도 자료만 반환합니다."""

    # pandas는 URL의 ZIP 압축 CSV도 직접 읽을 수 있습니다.
    df = pd.read_csv(DATA_URL, compression="zip")

    # 열 이름에 혹시 포함된 앞뒤 공백을 제거합니다.
    df.columns = df.columns.astype(str).str.strip()

    # 필수 열이 실제로 존재하는지 확인합니다.
    required_cols = ["연도", "시도", "시군구", "동"]
    missing_cols = [
        col for col in required_cols if col not in df.columns
    ]

    if missing_cols:
        raise ValueError(
            f"필수 열이 없습니다: {', '.join(missing_cols)}"
        )

    # 연도를 숫자로 변환합니다.
    df["연도"] = pd.to_numeric(df["연도"], errors="coerce")
    df = df.dropna(subset=["연도"]).copy()
    df["연도"] = df["연도"].astype(int)

    # 2015~2026년 중 데이터에 실제 존재하는 가장 최신 연도를 선택합니다.
    df = df[df["연도"].between(2015, 2026)].copy()

    if df.empty:
        raise ValueError("2015~2026년 인구 데이터가 없습니다.")

    latest_year = int(df["연도"].max())
    df = df[df["연도"] == latest_year].copy()

    # 나이별 남녀 인구 열이 빠져 있다면 오류를 알립니다.
    missing_population_cols = [
        col for col in POPULATION_COLS if col not in df.columns
    ]

    if missing_population_cols:
        preview = ", ".join(missing_population_cols[:5])
        raise ValueError(
            "인구 열을 찾을 수 없습니다. "
            f"누락된 열 예시: {preview}"
        )

    # 인구 열을 숫자로 변환합니다.
    # 숫자가 아닌 값은 결측치로 처리합니다.
    for col in POPULATION_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # 지역 이름의 앞뒤 공백을 제거합니다.
    for col in ["시도", "시군구", "동"]:
        df[col] = df[col].fillna("").astype(str).str.strip()

    # 빈 지역 이름이 포함된 행은 제외합니다.
    df = df[
        (df["시도"] != "")
        & (df["시군구"] != "")
        & (df["동"] != "")
    ].copy()

    return df, latest_year


# --------------------------------------------------
# 3. 데이터 로딩 오류 처리
# --------------------------------------------------
try:
    df, latest_year = load_data()
except Exception as e:
    st.error("인구 데이터를 불러오지 못했습니다.")
    st.exception(e)
    st.stop()


st.caption(
    f"📅 데이터 기준 연도: {latest_year}년 "
    "| 데이터에 실제 존재하는 최신 연도를 자동 선택합니다."
)


# --------------------------------------------------
# 4. 시도 → 시군구 → 동 드롭다운
# --------------------------------------------------
st.subheader("📍 지역 선택")

col1, col2, col3 = st.columns(3)

# 첫 번째 드롭다운: 시도
sido_list = sorted(df["시도"].unique().tolist())

with col1:
    selected_sido = st.selectbox(
        "① 시도",
        options=sido_list,
        key="selected_sido",
    )

# 선택한 시도에 속하는 시군구만 표시합니다.
sigungu_df = df[df["시도"] == selected_sido]
sigungu_list = sorted(sigungu_df["시군구"].unique().tolist())

with col2:
    selected_sigungu = st.selectbox(
        "② 시군구",
        options=sigungu_list,
        key="selected_sigungu",
    )

# 선택한 시도와 시군구에 속하는 동만 표시합니다.
dong_df = sigungu_df[
    sigungu_df["시군구"] == selected_sigungu
]
dong_list = sorted(dong_df["동"].unique().tolist())

with col3:
    selected_dong = st.selectbox(
        "③ 읍·면·동",
        options=dong_list,
        key="selected_dong",
    )


# --------------------------------------------------
# 5. 선택한 동네의 인구 데이터 추출
# --------------------------------------------------
selected_df = df[
    (df["시도"] == selected_sido)
    & (df["시군구"] == selected_sigungu)
    & (df["동"] == selected_dong)
]

if selected_df.empty:
    st.warning("선택한 지역의 인구 데이터가 없습니다.")
    st.stop()

# 같은 지역에 여러 행이 존재할 가능성에 대비해
# 나이별 인구를 합산합니다.
male_population = (
    selected_df[MALE_COLS].sum(axis=0).to_numpy(dtype=float)
)
female_population = (
    selected_df[FEMALE_COLS].sum(axis=0).to_numpy(dtype=float)
)

# 남성은 왼쪽에 표시하기 위해 음수로 변환합니다.
male_negative = -male_population

# 전체 인구 및 성별 인구를 계산합니다.
male_total = int(male_population.sum())
female_total = int(female_population.sum())
total_population = male_total + female_total


# --------------------------------------------------
# 6. 요약 정보
# --------------------------------------------------
st.subheader(
    f"📊 {selected_sido} {selected_sigungu} {selected_dong}"
)

metric1, metric2, metric3 = st.columns(3)

metric1.metric("전체 인구", f"{total_population:,}명")
metric2.metric("남성 인구", f"{male_total:,}명")
metric3.metric("여성 인구", f"{female_total:,}명")


# --------------------------------------------------
# 7. 인구 피라미드 가로 막대그래프
# --------------------------------------------------
fig = go.Figure()

# 남성: 음수 값이므로 0을 기준으로 왼쪽으로 뻗습니다.
fig.add_trace(
    go.Bar(
        x=male_negative,
        y=AGES,
        name="남성",
        orientation="h",
        marker_color="#6F91C8",
        customdata=male_population,
        hovertemplate=(
            "나이: %{y}<br>"
            "남성 인구: %{customdata:,.0f}명"
            "<extra></extra>"
        ),
    )
)

# 여성: 양수 값이므로 0을 기준으로 오른쪽으로 뻗습니다.
fig.add_trace(
    go.Bar(
        x=female_population,
        y=AGES,
        name="여성",
        orientation="h",
        marker_color="#E9A08B",
        customdata=female_population,
        hovertemplate=(
            "나이: %{y}<br>"
            "여성 인구: %{customdata:,.0f}명"
            "<extra></extra>"
        ),
    )
)

# 좌우 인구 규모가 서로 비교되도록 대칭 축 범위를 설정합니다.
max_population = max(
    float(male_population.max()),
    float(female_population.max()),
    1.0,
)

# 보기 좋도록 최대값을 약간 여유 있게 설정합니다.
axis_limit = max_population * 1.12

fig.update_layout(
    title=dict(
        text=f"{selected_dong} 연령별 인구 구조 ({latest_year}년)",
        x=0.5,
        xanchor="center",
        font=dict(size=20, color="#70452E"),
    ),
    barmode="overlay",
    bargap=0.12,
    height=1250,
    plot_bgcolor="#FFFDF9",
    paper_bgcolor="#FFF9F2",
    font=dict(
        family="Arial, sans-serif",
        size=12,
        color="#59483D",
    ),
    legend=dict(
        title="성별",
        orientation="h",
        yanchor="bottom",
        y=1.01,
        xanchor="center",
        x=0.5,
    ),
    margin=dict(l=85, r=35, t=100, b=75),
)

# 중요: y축 나이 순서는 직접 고정합니다.
# categoryarray에는 0세부터 100세 이상까지 순서대로 넣습니다.
# Plotly의 카테고리 축은 categoryarray의 첫 항목을 아래가 아닌
# 위에 표시할 수 있으므로, 화면에서 0세가 아래에 오도록
# categoryarray를 역순으로 지정합니다.
# 이는 축을 뒤집는 옵션이 아니라 카테고리 배치 순서를 지정하는 것입니다.
fig.update_yaxes(
    type="category",
    categoryorder="array",
    categoryarray=AGES[::-1],
    title_text="나이",
    tickmode="array",
    tickvals=AGES,
    ticktext=AGES,
    showgrid=False,
    ticks="outside",
    tickfont=dict(size=10),
    automargin=True,
)

# x축의 음수 눈금은 절댓값으로 표시합니다.
# 실제 데이터는 남성 음수 / 여성 양수로 유지됩니다.
tick_step = max(1, int(np.ceil(axis_limit / 5)))
tick_max = int(np.ceil(axis_limit / tick_step) * tick_step)
tick_values = list(range(-tick_max, tick_max + 1, tick_step))

fig.update_xaxes(
    title_text="인구 (명)",
    range=[-tick_max, tick_max],
    tickmode="array",
    tickvals=tick_values,
    ticktext=[f"{abs(v):,}" for v in tick_values],
    zeroline=True,
    zerolinewidth=2,
    zerolinecolor="#B8A18D",
    gridcolor="#EDE0D3",
    showgrid=True,
)

# 그래프 출력
st.plotly_chart(fig, use_container_width=True)

# 나이축 순서가 의도한 대로 지정되었는지 화면에 안내합니다.
st.caption(
    "축 순서 확인: 맨 아래는 0세, 맨 위는 100세 이상입니다. "
    "남성은 왼쪽, 여성은 오른쪽이며, "
    "가로축의 인구 눈금은 양쪽 모두 절댓값으로 표시됩니다."
)


# --------------------------------------------------
# 8. 연령별 인구 표
# --------------------------------------------------
with st.expander("📋 연령별 남녀 인구 표 보기"):
    population_table = pd.DataFrame(
        {
            "나이": AGES,
            "남성 인구": male_population.astype(int),
            "여성 인구": female_population.astype(int),
        }
    )

    population_table["합계"] = (
        population_table["남성 인구"]
        + population_table["여성 인구"]
    )

    st.dataframe(
        population_table,
        use_container_width=True,
        hide_index=True,
    )

st.markdown(
    """
    ---
    <div style="text-align:center; color:#9B806B;">
        동네별 인구 피라미드 · 데이터 기반 연령 구조 살펴보기
    </div>
    """,
    unsafe_allow_html=True,
)
