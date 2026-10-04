# 基于规则的电影推荐系统

《人工智能基础》课程学习项目，使用 Streamlit 展示可解释的电影筛选规则。

## 功能

- 按类型、演员、导演、最低评分、年份区间、最长时长组合查询。
- 各种条件之间采用 AND；类型或演员多选采用 OR。
- 结果按评分降序排列；空条件显示全部电影。
- 内置 50 条静态电影演示数据；不依赖外部 API。

## 本地运行

建议 Python 3.12。进入本目录后执行：

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m streamlit run app.py --server.address 127.0.0.1
```

Linux/macOS 将 `.venv/Scripts/python` 改为 `.venv/bin/python`。浏览器访问本机 8501 端口。

## 测试

```powershell
python -m pytest tests -q
```

## 代码结构

- `src/data_loader.py`：读取 CSV，转换列表与数值字段。
- `src/rule_engine.py`：原子条件、规则组合和筛选排序。
- `src/recommender.py`：供界面调用的推荐器。
- `app.py`：Streamlit 界面。
- `tests/test_rule_engine.py`：规则匹配与排序的单元测试。

数据中的电影标题、主创及评分用于课程演示，评分不是实时更新。系统按显式规则过滤，不包含用户画像、模型训练或在线数据采集。
