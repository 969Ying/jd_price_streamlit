import pandas as pd
import streamlit as st
import plotly.express as px
import io
from pathlib import Path

# 添加缓存装饰器提升加载性能
@st.cache_data(ttl=3600)
def load_data(sheet_name):
    try:
        # 检查文件是否存在
        if not Path('data/AVC-全球TV面板价格月度数据报告.xlsx').exists():
            raise FileNotFoundError('数据文件未找到')
            
        df = pd.read_excel('data/AVC-全球TV面板价格月度数据报告.xlsx', sheet_name='Average')
        
        # 空值处理
        df = df.dropna(subset=['Company', 'Size'])
        df = df.ffill()
        
        # 预处理日期列
        date_columns = [col for col in df.columns if isinstance(col, str) and '.' in col and len(col.split('.')[0]) == 2]
        df[date_columns] = df[date_columns].apply(pd.to_numeric, errors='coerce')

        years = sorted(set([col.split('.')[0] for col in date_columns if isinstance(col, str)]))
        return df, date_columns, years
    
    except FileNotFoundError as e:
        st.error(f'错误：{str(e)}，请检查文件路径')
    except Exception as e:
        st.error(f'数据处理失败：{str(e)}')
        st.error('原始数据格式可能有误，请检查Excel文件结构')
    
    return pd.DataFrame(), [], []

st.title('TV面板价格数据分析')

# 初始化数据
if 'data_loaded' not in st.session_state:
    df, date_columns, years = load_data('Sheet1')
    if not df.empty:
        st.session_state.df = df
        st.session_state.date_columns = date_columns
        st.session_state.years = years
    st.session_state.data_loaded = True

# 使用原生表格组件显示数据
if 'df' in st.session_state and not st.session_state.df.empty:
    st.header('数据概览')
    st.dataframe(
        st.session_state.df.head(100),
        column_config={
            "Company": "厂商",
            "Size": "尺寸",
            "Price": st.column_config.NumberColumn(format="¥%.2f")
        },
        hide_index=True,
    )

# # ... existing code ...
if 'date_columns' in st.session_state:
    date_columns = st.session_state.date_columns
else:
    st.error('日期列数据未正确加载，请检查数据文件。')
    date_columns = []
# # ... existing code ...

# 替换matplotlib图表为Plotly交互式图表
st.header('价格趋势分析')
if date_columns:
    selected_columns = st.multiselect('选择时间序列', date_columns, default=date_columns[:3])
    fig = px.line(df.melt(id_vars=['Company'], value_vars=selected_columns), 
                 x='variable', y='value', color='Company',
                 title='面板价格趋势', labels={'variable':'日期','value':'价格'})
    st.plotly_chart(fig)

# 添加时间范围筛选功能
if years:
    start_year, end_year = st.slider('选择时间范围', 
                                    min_value=int(min(years)), 
                                    max_value=int(max(years)),
                                    value=(int(min(years)), int(max(years))))
    filtered_columns = [col for col in date_columns if start_year <= int(col.split('.')[0]) <= end_year]
    
    if filtered_columns:
        st.header('时间序列分析')
        fig = px.area(df[['Company'] + filtered_columns].set_index('Company').T,
                     title=f'{start_year}-{end_year} 价格变化趋势')
        st.plotly_chart(fig)


def generate_title_wordcloud(text):
    wordcloud = WordCloud(
        width=1200,
        height=600,
        background_color='white',
        font_path='simhei.ttf',
        max_words=150,
        collocations=False,
        min_font_size=12,
        max_font_size=200,
        colormap='Blues'
    )
    wordcloud.generate(text)
    
    plt.figure(figsize=(24,12))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    buf.seek(0)
    plt.close()
    return buf

# 添加动态筛选控件
with st.expander("高级筛选选项"):
    col1, col2 = st.columns(2)
    with col1:
        selected_years = st.multiselect('选择年份', options=years, default=years[-2:])
    with col2:
        if 'df' in st.session_state and not st.session_state.df.empty and 'Company' in st.session_state.df.columns:
            selected_companies = st.multiselect('选择厂商', options=st.session_state.df['Company'].unique(), default=st.session_state.df['Company'].unique()[:3])

# 应用筛选条件
if 'Company' in df.columns:
    filtered_df = df[df['Company'].isin(selected_companies)]
else:
    st.error("数据中不存在'Company'列，请检查数据。")
    filtered_df = pd.DataFrame()
filtered_columns = [col for col in date_columns if col.split('.')[0] in selected_years]

# 展示筛选后的分析结果
if not filtered_df.empty and filtered_columns:
    st.header('筛选结果分析')
    fig = px.line(filtered_df.melt(id_vars=['Company'], value_vars=filtered_columns),
                 x='variable', y='value', color='Company',
                 title='筛选时间段价格趋势', labels={'variable':'日期','value':'价格'})
    st.plotly_chart(fig)