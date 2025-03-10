import streamlit as st

def show_data_query(df):
    st.title("数据查询")
    
    # 查询条件
    col1, col2, col3 = st.columns(3)
    
    with col1:
        brand_filter = st.multiselect(
            "选择品牌",
            options=sorted(df['厂商'].unique())
        )
    
    with col2:
        price_range = st.slider(
            "价格范围",
            float(df['清洗价格'].min()),
            float(df['清洗价格'].max()),
            (float(df['清洗价格'].min()), float(df['清洗价格'].max()))
        )
    
    with col3:
        size_filter = st.multiselect(
            "选择尺寸",
            options=sorted(df['尺寸'].unique())
        )
    
    # 标题搜索
    search_term = st.text_input("搜索商品标题")
    
    # 应用筛选
    query_df = df.copy()
    if brand_filter:
        query_df = query_df[query_df['厂商'].isin(brand_filter)]
    query_df = query_df[
        (query_df['清洗价格'] >= price_range[0]) & 
        (query_df['清洗价格'] <= price_range[1])
    ]
    if size_filter:
        query_df = query_df[query_df['尺寸'].isin(size_filter)]
    if search_term:
        query_df = query_df[query_df['标题'].str.contains(search_term, case=False)]
    
    # 显示结果
    st.write(f"找到 {len(query_df)} 条记录")
    st.dataframe(query_df) 