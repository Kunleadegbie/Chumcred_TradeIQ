# utils/ngx_symbols.py

NGX_TICKER_MAP = {
    "AIRTELAFRI": "AIRTELAFRI.XNSA",
    "MTNN": "MTNN.XNSA",
    "DANGCEM": "DANGCEM.XNSA",
    "BUACEMENT": "BUACEMENT.XNSA",
    "ZENITHBANK": "ZENITHBANK.XNSA",
    "ZENITH": "ZENITHBANK.XNSA",
    "GTCO": "GTCO.XNSA",
    "GTB": "GTCO.XNSA",
    "ACCESSCORP": "ACCESSCORP.XNSA",
    "ACCESS": "ACCESSCORP.XNSA",
    "UBA": "UBA.XNSA",
    "FBNH": "FBNH.XNSA",
    "SEPLAT": "SEPLAT.XNSA",
    "NGXGROUP": "NGXGROUP.XNSA",
    "STANBIC": "STANBIC.XNSA",
    "STANBICIBTC": "STANBIC.XNSA",
}

SUPPORTED_NGX_SYMBOLS = {
    "AIRTELAFRI.XNSA",
    "MTNN.XNSA",
    "DANGCEM.XNSA",
    "BUACEMENT.XNSA",
    "ZENITHBANK.XNSA",
    "GTCO.XNSA",
    "ACCESSCORP.XNSA",
    "UBA.XNSA",
    "FBNH.XNSA",
    "SEPLAT.XNSA",
    "NGXGROUP.XNSA",
    "STANBIC.XNSA",
}


def normalize_ngx_symbol(symbol: str) -> str:
    """
    Convert user input like:
    - MTNN
    - mtnn
    - MTNN.LG
    - MTNN.XNSA
    into standard EODHD NGX format:
    - MTNN.XNSA
    """
    if not symbol:
        return ""

    s = symbol.strip().upper()

    # direct alias map first
    if s in NGX_TICKER_MAP:
        return NGX_TICKER_MAP[s]

    # convert old .LG suffix to .XNSA
    if s.endswith(".LG"):
        s = s[:-3] + ".XNSA"

    # leave .XNSA unchanged
    if s.endswith(".XNSA"):
        return s

    # add .XNSA if no suffix exists
    if "." not in s:
        return f"{s}.XNSA"

    return s


def normalize_ngx_symbol_list(symbols_text: str) -> list[str]:
    """
    Convert comma-separated input into a clean unique list.
    """
    raw_symbols = [s.strip() for s in symbols_text.split(",") if s.strip()]
    normalized = [normalize_ngx_symbol(s) for s in raw_symbols]

    # preserve order while removing duplicates
    unique_symbols = list(dict.fromkeys(normalized))
    return unique_symbols


def get_display_name(symbol: str) -> str:
    """
    Convert MTNN.XNSA -> MTNN for charts/tables.
    """
    if not symbol:
        return ""
    return symbol.replace(".XNSA", "").replace(".LG", "")