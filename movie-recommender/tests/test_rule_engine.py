"""
test_rule_engine.py
规则匹配引擎 + 推荐器的单元测试

运行方式:
    pytest tests/test_rule_engine.py -v
"""

import os
import sys

# 让 pytest 能找到 src/ 包
_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _PROJECT_ROOT)

import pytest
from src.data_loader import load_movies, get_unique_values
from src.rule_engine import (
    GenreContains,
    ActorContains,
    DirectorEquals,
    RatingAtLeast,
    YearBetween,
    DurationAtMost,
    Rule,
    RuleEngine,
    build_rule_from_input,
)
from src.recommender import Recommender


# =========================================================
# Fixtures
# =========================================================
@pytest.fixture(scope="module")
def movies():
    """加载电影数据集 (供所有测试复用)。"""
    return load_movies()


@pytest.fixture(scope="module")
def recommender():
    """构造推荐器。"""
    return Recommender()


# =========================================================
# 数据加载测试
# =========================================================
class TestDataLoader:
    def test_load_returns_list(self, movies):
        assert isinstance(movies, list)
        assert len(movies) > 0

    def test_movie_has_required_fields(self, movies):
        required = {"movie_id", "title", "genres", "actors", "director", "rating"}
        for m in movies:
            assert required.issubset(m.keys()), f"电影 {m.get('title')} 缺少字段"

    def test_movie_count_is_50(self, movies):
        """数据集应为 50 部。"""
        assert len(movies) == 50

    def test_genres_are_list(self, movies):
        for m in movies:
            assert isinstance(m["genres"], list)

    def test_actors_are_list(self, movies):
        for m in movies:
            assert isinstance(m["actors"], list)

    def test_rating_in_range(self, movies):
        for m in movies:
            assert 0.0 <= m["rating"] <= 10.0

    def test_get_unique_values_genres(self, movies):
        genres = get_unique_values(movies, "genres")
        assert isinstance(genres, list)
        assert len(genres) > 5
        assert genres == sorted(genres)  # 应排好序

    def test_get_unique_values_directors(self, movies):
        directors = get_unique_values(movies, "director")
        assert "克里斯托弗·诺兰" in directors


# =========================================================
# 原子条件测试
# =========================================================
class TestConditions:
    def test_genre_contains_match(self, movies):
        cond = GenreContains(["喜剧"])
        # 至少有一部喜剧电影能匹配
        matched = [m for m in movies if cond.evaluate(m)]
        assert len(matched) > 0
        for m in matched:
            assert "喜剧" in m["genres"]

    def test_genre_contains_or_logic(self, movies):
        """多类型之间是 OR 关系。"""
        cond = GenreContains(["喜剧", "动作"])
        matched = [m for m in movies if cond.evaluate(m)]
        for m in matched:
            assert ("喜剧" in m["genres"]) or ("动作" in m["genres"])

    def test_genre_contains_empty_always_true(self):
        cond = GenreContains([])
        assert cond.evaluate({"genres": ["科幻"]}) is True

    def test_actor_contains_match(self, movies):
        cond = ActorContains(["周星驰"])
        matched = [m for m in movies if cond.evaluate(m)]
        assert len(matched) > 0
        for m in matched:
            assert "周星驰" in m["actors"]

    def test_director_equals_match(self, movies):
        cond = DirectorEquals(["宫崎骏"])
        matched = [m for m in movies if cond.evaluate(m)]
        assert len(matched) >= 3  # 宫崎骏有多部
        for m in matched:
            assert m["director"] == "宫崎骏"

    def test_rating_at_least(self, movies):
        cond = RatingAtLeast(9.0)
        for m in movies:
            if cond.evaluate(m):
                assert m["rating"] >= 9.0

    def test_year_between(self, movies):
        cond = YearBetween(min_year=2000, max_year=2010)
        for m in movies:
            if cond.evaluate(m):
                assert 2000 <= m["year"] <= 2010

    def test_duration_at_most(self, movies):
        cond = DurationAtMost(100)
        for m in movies:
            if cond.evaluate(m):
                assert m["duration"] <= 100


# =========================================================
# 规则组合测试
# =========================================================
class TestRule:
    def test_rule_and_logic(self, movies):
        """规则要求: 类型是喜剧 AND 评分 >= 9.0"""
        rule = Rule([
            GenreContains(["喜剧"]),
            RatingAtLeast(9.0),
        ])
        matched = [m for m in movies if rule.matches(m)]
        assert len(matched) > 0
        for m in matched:
            assert "喜剧" in m["genres"]
            assert m["rating"] >= 9.0

    def test_rule_three_conditions(self, movies):
        """规则: 宫崎骏导演 AND 动画类型 AND 评分 >= 9.0"""
        rule = Rule([
            DirectorEquals(["宫崎骏"]),
            GenreContains(["动画"]),
            RatingAtLeast(9.0),
        ])
        matched = [m for m in movies if rule.matches(m)]
        for m in matched:
            assert m["director"] == "宫崎骏"
            assert "动画" in m["genres"]
            assert m["rating"] >= 9.0

    def test_rule_no_match(self, movies):
        """不可能满足的规则应返回 0 部。"""
        rule = Rule([
            GenreContains(["科幻"]),
            DirectorEquals(["周星驰"]),  # 周星驰没拍科幻
        ])
        matched = [m for m in movies if rule.matches(m)]
        assert len(matched) == 0


# =========================================================
# RuleEngine 测试
# =========================================================
class TestRuleEngine:
    def test_engine_returns_sorted_by_rating(self, movies):
        """结果应按评分降序排列。"""
        rule = Rule([GenreContains(["动画"])])
        results = RuleEngine.apply(rule, movies)
        if len(results) >= 2:
            ratings = [m["rating"] for m in results]
            assert ratings == sorted(ratings, reverse=True)

    def test_engine_empty_rule_returns_all(self, movies):
        """空规则应返回全部电影(按评分降序)。"""
        rule = Rule([])
        results = RuleEngine.apply(rule, movies)
        assert len(results) == len(movies)


# =========================================================
# 用户输入 -> Rule 的转换
# =========================================================
class TestBuildRuleFromInput:
    def test_empty_input(self):
        """完全空输入应得到空 Rule。"""
        rule = build_rule_from_input({})
        assert rule.conditions == []

    def test_partial_input(self, movies):
        """只填部分字段, 未填字段应被忽略。"""
        rule = build_rule_from_input({"director": "王家卫"})
        results = RuleEngine.apply(rule, movies)
        assert all(m["director"] == "王家卫" for m in results)

    def test_full_input(self, movies):
        """全字段填写, 验证 AND 组合。"""
        rule = build_rule_from_input({
            "genres": ["剧情"],
            "actors": ["梁朝伟"],
            "director": "王家卫",
            "min_rating": 8.0,
        })
        results = RuleEngine.apply(rule, movies)
        for m in results:
            assert "剧情" in m["genres"]
            assert "梁朝伟" in m["actors"]
            assert m["director"] == "王家卫"
            assert m["rating"] >= 8.0


# =========================================================
# 推荐器 (门面) 测试
# =========================================================
class TestRecommender:
    def test_recommend_returns_list(self, recommender):
        results = recommender.recommend({"genres": ["科幻"]})
        assert isinstance(results, list)

    def test_recommend_filters_correctly(self, recommender):
        results = recommender.recommend({"director": "宫崎骏"})
        assert len(results) >= 3
        for m in results:
            assert m["director"] == "宫崎骏"

    def test_recommend_multi_condition(self, recommender):
        results = recommender.recommend({
            "genres": ["喜剧"],
            "min_rating": 8.5,
        })
        assert len(results) > 0
        for m in results:
            assert "喜剧" in m["genres"]
            assert m["rating"] >= 8.5

    def test_total_movies(self, recommender):
        assert recommender.total_movies() == 50

    def test_all_genres_non_empty(self, recommender):
        assert len(recommender.all_genres()) > 0

    def test_all_actors_non_empty(self, recommender):
        assert len(recommender.all_actors()) > 0

    def test_all_directors_non_empty(self, recommender):
        assert len(recommender.all_directors()) > 0


# =========================================================
# 边界情况测试
# =========================================================
class TestEdgeCases:
    def test_rating_zero_returns_all(self, movies):
        rule = Rule([RatingAtLeast(0)])
        results = RuleEngine.apply(rule, movies)
        assert len(results) == len(movies)

    def test_rating_too_high_returns_none(self, movies):
        rule = Rule([RatingAtLeast(10.0)])
        results = RuleEngine.apply(rule, movies)
        assert len(results) == 0

    def test_movie_with_none_rating_excluded(self):
        """评分为 None 的电影不应被 RatingAtLeast 选中。"""
        rule = Rule([RatingAtLeast(5.0)])
        movie = {"title": "测试电影", "genres": [], "actors": [], "rating": None}
        assert rule.matches(movie) is False

    def test_year_with_no_bounds(self, movies):
        """年份范围只给一边。"""
        rule = Rule([YearBetween(min_year=2010, max_year=None)])
        for m in movies:
            if rule.matches(m):
                assert m["year"] >= 2010
