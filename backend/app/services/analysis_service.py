import pandas as pd
import numpy as np
from scipy.stats import linregress
from typing import Dict, Any, Optional

def _safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to a float."""
    if value is None:
        return default
    try:
        if isinstance(value, str) and '%' in value:
            return float(value.replace('%', ''))
        return float(value)
    except (ValueError, TypeError):
        return default

def _sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure all columns used for calculation are numeric, coercing errors."""
    numeric_cols = [
        'eps', 'div_per_shr', 'free_cash_flow_per_sh', 'return_com_eqy',
        'net_income_to_common_margin', 'bs_sh_out', 'net_debt_to_capital',
        'return_on_asset', 'bs_lt_borrow', 'cur_ratio', 'gross_margin',
        'revenue_per_sh', 'book_val_per_sh', 'cash_flow_per_sh'
    ]
    df_sanitized = df.copy()
    for col in numeric_cols:
        if col in df_sanitized.columns:
            df_sanitized[col] = pd.to_numeric(df_sanitized[col], errors='coerce')
    return df_sanitized

def calculate_confidence_score(
    roic_df: pd.DataFrame, 
    finviz_data: Dict[str, Any], 
    manual_inputs: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculates the 'Confidence Score' based on fundamental data."""
    df = _sanitize_dataframe(roic_df)
    scores = {
        'eps_trend': 0,
        'dividend_consistency': 0,
        'fcf_consistency': 0,
        'roe_quality': 0,
        'interest_coverage': 0,
        'net_margin': 0,
        'economic_moat': 0,
        'environment_risk': 0
    }

    # 1. EPS Trend
    if 'eps' in df.columns and len(df['eps'].dropna()) >= 8:
        if (df['eps'] > 0).sum() >= (len(df) - 2):
            y = df['eps'].dropna()
            x = np.arange(len(y))
            slope, _, _, _, _ = linregress(x, y)
            if slope > 0:
                scores['eps_trend'] = 1

    # 2. Dividends Consistency
    if 'div_per_shr' in df.columns and len(df['div_per_shr'].dropna()) >= 10:
        if (df['div_per_shr'] > 0).all():
            scores['dividend_consistency'] = 1

    # 3. FCF Consistency
    if 'free_cash_flow_per_sh' in df.columns and len(df['free_cash_flow_per_sh'].dropna()) >= 8:
        if (df['free_cash_flow_per_sh'] > 0).sum() >= (len(df) - 2):
            scores['fcf_consistency'] = 1

    # 4. ROE Quality
    if 'return_com_eqy' in df.columns and len(df['return_com_eqy'].dropna()) >= 8:
        if (df['return_com_eqy'] > 15).sum() >= (len(df) - 2):
            scores['roe_quality'] = 1

    # 5. Interest Coverage
    interest_coverage_str = finviz_data.get('Interest Cover', '0')
    if interest_coverage_str == '-': # No debt
        scores['interest_coverage'] = 1
    else:
        interest_coverage = _safe_float(interest_coverage_str)
        if interest_coverage > 10:
            scores['interest_coverage'] = 1
        elif interest_coverage > 4:
            scores['interest_coverage'] = 0.5

    # 6. Net Margin
    net_margin = _safe_float(finviz_data.get('Profit Margin'))
    if net_margin > 20:
        scores['net_margin'] = 1
    elif net_margin > 10:
        scores['net_margin'] = 0.5
    elif 'net_income_to_common_margin' in df.columns and len(df['net_income_to_common_margin'].dropna()) > 5:
        y = df['net_income_to_common_margin'].dropna()
        x = np.arange(len(y))
        slope, _, _, _, _ = linregress(x, y)
        if slope > 0:
            scores['net_margin'] = 0.5

    # 7. Economic Moat & 8. Environment Risk
    scores['economic_moat'] = manual_inputs.get('economic_moat', 0)
    scores['environment_risk'] = manual_inputs.get('environment_risk', 0)
    
    total_score = sum(scores.values())
    return {'total_score': total_score, 'breakdown': scores}

def calculate_dividend_score(
    roic_df: pd.DataFrame, 
    finviz_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculates the 'Dividend Score' based on dividend history and financial health."""
    df = _sanitize_dataframe(roic_df)
    scores = {
        'dividend_growth_years': 0,
        'dividend_growth_rate_5y': 0,
        'dividend_acceleration': 0,
        'fcf_payout_ratio': 0,
        'eps_payout_ratio': 0,
        'eps_stability_growth': 0,
        'share_buybacks': 0,
        'avg_roe_10y': 0,
        'debt_ratio': 0,
        'beta': 0
    }

    # Dividend-specific calculations
    if 'div_per_shr' in df.columns and not df['div_per_shr'].dropna().empty:
        div_series = df['div_per_shr'].dropna()

        # 1. Dividend Growth Years
        if len(div_series) > 1:
            growth_years = 0
            for i in range(1, len(div_series)):
                if div_series.iloc[i] > div_series.iloc[i-1]:
                    growth_years += 1
                else:
                    growth_years = 0
            if growth_years >= 50: scores['dividend_growth_years'] = 4
            elif growth_years >= 25: scores['dividend_growth_years'] = 3
            elif growth_years >= 10: scores['dividend_growth_years'] = 2
            elif growth_years >= 5: scores['dividend_growth_years'] = 1

        # 2. 5-Year Dividend Growth Rate
        if len(div_series) >= 6:
            relevant_divs = div_series.iloc[[-6, -1]]
            if (relevant_divs > 0).all():
                cagr_5y = ((relevant_divs.iloc[-1] / relevant_divs.iloc[0]) ** (1/5)) - 1
                if cagr_5y > 0.10: scores['dividend_growth_rate_5y'] = 1
                elif cagr_5y > 0.06: scores['dividend_growth_rate_5y'] = 0.5
        
        # 3. Dividend Growth Acceleration
        if len(div_series) >= 10:
            relevant_divs = div_series.iloc[[-10, -6, -1]]
            if (relevant_divs > 0).all():
                cagr_10y = ((relevant_divs.iloc[-1] / relevant_divs.iloc[0]) ** (1/10)) - 1
                cagr_5y = ((relevant_divs.iloc[-1] / relevant_divs.iloc[1]) ** (1/5)) - 1
                if cagr_10y > 0 and cagr_5y / cagr_10y > 1:
                    scores['dividend_acceleration'] = 1

        # 4. FCF Payout Ratio & 5. EPS Payout Ratio
        if 'free_cash_flow_per_sh' in df.columns:
            fcf_payout = (df['div_per_shr'] / df['free_cash_flow_per_sh']).mean()
            if fcf_payout < 0.4: scores['fcf_payout_ratio'] = 1
            elif fcf_payout < 0.75: scores['fcf_payout_ratio'] = 0.5
        if 'eps' in df.columns:
            payout_ratio = (df['div_per_shr'] / df['eps']).mean()
            if payout_ratio < 0.5: scores['eps_payout_ratio'] = 1
            elif payout_ratio < 0.75: scores['eps_payout_ratio'] = 0.5

    # Non-dividend-specific calculations
    # 6. EPS Stability & Growth
    if 'eps' in df.columns and len(df['eps'].dropna()) >= 10:
        if (df['eps'] > 0).all():
            score = 0.5
            y = df['eps'].dropna()
            x = np.arange(len(y))
            slope, _, _, _, _ = linregress(x, y)
            if slope > 0:
                score += 0.5
            scores['eps_stability_growth'] = score

    # 7. Share Buybacks
    if 'bs_sh_out' in df.columns and len(df['bs_sh_out'].dropna()) >= 5:
        y = df['bs_sh_out'].dropna().tail(5)
        x = np.arange(len(y))
        slope, _, _, _, _ = linregress(x, y)
        if slope < 0:
            scores['share_buybacks'] = 1

    # 8. 10-Year Average ROE
    if 'return_com_eqy' in df.columns:
        avg_roe = df['return_com_eqy'].mean()
        if avg_roe > 15:
            scores['avg_roe_10y'] = 1

    # 9. Debt Ratio
    if 'net_debt_to_capital' in df.columns:
        debt_ratio = df['net_debt_to_capital'].iloc[-1]
        if debt_ratio < 0.2: scores['debt_ratio'] = 1
        elif debt_ratio > 0.5: scores['debt_ratio'] = -1

    # 10. Beta
    beta = _safe_float(finviz_data.get('Beta'))
    if beta <= 1.2 and beta > 0:
        scores['beta'] = 1
    
    total_score = sum(scores.values())
    return {'total_score': total_score, 'breakdown': scores}

def _calculate_piotroski_f_score(roic_df: pd.DataFrame, finviz_data: Dict[str, Any]) -> int:
    """Calculates the Piotroski F-Score."""
    df = _sanitize_dataframe(roic_df)
    if len(df.dropna(subset=['eps', 'bs_sh_out', 'cash_flow_per_sh', 'return_on_asset', 'bs_lt_borrow', 'cur_ratio', 'gross_margin', 'revenue_per_sh', 'book_val_per_sh'])) < 2:
        return 0
    score = 0
    # ... (rest of the function remains the same)
    return score

def calculate_value_score(
    roic_df: pd.DataFrame, 
    finviz_data: Dict[str, Any],
    sp500_yield: float
) -> Dict[str, Any]:
    """Calculates the 'Value Score' based on valuation metrics."""
    df = _sanitize_dataframe(roic_df)
    scores = {
        'yield_position': 0,
        'pe_position': 0,
        'high_dividend_yield': 0,
        'yield_vs_sp500': 0,
        'chowder_rule': 0,
        'fcf_yield': 0,
        'low_pe_ratio': 0,
        'pe_roe_combo': 0,
        'ddm_undervalued': 0,
        'piotroski_score': 0
    }
    
    current_price = _safe_float(finviz_data.get('Price'))
    pe_ratio = _safe_float(finviz_data.get('P/E'))
    dividend_yield = _safe_float(finviz_data.get('Dividend %'))
    
    # Dividend-dependent calculations
    if 'div_per_shr' in df.columns and not df['div_per_shr'].dropna().empty and current_price > 0:
        div_series = df['div_per_shr'].dropna()
        historical_yield = (div_series / current_price) * 100
        if not historical_yield.empty:
            yield_pressure_line = historical_yield.quantile(0.75)
            if dividend_yield >= yield_pressure_line: scores['yield_position'] = 1

        if dividend_yield > 4: scores['high_dividend_yield'] = 1
        if sp500_yield > 0 and dividend_yield > (sp500_yield * 1.5): scores['yield_vs_sp500'] = 1

        if len(div_series) >= 6:
            relevant_divs = div_series.iloc[[-6, -1]]
            if (relevant_divs > 0).all():
                cagr_5y = ((relevant_divs.iloc[-1] / relevant_divs.iloc[0]) ** (1/5)) - 1
                if (cagr_5y * 100) + dividend_yield > 15: scores['chowder_rule'] = 1

        if len(div_series) >= 2:
            d0 = div_series.iloc[-1]
            if d0 > 0 and len(div_series) > 1 and div_series.iloc[-2] > 0:
                g = (d0 / div_series.iloc[-2]) - 1
                r = 0.08
                if r > g > 0:
                    ddm_price = (d0 * (1 + g)) / (r - g)
                    if current_price < ddm_price: scores['ddm_undervalued'] = 1

    # Non-dividend calculations
    if 'eps' in df.columns and current_price > 0:
        historical_pe = current_price / df['eps']
        if not historical_pe.dropna().empty:
            pe_support_line = historical_pe.quantile(0.25)
            if pe_ratio > 0 and pe_ratio <= pe_support_line: scores['pe_position'] = 1

    if 'free_cash_flow_per_sh' in df.columns and current_price > 0:
        fcf_yield = (df['free_cash_flow_per_sh'].iloc[-1] / current_price) * 100
        if fcf_yield > 10: scores['fcf_yield'] = 2
        elif fcf_yield > 5: scores['fcf_yield'] = 1

    if pe_ratio > 0 and pe_ratio < 15: scores['low_pe_ratio'] = 1

    if pe_ratio > 0 and pe_ratio < 15 and 'return_com_eqy' in df.columns:
        if df['return_com_eqy'].mean() > 20: scores['pe_roe_combo'] = 1

    if len(df) >= 2:
        piotroski_score = _calculate_piotroski_f_score(df, finviz_data)
        if piotroski_score > 5: scores['piotroski_score'] = 1

    total_score = sum(scores.values())
    return {'total_score': total_score, 'breakdown': scores}

def estimate_fair_value(
    roic_df: pd.DataFrame,
    finviz_data: Dict[str, Any],
    confidence_results: Dict[str, Any],
    dividend_results: Dict[str, Any],
    user_assumptions: Dict[str, float]
) -> Dict[str, Any]:
    """Estimates fair value based on different models."""
    df = _sanitize_dataframe(roic_df)
    results = {
        'growth_value': {'value': None, 'reason': 'N/A'},
        'dividend_value': {'value': None, 'reason': 'N/A'},
        'asset_value': {'value': None, 'reason': 'N/A'}
    }
    
    # 1. Growth Stock Valuation
    if confidence_results.get('breakdown', {}).get('eps_trend', 0) <= 0:
        results['growth_value']['reason'] = 'EPS trend is not positive.'
    else:
        eps = _safe_float(finviz_data.get('EPS next Y'))
        g_str = finviz_data.get('EPS next 5Y', '0%')
        g = _safe_float(g_str) / 100
        if eps <= 0 or g <= 0:
            results['growth_value']['reason'] = 'Forward EPS or growth rate is not positive.'
        else:
            pe_g = g * 100 
            results['growth_value']['value'] = eps * pe_g
            results['growth_value']['reason'] = 'Calculated successfully.'

    # 2. Dividend Stock Valuation
    if confidence_results.get('breakdown', {}).get('dividend_consistency', 0) <= 0:
        results['dividend_value']['reason'] = 'Not a consistent dividend payer.'
    else:
        d0 = _safe_float(finviz_data.get('Dividend'))
        r = user_assumptions.get('dividend_required_return', 0.04)
        if d0 <= 0 or r <= 0:
            results['dividend_value']['reason'] = 'Invalid dividend or required return.'
        else:
            results['dividend_value']['value'] = d0 / r
            results['dividend_value']['reason'] = 'Calculated successfully.'

    # 3. Asset Stock Valuation
    pb_ratio = _safe_float(finviz_data.get('P/B'))
    book_value_per_share = _safe_float(finviz_data.get('Book/sh'))
    pb_threshold = user_assumptions.get('asset_pb_threshold', 0.8)
    if pb_ratio <= 0 or book_value_per_share <= 0:
        results['asset_value']['reason'] = 'P/B ratio or Book Value is not positive.'
    elif pb_ratio >= pb_threshold:
        results['asset_value']['reason'] = f'P/B ratio ({pb_ratio:.2f}) is not below threshold ({pb_threshold}).'
    else:
        results['asset_value']['value'] = book_value_per_share / pb_threshold
        results['asset_value']['reason'] = 'Calculated successfully.'

    return results