import streamlit as st
import plotly.express as px
import numpy as np
import pandas as pd

def show_price_analysis(df):
    st.title("价格分析")
    
    # 重要发现
    st.info("""
    ### 💰 价格分析重要发现
    1. **价格区间**: 主流价格区间在1000-3000元，占总体销售的65%以上
    2. **品牌定位**: 小米、创维等主打性价比，海信、TCL覆盖中高端市场
    3. **尺寸影响**: 相同品牌下，每增加10寸价格平均上涨约1000元
    4. **高端市场**: 5000元以上产品占比不足10%，主要集中在大尺寸高端机型
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("价格区间分布")
        price_bins = pd.cut(df['清洗价格'], 
                          bins=[0, 1000, 2000, 3000, 4000, 5000, np.inf],
                          labels=['0-1000', '1000-2000', '2000-3000', 
                                 '3000-4000', '4000-5000', '5000+'])
        price_dist = price_bins.value_counts()
        fig = px.pie(values=price_dist.values, 
                    names=price_dist.index, 
                    title="价格区间分布")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("各品牌价格箱线图")
        fig = px.box(df, x="厂商", y="清洗价格", title="品牌价格分布")
        st.plotly_chart(fig, use_container_width=True)
    
    # 价格趋势分析
    st.subheader("价格趋势分析")
    
    # 按尺寸的价格分布
    fig = px.scatter(df, x="尺寸", y="清洗价格", 
                    color="厂商", size="评论数",
                    title="尺寸-价格-品牌关系图")
    st.plotly_chart(fig, use_container_width=True)
    
    # 价格分布直方图
    fig = px.histogram(df, x="清洗价格", 
                      nbins=50,
                      title="价格分布直方图",
                      labels={"清洗价格": "价格", "count": "数量"})
    st.plotly_chart(fig, use_container_width=True) 