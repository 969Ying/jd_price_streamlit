import streamlit as st
import pandas as pd
from pathlib import Path
from pages.overview import show_overview
from pages.data_query import show_data_query


# 设置页面配置
st.set_page_config(
    page_title="京东电视数据分析",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 隐藏侧边栏的默认标题
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none}
    </style>
""", unsafe_allow_html=True)

# 读取数据函数
@st.cache_data
def load_data():
    file_path = Path("data/20250304-0317已清洗new.xlsx")
    df = pd.read_excel(file_path)
    df['爬取时间'] = pd.to_datetime(df['爬取时间'])
    return df

def main():
    df = load_data()
    
    # 侧边栏导航 - 直接显示选择框
    page = st.sidebar.selectbox(
        "选择页面",
        ["数据概览", "数据查询"]
    )
    
    # 页面路由
    if page == "数据概览":
        show_overview(df)
    elif page == "数据查询":
        show_data_query(df)


if __name__ == "__main__":
    main()
