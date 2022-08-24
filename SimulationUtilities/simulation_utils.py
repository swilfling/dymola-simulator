import os
from typing import List

import numpy as np
import pandas as pd
import seaborn as sns
import tikzplotlib
from matplotlib import pyplot as plt, dates as mdates

########################################### Simulation #################################################################

def create_df(trajectories, labels):
    """
    Create dataframe from trajectories
    @param trajectories: trajectory values
    @param labels: labels
    @return dataframe
    """
    return pd.DataFrame(data=np.array(trajectories[1:]).T, columns=labels[1:], index=pd.TimedeltaIndex(trajectories[0], unit='s'))

######################################### Plotting ####################################################################

def plot_multiple_results(list_simulation_results: List[pd.DataFrame], plot_path, output_file_name, **kwargs):
    """
    Plot multiple simulation results in one plot
    @param list_simulation_results: list of dataframes containing results
    @param plot_path: plot dir
    @param output_file_name: filename
    Optional arguments: plotting arguments
    for instance ylim, xlim, ylabel, figsize, set_colors...
    """
    if len(list_simulation_results) > 0:
        colors = kwargs.pop('colors', None)
        fig, ax = create_figure(output_file_name, **kwargs)
        linestyles=["--" if i % 2 else "-" for i in range(len(list_simulation_results))]
        for simulation_results, linestyle in zip(list_simulation_results, linestyles):
            cycler = plt.cycler(color=sns.color_palette(colors, simulation_results.shape[1]))
            plot_df(ax,simulation_results, linestyle=linestyle, set_colors=kwargs.pop('set_colors',False), cycler=cycler, show_ylabel=True)
        save_figure(plot_path, output_file_name)


def plot_result(data, plot_path="./", output_file_name='Result', store_to_csv=True, **kwargs):
    """
    Plot simulation results
    @param data: dataframe containing results
    @param plot_path: plot dir
    @param output_file_name: filename
    @param store_to_csv: additionally store csv
    Optional arguments: plotting arguments
    for instance ylim, xlim, ylabel, figsize,...
    """
    fig, ax, = create_figure(output_file_name, figsize=kwargs.pop('figsize', None))
    plt.xlabel('Time')
    if kwargs.get('ylim',None):
        plt.set_ylim(kwargs.pop('ylim'))
    if kwargs.get('ylabel',None):
        plt.ylabel(kwargs.pop('ylabel'))
    plot_df(ax, data, **kwargs)
    save_figure(plot_path,output_file_name)
    if store_to_csv:
        data.to_csv(os.path.join(plot_path, f'{output_file_name}.csv'), index=True)


def create_figure(fig_title="", **kwargs):
    """
    Create figure
    @param fig_title: Title
    @return: figure, axis handle
    """
    fig = plt.figure(figsize=kwargs.pop('figsize',(20, 10)))
    plt.tight_layout()
    plt.grid('both')
    plt.suptitle(fig_title)
    ax = plt.gca()
    return fig, ax


def plot_df(ax: plt.Axes, simulation_results: pd.DataFrame, **kwargs):
    """
    Plot pandas data frame on axis.
    @param ax: Axis to plot on
    @param simulation_results: data frame
    Optional arguments:
    show_legend: Decide whether to show legend or not
    show_ylabel: Show ylabel
    cycler: cycler for colormap
    set_colors: if use of cycler necessary
    xdate_format: use xdate format
    """
    if simulation_results is not None:
        show_legend = kwargs.pop('show_legend', True)
        if kwargs.pop('show_ylabel', True):
            ax.set_ylabel(label_list_to_str(list(simulation_results.columns)))
        cycler = kwargs.pop('cycler',None)
        if kwargs.pop('set_colors', False):
            ax.set_prop_cycle(cycler)
        if kwargs.get('xdate_format', None):
            ax.xaxis.set_major_formatter(mdates.DateFormatter(kwargs.pop('xdate_format')))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        if type(simulation_results.index) == pd.TimedeltaIndex:
            ax.plot(create_time_axis_days(simulation_results.index), simulation_results, **kwargs)
            ax.set_xlabel("Time [Days]")
        else:
            ax.plot(simulation_results, **kwargs)
        if show_legend:
            ax.legend(simulation_results.columns)


def save_figure(plot_path, output_file_name, format="png",store_tikz=True):
    """
    Save figure - store to tikz optional
    @param plot_path: dir to plot
    @param output_file_name: filename
    @param format: file format
    @param store_tikz: store to tikz
    """
    filename = str(output_file_name).replace(" ", "_")
    plt.savefig(os.path.join(plot_path, f"{filename}.{format}"), format=format)
    if store_tikz:
        tikzplotlib.save(os.path.join(plot_path, f"{filename}.tex"))
    plt.show()


def label_list_to_str(labels):
    return ", ".join(label for label in labels) if type(labels) == list else str(labels)


def create_time_axis_days(index, divider=3600 * 24):
    return [val.total_seconds() / divider for val in index]