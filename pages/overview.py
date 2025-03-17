import streamlit as st
import plotly.express as px
import jieba
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io
import pandas as pd

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

    # 价格监控告警区域
    st.header("📊 价格监控告警")

    # 价格变化表格（新增在数据大屏部分）
    st.subheader("价格变化最大的商品TOP5")

    # 指定四个厂商
    selected_manufacturers = ['小米', '创维', '海信', 'TCL']

    # 创建上下布局，每行两个厂商
    top_col1, top_col2 = st.columns(2)
    bottom_col1, bottom_col2 = st.columns(2)

    # 格式化价格变化列并添加颜色样式
    def format_price_change(price_change_str):
        try:
            price_change = float(price_change_str.replace('￥', ''))
            if price_change >= 0:
                return f"<span style='color: green;'>+ {price_change_str}</span>"
            else:
                return f"<span style='color: red;'>{price_change_str}</span>"
        except ValueError:
            return price_change_str

    # 定义价格箭头样式
    def get_price_arrow(price_change_str):
        try:
            price_change = float(price_change_str.replace('￥', ''))
            if price_change >= 0:
                return '<span style="color: darkgreen;">↑</span>'
            else:
                return '<span style="color: darkred;">↓</span>'
        except ValueError:
            return ''

    # 应用样式到 DataFrame
    def style_dataframe(df):
        def highlight_rows(row):
            price_change_str = row['价格变化']
            try:
                price_change = float(price_change_str.replace('￥', ''))
                if price_change >= 0:
                    return ['background-color: lightgreen'] * len(row)
                else:
                    return ['background-color: lightcoral'] * len(row)
            except ValueError:
                return [''] * len(row)
        return df.style.apply(highlight_rows, axis=1)

    for i, manufacturer in enumerate(selected_manufacturers):
        # 筛选对应厂商的数据
        manufacturer_df = df[df['厂商'] == manufacturer]
        manufacturer_df = manufacturer_df[manufacturer_df['机型'] != '通用型号']  # 过滤通用型号

        def calculate_price_change(group):
            sorted_group = group.sort_values('爬取时间')
            if len(sorted_group) < 2:
                return 0
            latest_price = sorted_group['清洗价格'].iloc[-1]
            previous_price = sorted_group['清洗价格'].iloc[-2]
            return latest_price - previous_price

        # 计算价格变化最大的商品TOP5
        price_changes = manufacturer_df.groupby(['机型', '店铺']).apply(calculate_price_change).reset_index(name='价格变化')
        latest_prices = manufacturer_df.groupby(['机型', '店铺']).agg(
            最新价格=('清洗价格', 'last'),
            变化日期=('爬取时间', 'max')
        ).reset_index()
        price_changes = price_changes.merge(latest_prices, on=['机型', '店铺'])
        # 格式化日期列
        price_changes['变化日期'] = price_changes['变化日期'].dt.strftime('%Y-%m-%d')
        price_changes = price_changes.sort_values('价格变化', key=lambda x: x.abs(), ascending=False).head(5)
        price_changes = price_changes.reset_index(drop=True)

        # 将价格变化转换为带￥的字符串格式
        price_changes['价格变化'] = price_changes['价格变化'].apply(lambda x: f"{x}￥")

        # 格式化价格变化列
        price_changes['价格变化'] = price_changes['价格变化'].apply(format_price_change)

        # 添加价格箭头到最新价格列
        price_changes['最新价格'] = price_changes.apply(lambda row: f"{get_price_arrow(row['价格变化'].replace('<span style=\'color: green;\'>+ ', '').replace('<span style=\'color: red;\'>', '').replace('</span>', ''))} ¥{row['最新价格']:.0f}", axis=1)

        # 应用样式到 DataFrame
        styled_df = style_dataframe(price_changes[['机型', '店铺', '价格变化', '最新价格', '变化日期']])

        # 根据循环索引分配列容器
        if i == 0:
            col = top_col1
        elif i == 1:
            col = top_col2
        elif i == 2:
            col = bottom_col1
        else:
            col = bottom_col2

        # 添加厂商标题
        col.markdown(
        f"""
        <h2 style="font-size: 1.2rem; margin: 0;">
            {manufacturer}
        </h2>
        """,
        unsafe_allow_html=True
        )
        # 直接使用 styled_df 转换为 HTML
        html_table = styled_df.to_html(escape=False, index=False, header=True)
        col.write(html_table, unsafe_allow_html=True)


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

    # 新增筛选控件
    st.subheader("产品价格 & 评论数量波动变化")
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            selected_manufacturer = st.selectbox("选择厂商", options=['全部'] + sorted(df['厂商'].unique().tolist()))
        with col2:
            selected_model = st.selectbox("选择机型", options=['全部'] + sorted(df['机型'].unique().tolist()))

    # 筛选数据
    filtered_df = df.copy()
    if selected_manufacturer != '全部':
        filtered_df = filtered_df[filtered_df['厂商'] == selected_manufacturer]
    if selected_model != '全部':
        filtered_df = filtered_df[filtered_df['机型'] == selected_model]

    # 绘制价格评论波动图表
    if not filtered_df.empty:
        fig = px.scatter(filtered_df, 
                        x='爬取时间', 
                        y='清洗价格',
                        size='评论数',
                        color='厂商',
                        title=f'{selected_manufacturer} {selected_model} 价格波动趋势',
                        labels={'爬取时间': '日期', '清洗价格': '价格'})
        fig.update_layout(xaxis_title='日期',
                         yaxis_title='价格',
                         hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)

    # 核心卖点词云分析
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

        plt.figure(figsize=(20, 10))
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

    # 以下内容移到布局最后
    # ================== 原有其他内容 ==================
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
