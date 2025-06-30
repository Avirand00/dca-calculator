import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go


def calculate_dca(filtered_data: pd.DataFrame, regular_contribution: float, initial_investment: float):
    """Return a DataFrame containing the DCA log and totals.

    Parameters
    ----------
    filtered_data : pd.DataFrame
        DataFrame indexed by date with a ``Close`` column.
    regular_contribution : float
        The contribution added at each interval.
    initial_investment : float
        Extra amount invested on the first interval.

    Returns
    -------
    Tuple[pd.DataFrame, float, float]
        The DCA log, total shares and total amount invested.
    """

    total_invested = 0.0
    total_shares = 0.0
    dca_log = []

    for i, (date, row) in enumerate(filtered_data.iterrows()):
        price = row["Close"]
        contribution = regular_contribution
        if i == 0:
            contribution += initial_investment
        total_shares += contribution / price
        total_invested += contribution
        dca_log.append(
            {
                "Date": date,
                "Price": price,
                "Total Shares": total_shares,
                "Total Investment": total_invested,
                "Portfolio Value": total_shares * price,
            }
        )

    return pd.DataFrame(dca_log), total_shares, total_invested


def main():

    st.set_page_config(page_title="DCA Calculator", page_icon="💰")

    # Title
    st.title("Dollar Cost Averaging (DCA) Calculator")

    # Sidebar Inputs
    st.sidebar.header("Investment Parameters")
    ticker = st.sidebar.text_input("Stock Ticker (e.g., AAPL, TSLA)", value="AAPL")
    initial_investment = st.sidebar.number_input("Initial Investment ($)", min_value=0.0, value=0.0)
    regular_contribution = st.sidebar.number_input("Regular Contribution ($)", min_value=0.0, value=100.0)
    frequency = st.sidebar.selectbox("Contribution Frequency", ["Daily", "Weekly", "Monthly"])

    # Date Picker for Backtesting Range
    st.sidebar.header("Backtesting Date Range")
    start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime("2018-01-01"))
    end_date = st.sidebar.date_input("End Date", value=pd.to_datetime("today"))

    if start_date >= end_date:
        st.error("Start date must be earlier than end date. Please adjust the dates.")
        st.stop()

    # Fetch Stock Data within Selected Date Range
    try:
        stock_data = yf.Ticker(ticker).history(start=start_date, end=end_date)
        stock_data.reset_index(inplace=True)
        stock_data = stock_data[["Date", "Close"]]
        stock_data["Date"] = pd.to_datetime(stock_data["Date"])

        # Remove timezone information from the Date column
        stock_data["Date"] = stock_data["Date"].dt.tz_localize(None)

        if stock_data.empty:
            st.error("No data available for the selected date range. Please choose a different range.")
            st.stop()

        st.sidebar.success(f"Data fetched for {ticker}!")
    except Exception as e:
        st.sidebar.error("Error fetching stock data. Please check the ticker symbol.")
        st.stop()

    # Filter Data Based on Selected Dates (Redundant but Ensures Safety)
    filtered_data = stock_data[(stock_data["Date"] >= pd.Timestamp(start_date)) & (stock_data["Date"] <= pd.Timestamp(end_date))]

    # Adjust frequency
    filtered_data.set_index("Date", inplace=True)
    if frequency == "Weekly":
        filtered_data = filtered_data.resample("W").mean()
    elif frequency == "Monthly":
        filtered_data = filtered_data.resample("M").mean()

    dca_df, total_shares, total_invested = calculate_dca(
        filtered_data,
        regular_contribution=regular_contribution,
        initial_investment=initial_investment,
    )

    contributions = dca_df["Total Investment"]
    portfolio_value = dca_df["Portfolio Value"]

    # Results
    st.subheader("Results")
    final_value = portfolio_value.iloc[-1]
    net_gain_loss = final_value - total_invested

    st.write(f"**Total Invested:** ${total_invested:.2f}")
    st.write(f"**Final Portfolio Value:** ${final_value:.2f}")
    st.write(f"**Net Gain/Loss:** ${net_gain_loss:.2f} ({net_gain_loss / total_invested * 100:.2f}%)")

    # Visualizations
    st.subheader("Visualizations")

    # Asset Price Over Time
    price_fig = go.Figure()
    price_fig.add_trace(
        go.Scatter(x=filtered_data.index, y=filtered_data["Close"], mode="lines", name="Asset Price")
    )
    price_fig.update_layout(title="Asset Price Over Time", xaxis_title="Date", yaxis_title="Price ($)")
    st.plotly_chart(price_fig)

    # Portfolio Value vs Total Invested
    portfolio_fig = go.Figure()
    portfolio_fig.add_trace(
        go.Scatter(x=filtered_data.index, y=portfolio_value, mode="lines", name="Portfolio Value")
    )
    portfolio_fig.add_trace(
        go.Scatter(
            x=filtered_data.index,
            y=contributions,
            mode="lines",
            name="Total Invested",
            line=dict(dash="dash"),
        )
    )
    portfolio_fig.update_layout(title="Portfolio Value vs Total Invested", xaxis_title="Date", yaxis_title="Value ($)")
    st.plotly_chart(portfolio_fig)

    # Stacked Bar Chart
    fig = go.Figure()

    # Add Total Invested
    fig.add_trace(
        go.Bar(
            x=dca_df["Date"],
            y=dca_df["Total Investment"],
            name="Total Invested",
            marker_color="blue",
        )
    )

    # Add Profit/Loss
    fig.add_trace(
        go.Bar(
            x=dca_df["Date"],
            y=dca_df["Portfolio Value"] - dca_df["Total Investment"],
            name="Profit/Loss",
            marker_color="green",
        )
    )

    # Update layout for better appearance
    fig.update_layout(
        title="DCA Results: Total Invested and Profit/Loss",
        xaxis_title="Years",
        yaxis_title="Amount ($)",
        barmode="stack",  # Stacked bars
        legend_title="Legend",
    )

    # Display in Streamlit
    st.plotly_chart(fig)


if __name__ == "__main__":
    main()

