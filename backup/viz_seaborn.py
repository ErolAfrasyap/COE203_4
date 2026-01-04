import seaborn as sns
import matplotlib.pyplot as plt

def fig_hist(values, title, xlabel):
    fig = plt.figure(figsize=(10, 4))
    ax = fig.add_subplot(111)
    sns.histplot(values, kde=True, ax=ax, bins=20)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Count")
    fig.tight_layout()
    return fig

def fig_box(values, title, xlabel):
    fig = plt.figure(figsize=(10, 4))
    ax = fig.add_subplot(111)
    sns.boxplot(x=values, ax=ax)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    fig.tight_layout()
    return fig
