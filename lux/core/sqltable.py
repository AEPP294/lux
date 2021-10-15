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

import traceback

# from lux.executor.Executor import *
import warnings
from typing import Callable, Dict, List, Union

import pandas as pd

from lux.core.frame import LuxDataFrame
from lux.core.series import LuxSeries
from lux.history.history import History
from lux.utils.date_utils import is_datetime_series
from lux.utils.message import Message
from lux.utils.utils import check_import_lux_widget
from lux.vis.Clause import Clause
from lux.vis.Vis import Vis
from lux.vis.VisList import VisList


class LuxSQLTable(LuxDataFrame):
    """
    A subclass of Lux.LuxDataFrame that houses other variables and functions for generating visual recommendations. Does not support normal pandas functionality.
    """

    # MUST register here for new properties!!
    _metadata = [
        "_intent",
        "_inferred_intent",
        "_data_type",
        "unique_values",
        "cardinality",
        "_rec_info",
        "_min_max",
        "_current_vis",
        "_widget",
        "_recommendation",
        "_prev",
        "_history",
        "_saved_export",
        "_sampled",
        "_toggle_pandas_display",
        "_message",
        "_pandas_only",
        "pre_aggregated",
        "_type_override",
        "_length",
        "_setup_done",
    ]

    def __init__(self, *args, table_name="", **kw):
        super(LuxSQLTable, self).__init__(*args, **kw)

        if lux.config.executor.name != "GeneralDatabaseExecutor":
            from lux.executor.SQLExecutor import SQLExecutor

            lux.config.executor = SQLExecutor()

        self._length = 0
        self._setup_done = False
        if table_name != "":
            self.set_SQL_table(table_name)
        warnings.formatwarning = lux.warning_format

    def __len__(self):
        if self._setup_done:
            return self._length
        else:
            return super(LuxSQLTable, self).__len__()

    def set_SQL_table(self, t_name):
        # function that ties the Lux Dataframe to a SQL database table
        if self.table_name != "":
            warnings.warn(
                f"\nThis LuxSQLTable is already tied to a database table. Please create a new Lux dataframe and connect it to your table '{t_name}'.",
                stacklevel=2,
            )
        else:
            self.table_name = t_name

        try:
            lux.config.executor.compute_dataset_metadata(self)
        except Exception as error:
            error_str = str(error)
            if f'relation "{t_name}" does not exist' in error_str:
                warnings.warn(
                    f"\nThe table '{t_name}' does not exist in your database./",
                    stacklevel=2,
                )

    def maintain_metadata(self):
        # Check that metadata has not yet been computed
        if not hasattr(self, "_metadata_fresh") or not self._metadata_fresh:
            # only compute metadata information if the dataframe is non-empty
            lux.config.executor.compute_dataset_metadata(self)
            self._infer_structure()
            self._metadata_fresh = True

    def expire_metadata(self):
        """
        Expire all saved metadata to trigger a recomputation the next time the data is required.
        """
        # self._metadata_fresh = False
        # self._data_type = None
        # self.unique_values = None
        # self.cardinality = None
        # self._min_max = None
        # self.pre_aggregated = None

    def _ipython_display_(self):
        import ipywidgets as widgets
        from IPython.display import HTML, Markdown, clear_output, display

        try:
            if self._pandas_only:
                display(self.display_pandas())
                self._pandas_only = False
            if not self.index.nlevels >= 2 or self.columns.nlevels >= 2:
                self.maintain_metadata()

                if self._intent != [] and (not hasattr(self, "_compiled") or not self._compiled):
                    from lux.processor.Compiler import Compiler

                    self.current_vis = Compiler.compile_intent(self, self._intent)

            if lux.config.default_display == "lux":
                self._toggle_pandas_display = False
            else:
                self._toggle_pandas_display = True

            # df_to_display.maintain_recs() # compute the recommendations (TODO: This can be rendered in another thread in the background to populate self._widget)
            self.maintain_recs()

            # Observers(callback_function, listen_to_this_variable)
            self._widget.observe(self.remove_deleted_recs, names="deletedIndices")
            self._widget.observe(self.set_intent_on_click, names="selectedIntentIndex")

            button = widgets.Button(
                description="Toggle Table/Lux",
                layout=widgets.Layout(width="200px", top="6px", bottom="6px"),
            )
            self.output = widgets.Output()
            self._sampled = lux.config.executor.execute_preview(self)
            display(button, self.output)

            def on_button_clicked(b):
                with self.output:
                    if b:
                        self._toggle_pandas_display = not self._toggle_pandas_display
                    clear_output()

                    # create connection string to display
                    connect_str = self.table_name
                    connection_type = str(type(lux.config.SQLconnection))
                    if "psycopg2.extensions.connection" in connection_type:
                        connection_dsn = lux.config.SQLconnection.get_dsn_parameters()
                        host_name = connection_dsn["host"]
                        host_port = connection_dsn["port"]
                        dbname = connection_dsn["dbname"]
                        connect_str = host_name + ":" + host_port + "/" + dbname

                    elif "sqlalchemy.engine.base.Engine" in connection_type:
                        db_connection = str(lux.config.SQLconnection)
                        db_start = db_connection.index("@") + 1
                        db_end = len(db_connection) - 1
                        connect_str = db_connection[db_start:db_end]

                    if self._toggle_pandas_display:
                        notification = "Here is a preview of the **{}** database table: **{}**".format(
                            self.table_name, connect_str
                        )
                        display(Markdown(notification), self._sampled.display_pandas())
                    else:
                        # b.layout.display = "none"
                        display(self._widget)
                        # b.layout.display = "inline-block"

            button.on_click(on_button_clicked)
            on_button_clicked(None)

        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            if lux.config.pandas_fallback:
                warnings.warn(
                    "\nUnexpected error in rendering Lux widget and recommendations. "
                    "Falling back to Pandas display.\n"
                    "Please report the following issue on Github: https://github.com/lux-org/lux/issues \n",
                    stacklevel=2,
                )
                warnings.warn(traceback.format_exc())
                display(self.display_pandas())
            else:
                raise
