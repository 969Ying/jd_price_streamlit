import streamlit as st
import plotly.express as px
import jieba
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io
import pandas as pd
import numpy as np
from PIL import Image
import random

def show_overview(df):
    st.title('京东电视商品数据分析平台')

    # 在标题下方添加数据范围和更新日期说明
    st.markdown("""
    <div style='font-size: 0.9rem; color: gray;'>
        数据范围：全国 | 最新更新日期：{update_date}
    </div>
    """.format(update_date=df['爬取时间'].max().strftime('%Y-%m-%d %H:%M')), unsafe_allow_html=True)

    # 在侧边栏添加刷新数据按钮
    if st.sidebar.button("刷新数据"):
        st.experimental_rerun()  # 重新加载页面

    # 计算前一天的数据
    latest_date = df['爬取时间'].max()
    previous_date = latest_date - pd.Timedelta(days=1)
    df_previous = df[df['爬取时间'] == previous_date]

    # 在侧边栏显示数据概要
    st.sidebar.header("数据概要")
    current_total_products = len(df.sort_values('爬取时间').drop_duplicates(subset=['机型'], keep='last'))
    previous_total_products = len(df_previous.sort_values('爬取时间').drop_duplicates(subset=['机型'], keep='last'))
    st.sidebar.metric("商品总数", f"{current_total_products:,}",
                      delta=f"{current_total_products - previous_total_products} 商品")

    current_avg_price = df['清洗价格'].mean()
    previous_avg_price = df_previous['清洗价格'].mean()
    st.sidebar.metric("平均价格", f"¥{current_avg_price:,.0f}",
                      delta=f"环比 {current_avg_price - previous_avg_price:,.0f}")

    current_median_price = df['清洗价格'].median()
    previous_median_price = df_previous['清洗价格'].median()
    st.sidebar.metric("中位数", f"¥{current_median_price:,.0f}",
                      delta=f"环比 {current_median_price - previous_median_price:,.0f}")

    current_max_price = df['清洗价格'].max()
    previous_max_price = df_previous['清洗价格'].max()
    st.sidebar.metric("最高价格", f"¥{current_max_price:,.0f}",
                      delta=f"环比 {current_max_price - previous_max_price:,.0f}")

    current_min_price = df['清洗价格'].min()
    previous_min_price = df_previous['清洗价格'].min()
    st.sidebar.metric("最低价格", f"¥{current_min_price:,.0f}",
                      delta=f"环比 {current_min_price - previous_min_price:,.0f}")

    # 添加浏览数据
    st.sidebar.header("浏览数据")
    # 假设访问量和访问人数是从其他数据源获取的
    current_visits = 123456
    previous_visits = 120000  # 示例数据
    st.sidebar.metric("访问量", f"{current_visits:,}",
                      delta=f"环比 {current_visits - previous_visits:,}")

    current_users = 12345
    previous_users = 12000  # 示例数据
    st.sidebar.metric("访问人数", f"{current_users:,}",
                      delta=f"环比 {current_users - previous_users:,}")

    # 核心卖点词云分析
    st.subheader("核心卖点词云分析")

    # 处理文本
    def preprocess_text(text):
        remove_words = ['屏幕', '智能', '能效', '显示', '分辨率', '尺寸', '功能', '特点', '参数']
        for word in remove_words:
            text = text.replace(f"{word}：", "")
            text = text.replace(f"{word}:", "")  # 处理英文冒号的情况
        return text

    text = ' '.join(df['核心卖点'].dropna().apply(preprocess_text))

    # 分词并去除停用词
    def process_words(text):
        stop_words = set(['的', '了', '和', '与', '及', '或', '等', '中', '为', '以'])
        words = jieba.cut(text)
        return ' '.join([word for word in words if word not in stop_words and len(word) > 1])

    # 处理文本
    words = process_words(text)

    # 莫兰迪色系颜色函数
    def morandi_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
        morandi_colors = [
            (199, 178, 153),  # 浅棕色
            (183, 164, 142),  # 灰棕色
            (168, 153, 134),  # 灰褐色
            (153, 138, 122),  # 深灰褐色
            (138, 123, 110)   # 深褐色
        ]
        color = random.choice(morandi_colors)
        return f"rgb{color}"

    # 生成词云
    def generate_wordcloud(text):
        wordcloud = WordCloud(
            width=400,
            height=200,
            background_color='white',
            font_path='simhei.ttf',
            max_words=100,
            color_func=morandi_color_func,  # 使用莫兰迪色系颜色函数
            collocations=False,
            min_font_size=12,
            max_font_size=160,
            prefer_horizontal=0.7,  # 允许更多垂直文字
            random_state=42  # 设置随机种子以确保可重复性
        ).generate(text)

        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')

        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
        buf.seek(0)
        plt.close()
        return buf

    # 为每个厂商生成词云
    cols = st.columns(4)
    for i, manufacturer in enumerate(['小米', '创维', '海信', 'TCL']):
        manufacturer_df = df[df['厂商'] == manufacturer]
        text = ' '.join(manufacturer_df['核心卖点'].dropna().apply(preprocess_text))
        words = process_words(text)
        if words:  # 确保处理后的文本非空
            wordcloud_image = generate_wordcloud(words)
            cols[i].image(wordcloud_image, caption=manufacturer)
        else:
            cols[i].warning(f"{manufacturer} 的处理后的文本为空，无法生成词云")

    # 价格监控告警区域
    st.header("📊价格变化最大的商品TOP5")
    st.markdown("<div style='font-size: 0.9rem; color: gray;'>价格变化逻辑：计算每个商品的最新价格与前一次价格的差异。</div>", unsafe_allow_html=True)

    # 价格变化表格（新增在数据大屏部分）
    # 指定四个厂商
    selected_manufacturers = ['小米', '创维', '海信', 'TCL']

    # 创建上下布局，每行两个厂商
    top_col1, top_col2 = st.columns(2)
    bottom_col1, bottom_col2 = st.columns(2)

    # 格式化价格变化列并添加颜色样式
    def format_price_change(price_change):
        if price_change >= 0:
            return f"<span style='color: green;'>↑ {price_change:.2f}</span>"
        else:
            return f"<span style='color: red;'>↓ {price_change:.2f}</span>"

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

        # 计算价格变化最大的商品
        price_changes = manufacturer_df.groupby(['机型', '店铺', '尺寸']).apply(calculate_price_change).reset_index().rename(columns={0: '价格变化'})
        latest_prices = manufacturer_df.groupby(['机型', '店铺', '尺寸']).agg(
            最新价格=('清洗价格', 'last'),
            变化日期=('爬取时间', 'max')
        ).reset_index()
        price_changes = price_changes.merge(latest_prices, on=['机型', '店铺', '尺寸'])
        # 格式化日期列
        price_changes['变化日期'] = price_changes['变化日期'].dt.strftime('%Y-%m-%d')
        price_changes = price_changes.sort_values('价格变化', key=lambda x: x.abs(), ascending=False)

        # 添加搜索和筛选功能
        with st.expander(f"{manufacturer} 价格变化表格"):
            search_model = st.text_input(f"搜索{manufacturer}的机型")
            selected_store = st.multiselect(f"选择{manufacturer}的店铺", options=price_changes['店铺'].unique())
            selected_size = st.multiselect(f"选择{manufacturer}的尺寸", options=price_changes['尺寸'].unique())

            # 应用搜索和筛选
            if search_model:
                price_changes = price_changes[price_changes['机型'].str.contains(search_model)]
            if selected_store:
                price_changes = price_changes[price_changes['店铺'].isin(selected_store)]
            if selected_size:
                price_changes = price_changes[price_changes['尺寸'].isin(selected_size)]

            # 分页
            page_size = 5
            total_pages = (len(price_changes) + page_size - 1) // page_size
            page_number = st.number_input(f"选择页码 (1-{total_pages})", min_value=1, max_value=total_pages, step=1) - 1

            # 显示当前页的数据
            start_idx = page_number * page_size
            end_idx = start_idx + page_size
            current_page_data = price_changes.iloc[start_idx:end_idx]

            # 美化表格
            html_table = current_page_data.to_html(
                escape=False,
                index=False,
                header=True,
                formatters={'价格变化': format_price_change}
            )
            st.write(html_table, unsafe_allow_html=True)

    # 第二行：价格和尺寸分析
    col1, col2 = st.columns(2)

    with col1:
        # 价格占比图表
        price_bins = pd.cut(df['清洗价格'], bins=[0, 1000, 2000, 3000, 4000, 5000, 10000, float('inf')])
        price_counts = price_bins.value_counts().sort_index()
        fig = px.pie(values=price_counts.values, 
                    names=price_counts.index.astype(str), 
                    title="价格区间占比",
                    labels={"names": "价格区间", "values": "数量"})
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
            selected_manufacturer = st.selectbox(
                "选择厂商", 
                options=['全部'] + sorted(df['厂商'].unique()),
                index=0  # 默认选择全部
            )
        with col2:
            if selected_manufacturer == '全部':
                # 如果选择全部，默认显示小米的前5个机型
                default_models = sorted(df[df['厂商'] == '小米']['机型'].unique())[:5]
                selected_models = st.multiselect(
                    "选择机型（可多选）",
                    options=sorted(df['机型'].unique()),
                    default=default_models
                )
            else:
                # 如果选择了特定厂商，显示该厂商的任意五个机型
                manufacturer_models = sorted(df[df['厂商'] == selected_manufacturer]['机型'].unique())
                default_models = manufacturer_models[:5]  # 默认选择任意五个机型
                selected_models = st.multiselect(
                    "选择机型（可多选）",
                    options=manufacturer_models,
                    default=default_models
                )

    # 筛选数据
    filtered_df = df.copy()
    if selected_manufacturer != '全部':
        filtered_df = filtered_df[filtered_df['厂商'] == selected_manufacturer]
    if selected_models:  # 改为使用选中的多个机型
        filtered_df = filtered_df[filtered_df['机型'].isin(selected_models)]
    elif selected_manufacturer == '小米':  # 如果是小米但没有选择机型，默认显示前5个
        default_models = sorted(df[df['厂商'] == '小米']['机型'].unique())[:5]
        filtered_df = filtered_df[filtered_df['机型'].isin(default_models)]

    # 如果不为空，绘制价格评论波动图表
    if not filtered_df.empty:
        # 创建两列布局
        col1, col2 = st.columns(2)
        
        with col1:
            # 价格波动折线图 - 按机型分组
            price_df = filtered_df.groupby(['爬取时间', '机型'])['清洗价格'].mean().reset_index()
            fig = px.line(price_df, 
                         x='爬取时间',
                         y='清洗价格',
                         color='机型',  # 按机型分组显示不同颜色
                         title=f'{selected_manufacturer} 价格波动趋势',
                         labels={'爬取时间': '日期', '清洗价格': '价格'})
            fig.update_xaxes(tickformat='%Y-%m-%d', tickmode='auto')
            fig.update_layout(
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 评论数波动折线图
            if '评论数' in filtered_df.columns:
                try:
                    # 将评论数转换为数值
                    filtered_df['处理评论数'] = filtered_df['评论数'].apply(lambda x: 
                        float(str(x).replace('万+', '0000').replace('万', '0000')
                              .replace('+', '').replace(',', ''))
                        if pd.notnull(x) else 0
                    )
                    
                    comment_df = filtered_df.groupby(['爬取时间', '机型'])['处理评论数'].mean().reset_index()
                    fig = px.line(comment_df, 
                                x='爬取时间',
                                y='处理评论数',
                                color='机型',  # 按机型分组显示不同颜色
                                title=f'{selected_manufacturer} 评论数趋势',
                                labels={'爬取时间': '日期', '处理评论数': '评论数'})
                    fig.update_xaxes(tickformat='%Y-%m-%d', tickmode='auto')
                    fig.update_layout(
                        hovermode='x unified',
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        )
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"处理评论数据时出错: {str(e)}")
            else:
                st.warning("未找到评论数据列")

   