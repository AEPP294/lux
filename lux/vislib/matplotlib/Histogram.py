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

from lux.vislib.matplotlib.MatplotlibChart import MatplotlibChart
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


class Histogram(MatplotlibChart):
    """
    Histogram is a subclass of AltairChart that render as a histograms.
    All rendering properties for histograms are set here.

    See Also
    --------
    matplotlib.org
    """

    def __init__(self, vis, fig, ax):
        super().__init__(vis, fig, ax)

    def __repr__(self):
        return f"Histogram <{str(self.vis)}>"

    def initialize_chart(self):
        self.tooltip = False
        measure = self.vis.get_attr_by_data_model("measure", exclude_record=True)[0]
        msr_attr = self.vis.get_attr_by_channel(measure.channel)[0]

        msr_attr_abv = msr_attr.attribute

        if len(msr_attr.attribute) > 17:
            msr_attr_abv = msr_attr.attribute[:10] + "..." + msr_attr.attribute[-7:]

        x_min = self.vis.min_max[msr_attr.attribute][0]
        x_max = self.vis.min_max[msr_attr.attribute][1]

        # msr_attr.attribute = msr_attr.attribute.replace(".", "")

        x_range = abs(max(self.vis.data[msr_attr.attribute]) - min(self.vis.data[msr_attr.attribute]))
        plot_range = abs(x_max - x_min)
        markbar = x_range / plot_range * 12

        df = pd.DataFrame(self.data)

        objects = df[msr_attr.attribute]

        counts, bins = np.histogram(self.data)
        self.ax.hist(bins[:-1], bins, weights=counts, range=(x_min, x_max), rwidth=0.6)

        x_label = ""
        y_label = ""
        if measure.channel == "x":
            x_label = f"{msr_attr.attribute} (binned)"
            y_label = "Number of Records"
        elif measure.channel == "y":
            x_label = "Number of Records"
            y_label = f"{msr_attr.attribute} (binned)"

        self.ax.set_xlabel(x_label)
        self.ax.set_ylabel(y_label)
        plt.tight_layout()

        self.code += "import matplotlib.pyplot as plt\n"
        self.code += "import numpy as np\n"
        self.code += "from math import nan\n"
        self.code += f"df = pd.DataFrame({str(self.data.to_dict())})\n"

        self.code += f"fig, ax = plt.subplots()\n"
        self.code += f"objects = df['{msr_attr.attribute}']\n"

        self.code += f"counts, bins = np.histogram({str(self.data.to_dict())})\n"
        self.code += f"ax.hist(bins[:-1], bins, weights=counts, range=('{x_min}', '{x_max}'))\n"
        self.code += f"ax.set_xlabel('{x_label}')\n"
        self.code += f"ax.set_ylabel('{y_label}')\n"
        self.code += f"fig\n"
