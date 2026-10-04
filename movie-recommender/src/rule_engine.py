"""
rule_engine.py
基于规则的匹配引擎 —— 系统核心模块

设计思路:
- Condition: 原子条件，每种条件是一个类，封装"判断某部电影是否满足某个规则"
- Rule:      条件组合，多个 Condition 通过 AND 组合
- RuleEngine: 接收 Rule 与电影列表，返回匹配的电影

这种设计的优点:
1. 新增条件只需添加新类，无需改动引擎
2. 条件之间相互独立，便于单元测试
3. 规则可序列化(便于将来扩展为配置文件)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Iterable


# =========================================================
# 原子条件 (Condition)
# =========================================================
class Condition(ABC):
    """所有条件的抽象基类。"""

    @abstractmethod
    def evaluate(self, movie: Dict[str, Any]) -> bool:
        """判断一部电影是否满足此条件。"""
        raise NotImplementedError

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__dict__})"


class GenreContains(Condition):
    """电影类型包含指定类型之一(多类型之间是 OR 关系)。"""

    def __init__(self, genres: Iterable[str]):
        self.genres = [g for g in genres if g]

    def evaluate(self, movie: Dict[str, Any]) -> bool:
        if not self.genres:  # 空条件视为永远成立
            return True
        movie_genres = set(movie.get("genres", []) or [])
        return any(g in movie_genres for g in self.genres)


class ActorContains(Condition):
    """电影主演列表包含指定演员之一(OR 关系)。"""

    def __init__(self, actors: Iterable[str]):
        self.actors = [a for a in actors if a]

    def evaluate(self, movie: Dict[str, Any]) -> bool:
        if not self.actors:
            return True
        movie_actors = set(movie.get("actors", []) or [])
        return any(a in movie_actors for a in self.actors)


class DirectorEquals(Condition):
    """电影导演是指定导演之一。"""

    def __init__(self, directors: Iterable[str]):
        self.directors = [d for d in directors if d]

    def evaluate(self, movie: Dict[str, Any]) -> bool:
        if not self.directors:
            return True
        return movie.get("director") in self.directors


class RatingAtLeast(Condition):
    """电影评分不低于指定值。"""

    def __init__(self, min_rating: float):
        self.min_rating = float(min_rating)

    def evaluate(self, movie: Dict[str, Any]) -> bool:
        rating = movie.get("rating")
        if rating is None:
            return False
        return rating >= self.min_rating


class YearBetween(Condition):
    """电影上映年份在 [min_year, max_year] 闭区间内。"""

    def __init__(self, min_year: int = None, max_year: int = None):
        self.min_year = min_year
        self.max_year = max_year

    def evaluate(self, movie: Dict[str, Any]) -> bool:
        year = movie.get("year")
        if year is None:
            return False
        if self.min_year is not None and year < self.min_year:
            return False
        if self.max_year is not None and year > self.max_year:
            return False
        return True


class DurationAtMost(Condition):
    """电影时长不超过指定分钟数。"""

    def __init__(self, max_duration: int):
        self.max_duration = int(max_duration)

    def evaluate(self, movie: Dict[str, Any]) -> bool:
        duration = movie.get("duration")
        if duration is None:
            return False
        return duration <= self.max_duration


# =========================================================
# 规则 (Rule) —— 多个 Condition 通过 AND 组合
# =========================================================
class Rule:
    """
    一条完整的推荐规则。
    rule.conditions 是一个 Condition 列表，电影必须满足所有条件才匹配。
    """

    def __init__(self, conditions: List[Condition]):
        self.conditions = conditions

    def matches(self, movie: Dict[str, Any]) -> bool:
        """判断一部电影是否满足所有条件。"""
        for cond in self.conditions:
            if not cond.evaluate(movie):
                return False
        return True

    def __repr__(self):
        return f"Rule(conditions={self.conditions!r})"


# =========================================================
# 规则引擎 (RuleEngine)
# =========================================================
class RuleEngine:
    """核心匹配引擎。"""

    @staticmethod
    def apply(rule: Rule, movies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        对电影列表应用规则，返回所有匹配的电影。
        结果按评分从高到低排序。
        """
        matched = [m for m in movies if rule.matches(m)]
        # 评分高的排前面；评分为 None 的排最后
        matched.sort(key=lambda m: (m.get("rating") is None, -(m.get("rating") or 0)))
        return matched


# =========================================================
# 便捷构造: 把用户输入字典转成 Rule
# =========================================================
def build_rule_from_input(user_input: Dict[str, Any]) -> Rule:
    """
    把界面层传入的用户输入字典转换为 Rule 对象。
    user_input 字段约定:
        - genres:        List[str]  选中的类型
        - actors:        List[str]  选中的演员
        - director:      str        选中的导演(单选, None 表示不限)
        - min_rating:    float      最低评分
        - min_year:      int or None 最早年份
        - max_year:      int or None 最晚年份
        - max_duration:  int or None 最长时长(分钟)

    所有未提供/为空的条件都会被跳过 (即"不限")。
    """
    conditions: List[Condition] = []

    genres = user_input.get("genres") or []
    if genres:
        conditions.append(GenreContains(genres))

    actors = user_input.get("actors") or []
    if actors:
        conditions.append(ActorContains(actors))

    director = user_input.get("director")
    if director:
        # 单选也用 DirectorEquals, 内部按列表处理以保持接口一致
        conditions.append(DirectorEquals([director]))

    min_rating = user_input.get("min_rating")
    if min_rating is not None:
        conditions.append(RatingAtLeast(min_rating))

    min_year = user_input.get("min_year")
    max_year = user_input.get("max_year")
    if min_year is not None or max_year is not None:
        conditions.append(YearBetween(min_year, max_year))

    max_duration = user_input.get("max_duration")
    if max_duration is not None:
        conditions.append(DurationAtMost(max_duration))

    return Rule(conditions)
