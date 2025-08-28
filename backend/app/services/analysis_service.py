import pandas as pd
import numpy as np
from scipy.stats import linregress
from typing import Dict, Any, Optional

def _safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to a float."""
    if value is None:
        return default
    try:
        # Handle percentage strings
        if isinstance(value, str) and '%' in value:
            return float(value.replace('%', ''))
        return float(value)
    except (ValueError, TypeError):
        return default

def calculate_confidence_score(
    roic_df: pd.DataFrame, 
    finviz_data: Dict[str, Any], 
    manual_inputs: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculates the 'Confidence Score' based on fundamental data."""
    scores = {}
    total_score = 0

    print(roic_df.columns)

    # 1. EPS Trend
    if 'eps' in roic_df.columns and len(roic_df['eps'].dropna()) >= 8:
        if (roic_df['eps'] > 0).sum() >= (len(roic_df) - 2):
            y = roic_df['eps'].dropna()
            x = np.arange(len(y))
            slope, _, _, _, _ = linregress(x, y)
            if slope > 0:
                scores['eps_trend'] = 1
                total_score += 1
            else:
                scores['eps_trend'] = 0
        else:
            scores['eps_trend'] = 0
    else:
        scores['eps_trend'] = 0

    # 2. Dividends Consistency
    if 'div_per_shr' in roic_df.columns and len(roic_df['div_per_shr']) >= 10:
        if roic_df['div_per_shr'].notna().sum() >= 10 and (roic_df['div_per_shr'] > 0).all():
            scores['dividend_consistency'] = 1
            total_score += 1
        else:
            scores['dividend_consistency'] = 0
    else:
        scores['dividend_consistency'] = 0

    # 3. FCF Consistency
    if 'free_cash_flow_per_sh' in roic_df.columns and len(roic_df['free_cash_flow_per_sh'].dropna()) >= 8:
        if (roic_df['free_cash_flow_per_sh'] > 0).sum() >= (len(roic_df) - 2):
            scores['fcf_consistency'] = 1
            total_score += 1
        else:
            scores['fcf_consistency'] = 0
    else:
        scores['fcf_consistency'] = 0

    # 4. ROE Quality
    if 'return_com_eqy' in roic_df.columns and len(roic_df['return_com_eqy'].dropna()) >= 8:
        if (roic_df['return_com_eqy'] > 15).sum() >= (len(roic_df) - 2):
            scores['roe_quality'] = 1
            total_score += 1
        else:
            scores['roe_quality'] = 0
    else:
        scores['roe_quality'] = 0

    # 5. Interest Coverage
    interest_coverage_str = finviz_data.get('Interest Cover', '0')
    if interest_coverage_str == '-': # No debt
        scores['interest_coverage'] = 1
        total_score += 1
    else:
        interest_coverage = _safe_float(interest_coverage_str)
        if interest_coverage > 10:
            scores['interest_coverage'] = 1
            total_score += 1
        elif interest_coverage > 4:
            scores['interest_coverage'] = 0.5
            total_score += 0.5
        else:
            scores['interest_coverage'] = 0

    # 6. Net Margin
    net_margin = _safe_float(finviz_data.get('Profit Margin'))
    if net_margin > 20:
        scores['net_margin'] = 1
        total_score += 1
    elif net_margin > 10:
        scores['net_margin'] = 0.5
        total_score += 0.5
    elif 'net_income_to_common_margin' in roic_df.columns and len(roic_df['net_income_to_common_margin'].dropna()) > 5:
        y = roic_df['net_income_to_common_margin'].dropna()
        x = np.arange(len(y))
        slope, _, _, _, _ = linregress(x, y)
        if slope > 0:
            scores['net_margin'] = 0.5
            total_score += 0.5
        else:
            scores['net_margin'] = 0
    else:
        scores['net_margin'] = 0

    # 7. Economic Moat & 8. Environment Risk
    moat_score = manual_inputs.get('economic_moat', 0)
    scores['economic_moat'] = moat_score
    total_score += moat_score
    
    risk_score = manual_inputs.get('environment_risk', 0)
    scores['environment_risk'] = risk_score
    total_score += risk_score

    return {'total_score': total_score, 'breakdown': scores}

def calculate_dividend_score(
    roic_df: pd.DataFrame, 
    finviz_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculates the 'Dividend Score' based on dividend history and financial health."""
    scores = {}
    total_score = 0
    
    div_series = roic_df['div_per_shr'].dropna()

    # 1. Dividend Growth Years
    if len(div_series) > 1:
        growth_years = 0
        for i in range(1, len(div_series)):
            if div_series.iloc[i] > div_series.iloc[i-1]:
                growth_years += 1
            else:
                growth_years = 0 # Reset on any decrease
        
        if growth_years >= 50: scores['dividend_growth_years'] = 4
        elif growth_years >= 25: scores['dividend_growth_years'] = 3
        elif growth_years >= 10: scores['dividend_growth_years'] = 2
        elif growth_years >= 5: scores['dividend_growth_years'] = 1
        else: scores['dividend_growth_years'] = 0
        total_score += scores['dividend_growth_years']

    # 2. 5-Year Dividend Growth Rate
    if len(div_series) >= 6:
        cagr_5y = ((div_series.iloc[-1] / div_series.iloc[-6]) ** (1/5)) - 1
        if cagr_5y > 0.10:
            scores['dividend_growth_rate_5y'] = 1
            total_score += 1
        elif cagr_5y > 0.06:
            scores['dividend_growth_rate_5y'] = 0.5
            total_score += 0.5
        else:
            scores['dividend_growth_rate_5y'] = 0
    else:
        scores['dividend_growth_rate_5y'] = 0

    # 3. Dividend Growth Acceleration
    if len(div_series) >= 10:
        cagr_10y = ((div_series.iloc[-1] / div_series.iloc[-10]) ** (1/10)) - 1
        cagr_5y = ((div_series.iloc[-1] / div_series.iloc[-6]) ** (1/5)) - 1
        if cagr_10y > 0 and cagr_5y / cagr_10y > 1:
            scores['dividend_acceleration'] = 1
            total_score += 1
        else:
            scores['dividend_acceleration'] = 0
    else:
        scores['dividend_acceleration'] = 0

    # 4. FCF Payout Ratio
    if 'free_cash_flow_per_sh' in roic_df.columns:
        fcf_payout = (roic_df['div_per_shr'] / roic_df['free_cash_flow_per_sh']).mean()
        if fcf_payout < 0.4:
            scores['fcf_payout_ratio'] = 1
            total_score += 1
        elif fcf_payout < 0.75:
            scores['fcf_payout_ratio'] = 0.5
            total_score += 0.5
        else:
            scores['fcf_payout_ratio'] = 0
    else:
        scores['fcf_payout_ratio'] = 0

    # 5. EPS Payout Ratio
    if 'eps' in roic_df.columns:
        payout_ratio = (roic_df['div_per_shr'] / roic_df['eps']).mean()
        if payout_ratio < 0.5:
            scores['eps_payout_ratio'] = 1
            total_score += 1
        elif payout_ratio < 0.75:
            scores['eps_payout_ratio'] = 0.5
            total_score += 0.5
        else:
            scores['eps_payout_ratio'] = 0
    else:
        scores['eps_payout_ratio'] = 0

    # 6. EPS Stability & Growth
    if 'eps' in roic_df.columns and len(roic_df['eps'].dropna()) >= 10:
        if (roic_df['eps'] > 0).all():
            scores['eps_stability_growth'] = 0.5
            y = roic_df['eps'].dropna()
            x = np.arange(len(y))
            slope, _, _, _, _ = linregress(x, y)
            if slope > 0:
                scores['eps_stability_growth'] += 0.5
            total_score += scores['eps_stability_growth']
        else:
            scores['eps_stability_growth'] = 0
    else:
        scores['eps_stability_growth'] = 0

    # 7. Share Buybacks
    if 'bs_sh_out' in roic_df.columns and len(roic_df['bs_sh_out'].dropna()) >= 5:
        y = roic_df['bs_sh_out'].dropna().tail(5)
        x = np.arange(len(y))
        slope, _, _, _, _ = linregress(x, y)
        if slope < 0:
            scores['share_buybacks'] = 1
            total_score += 1
        else:
            scores['share_buybacks'] = 0
    else:
        scores['share_buybacks'] = 0

    # 8. 10-Year Average ROE
    if 'return_com_eqy' in roic_df.columns:
        avg_roe = roic_df['return_com_eqy'].mean()
        if avg_roe > 15:
            scores['avg_roe_10y'] = 1
            total_score += 1
        else:
            scores['avg_roe_10y'] = 0
    else:
        scores['avg_roe_10y'] = 0

    # 9. Debt Ratio
    # Net Debt = (Short Term Debt + Long Term Debt) - Cash & Equivalents
    # Market Cap from Finviz
    if 'net_debt_to_capital' in roic_df.columns:
        
        debt_ratio = roic_df['net_debt_to_capital'].iloc[-1]
        '''
        market_cap_str = finviz_data.get('Market Cap', '0')
        market_cap = 0
        if 'B' in market_cap_str:
            market_cap = _safe_float(market_cap_str.replace('B', '')) * 1e9
        elif 'M' in market_cap_str:
            market_cap = _safe_float(market_cap_str.replace('M', '')) * 1e6
        '''
        #if market_cap > 0:
        #    debt_ratio = net_debt / market_cap
        if debt_ratio < 0.2:
            scores['debt_ratio'] = 1
            total_score += 1
        elif debt_ratio > 0.5:
            scores['debt_ratio'] = -1
            total_score -= 1
        else:
            scores['debt_ratio'] = 0
        #else:
        #    scores['debt_ratio'] = 0
    else:
        scores['debt_ratio'] = 0

    # 10. Beta
    beta = _safe_float(finviz_data.get('Beta'))
    if beta <= 1.2 and beta > 0:
        scores['beta'] = 1
        total_score += 1
    else:
        scores['beta'] = 0

    return {'total_score': total_score, 'breakdown': scores}

def _calculate_piotroski_f_score(roic_df: pd.DataFrame, finviz_data: Dict[str, Any]) -> int:
    """Calculates the Piotroski F-Score."""
    score = 0
    df = roic_df.iloc[-2:].reset_index() # Last two years
    
    # Profitability
    net_income = df['eps'].iloc[-1] * df['bs_sh_out'].iloc[-1]
    ocf = df['cash_flow_per_sh'].iloc[-1] * df['bs_sh_out'].iloc[-1]
    if net_income > 0: score += 1
    if ocf > net_income: score += 1
    if df['return_on_asset'].iloc[-1] > 0: score += 1
    
    # Leverage, Liquidity, Source of Funds
    if df['bs_lt_borrow'].iloc[-1] <= df['bs_lt_borrow'].iloc[-2]: score += 1
    if df['cur_ratio'].iloc[-1] > df['cur_ratio'].iloc[-2]: score += 1
    if df['bs_sh_out'].iloc[-1] <= df['bs_sh_out'].iloc[-2]: score += 1
        
    # Operating Efficiency
    if df['gross_margin'].iloc[-1] > df['gross_margin'].iloc[-2]: score += 1
    ato_1 = df['revenue_per_sh'].iloc[-1]/df['book_val_per_sh'].iloc[-1]
    ato_2 = df['revenue_per_sh'].iloc[-2]/df['book_val_per_sh'].iloc[-2]
    if ato_1 > ato_2: score += 1
        
    return score

def calculate_value_score(
    roic_df: pd.DataFrame, 
    finviz_data: Dict[str, Any],
    sp500_yield: float
) -> Dict[str, Any]:
    """Calculates the 'Value Score' based on valuation metrics."""
    scores = {}
    total_score = 0
    
    current_price = _safe_float(finviz_data.get('Price'))
    pe_ratio = _safe_float(finviz_data.get('P/E'))
    dividend_yield = _safe_float(finviz_data.get('Dividend %'))
    
    # 1. Yield vs 10-Year High
    if 'div_per_shr' in roic_df.columns and current_price > 0:
        historical_yield = (roic_df['div_per_shr'] / current_price) * 100
        if not historical_yield.empty:
            yield_pressure_line = historical_yield.quantile(0.75) # Approx. resistance
            if dividend_yield >= yield_pressure_line:
                scores['yield_position'] = 1
                total_score += 1
            else:
                scores['yield_position'] = 0
    else:
        scores['yield_position'] = 0

    # 2. P/E vs 10-Year Low
    if 'eps' in roic_df.columns and current_price > 0:
        historical_pe = current_price / roic_df['eps']
        if not historical_pe.empty:
            pe_support_line = historical_pe.quantile(0.25) # Approx. support
            if pe_ratio <= pe_support_line:
                scores['pe_position'] = 1
                total_score += 1
            else:
                scores['pe_position'] = 0
    else:
        scores['pe_position'] = 0

    # 3. Dividend Yield > 4%
    if dividend_yield > 4:
        scores['high_dividend_yield'] = 1
        total_score += 1
    else:
        scores['high_dividend_yield'] = 0

    # 4. Dividend Yield vs S&P 500
    if sp500_yield > 0 and dividend_yield > (sp500_yield * 1.5):
        scores['yield_vs_sp500'] = 1
        total_score += 1
    else:
        scores['yield_vs_sp500'] = 0

    # 5. Chowder Rule
    if len(roic_df['div_per_shr'].dropna()) >= 6:
        cagr_5y = ((roic_df['div_per_shr'].iloc[-1] / roic_df['div_per_shr'].iloc[-6]) ** (1/5)) - 1
        if (cagr_5y * 100) + dividend_yield > 15:
            scores['chowder_rule'] = 1
            total_score += 1
        else:
            scores['chowder_rule'] = 0
    else:
        scores['chowder_rule'] = 0

    # 6. FCF Yield
    if 'free_cash_flow_per_sh' in roic_df.columns and current_price > 0:
        fcf_yield = (roic_df['free_cash_flow_per_sh'].iloc[-1] / current_price) * 100
        if fcf_yield > 10:
            scores['fcf_yield'] = 2
            total_score += 2
        elif fcf_yield > 5:
            scores['fcf_yield'] = 1
            total_score += 1
        else:
            scores['fcf_yield'] = 0
    else:
        scores['fcf_yield'] = 0

    # 7. P/E < 15
    if pe_ratio < 15 and pe_ratio > 0:
        scores['low_pe_ratio'] = 1
        total_score += 1
    else:
        scores['low_pe_ratio'] = 0

    # 8. P/E < 15 and 10Y Avg ROE > 20%
    if pe_ratio < 15 and pe_ratio > 0 and 'return_com_eqy' in roic_df.columns:
        if roic_df['return_com_eqy'].mean() > 20:
            scores['pe_roe_combo'] = 1
            total_score += 1
        else:
            scores['pe_roe_combo'] = 0
    else:
        scores['pe_roe_combo'] = 0

    # 9. DDM (Dividend Discount Model)
    # Simplified DDM: Fair Value = D1 / (r - g)
    # D1 = D0 * (1 + g)
    if len(roic_df['div_per_shr'].dropna()) >= 2:
        d0 = roic_df['div_per_shr'].iloc[-1]
        g = (d0 / roic_df['div_per_shr'].iloc[-2]) - 1
        r = 0.08 # Required rate of return, can be made dynamic
        if r > g > 0:
            ddm_price = (d0 * (1 + g)) / (r - g)
            if current_price < ddm_price:
                scores['ddm_undervalued'] = 1
                total_score += 1
            else:
                scores['ddm_undervalued'] = 0
        else:
            scores['ddm_undervalued'] = 0
    else:
        scores['ddm_undervalued'] = 0

    # 10. Piotroski Score
    if len(roic_df) >= 2:
        piotroski_score = _calculate_piotroski_f_score(roic_df, finviz_data)
        if piotroski_score > 5:
            scores['piotroski_score'] = 1
            total_score += 1
        else:
            scores['piotroski_score'] = 0
    else:
        scores['piotroski_score'] = 0

    return {'total_score': total_score, 'breakdown': scores}

def estimate_fair_value(
    roic_df: pd.DataFrame,
    finviz_data: Dict[str, Any],
    confidence_results: Dict[str, Any],
    dividend_results: Dict[str, Any],
    user_assumptions: Dict[str, float]
) -> Dict[str, Optional[float]]:
    """Estimates fair value based on different models."""
    results = {
        'growth_value': None,
        'dividend_value': None,
        'asset_value': None
    }
    
    # 1. Growth Stock Valuation
    if confidence_results.get('breakdown', {}).get('eps_trend', 0) > 0:
        eps = _safe_float(finviz_data.get('EPS next Y'))
        g_str = finviz_data.get('EPS next 5Y', '0%')
        g = _safe_float(g_str) / 100
        if eps > 0 and g > 0:
            # Graham's Formula: V = EPS * (8.5 + 2G)
            # Using a simplified P/E = G*100 model for high growth
            pe_g = g * 100 
            results['growth_value'] = eps * pe_g

    # 2. Dividend Stock Valuation
    if confidence_results.get('breakdown', {}).get('dividend_consistency', 0) > 0:
        d0 = _safe_float(finviz_data.get('Dividend'))
        r = user_assumptions.get('dividend_required_return', 0.04)
        if d0 > 0 and r > 0:
            results['dividend_value'] = d0 / r

    # 3. Asset Stock Valuation
    pb_ratio = _safe_float(finviz_data.get('P/B'))
    book_value_per_share = _safe_float(finviz_data.get('Book/sh'))
    pb_threshold = user_assumptions.get('asset_pb_threshold', 0.8)
    if pb_ratio > 0 and pb_ratio < pb_threshold:
        results['asset_value'] = book_value_per_share / pb_threshold

    return results