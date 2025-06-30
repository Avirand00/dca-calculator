import pytest
import sys
import types
import pandas as pd

# Create minimal dummy modules to satisfy imports in calculator
sys.modules.setdefault('streamlit', types.ModuleType('streamlit'))
sys.modules.setdefault('yfinance', types.ModuleType('yfinance'))
plotly = types.ModuleType('plotly')
plotly.graph_objects = types.ModuleType('graph_objects')
sys.modules.setdefault('plotly', plotly)
sys.modules.setdefault('plotly.graph_objects', plotly.graph_objects)

from calculator import calculate_dca


def test_calculate_dca_basic():
    prices = pd.DataFrame({"Close": [10.0, 20.0, 40.0]}, index=pd.date_range('2020-01-01', periods=3))
    dca_df, total_shares, total_invested = calculate_dca(prices, regular_contribution=100, initial_investment=50)

    assert total_shares == pytest.approx(22.5)
    assert total_invested == pytest.approx(350)
    assert dca_df["Total Shares"].iloc[-1] == pytest.approx(22.5)
    assert dca_df["Total Investment"].iloc[-1] == pytest.approx(350)
