"""
data_loader.py
电影数据加载与预处理模块
负责从 CSV 文件读取电影数据，清洗并转换为适合规则匹配的结构。
"""

import csv
import os
from typing import List, Dict, Any


# ---------- 路径常量 ----------
# 项目根目录：movie-recommender/
# 数据文件位于 movie-recommender/data/movies.csv
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
DATA_FILE = os.path.join(_PROJECT_ROOT, "data", "movies.csv")


def _parse_pipe_field(value: str) -> List[str]:
    """
    解析用 '|' 分隔的字符串字段（如类型、演员），
    去除两端空白后返回列表。
    """
    if not value:
        return []
    return [item.strip() for item in value.split("|") if item.strip()]


def _coerce_numeric(value: str, target_type):
    """
    把字符串转为数值，失败时返回 None。
    用于处理 CSV 中可能缺失或异常的数字字段。
    """
    try:
        return target_type(value)
    except (ValueError, TypeError):
        return None


def load_movies(csv_path: str = DATA_FILE) -> List[Dict[str, Any]]:
    """
    加载电影数据集。

    返回值: List[Dict]，每个元素代表一部电影，结构如下:
        {
            'movie_id': int,
            'title': str,
            'genres': List[str],
            'actors': List[str],
            'director': str,
            'year': int or None,
            'rating': float or None,
            'duration': int or None,
            'description': str,
        }

    异常:
        FileNotFoundError: 当 csv_path 不存在时抛出。
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"电影数据文件未找到: {csv_path}")

    movies: List[Dict[str, Any]] = []
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 清洗: 跳过完全空行
            if not row.get("title"):
                continue

            movie = {
                "movie_id": _coerce_numeric(row.get("movie_id", ""), int),
                "title": (row.get("title") or "").strip(),
                # 多值字段用 '|' 分隔，拆为列表
                "genres": _parse_pipe_field(row.get("genres", "")),
                "actors": _parse_pipe_field(row.get("actors", "")),
                "director": (row.get("director") or "").strip(),
                "year": _coerce_numeric(row.get("year", ""), int),
                "rating": _coerce_numeric(row.get("rating", ""), float),
                "duration": _coerce_numeric(row.get("duration", ""), int),
                "description": (row.get("description") or "").strip(),
            }
            movies.append(movie)

    return movies


def get_unique_values(movies: List[Dict[str, Any]], field: str) -> List[str]:
    """
    从电影列表中提取某字段的所有唯一值并排序。
    field 支持 'genres' / 'actors' / 'director'。
    用于界面下拉/多选控件的数据源。
    """
    seen = set()
    for m in movies:
        value = m.get(field)
        if field in ("genres", "actors"):
            for item in value or []:
                seen.add(item)
        else:
            if value:
                seen.add(value)
    return sorted(seen)


if __name__ == "__main__":
    # 快速自测
    data = load_movies()
    print(f"已加载 {len(data)} 部电影")
    if data:
        print("样例:", data[0])
