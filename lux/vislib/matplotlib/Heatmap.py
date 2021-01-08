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


class Heatmap(MatplotlibChart):
    """
    Heatmap is a subclass of MatplotlibChart that render as a heatmap.
    All rendering properties for heatmap are set here.

    See Also
    --------
    matplotlib.org
    """

    def __init__(self, vis, fig, ax):
        super().__init__(vis, fig, ax)

    def __repr__(self):
        return f"Heatmap <{str(self.vis)}>"

    def initialize_chart(self):
        # return NotImplemented
        x_attr = self.vis.get_attr_by_channel("x")[0]
        y_attr = self.vis.get_attr_by_channel("y")[0]

        x_attr_abv = x_attr.attribute
        y_attr_abv = y_attr.attribute

        if len(x_attr.attribute) > 25:
            x_attr_abv = x_attr.attribute[:15] + "..." + x_attr.attribute[-10:]
        if len(y_attr.attribute) > 25:
            y_attr_abv = y_attr.attribute[:15] + "..." + y_attr.attribute[-10:]

        df = pd.pivot_table(data=self.data, index="xBinStart", values="count", columns="yBinStart")
        df = df.apply(lambda x: np.log(x), axis=1)
        df = df.values

        plt.imshow(df, cmap="Blues")
        self.ax.set_aspect("auto")
        plt.gca().invert_yaxis()

        self.ax.set_xlabel(x_attr_abv)
        self.ax.set_ylabel(y_attr_abv)
        self.ax.grid(False)
        plt.tight_layout()

        # self.code += "import matplotlib.pyplot as plt\n"
        # self.code += "import numpy as np\n"
        # self.code += "from math import nan\n"
        # self.code += f"df = pd.pivot_table({str(self.data.to_dict())})\n"

        # self.code += f"fig, ax = plt.subplots()\n"
        # self.code += f"objects = df['{bar_attr}']\n"
        # self.code += f"y_pos = np.arange(len(objects))\n"
        # self.code += f"performance = df['{measure_attr}']\n"

        # self.code += f"ax.bar(y_pos, performance, align='center', alpha=0.5)\n"
        # self.code += f"ax.set_xlabel('{x_attr_abv}')\n"
        # self.code += f"ax.set_ylabel('{y_attr_abv}')\n"
        self.code += f"fig\n"
