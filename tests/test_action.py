from .context import lux
import pytest
import pandas as pd

from lux.view.View import View
def test_vary_filter_val():
    df = pd.read_csv("lux/data/olympic.csv")
    view = View(["Height","SportType=Ball"])
    view = view.load(df)
    df.set_context_as_view(view)
    df.show_more()
    assert len(df.recommendation["Filter"]) == len(df["SportType"].unique())-1