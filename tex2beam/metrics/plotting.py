import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def plot_metrics(
    metrics: pd.DataFrame,
    bins: str = 10,
    figsize: tuple = (10, 3),
    sharey: bool = True,
    stat="count",
    cumulative=False,
    plot_title: str = None,
) -> None:
    args = {"bins": bins, "stat": stat, "cumulative": cumulative}
    # plot the distribution of precision, recall, f1 and kendall tau
    fig, axes = plt.subplots(ncols=4, figsize=figsize, sharey=sharey)

    sns.histplot(metrics["precision"], ax=axes[0], **args)
    sns.histplot(metrics["recall"], ax=axes[1], **args)
    sns.histplot(metrics["f1"], ax=axes[2], **args)
    sns.histplot(metrics["kendall_tau"], ax=axes[3], **args)

    axes[0].set_title("Precision")
    axes[1].set_title("Recall")
    axes[2].set_title("F1")
    axes[3].set_title("Kendall's $\\tau$")

    for ax in axes:
        ax.set_xlim(-0.1, 1.1)
        ax.set_xlabel("")
        ax.set_ylabel("")

    axes[-1].set_xlim(-1.1, 1.1)
    axes[0].set_ylabel("Count")

    if plot_title:
        fig.suptitle(plot_title)

    plt.tight_layout()
    plt.show()


def metrics_bar_plot(
    df: pd.DataFrame,
    figsize: tuple = (10, 3),
    plot_title: str = None,
    col: str = None,
    row: str = None,
    col_wrap: int = None,
    kind: str = "bar",
) -> plt.Figure:
    args = {}
    id_vars = ["Threshold"]
    if col:
        args["col"] = col
        id_vars.append(col)
    if row:
        args["row"] = row
        id_vars.append(row)
    if col_wrap:
        args["col_wrap"] = col_wrap

    df_tmp = df.rename(
        columns={
            "precision": "Precision",
            "recall": "Recall",
            "f1": "F1-score",
            "kendall_tau": "Kendall's $\\tau$",
            "threshold": "Threshold",
        }
    )

    df_plot = df_tmp.melt(
        id_vars=id_vars,
        value_vars=["Precision", "Recall", "F1-score", "Kendall's $\\tau$"],
    )

    fig = sns.catplot(
        data=df_plot,
        x="variable",
        y="value",
        hue="Threshold",
        kind="bar",
        aspect=2,
        legend_out=False,
        palette="tab10",
        **args,
    )

    fig.set_axis_labels("", "Score")
    if plot_title:
        plt.suptitle(plot_title)
    plt.tight_layout()
    plt.show()
    return fig


def plot_dataset_stats(
    df: pd.DataFrame, figsize: tuple = (10, 3), plot_title: str = None
) -> None:
    """Plot the distribution of the dataset statistics.

    Args:
        df: DataFrame containing the dataset statistics.
        figsize: Size of the plot.
        plot_title: Title of the plot.

    Returns:
        None
    """
    fig, axes = plt.subplots(ncols=4, figsize=figsize)
    sns.histplot(df["Frame Count"], ax=axes[0])
    sns.histplot(df["Word Count"], ax=axes[1])
    sns.histplot(df["Bullets/Frame"], ax=axes[2])
    sns.histplot(df["Words/Frame"], ax=axes[3])

    axes[0].set_title("Number of Slides")
    axes[1].set_title("Word Count")
    axes[2].set_title("Bullets per Frame")
    axes[3].set_title("Words per Frame")

    for ax in axes:
        ax.set_xlabel("")
        ax.set_ylabel("")

    axes[0].set_ylabel("Count")

    if plot_title:
        fig.suptitle(plot_title)

    plt.tight_layout()
    plt.show()

def plot_rouge_scores(
    df: pd.DataFrame,
    figsize: tuple = (10, 3),
    plot_title: str = None,
    **kwargs,
) -> plt.Figure:
    """Plot the distribution of the ROUGE scores.

    Args:
        df: DataFrame containing the ROUGE scores.
        figsize: Size of the plot.
        plot_title: Title of the plot.

    Returns:
        None
    """
    df_tmp = df.rename(
        columns={
            "rouge1": "ROUGE-1",
            "rouge2": "ROUGE-2",
            "rougeL": "ROUGE-L",
        }
    )

    df_plot = df_tmp.melt(
        id_vars="Method",
        value_vars=["ROUGE-1", "ROUGE-2", "ROUGE-L"],
        var_name="Metric",
        value_name="Value",
    )

    fig = sns.catplot(
        data=df_plot,
        x="Metric",
        y="Value",
        hue="Method",
        kind="bar",
        aspect=2,
        legend_out=False,
        palette="tab10",
        **kwargs,
    )

    fig.set_axis_labels("", "")
    if plot_title:
        plt.suptitle(plot_title)
    plt.tight_layout()
    plt.show()
    return fig



    # axes[0].set_title("ROUGE-1")
    # axes[1].set_title("ROUGE-2")
    # axes[2].set_title("ROUGE-L")

    # for ax in axes:
    #     ax.set_xlabel("")
    #     ax.set_ylabel("")

    # axes[0].set_ylabel("Count")

    g.set_axis_labels("", "Score")
    if plot_title:
        plt.suptitle(plot_title)
    plt.tight_layout()
    plt.show()
    