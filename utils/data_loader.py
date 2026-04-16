import pandas as pd
import requests

def parse_uploaded_csv(uploaded_file):
    prices = pd.read_csv(uploaded_file, parse_dates=["Date"])
    prices.set_index("Date", inplace=True)
    prices = prices.apply(pd.to_numeric, errors="coerce")
    prices = prices.dropna(how="all")
    prices = prices.dropna(axis=1, how="all")

    if prices.empty:
        raise ValueError("Uploaded CSV does not contain usable price data.")

    return prices

def fetch_eodhd_data(api_token, symbols_text, start_date, end_date):
    symbol_list = [s.strip() for s in symbols_text.split(",") if s.strip()]
    if not symbol_list:
        raise ValueError("Please provide at least one stock symbol.")

    all_data = pd.DataFrame()
    failed_symbols = []

    for symbol in symbol_list:
        url = (
            f"https://eodhd.com/api/eod/{symbol}"
            f"?from={start_date}&to={end_date}&api_token={api_token}&period=d&fmt=json"
        )

        response = requests.get(url, timeout=30)

        if response.status_code != 200:
            failed_symbols.append(symbol)
            continue

        try:
            json_data = response.json()
        except Exception:
            failed_symbols.append(symbol)
            continue

        if not isinstance(json_data, list) or len(json_data) == 0:
            failed_symbols.append(symbol)
            continue

        df = pd.DataFrame(json_data)

        if "date" not in df.columns:
            failed_symbols.append(symbol)
            continue

        price_col = None
        if "adjusted_close" in df.columns:
            price_col = "adjusted_close"
        elif "close" in df.columns:
            price_col = "close"

        if price_col is None:
            failed_symbols.append(symbol)
            continue

        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        all_data[symbol] = pd.to_numeric(df[price_col], errors="coerce")

    all_data = all_data.dropna(how="all")

    if all_data.empty:
        raise ValueError("No valid data was fetched from EODHD for the selected symbols/date range.")

    return all_data, failed_symbols

def update_data_session_state(st, prices, source_name):
    st.session_state.loaded_prices = prices
    st.session_state.data_source = source_name
    st.session_state.date_range = f"{prices.index.min().date()} to {prices.index.max().date()}"
    st.session_state.stocks_loaded = prices.shape[1]
    st.session_state.trading_days = prices.shape[0]
    st.session_state.selected_stock = prices.columns[0] if len(prices.columns) > 0 else None