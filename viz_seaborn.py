from typing import List, Any
import seaborn as sns
import matplotlib.pyplot as plt

def fig_hist(values: List[Any], title: str, xlabel: str):
    vals = [v for v in values if isinstance(v, (int, float))]
    fig = plt.Figure(figsize=(9, 3))
    ax = fig.add_subplot(111)
    sns.histplot(vals, kde=True, ax=ax)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    return fig

def fig_box(values: List[Any], title: str, ylabel: str):
    vals = [v for v in values if isinstance(v, (int, float))]
    fig = plt.Figure(figsize=(9, 3))
    ax = fig.add_subplot(111)
    sns.boxplot(x=vals, ax=ax)
    ax.set_title(title)
    ax.set_xlabel(ylabel)
    return fig
