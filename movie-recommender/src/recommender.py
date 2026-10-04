"""
recommender.py
推荐器 —— 把数据加载和规则引擎组合起来，提供统一的 recommend 接口。

这一层是"门面 (Facade)"，界面上只需要调用 Recommender.recommend()
即可完成整套流程，无需关心底层细节。
"""

from typing import List, Dict, Any

from .data_loader import load_movies, get_unique_values
from .rule_engine import RuleEngine, build_rule_from_input


class Recommender:
    """
    推荐器门面。
    用法:
        rec = Recommender()
        results = rec.recommend({
            "genres": ["喜剧", "动作"],
            "director": "周星驰",
            "min_rating": 8.0,
        })
    """

    def __init__(self, csv_path: str = None):
        # 构造时一次性加载电影数据, 避免每次推荐都读文件
        self.movies: List[Dict[str, Any]] = load_movies(csv_path) if csv_path else load_movies()

    # ---------------- 业务接口 ----------------
    def recommend(self, user_input: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        根据用户输入返回推荐电影列表 (按评分降序)。
        """
        rule = build_rule_from_input(user_input)
        return RuleEngine.apply(rule, self.movies)

    def all_genres(self) -> List[str]:
        """返回数据集中所有电影类型 (用于界面下拉数据源)。"""
        return get_unique_values(self.movies, "genres")

    def all_actors(self) -> List[str]:
        """返回数据集中所有演员 (用于界面下拉数据源)。"""
        return get_unique_values(self.movies, "actors")

    def all_directors(self) -> List[str]:
        """返回数据集中所有导演 (用于界面下拉数据源)。"""
        return get_unique_values(self.movies, "director")

    def total_movies(self) -> int:
        return len(self.movies)


if __name__ == "__main__":
    # 快速自测
    rec = Recommender()
    print(f"电影总数: {rec.total_movies()}")
    print(f"类型数: {len(rec.all_genres())}, 演员数: {len(rec.all_actors())}, 导演数: {len(rec.all_directors())}")

    # 测试用例: 周星驰导演, 评分 >= 8.5
    results = rec.recommend({"director": "周星驰", "min_rating": 8.5})
    print(f"\n周星驰导演且评分>=8.5的电影: {len(results)} 部")
    for m in results:
        print(f"  - {m['title']} ({m['rating']})")
