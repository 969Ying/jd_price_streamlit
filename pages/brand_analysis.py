import streamlit as st
import plotly.express as px
import pandas as pd

def show_brand_analysis(df):
    st.title("品牌分析")
    
    # 重要发现
    st.info("""
    ### 🏢 品牌分析重要发现
    1. **市场格局**: 小米、创维、海信三大品牌占据市场主导地位
    2. **用户反馈**: 小米和创维获得最多用户评论，用户参与度高
    3. **价格策略**: 不同品牌价格区间差异明显，反映出差异化定位
    4. **产品线**: 主流品牌均已覆盖全尺寸产品线，竞争日趋激烈
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("品牌市场份额")
        brand_counts = df['厂商'].value_counts()
        fig = px.pie(values=brand_counts.values, 
                    names=brand_counts.index, 
                    title="品牌市场份额")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("品牌评论数对比")
        brand_comments = df.groupby('厂商')['评论数'].mean().sort_values(ascending=False)
        fig = px.bar(x=brand_comments.index, 
                    y=brand_comments.values, 
                    title="各品牌平均评论数")
        st.plotly_chart(fig, use_container_width=True)
    
    # 品牌尺寸覆盖分析
    st.subheader("品牌尺寸覆盖分析")
    size_coverage = pd.crosstab(df['厂商'], df['尺寸'])
    fig = px.imshow(size_coverage,
                    labels=dict(x="尺寸", y="品牌", color="产品数量"),
                    title="品牌-尺寸覆盖热力图")
    st.plotly_chart(fig, use_container_width=True)
    
    # 品牌价格区间分析
    st.subheader("品牌价格区间分析")
    fig = px.box(df, x="厂商", y="清洗价格",
                 title="各品牌价格分布")
    st.plotly_chart(fig, use_container_width=True)
    
    # 品牌店铺类型分析
    st.subheader("品牌店铺类型分析")
    shop_type = pd.crosstab(df['厂商'], df['店铺类型'])
    fig = px.bar(shop_type, 
                 title="品牌店铺类型分布",
                 labels={"value": "数量", "厂商": "品牌"})
    st.plotly_chart(fig, use_container_width=True) 