#!/usr/bin/env python3
"""
formule_report_pf.py
Modulo di calcolo per tutti gli indicatori del Report PF
Based on: SCHEMA SOCIETA' DI PERSONE ORDINARIA.docx

Implementa tutte le formule per:
- Valutazione d'impresa (NOPAT, EM Score, PD)
- Indicatori finanziari (Debt Management, Cash Generation)
- Indicatori operativi (Leverage, Productivity)
- Analisi economica (Fixed/Variable Costs, BEP)
- Sostenibilità (ROE Decomposition)
"""

from decimal import Decimal
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum
import statistics


class DebtRating(str, Enum):
    """Rating scale for debt management"""
    AAA = "AAA"
    AA = "AA"
    A_PLUS = "A+"
    A = "A"
    A_MINUS = "A-"
    BBB = "BBB"
    BB_PLUS = "BB+"
    BB = "BB"
    B_PLUS = "B+"
    B = "B"
    B_MINUS = "B-"
    CCC_PLUS = "CCC+"
    CCC = "CCC"
    C = "C"
    D = "D"
    NA = "N/A"


class ReportPFCalculator:
    """
    Calcolatore completo per Report PF - Società di Persone
    """

    def __init__(self, data_2023: Dict[str, Any], data_2022: Dict[str, Any]):
        """
        Initialize with 2-year data

        Args:
            data_2023: Most recent year data
            data_2022: Previous year data
        """
        self.current = data_2023
        self.previous = data_2022

    def _to_float(self, value: Any) -> float:
        """Safe conversion to float"""
        if isinstance(value, (int, float, Decimal)):
            return float(value)
        return 0.0

    # ========================================================================
    # SECTION 1: VALUTAZIONE DI IMPRESA (Business Valuation)
    # ========================================================================

    def calculate_em_score(self, year_data: Dict[str, Any]) -> float:
        """
        Calculate EM Score (Altman Z-Score variant for Italian businesses)

        Formula: 3.25 + 6.56 * [(Current Assets - Current Liabilities) / Total Assets]
                      + 6.72 * (Operating Income / Total Assets)
        """
        rs = year_data.get("quadro_rs", {})
        risultati = year_data.get("risultati", {})

        # Current Assets
        current_assets = (
            self._to_float(rs.get("rimanenze", 0)) +
            self._to_float(rs.get("crediti_clienti", 0)) +
            self._to_float(rs.get("altri_crediti", 0)) +
            self._to_float(rs.get("attivita_finanziarie", 0)) +
            self._to_float(rs.get("disponibilita_liquide", 0)) +
            self._to_float(rs.get("ratei_risconti_attivi", 0))
        )

        # Current Liabilities
        current_liabilities = (
            self._to_float(rs.get("debiti_banche_breve", 0)) +
            self._to_float(rs.get("debiti_fornitori", 0)) +
            self._to_float(rs.get("altri_debiti", 0)) +
            self._to_float(rs.get("ratei_risconti_passivi", 0))
        )

        total_assets = self._to_float(rs.get("totale_attivo", 1))
        operating_income = self._to_float(risultati.get("reddito_operativo", 0))

        if total_assets == 0:
            return 0.0

        working_capital_ratio = (current_assets - current_liabilities) / total_assets
        profitability_ratio = operating_income / total_assets

        em_score = 3.25 + (6.56 * working_capital_ratio) + (6.72 * profitability_ratio)

        return round(em_score, 2)

    def map_em_to_pd(self, em_score: float) -> float:
        """
        Map EM Score to Probability of Default (PD)
        Based on table from schema
        """
        if em_score >= 8.15:
            return 0.01
        elif em_score >= 7.60:
            return 0.02
        elif em_score >= 7.30:
            return 0.03
        elif em_score >= 7.00:
            return 0.04
        elif em_score >= 6.85:
            return 0.05
        elif em_score >= 6.65:
            return 0.07
        elif em_score >= 6.40:
            return 0.09
        elif em_score >= 6.25:
            return 0.14
        elif em_score >= 5.85:
            return 0.21
        elif em_score >= 5.65:
            return 0.31
        elif em_score >= 5.25:
            return 0.52
        elif em_score >= 4.95:
            return 0.86
        elif em_score >= 4.75:
            return 1.43
        elif em_score >= 4.40:
            return 2.03
        elif em_score >= 4.15:
            return 2.88
        elif em_score >= 3.75:
            return 4.09
        elif em_score >= 3.20:
            return 6.94
        elif em_score >= 2.50:
            return 11.78
        elif em_score >= 1.75:
            return 14.00
        else:
            return 20.00

    def map_pd_to_discount_rate(self, pd: float) -> float:
        """
        Map PD to discount rate R°
        Simplified mapping: R° = Risk-free rate + Credit Spread
        """
        # Risk-free rate (e.g., Italian BTPs)
        risk_free = 0.035  # 3.5%

        # Credit spread based on PD
        if pd <= 0.05:
            spread = 0.02  # 2%
        elif pd <= 0.50:
            spread = 0.04  # 4%
        elif pd <= 2.00:
            spread = 0.06  # 6%
        elif pd <= 5.00:
            spread = 0.08  # 8%
        elif pd <= 10.00:
            spread = 0.10  # 10%
        else:
            spread = 0.15  # 15%

        return risk_free + spread

    def calculate_nopat_valuation(self) -> Dict[str, Any]:
        """
        Calculate business valuation using NOPAT method

        Returns:
            Dict with EM Score, PD, discount rate, NOPAT, and valuation
        """
        # Calculate EM Score for both years
        em_2023 = self.calculate_em_score(self.current)
        em_2022 = self.calculate_em_score(self.previous)

        # Use current year EM for PD
        pd = self.map_em_to_pd(em_2023)
        discount_rate = self.map_pd_to_discount_rate(pd)

        # Calculate average NOPAT (Operating Income after tax)
        # Assuming 30% tax rate
        tax_rate = 0.30

        nopat_2023 = self._to_float(self.current.get("risultati", {}).get("reddito_operativo", 0)) * (1 - tax_rate)
        nopat_2022 = self._to_float(self.previous.get("risultati", {}).get("reddito_operativo", 0)) * (1 - tax_rate)

        avg_nopat = (nopat_2023 + nopat_2022) / 2

        # Valuation = NOPAT / Discount Rate
        valuation = avg_nopat / discount_rate if discount_rate > 0 else 0

        return {
            "em_score_2023": em_2023,
            "em_score_2022": em_2022,
            "probability_default": pd,
            "discount_rate": round(discount_rate, 4),
            "nopat_2023": round(nopat_2023, 2),
            "nopat_2022": round(nopat_2022, 2),
            "avg_nopat": round(avg_nopat, 2),
            "valuation": round(valuation, 2),
            "interpretation": self._interpret_em_score(em_2023)
        }

    def _interpret_em_score(self, em_score: float) -> str:
        """Interpret EM Score"""
        if em_score >= 7.00:
            return "Excellent financial health - Low bankruptcy risk"
        elif em_score >= 5.00:
            return "Good financial health - Moderate risk"
        elif em_score >= 3.00:
            return "Fair financial health - Some concerns"
        else:
            return "Poor financial health - High bankruptcy risk"

    # ========================================================================
    # SECTION 2: SEZIONE FINANZIARIA (Financial Indicators)
    # ========================================================================

    def calculate_debt_management(self) -> Dict[str, Any]:
        """
        Calculate Debt Management Rating

        Formula: MOL / Interest Expense
        Returns rating from AAA to D
        """
        risultati = self.current.get("risultati", {})
        costi = self.current.get("costi", {})

        mol = self._to_float(risultati.get("mol", 0))
        interest = self._to_float(costi.get("oneri_finanziari", 0))

        if mol < 0:
            return {
                "ratio": None,
                "rating": DebtRating.NA,
                "interpretation": "MOL is negative - debt management ratio not applicable"
            }

        if interest == 0:
            return {
                "ratio": float('inf'),
                "rating": DebtRating.AAA,
                "interpretation": "No interest expense - excellent position"
            }

        ratio = mol / interest
        rating = self._map_ratio_to_rating(ratio)

        return {
            "ratio": round(ratio, 2),
            "rating": rating,
            "mol": round(mol, 2),
            "interest_expense": round(interest, 2),
            "interpretation": f"Company can cover interest {ratio:.1f}x - {rating.value} rating"
        }

    def _map_ratio_to_rating(self, ratio: float) -> DebtRating:
        """Map interest coverage ratio to debt rating"""
        if ratio > 12.50:
            return DebtRating.AAA
        elif ratio > 9.50:
            return DebtRating.AA
        elif ratio > 7.50:
            return DebtRating.A_PLUS
        elif ratio > 6.00:
            return DebtRating.A
        elif ratio > 4.50:
            return DebtRating.A_MINUS
        elif ratio > 4.00:
            return DebtRating.BBB
        elif ratio > 3.50:
            return DebtRating.BB_PLUS
        elif ratio > 3.00:
            return DebtRating.BB
        elif ratio > 2.50:
            return DebtRating.B_PLUS
        elif ratio > 2.00:
            return DebtRating.B
        elif ratio > 1.50:
            return DebtRating.B_MINUS
        elif ratio > 1.25:
            return DebtRating.CCC_PLUS
        elif ratio > 0.80:
            return DebtRating.CCC
        elif ratio > 0.50:
            return DebtRating.C
        else:
            return DebtRating.D

    def calculate_cash_generation(self) -> Dict[str, Any]:
        """
        Calculate Free Cash Flow

        Formula: MOL + Ammortamenti
                 - Δ(Working Capital)
                 - Δ(Fixed Assets)
        """
        # Current year
        rs_curr = self.current.get("quadro_rs", {})
        risultati_curr = self.current.get("risultati", {})
        costi_curr = self.current.get("costi", {})
        patrimonio_curr = self.current.get("patrimonio", {})

        # Previous year
        rs_prev = self.previous.get("quadro_rs", {})
        patrimonio_prev = self.previous.get("patrimonio", {})

        # Operating Cash Flow
        mol = self._to_float(risultati_curr.get("mol", 0))
        ammortamenti = self._to_float(costi_curr.get("ammortamenti", 0))

        operating_cf = mol + ammortamenti

        # Working Capital Change
        wc_curr = self._calculate_working_capital(rs_curr)
        wc_prev = self._calculate_working_capital(rs_prev)
        delta_wc = wc_curr - wc_prev

        # Fixed Assets Change (Capex)
        fa_curr = self._to_float(patrimonio_curr.get("valore_beni_strumentali", 0))
        fa_prev = self._to_float(patrimonio_prev.get("valore_beni_strumentali", 0))
        capex = fa_curr - fa_prev

        # Free Cash Flow
        fcf = operating_cf - delta_wc - capex

        return {
            "operating_cash_flow": round(operating_cf, 2),
            "working_capital_change": round(delta_wc, 2),
            "capex": round(capex, 2),
            "free_cash_flow": round(fcf, 2),
            "components": {
                "mol": round(mol, 2),
                "ammortamenti": round(ammortamenti, 2),
                "working_capital_2023": round(wc_curr, 2),
                "working_capital_2022": round(wc_prev, 2),
                "fixed_assets_2023": round(fa_curr, 2),
                "fixed_assets_2022": round(fa_prev, 2)
            },
            "interpretation": self._interpret_fcf(fcf)
        }

    def _calculate_working_capital(self, rs: Dict[str, Any]) -> float:
        """Calculate Net Operating Working Capital"""
        current_assets = (
            self._to_float(rs.get("rimanenze", 0)) +
            self._to_float(rs.get("crediti_clienti", 0)) +
            self._to_float(rs.get("altri_crediti", 0)) +
            self._to_float(rs.get("disponibilita_liquide", 0)) +
            self._to_float(rs.get("ratei_risconti_attivi", 0))
        )

        current_liabilities = (
            self._to_float(rs.get("debiti_fornitori", 0)) +
            self._to_float(rs.get("altri_debiti", 0)) +
            self._to_float(rs.get("ratei_risconti_passivi", 0))
        )

        return current_assets - current_liabilities

    def _interpret_fcf(self, fcf: float) -> str:
        """Interpret Free Cash Flow"""
        if fcf > 0:
            return "Positive FCF - Company generates cash from operations"
        elif fcf > -50000:
            return "Slightly negative FCF - Minor cash needs"
        else:
            return "Negative FCF - Company needs external financing"

    # ========================================================================
    # SECTION 3: SEZIONE OPERATIVA (Operating Indicators)
    # ========================================================================

    def calculate_operating_leverage(self) -> Dict[str, Any]:
        """
        Calculate Operating Leverage

        Formula: Δ Operating Income / Δ Revenue
        """
        # Revenue change
        rev_curr = self._to_float(self.current.get("ricavi", {}).get("ricavi_dichiarati", 0))
        rev_prev = self._to_float(self.previous.get("ricavi", {}).get("ricavi_dichiarati", 0))
        delta_revenue = rev_curr - rev_prev

        # Operating Income change
        oi_curr = self._to_float(self.current.get("risultati", {}).get("reddito_operativo", 0))
        oi_prev = self._to_float(self.previous.get("risultati", {}).get("reddito_operativo", 0))
        delta_oi = oi_curr - oi_prev

        if delta_revenue == 0:
            leverage = 0
        else:
            leverage = delta_oi / delta_revenue

        return {
            "operating_leverage": round(leverage, 4),
            "delta_operating_income": round(delta_oi, 2),
            "delta_revenue": round(delta_revenue, 2),
            "revenue_2023": round(rev_curr, 2),
            "revenue_2022": round(rev_prev, 2),
            "operating_income_2023": round(oi_curr, 2),
            "operating_income_2022": round(oi_prev, 2),
            "interpretation": f"1% revenue change → {leverage*100:.2f}% operating income change"
        }

    def calculate_asset_turnover(self) -> Dict[str, Any]:
        """
        Calculate Asset Turnover (Capacità Produttiva)

        Formula: Fixed Assets / Revenue
        Higher ratio = less efficient asset utilization
        """
        # Current year
        fa_curr = self._to_float(self.current.get("patrimonio", {}).get("valore_beni_strumentali", 0))
        rev_curr = self._to_float(self.current.get("ricavi", {}).get("ricavi_dichiarati", 0))

        # Previous year
        fa_prev = self._to_float(self.previous.get("patrimonio", {}).get("valore_beni_strumentali", 0))
        rev_prev = self._to_float(self.previous.get("ricavi", {}).get("ricavi_dichiarati", 0))

        ratio_curr = fa_curr / rev_curr if rev_curr > 0 else 0
        ratio_prev = fa_prev / rev_prev if rev_prev > 0 else 0

        return {
            "asset_turnover_2023": round(ratio_curr, 2),
            "asset_turnover_2022": round(ratio_prev, 2),
            "fixed_assets_2023": round(fa_curr, 2),
            "fixed_assets_2022": round(fa_prev, 2),
            "revenue_2023": round(rev_curr, 2),
            "revenue_2022": round(rev_prev, 2),
            "trend": "Improving" if ratio_curr < ratio_prev else "Worsening",
            "interpretation": f"Company has {ratio_curr:.2f}€ in assets per 1€ revenue"
        }

    def calculate_production_leverage(self) -> Dict[str, Any]:
        """
        Calculate Production Leverage

        Formula: Value Added / Labor Cost
        """
        # Current year
        va_curr = self._to_float(self.current.get("risultati", {}).get("valore_aggiunto", 0))
        labor_curr = self._to_float(self.current.get("costi", {}).get("costo_personale", 0))

        # Previous year
        va_prev = self._to_float(self.previous.get("risultati", {}).get("valore_aggiunto", 0))
        labor_prev = self._to_float(self.previous.get("costi", {}).get("costo_personale", 0))

        ratio_curr = va_curr / labor_curr if labor_curr > 0 else 0
        ratio_prev = va_prev / labor_prev if labor_prev > 0 else 0

        return {
            "production_leverage_2023": round(ratio_curr, 2),
            "production_leverage_2022": round(ratio_prev, 2),
            "value_added_2023": round(va_curr, 2),
            "value_added_2022": round(va_prev, 2),
            "labor_cost_2023": round(labor_curr, 2),
            "labor_cost_2022": round(labor_prev, 2),
            "trend_pct": round((ratio_curr - ratio_prev) / ratio_prev * 100, 1) if ratio_prev > 0 else 0,
            "interpretation": f"Company generates {ratio_curr:.2f}€ value per 1€ labor cost"
        }

    def calculate_productivity_per_capita(self) -> Dict[str, Any]:
        """
        Calculate Productivity per Employee

        Formula: Value Added / Number of Employees
        """
        # Current year
        va_curr = self._to_float(self.current.get("risultati", {}).get("valore_aggiunto", 0))
        emp_curr = self._to_float(self.current.get("personale", {}).get("numero_addetti_equivalenti", 1))

        # Previous year
        va_prev = self._to_float(self.previous.get("risultati", {}).get("valore_aggiunto", 0))
        emp_prev = self._to_float(self.previous.get("personale", {}).get("numero_addetti_equivalenti", 1))

        prod_curr = va_curr / emp_curr if emp_curr > 0 else 0
        prod_prev = va_prev / emp_prev if emp_prev > 0 else 0

        change_pct = ((prod_curr - prod_prev) / prod_prev * 100) if prod_prev > 0 else 0

        return {
            "productivity_2023": round(prod_curr, 2),
            "productivity_2022": round(prod_prev, 2),
            "change_pct": round(change_pct, 1),
            "value_added_2023": round(va_curr, 2),
            "value_added_2022": round(va_prev, 2),
            "employees_2023": round(emp_curr, 2),
            "employees_2022": round(emp_prev, 2),
            "interpretation": f"Each employee generates {prod_curr:,.0f}€ value added ({change_pct:+.1f}% vs 2022)"
        }

    # ========================================================================
    # SECTION 4: SEZIONE ECONOMICA (Economic Analysis)
    # ========================================================================

    def calculate_fixed_variable_costs(self) -> Dict[str, Any]:
        """
        Analyze Fixed vs Variable Costs

        Fixed: Rent + Labor + Depreciation + Other
        Variable: Materials + Services - Inventory change
        """
        costi = self.current.get("costi", {})

        # Fixed Costs
        fixed_costs = (
            self._to_float(costi.get("godimento_beni_terzi", 0)) +
            self._to_float(costi.get("costo_personale", 0)) +
            self._to_float(costi.get("spese_collaboratori", 0)) +
            self._to_float(costi.get("altri_costi", 0)) +
            self._to_float(costi.get("ammortamenti", 0)) +
            self._to_float(costi.get("accantonamenti", 0))
        )

        # Variable Costs
        variable_costs = (
            self._to_float(costi.get("esistenze_iniziali", 0)) +
            self._to_float(costi.get("costo_materie_prime", 0)) +
            self._to_float(costi.get("costo_servizi", 0)) -
            self._to_float(costi.get("rimanenze_finali", 0))
        )

        total_costs = fixed_costs + variable_costs
        fixed_pct = (fixed_costs / total_costs * 100) if total_costs > 0 else 0
        variable_pct = (variable_costs / total_costs * 100) if total_costs > 0 else 0

        return {
            "fixed_costs": round(fixed_costs, 2),
            "variable_costs": round(variable_costs, 2),
            "total_costs": round(total_costs, 2),
            "fixed_percentage": round(fixed_pct, 1),
            "variable_percentage": round(variable_pct, 1),
            "breakdown": {
                "rent": round(self._to_float(costi.get("godimento_beni_terzi", 0)), 2),
                "labor": round(self._to_float(costi.get("costo_personale", 0)), 2),
                "depreciation": round(self._to_float(costi.get("ammortamenti", 0)), 2),
                "other_fixed": round(self._to_float(costi.get("altri_costi", 0)), 2),
                "materials": round(self._to_float(costi.get("costo_materie_prime", 0)), 2),
                "services": round(self._to_float(costi.get("costo_servizi", 0)), 2)
            },
            "interpretation": f"Cost structure: {fixed_pct:.0f}% fixed, {variable_pct:.0f}% variable"
        }

    def calculate_break_even_point(self) -> Dict[str, Any]:
        """
        Calculate Break Even Point

        Formula: Fixed Costs / (1 - (Variable Costs / Revenue))
        """
        cost_analysis = self.calculate_fixed_variable_costs()
        revenue = self._to_float(self.current.get("ricavi", {}).get("ricavi_dichiarati", 0))

        fixed_costs = cost_analysis["fixed_costs"]
        variable_costs = cost_analysis["variable_costs"]

        if revenue == 0:
            return {
                "break_even_point": 0,
                "margin_of_safety": 0,
                "interpretation": "Cannot calculate - no revenue"
            }

        contribution_margin_ratio = 1 - (variable_costs / revenue)

        if contribution_margin_ratio <= 0:
            return {
                "break_even_point": float('inf'),
                "margin_of_safety": -100,
                "interpretation": "Variable costs exceed revenue - no break-even possible"
            }

        bep = fixed_costs / contribution_margin_ratio
        margin_of_safety = ((revenue - bep) / revenue * 100) if revenue > 0 else 0

        return {
            "break_even_point": round(bep, 2),
            "actual_revenue": round(revenue, 2),
            "margin_of_safety": round(margin_of_safety, 1),
            "contribution_margin_ratio": round(contribution_margin_ratio, 3),
            "fixed_costs": round(fixed_costs, 2),
            "variable_costs": round(variable_costs, 2),
            "interpretation": self._interpret_bep(margin_of_safety)
        }

    def _interpret_bep(self, margin: float) -> str:
        """Interpret Break Even Point margin of safety"""
        if margin > 30:
            return f"Excellent safety margin ({margin:.1f}%) - Low risk"
        elif margin > 20:
            return f"Good safety margin ({margin:.1f}%) - Moderate risk"
        elif margin > 10:
            return f"Adequate safety margin ({margin:.1f}%) - Some risk"
        elif margin > 0:
            return f"Thin safety margin ({margin:.1f}%) - High risk"
        else:
            return f"Below break-even ({margin:.1f}%) - Critical situation"

    # ========================================================================
    # SECTION 5: SOSTENIBILITÀ (Sustainability)
    # ========================================================================

    def calculate_roe_sustainability(self) -> Dict[str, Any]:
        """
        Calculate ROE with decomposition and growth projection

        Formula: ROE = [(RO/TA) + (RO/TA - i/D) × (D/E)] × [(NI - NI×tax) / NI]
        where RO is projected for next year using linear trend
        """
        # Project Operating Income for 2024
        oi_2023 = self._to_float(self.current.get("risultati", {}).get("reddito_operativo", 0))
        oi_2022 = self._to_float(self.previous.get("risultati", {}).get("reddito_operativo", 0))
        oi_trend = oi_2023 - oi_2022
        oi_projected = oi_2023 + oi_trend

        # Current year data
        rs = self.current.get("quadro_rs", {})
        costi = self.current.get("costi", {})
        risultati = self.current.get("risultati", {})

        total_assets = self._to_float(rs.get("totale_attivo", 1))
        interest = self._to_float(costi.get("oneri_finanziari", 0))
        debt = (
            self._to_float(rs.get("debiti_banche_breve", 0)) +
            self._to_float(rs.get("debiti_banche_lungo", 0))
        )
        equity = self._to_float(rs.get("patrimonio_netto", 1))
        net_income = self._to_float(risultati.get("reddito_impresa", 0))

        # Calculate components
        roa = oi_projected / total_assets if total_assets > 0 else 0
        interest_rate = interest / debt if debt > 0 else 0
        leverage = debt / equity if equity > 0 else 0
        tax_rate = 0.30

        # ROE Decomposition
        roe = (roa + (roa - interest_rate) * leverage) * (1 - tax_rate)

        return {
            "roe": round(roe * 100, 2),  # as percentage
            "projected_operating_income_2024": round(oi_projected, 2),
            "components": {
                "roa": round(roa * 100, 2),
                "interest_rate": round(interest_rate * 100, 2),
                "leverage": round(leverage, 2),
                "tax_rate": round(tax_rate * 100, 1)
            },
            "trend": {
                "operating_income_2023": round(oi_2023, 2),
                "operating_income_2022": round(oi_2022, 2),
                "growth": round(oi_trend, 2)
            },
            "interpretation": self._interpret_roe(roe),
            "sustainability": "Sustainable" if roe > 0 else "Not sustainable"
        }

    def _interpret_roe(self, roe: float) -> str:
        """Interpret ROE"""
        roe_pct = roe * 100
        if roe_pct > 15:
            return f"Excellent ROE ({roe_pct:.1f}%) - Strong returns"
        elif roe_pct > 10:
            return f"Good ROE ({roe_pct:.1f}%) - Solid returns"
        elif roe_pct > 5:
            return f"Fair ROE ({roe_pct:.1f}%) - Modest returns"
        elif roe_pct > 0:
            return f"Low ROE ({roe_pct:.1f}%) - Weak returns"
        else:
            return f"Negative ROE ({roe_pct:.1f}%) - Loss-making"

    # ========================================================================
    # COMPLETE REPORT GENERATION
    # ========================================================================

    def generate_complete_report(self) -> Dict[str, Any]:
        """
        Generate complete Report PF with all indicators
        """
        return {
            "company_info": {
                "codice_fiscale": self.current.get("identificativi", {}).get("codice_fiscale"),
                "ragione_sociale": self.current.get("identificativi", {}).get("ragione_sociale"),
                "anno_corrente": self.current.get("identificativi", {}).get("anno"),
                "anno_precedente": self.previous.get("identificativi", {}).get("anno")
            },
            "valutazione": self.calculate_nopat_valuation(),
            "finanziari": {
                "debt_management": self.calculate_debt_management(),
                "cash_generation": self.calculate_cash_generation()
            },
            "operativi": {
                "operating_leverage": self.calculate_operating_leverage(),
                "asset_turnover": self.calculate_asset_turnover(),
                "production_leverage": self.calculate_production_leverage(),
                "productivity": self.calculate_productivity_per_capita()
            },
            "economici": {
                "cost_analysis": self.calculate_fixed_variable_costs(),
                "break_even": self.calculate_break_even_point()
            },
            "sostenibilita": self.calculate_roe_sustainability()
        }


class ReportPFCalculatorSemplificato:
    """
    Calculator for Contabilità Semplificata entities (Quadro RG).

    These entities have NO balance sheet (stato patrimoniale) - all quadro_rs
    fields are zero. Only ISA Prospetto Economico data is available.

    Computes 8 indicators in 3 sections:
    - FINANZIARIA: Gestione del Debito, Capacità di Generare Cassa
    - OPERATIVA: Leva Operativa, Capacità Produttiva Inutilizzata, Leva Produttiva, Produttività Pro Capite
    - ECONOMICA: Costi Fissi/Variabili, Break Even Point
    """

    def __init__(self, data_current: Dict[str, Any], data_previous: Dict[str, Any]):
        self.current = data_current
        self.previous = data_previous

    def _to_float(self, value: Any) -> float:
        if isinstance(value, (int, float, Decimal)):
            return float(value)
        return 0.0

    # --- FINANZIARIA ---

    def calculate_debt_management(self) -> Dict[str, Any]:
        """MOL / Oneri Finanziari → Rating AAA-D"""
        risultati = self.current.get("risultati", {})
        costi = self.current.get("costi", {})

        mol = self._to_float(risultati.get("mol", 0))
        interest = self._to_float(costi.get("oneri_finanziari", 0))

        if mol < 0:
            return {
                "ratio": None,
                "rating": DebtRating.NA,
                "interpretation": "MOL is negative - debt management ratio not applicable"
            }

        if interest == 0:
            return {
                "ratio": float('inf'),
                "rating": DebtRating.AAA,
                "interpretation": "No interest expense - excellent position"
            }

        ratio = mol / interest
        rating = self._map_ratio_to_rating(ratio)

        return {
            "ratio": round(ratio, 2),
            "rating": rating,
            "mol": round(mol, 2),
            "interest_expense": round(interest, 2),
            "interpretation": f"Company can cover interest {ratio:.1f}x - {rating.value} rating"
        }

    def _map_ratio_to_rating(self, ratio: float) -> DebtRating:
        if ratio > 12.50:
            return DebtRating.AAA
        elif ratio > 9.50:
            return DebtRating.AA
        elif ratio > 7.50:
            return DebtRating.A_PLUS
        elif ratio > 6.00:
            return DebtRating.A
        elif ratio > 4.50:
            return DebtRating.A_MINUS
        elif ratio > 4.00:
            return DebtRating.BBB
        elif ratio > 3.50:
            return DebtRating.BB_PLUS
        elif ratio > 3.00:
            return DebtRating.BB
        elif ratio > 2.50:
            return DebtRating.B_PLUS
        elif ratio > 2.00:
            return DebtRating.B
        elif ratio > 1.50:
            return DebtRating.B_MINUS
        elif ratio > 1.25:
            return DebtRating.CCC_PLUS
        elif ratio > 0.80:
            return DebtRating.CCC
        elif ratio > 0.50:
            return DebtRating.C
        else:
            return DebtRating.D

    def calculate_cash_generation(self) -> Dict[str, Any]:
        """
        Capacità di Generare Cassa (simplified, no balance sheet).
        Formula: MOL - Δ(Beni strumentali)
        """
        risultati_curr = self.current.get("risultati", {})
        patrimonio_curr = self.current.get("patrimonio", {})
        patrimonio_prev = self.previous.get("patrimonio", {})

        mol = self._to_float(risultati_curr.get("mol", 0))
        fa_curr = self._to_float(patrimonio_curr.get("valore_beni_strumentali", 0))
        fa_prev = self._to_float(patrimonio_prev.get("valore_beni_strumentali", 0))
        delta_fa = fa_curr - fa_prev

        cash_generation = mol - delta_fa

        return {
            "cash_generation": round(cash_generation, 2),
            "mol": round(mol, 2),
            "delta_fixed_assets": round(delta_fa, 2),
            "fixed_assets_current": round(fa_curr, 2),
            "fixed_assets_previous": round(fa_prev, 2),
            "interpretation": "Positive" if cash_generation > 0 else "Negative"
        }

    # --- OPERATIVA ---

    def calculate_operating_leverage(self) -> Dict[str, Any]:
        """Leva Operativa: Δ Reddito Operativo / Δ Ricavi"""
        rev_curr = self._to_float(self.current.get("ricavi", {}).get("ricavi_dichiarati", 0))
        rev_prev = self._to_float(self.previous.get("ricavi", {}).get("ricavi_dichiarati", 0))
        delta_revenue = rev_curr - rev_prev

        oi_curr = self._to_float(self.current.get("risultati", {}).get("reddito_operativo", 0))
        oi_prev = self._to_float(self.previous.get("risultati", {}).get("reddito_operativo", 0))
        delta_oi = oi_curr - oi_prev

        leverage = delta_oi / delta_revenue if delta_revenue != 0 else 0

        return {
            "operating_leverage": round(leverage, 4),
            "delta_operating_income": round(delta_oi, 2),
            "delta_revenue": round(delta_revenue, 2),
            "revenue_current": round(rev_curr, 2),
            "revenue_previous": round(rev_prev, 2),
            "operating_income_current": round(oi_curr, 2),
            "operating_income_previous": round(oi_prev, 2),
            "interpretation": f"1% revenue change → {leverage*100:.2f}% operating income change"
        }

    def calculate_asset_turnover(self) -> Dict[str, Any]:
        """Capacità Produttiva Inutilizzata: Beni strumentali / Ricavi"""
        fa_curr = self._to_float(self.current.get("patrimonio", {}).get("valore_beni_strumentali", 0))
        rev_curr = self._to_float(self.current.get("ricavi", {}).get("ricavi_dichiarati", 0))

        fa_prev = self._to_float(self.previous.get("patrimonio", {}).get("valore_beni_strumentali", 0))
        rev_prev = self._to_float(self.previous.get("ricavi", {}).get("ricavi_dichiarati", 0))

        ratio_curr = fa_curr / rev_curr if rev_curr > 0 else 0
        ratio_prev = fa_prev / rev_prev if rev_prev > 0 else 0

        return {
            "asset_turnover_current": round(ratio_curr, 2),
            "asset_turnover_previous": round(ratio_prev, 2),
            "fixed_assets_current": round(fa_curr, 2),
            "fixed_assets_previous": round(fa_prev, 2),
            "revenue_current": round(rev_curr, 2),
            "revenue_previous": round(rev_prev, 2),
            "trend": "Improving" if ratio_curr < ratio_prev else "Worsening",
            "interpretation": f"Company has {ratio_curr:.2f}€ in assets per 1€ revenue"
        }

    def calculate_production_leverage(self) -> Dict[str, Any]:
        """Leva Produttiva: Valore Aggiunto / Costo del Personale"""
        va_curr = self._to_float(self.current.get("risultati", {}).get("valore_aggiunto", 0))
        labor_curr = self._to_float(self.current.get("costi", {}).get("costo_personale", 0))

        va_prev = self._to_float(self.previous.get("risultati", {}).get("valore_aggiunto", 0))
        labor_prev = self._to_float(self.previous.get("costi", {}).get("costo_personale", 0))

        ratio_curr = va_curr / labor_curr if labor_curr > 0 else 0
        ratio_prev = va_prev / labor_prev if labor_prev > 0 else 0

        return {
            "production_leverage_current": round(ratio_curr, 2),
            "production_leverage_previous": round(ratio_prev, 2),
            "value_added_current": round(va_curr, 2),
            "value_added_previous": round(va_prev, 2),
            "labor_cost_current": round(labor_curr, 2),
            "labor_cost_previous": round(labor_prev, 2),
            "trend_pct": round((ratio_curr - ratio_prev) / ratio_prev * 100, 1) if ratio_prev > 0 else 0,
            "interpretation": f"Company generates {ratio_curr:.2f}€ value per 1€ labor cost"
        }

    def calculate_productivity_per_capita(self) -> Dict[str, Any]:
        """Produttività Pro Capite: Valore Aggiunto / Numero Addetti"""
        va_curr = self._to_float(self.current.get("risultati", {}).get("valore_aggiunto", 0))
        emp_curr = self._to_float(self.current.get("personale", {}).get("numero_addetti_equivalenti", 1))

        va_prev = self._to_float(self.previous.get("risultati", {}).get("valore_aggiunto", 0))
        emp_prev = self._to_float(self.previous.get("personale", {}).get("numero_addetti_equivalenti", 1))

        prod_curr = va_curr / emp_curr if emp_curr > 0 else 0
        prod_prev = va_prev / emp_prev if emp_prev > 0 else 0
        change_pct = ((prod_curr - prod_prev) / prod_prev * 100) if prod_prev > 0 else 0

        return {
            "productivity_current": round(prod_curr, 2),
            "productivity_previous": round(prod_prev, 2),
            "change_pct": round(change_pct, 1),
            "value_added_current": round(va_curr, 2),
            "value_added_previous": round(va_prev, 2),
            "employees_current": round(emp_curr, 2),
            "employees_previous": round(emp_prev, 2),
            "interpretation": f"Each employee generates {prod_curr:,.0f}€ value added ({change_pct:+.1f}% YoY)"
        }

    # --- ECONOMICA ---

    def calculate_fixed_variable_costs(self) -> Dict[str, Any]:
        """
        Costi Fissi vs Variabili.
        Fixed: godimento beni terzi + lavoro dipendente + collaboratori + costi residuali + ammortamenti + accantonamenti
        Variable: esistenze iniziali + acquisti materie prime + servizi - rimanenze finali
        """
        costi = self.current.get("costi", {})

        fixed_costs = (
            self._to_float(costi.get("godimento_beni_terzi", 0)) +
            self._to_float(costi.get("costo_personale", 0)) +
            self._to_float(costi.get("spese_collaboratori", 0)) +
            self._to_float(costi.get("altri_costi", 0)) +
            self._to_float(costi.get("ammortamenti", 0)) +
            self._to_float(costi.get("accantonamenti", 0))
        )

        variable_costs = (
            self._to_float(costi.get("esistenze_iniziali", 0)) +
            self._to_float(costi.get("costo_materie_prime", 0)) +
            self._to_float(costi.get("costo_servizi", 0)) -
            self._to_float(costi.get("rimanenze_finali", 0))
        )

        total_costs = fixed_costs + variable_costs
        fixed_pct = (fixed_costs / total_costs * 100) if total_costs > 0 else 0
        variable_pct = (variable_costs / total_costs * 100) if total_costs > 0 else 0

        return {
            "fixed_costs": round(fixed_costs, 2),
            "variable_costs": round(variable_costs, 2),
            "total_costs": round(total_costs, 2),
            "fixed_percentage": round(fixed_pct, 1),
            "variable_percentage": round(variable_pct, 1),
            "breakdown": {
                "rent": round(self._to_float(costi.get("godimento_beni_terzi", 0)), 2),
                "labor": round(self._to_float(costi.get("costo_personale", 0)), 2),
                "depreciation": round(self._to_float(costi.get("ammortamenti", 0)), 2),
                "other_fixed": round(self._to_float(costi.get("altri_costi", 0)), 2),
                "materials": round(self._to_float(costi.get("costo_materie_prime", 0)), 2),
                "services": round(self._to_float(costi.get("costo_servizi", 0)), 2)
            },
            "interpretation": f"Cost structure: {fixed_pct:.0f}% fixed, {variable_pct:.0f}% variable"
        }

    def calculate_break_even_point(self) -> Dict[str, Any]:
        """BEP = Costi Fissi / (1 - (Costi Variabili / Ricavi))"""
        cost_analysis = self.calculate_fixed_variable_costs()
        revenue = self._to_float(self.current.get("ricavi", {}).get("ricavi_dichiarati", 0))

        fixed_costs = cost_analysis["fixed_costs"]
        variable_costs = cost_analysis["variable_costs"]

        if revenue == 0:
            return {
                "break_even_point": 0,
                "margin_of_safety": 0,
                "interpretation": "Cannot calculate - no revenue"
            }

        contribution_margin_ratio = 1 - (variable_costs / revenue)

        if contribution_margin_ratio <= 0:
            return {
                "break_even_point": float('inf'),
                "margin_of_safety": -100,
                "interpretation": "Variable costs exceed revenue - no break-even possible"
            }

        bep = fixed_costs / contribution_margin_ratio
        margin_of_safety = ((revenue - bep) / revenue * 100)

        return {
            "break_even_point": round(bep, 2),
            "actual_revenue": round(revenue, 2),
            "margin_of_safety": round(margin_of_safety, 1),
            "contribution_margin_ratio": round(contribution_margin_ratio, 3),
            "fixed_costs": round(fixed_costs, 2),
            "variable_costs": round(variable_costs, 2),
            "interpretation": self._interpret_bep(margin_of_safety)
        }

    def _interpret_bep(self, margin: float) -> str:
        if margin > 30:
            return f"Excellent safety margin ({margin:.1f}%) - Low risk"
        elif margin > 20:
            return f"Good safety margin ({margin:.1f}%) - Moderate risk"
        elif margin > 10:
            return f"Adequate safety margin ({margin:.1f}%) - Some risk"
        elif margin > 0:
            return f"Thin safety margin ({margin:.1f}%) - High risk"
        else:
            return f"Below break-even ({margin:.1f}%) - Critical situation"

    # --- COMPLETE REPORT ---

    def generate_complete_report(self) -> Dict[str, Any]:
        """
        Generate simplified report with only ISA-based indicators.
        Omits valutazione (EM Score/NOPAT) and sostenibilità (ROE) sections
        which require balance sheet data not available in semplificata.
        """
        return {
            "company_info": {
                "codice_fiscale": self.current.get("identificativi", {}).get("codice_fiscale"),
                "ragione_sociale": self.current.get("identificativi", {}).get("ragione_sociale"),
                "anno_corrente": self.current.get("identificativi", {}).get("anno"),
                "anno_precedente": self.previous.get("identificativi", {}).get("anno")
            },
            "accounting_type": "semplificata",
            "finanziari": {
                "debt_management": self.calculate_debt_management(),
                "cash_generation": self.calculate_cash_generation()
            },
            "operativi": {
                "operating_leverage": self.calculate_operating_leverage(),
                "asset_turnover": self.calculate_asset_turnover(),
                "production_leverage": self.calculate_production_leverage(),
                "productivity": self.calculate_productivity_per_capita()
            },
            "economici": {
                "cost_analysis": self.calculate_fixed_variable_costs(),
                "break_even": self.calculate_break_even_point()
            }
        }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def load_biennio_data(json_path: str) -> Tuple[Dict, Dict]:
    """
    Load 2-year data from JSON file

    Returns:
        Tuple of (data_2023, data_2022)
    """
    import json

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data.get("anno_corrente", {}), data.get("anno_precedente", {})


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) < 2:
        print("Usage: python formule_report_pf.py <biennio.json>")
        sys.exit(1)

    json_path = sys.argv[1]
    data_2023, data_2022 = load_biennio_data(json_path)

    calculator = ReportPFCalculator(data_2023, data_2022)
    report = calculator.generate_complete_report()

    # Pretty print
    import json
    print(json.dumps(report, indent=2, ensure_ascii=False))
