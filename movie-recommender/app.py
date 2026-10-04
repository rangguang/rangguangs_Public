"""
app.py
基于规则的电影推荐系统 —— Streamlit Web 界面

运行方式:
    streamlit run app.py
浏览器会自动打开 http://localhost:8501
"""

import sys
import os

# 让 Python 能找到 src/ 包
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import streamlit as st

from src.recommender import Recommender


# =========================================================
# 页面配置
# =========================================================
st.set_page_config(
    page_title="基于规则的电影推荐系统",
    page_icon="🎬",
    layout="wide",
)


# =========================================================
# 初始化推荐器 (用 st.cache_resource 避免重复加载)
# =========================================================
@st.cache_resource
def get_recommender():
    return Recommender()


rec = get_recommender()


# =========================================================
# 顶部标题
# =========================================================
st.title("🎬 基于规则的电影推荐系统")
st.caption(
    f"数据集中共有 **{rec.total_movies()}** 部电影, "
    f"涵盖 **{len(rec.all_genres())}** 种类型、"
    f"**{len(rec.all_actors())}** 位演员、"
    f"**{len(rec.all_directors())}** 位导演。"
)
st.markdown("---")


# =========================================================
# 侧边栏: 条件输入
# =========================================================
with st.sidebar:
    st.header("🔍 推荐条件")
    st.caption("不填写的条件表示不限")

    selected_genres = st.multiselect(
        "喜欢的电影类型 (可多选, 内部为 OR)",
        options=rec.all_genres(),
    )

    selected_actors = st.multiselect(
        "喜欢的演员 (可多选, 内部为 OR)",
        options=rec.all_actors(),
    )

    director_options = ["(不限)"] + rec.all_directors()
    selected_director = st.selectbox(
        "喜欢的导演 (单选)",
        options=director_options,
        index=0,
    )
    if selected_director == "(不限)":
        selected_director = None

    min_rating = st.slider(
        "最低评分",
        min_value=0.0,
        max_value=10.0,
        value=0.0,
        step=0.1,
        help="只保留评分不低于此值的电影",
    )

    with st.expander("高级筛选 (可选)"):
        col1, col2 = st.columns(2)
        with col1:
            year_min = st.number_input(
                "最早年份",
                min_value=1900,
                max_value=2030,
                value=1900,
                step=1,
            )
        with col2:
            year_max = st.number_input(
                "最晚年份",
                min_value=1900,
                max_value=2030,
                value=2030,
                step=1,
            )
        max_duration = st.number_input(
            "最长时长 (分钟, 0 表示不限)",
            min_value=0,
            max_value=300,
            value=0,
            step=10,
        )

    recommend_btn = st.button("🎯 获取推荐", type="primary", use_container_width=True)


# =========================================================
# 主区域: 推荐结果
# =========================================================
user_input = {
    "genres": selected_genres,
    "actors": selected_actors,
    "director": selected_director,
    "min_rating": min_rating if min_rating > 0 else None,
    "min_year": year_min if year_min > 1900 else None,
    "max_year": year_max if year_max < 2030 else None,
    "max_duration": max_duration if max_duration > 0 else None,
}

# 触发条件: 用户点击按钮 OR 任一条件被填写
has_input = any(
    [
        selected_genres,
        selected_actors,
        selected_director,
        min_rating > 0,
    ]
)

if recommend_btn or has_input:
    results = rec.recommend(user_input)

    st.subheader(f"📋 推荐结果 (共 **{len(results)}** 部)")

    if not results:
        st.warning("⚠️ 没有找到符合条件的电影, 请放宽条件后重试。")
    else:
        # 用卡片形式展示每部电影
        for m in results:
            with st.container(border=True):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"### 🎞️ {m['title']}")
                    genres_str = " | ".join(m.get("genres") or [])
                    actors_str = " | ".join(m.get("actors") or [])
                    st.markdown(
                        f"**类型:** {genres_str}  \n"
                        f"**导演:** {m.get('director') or '未知'}  \n"
                        f"**主演:** {actors_str}  \n"
                        f"**简介:** {m.get('description') or ''}"
                    )
                with col_b:
                    rating = m.get("rating")
                    if rating is not None:
                        st.metric("评分", f"{rating:.1f}")
                    year = m.get("year")
                    duration = m.get("duration")
                    meta = []
                    if year:
                        meta.append(f"📅 {year}")
                    if duration:
                        meta.append(f"⏱️ {duration} 分钟")
                    if meta:
                        st.caption("  \n".join(meta))

                st.progress(
                    min(1.0, (rating or 0) / 10.0) if rating else 0.0,
                    text=f"评分进度: {rating:.1f}/10" if rating else "",
                )
else:
    # 初始状态提示
    st.info("👈 请在左侧选择条件, 或直接点击 **获取推荐** 查看全部电影。")
