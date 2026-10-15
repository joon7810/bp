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
    .warning-note {
        color: #A33D2D;
        background: #FFF0E8;
        border: 1px solid #E9A08B;
        border-radius: 10px;
        padding: 10px 14px;
        font-weight: 600;
        margin-top: 8px;
    }
    .insight-note {
        color: #70452E;
        background: #FFF1DF;
        border-left: 5px solid #D89A62;
        border-radius: 8px;
        padding: 14px 16px;
        margin-top: 10px;
        margin-bottom: 16px;
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
