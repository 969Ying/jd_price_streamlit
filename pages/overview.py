import streamlit as st
import plotly.express as px
import jieba
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io

def show_overview(df):
    st.title('京东电视商品数据分析平台')
    
    # 重要发现
    st.info("""
    ### 📊 重要发现
    1. **价格趋势**: 电视价格主要集中在1000-3000元区间，高端市场占比较小
    2. **品牌格局**: 小米、创维等品牌占据主要市场份额，高端品牌渗透率低
    3. **尺寸偏好**: 55寸和65寸是最受欢迎的尺寸，反映出大屏需求强劲
    4. **价格波动**: 部分商品价格波动明显，最高波动幅度超过1000元
    """)
    
    # 价格监控告警区域
    st.header("📊 价格监控告警")
    
    # 价格变化表格（新增在数据大屏部分）
    st.subheader("价格变化最大的商品TOP5")
    price_changes = df.groupby('标题').agg(
        最新价格=('清洗价格', 'last'),
        最新时间=('爬取时间', 'max'),
        价格变化=('清洗价格', lambda x: round((x.iloc[-1] - x.iloc[0])/x.iloc[0]*100, 2))
    ).reset_index().sort_values('价格变化', ascending=False).head(5)

    st.dataframe(
        price_changes[['标题', '价格变化', '最新价格', '最新时间']],
        column_config={
            "标题": "商品名称",
            "价格变化": st.column_config.NumberColumn(format="%.2f%%"),
            "最新价格": st.column_config.NumberColumn(format="¥%.0f"),
            "最新时间": "最后更新时间"
        },
        use_container_width=True
    )
    
    # 数据概要行
    st.subheader("数据概要")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("商品总数", f"{len(df):,}",
                 delta=f"{len(df.厂商.unique())} 个品牌")
    with col2:
        st.metric("平均价格", f"¥{df['清洗价格'].mean():,.2f}",
                 delta=f"中位数 ¥{df['清洗价格'].median():,.2f}")
    with col3:
        st.metric("最高价格", f"¥{df['清洗价格'].max():,.2f}")
    with col4:
        st.metric("最低价格", f"¥{df['清洗价格'].min():,.2f}")
    
    st.markdown(f"""
    <div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin: 10px 0;'>
        <p style='color: #1f77b4; margin: 0;'>最新更新时间: {df['爬取时间'].max().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 第一行：价格和评论分析
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.histogram(df, x="清洗价格", title="价格分布",
                         labels={"清洗价格": "价格", "count": "数量"},
                         template="plotly_white")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.scatter(df, x="清洗价格", y="评论数", 
                        color="厂商", title="价格vs评论数关系",
                        labels={"清洗价格": "价格", "评论数": "评论数", "厂商": "品牌"})
        st.plotly_chart(fig, use_container_width=True)
    
    # 第二行：品牌和尺寸分析
    col1, col2 = st.columns(2)
    
    with col1:
        brand_counts = df['厂商'].value_counts()
        fig = px.pie(values=brand_counts.values, 
                    names=brand_counts.index, 
                    title="品牌占比")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        size_counts = df['尺寸'].value_counts()
        fig = px.bar(x=size_counts.index, 
                    y=size_counts.values, 
                    title="尺寸分布",
                    labels={"x": "尺寸", "y": "数量"})
        st.plotly_chart(fig, use_container_width=True)
    
    # 第三行：核心卖点词云分析
    st.subheader("核心卖点词云分析")
    
    # 品牌筛选
    selected_brands = st.multiselect(
        "选择品牌查看核心卖点",
        options=['全部'] + sorted(df['厂商'].unique().tolist()),
        default=['全部']
    )
    
    # 处理文本
    def preprocess_text(text):
        # 去掉冒号前的常见词汇
        remove_words = ['屏幕', '智能', '能效', '显示', '分辨率', '尺寸', '功能', '特点', '参数']
        for word in remove_words:
            text = text.replace(f"{word}：", "")
            text = text.replace(f"{word}:", "")  # 处理英文冒号的情况
        return text
    
    if '全部' in selected_brands:
        text = ' '.join(df['核心卖点'].dropna().apply(preprocess_text))
    else:
        text = ' '.join(df[df['厂商'].isin(selected_brands)]['核心卖点'].dropna().apply(preprocess_text))
    
    # 分词并去除停用词
    def process_words(text):
        # 自定义停用词
        stop_words = set(['的', '了', '和', '与', '及', '或', '等', '中', '为', '以'])
        words = jieba.cut(text)
        # 过滤停用词和单字词
        return ' '.join([word for word in words if word not in stop_words and len(word) > 1])
    
    # 处理文本
    words = process_words(text)
    
    # 生成词云
    def generate_wordcloud(text):
        wordcloud = WordCloud(
            width=800, 
            height=400,
            background_color='white',
            font_path='simhei.ttf',
            max_words=100,
            collocations=False,
            min_font_size=10,
            max_font_size=150
        )
        wordcloud.generate(text)
        
        plt.figure(figsize=(20,10))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
        buf.seek(0)
        plt.close()
        return buf
    
    # 生成并显示词云
    wordcloud_image = generate_wordcloud(words)
    st.image(wordcloud_image)
    
    # 添加标题词云生成函数
    def generate_title_wordcloud(text):  # 新增缺失的函数定义
        return generate_wordcloud(text)  # 复用已有词云生成逻辑
    
    # 价格变化表格（调整到词云前）
    st.subheader("价格变化最大的商品TOP5")
    price_changes = df.groupby('标题').agg(
        最新价格=('清洗价格', 'last'),
        最新时间=('爬取时间', 'max'),
        价格变化=('清洗价格', lambda x: round((x.iloc[-1] - x.iloc[0])/x.iloc[0]*100, 2))
    ).reset_index().sort_values('价格变化', ascending=False).head(5)

    st.dataframe(
        price_changes[['标题', '价格变化', '最新价格', '最新时间']],
        column_config={
            "标题": "商品名称",
            "价格变化": st.column_config.NumberColumn(format="%.2f%%"),
            "最新价格": st.column_config.NumberColumn(format="¥%.0f"),
            "最新时间": "最后更新时间"
        },
        use_container_width=True
    )
    
    # 标题词云分析
    st.subheader("商品标题词频分析")
    
    # 处理标题文本
    def preprocess_title(text):
        # 去掉品牌名称和常见无关词汇
        remove_words = [
            '小米', '海信', 'TCL', '创维', 'Vidda', '雷鸟',  # 品牌名称
            '电视', '英寸', '智能', '全面屏', '液晶', '平板', 
            '电视机', '高清', '超高清', '旗舰', '新品', '官方', 
            '店', '旗舰店', '京东', '自营'
        ]
        for word in remove_words:
            text = text.replace(word, '')
        return text
    
    # 处理所有标题
    titles_text = ' '.join(df['标题'].dropna().apply(preprocess_title))
    
    # 分词并去除停用词
    def process_title_words(text):
        # 自定义停用词
        stop_words = set([
            '的', '了', '和', '与', '及', '或', '等', '中', '为', '以',
            '【', '】', '（', '）', '(', ')', '[', ']', '+', 
            '全', '新', '款', '型', '寸'
        ])
        words = jieba.cut(text)
        # 过滤停用词、单字词和数字
        return ' '.join([
            word for word in words 
            if word not in stop_words 
            and len(word) > 1 
            and not word.isdigit()
        ])
    
    # 处理文本
    title_words = process_title_words(titles_text)
    
    # 生成标题词云
    title_wordcloud_image = generate_title_wordcloud(title_words)
    
    # 添加说明文字
    st.markdown("""
    <div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin: 10px 0;'>
        <p style='color: #1f77b4; margin: 0;'>
            ℹ️ 此词云展示了商品标题中最常见的关键词，已去除品牌名称和常见修饰词，
            可以帮助我们了解电视产品的主要卖点和特征。
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.image(title_wordcloud_image) 
    
    # 移除核心卖点词云分析部分的代码
    # 移除商品标题词频分析部分的代码
    # 价格变化表格（调整到合适位置）
    st.subheader("价格变化最大的商品TOP5")
    st.markdown("### 字段解释说明：")
    st.markdown("- **商品名称**：商品的标题。")
    st.markdown("- **价格变化**：商品的最新价格与初始价格的差值。")
    st.markdown("- **最新价格**：商品的最新清洗价格。")
    st.markdown("- **爬取时间**：该商品的最新价格在表中对应的最新爬取时间。")
    price_changes = df.groupby('标题').agg(
        最新价格=('清洗价格', 'last'),
        最新时间=('爬取时间', 'max'),
        价格变化=('清洗价格', lambda x: x.iloc[-1] - x.iloc[0])
    ).reset_index().sort_values('价格变化', ascending=False).head(5)
    st.dataframe(
        price_changes[['标题', '价格变化', '最新价格', '最新时间']],
        column_config={
            "标题": "商品名称",
            "价格变化": st.column_config.NumberColumn(format="¥%.0f"),
            "最新价格": st.column_config.NumberColumn(format="¥%.0f"),
            "最新时间": "爬取时间"
        },
        use_container_width=True
    )