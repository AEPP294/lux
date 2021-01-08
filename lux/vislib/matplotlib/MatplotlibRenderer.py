#  Copyright 2019-2020 The Lux Authors.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import lux
import pandas as pd
from lux.vislib.matplotlib.BarChart import BarChart
from lux.vislib.matplotlib.ScatterChart import ScatterChart
from lux.vislib.matplotlib.LineChart import LineChart
from lux.vislib.matplotlib.Histogram import Histogram
from lux.vislib.matplotlib.Heatmap import Heatmap
import matplotlib.pyplot as plt


class MatplotlibRenderer:
    """
    Renderer for Charts based on Matplotlib (https://matplotlib.org/)
    """

    def __init__(self, output_type="matplotlib"):
        self.output_type = output_type

    def __repr__(self):
        return f"MatplotlibRenderer"

    def create_vis(self, vis, standalone=True):
        """
        Input Vis object and return a visualization specification

        Parameters
        ----------
        vis: lux.vis.Vis
                Input Vis (with data)
        standalone: bool
                Flag to determine if outputted code uses user-defined variable names or can be run independently
        Returns
        -------
        chart : altair.Chart
                Output Altair Chart Object
        """
        # Lazy Evaluation for 2D Binning
        if vis.mark == "scatter" and vis._postbin:
            vis._mark = "heatmap"
            from lux.executor.PandasExecutor import PandasExecutor

            PandasExecutor.execute_2D_binning(vis)
        # If a column has a Period dtype, or contains Period objects, convert it back to Datetime
        if vis.data is not None:
            for attr in list(vis.data.columns):
                if pd.api.types.is_period_dtype(vis.data.dtypes[attr]) or isinstance(
                    vis.data[attr].iloc[0], pd.Period
                ):
                    dateColumn = vis.data[attr]
                    vis.data[attr] = pd.PeriodIndex(dateColumn.values).to_timestamp()
                if pd.api.types.is_interval_dtype(vis.data.dtypes[attr]) or isinstance(
                    vis.data[attr].iloc[0], pd.Interval
                ):
                    vis.data[attr] = vis.data[attr].astype(str)
        plt.ioff()
        plt.rcParams.update({'font.size': 12})
        fig, ax = plt.subplots(figsize=(4.5, 4))
        ax.set_axisbelow(True)
        ax.grid(color="#dddddd")
        ax.spines["right"].set_color("#dddddd")
        ax.spines["top"].set_color("#dddddd")
        if vis.mark == "histogram":
            chart = Histogram(vis, fig, ax)
        elif vis.mark == "bar":
            chart = BarChart(vis, fig, ax)
        elif vis.mark == "scatter":
            chart = ScatterChart(vis, fig, ax)
        elif vis.mark == "line":
            chart = LineChart(vis, fig, ax)
        elif vis.mark == "heatmap":
            chart = Heatmap(vis, fig, ax)
        else:
            chart = None
            return chart
        if chart:
            if self.output_type == "matplotlib":
                return {"config": chart.chart, "vislib": "matplotlib"}
            if self.output_type == "matplotlib_code":
                return chart.code