"""基于规则的电影推荐系统核心模块。"""

from .data_loader import load_movies, get_unique_values
from .rule_engine import (
    Condition,
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
from .recommender import Recommender

__all__ = [
    "load_movies",
    "get_unique_values",
    "Condition",
    "GenreContains",
    "ActorContains",
    "DirectorEquals",
    "RatingAtLeast",
    "YearBetween",
    "DurationAtMost",
    "Rule",
    "RuleEngine",
    "build_rule_from_input",
    "Recommender",
]
