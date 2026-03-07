# KPI Gap Analysis - Report PF vs Schema Reference

**Date**: 2025-11-25
**Reference Document**: `reportpf/SCHEMA SOCIETA' DI PERSONE ORDINARIA.pdf`
**Current Implementation**: `components/reports/report-pf.tsx`
**Status**: ⚠️ Partial Implementation - Missing 2 KPIs

---

## Executive Summary

The Report PF currently implements **11 out of 13 KPIs** from the reference schema (84.6% complete). Two KPIs are missing:
1. **Capacità Produttiva Inutilizzata (2.02)** - Asset Turnover alternative calculation
2. **Adeguati Assetti (Section 4)** - ROE sustainability with revenue forecast

---

## Detailed KPI Comparison

### ✅ PAGINA DI VALUTAZIONE E INDICI (Valuation Page)

#### ✅ **Business Valuation**
**Schema Reference**: Page 1

| Element | Schema Formula | Current Implementation | Status |
|---------|---------------|----------------------|--------|
| NOPAT | `(ICI017 - 0,31 × ICI017)` average of 2 years | ✅ Backend calculates | ✅ |
| R° (Discount Rate) | `(RF + PD) / (1-PD)` where RF=0.035 | ✅ Backend calculates | ✅ |
| EM Score | `3,25 + 6,56×[(RS100+...RS105)-(RS110+RS112+RS113+RS114)]/RS106 + 6,72×(ICI017/RS106)` | ✅ Backend calculates | ✅ |
| PD (Probability Default) | Based on EM Score table (20 brackets) | ✅ Backend calculates from EM | ✅ |
| Valuation | `NOPAT / R°` | ✅ Displayed: `indicatori.valutazione.valuation` | ✅ |
| PFN Alert | If `PFN > Valuation` → Alert | ⚠️ **NOT IMPLEMENTED** | ❌ |

**PFN Formula**: `RS110 + RS111 - RS104 - RS105`

**What's Missing**:
- Alert when Net Financial Position (PFN) exceeds company valuation
- This is a critical warning for over-indebtedness

**Display Location**: Section 1 - "Valutazione Aziendale e Rating Creditizio"

---

### ✅ SEZIONE FINANZIARIA (Financial Section)

#### ✅ **1.01 - Gestione del Debito (Debt Management)**
**Schema Reference**: Page 2

| Element | Schema Formula | Current Implementation | Status |
|---------|---------------|----------------------|--------|
| Formula | `MOL / Interessi e altri oneri finanziari` | ✅ `indicatori.finanziari.debt_management` | ✅ |
| Rating Scale | AAA to D (15 brackets) | ✅ Badge displayed | ✅ |
| Alert if MOL < 0 | "Not applicable" warning | ✅ "N/A" badge with interpretation | ✅ |

**Data Codes**:
- MOL: `ICI014`
- Interessi: `ICI019`

**Display Location**: Section 5 - "Analisi Finanziaria"

---

#### ✅ **1.02 - Capacità di Generare Cassa (Cash Generation)**
**Schema Reference**: Page 3

| Element | Schema Formula | Current Implementation | Status |
|---------|---------------|----------------------|--------|
| Formula | `MOL - ΔCCNO - ΔBeni Strumentali` | ✅ `indicatori.finanziari.cash_generation` | ✅ |
| Operating Cash Flow | MOL + Ammortamenti | ✅ Displayed | ✅ |
| Free Cash Flow | OCF - ΔWC - CAPEX | ✅ Displayed | ✅ |
| Interpretation | Positive FCF = self-financing | ✅ Backend provides interpretation | ✅ |

**Data Codes**:
- MOL: `ICI014`
- CCNO: `(RS100+RS101+RS102+RS104+RS105) - (RS112-RS113-RS114)`
- Beni Strumentali: `ICI029`

**Display Location**: Section 5 - "Analisi Finanziaria"

---

### ✅ SEZIONE OPERATIVA (Operating Section)

#### ✅ **2.01 - Leva Operativa (Operating Leverage)**
**Schema Reference**: Page 4

| Element | Schema Formula | Current Implementation | Status |
|---------|---------------|----------------------|--------|
| Formula | `(ΔReddito Operativo) / (ΔRicavi)` | ✅ `indicatori.operativi.operating_leverage` | ✅ |
| Trend (2 years) | Year-over-year change | ✅ Shows Δ Ricavi and Δ RO | ✅ |
| Alert if RO < 0 | "Not applicable" warning | ✅ Backend handles edge case | ✅ |

**Data Codes**:
- Reddito Operativo: `ICI017`
- Ricavi: `ICI001`

**Display Location**: Section 3 - "Indicatori Operativi"

---

#### ❌ **2.02 - Capacità Produttiva Inutilizzata (Unused Capacity)**
**Schema Reference**: Page 5

| Element | Schema Formula | Current Implementation | Status |
|---------|---------------|----------------------|--------|
| Formula | `(Beni Strumentali / Ricavi) × 100` for both years | ❌ **NOT IMPLEMENTED** | ❌ |
| Trend | Compare T+1 vs T | ❌ Not shown | ❌ |

**Data Codes**:
- Beni Strumentali: `ICI029`
- Ricavi: `ICI001`

**What's Missing**:
- This is an **alternative calculation** to Asset Turnover
- Schema shows: Higher ratio = more unused capacity
- Current report shows **Asset Turnover** instead (reciprocal concept)
- Asset Turnover: `Ricavi / Beni Strumentali` (opposite of this KPI)

**Note**: The current implementation shows **Asset Turnover (2.02 alternative)**:
- ✅ Asset Turnover 2024: 1.81
- ✅ Asset Turnover 2023: 2.77
- ✅ Trend: "Improving"

**Recommendation**: Keep Asset Turnover (more intuitive), but add a note explaining the relationship:
- Asset Turnover = 1.81 means company has 1.81€ assets per 1€ revenue
- Reciprocal (55.2%) would be Unused Capacity ratio from schema

**Display Location**: Section 3 - "Indicatori Operativi" (currently shows Asset Turnover)

---

#### ✅ **2.03 - Leva Produttiva (Production Leverage)**
**Schema Reference**: Page 6

| Element | Schema Formula | Current Implementation | Status |
|---------|---------------|----------------------|--------|
| Formula | `Valore Aggiunto / Spese Lavoro Dipendente` | ✅ `indicatori.operativi.production_leverage` | ✅ |
| Trend (2 years) | Compare T+1 vs T | ✅ Shows -17.5% trend | ✅ |

**Data Codes**:
- Valore Aggiunto: `ICI011`
- Spese Lavoro: `ICI012`

**Display Location**: Section 3 - "Indicatori Operativi"

---

#### ✅ **2.04 - Produttività Pro Capite (Productivity per Employee)**
**Schema Reference**: Page 7

| Element | Schema Formula | Current Implementation | Status |
|---------|---------------|----------------------|--------|
| Formula | `Valore Aggiunto / Numero Addetti` | ✅ `indicatori.operativi.productivity` | ✅ |
| Trend (2 years) | Compare T+1 vs T | ✅ Shows -10.7% change | ✅ |

**Data Codes**:
- Valore Aggiunto: `ICI011`
- Numero Addetti: `ICI027`

**Display Location**: Section 3 - "Indicatori Operativi"

---

### ✅ SEZIONE ECONOMICA (Economic Section)

#### ✅ **3.01 - Determinazione Costi Fissi e Variabili**
**Schema Reference**: Page 8

| Element | Schema Formula | Current Implementation | Status |
|---------|---------------|----------------------|--------|
| Costi Fissi | Sum of: Godimento beni terzi + Lavoro + Collaboratori + Residuali + Ammortamenti + Accantonamenti | ✅ `indicatori.economici.cost_analysis` | ✅ |
| Costi Variabili | Esistenze iniziali + Acquisti MP + Servizi - Rimanenze finali | ✅ Calculated by backend | ✅ |
| Pie Chart | Show fixed vs variable split | ✅ `GraficoComposizioneCosti` | ✅ |

**Data Codes**:
- Godimento beni: `ICI009`
- Lavoro dipendente: `ICI012`
- Collaboratori: `ICI013`
- Residuali: `ICI010`
- Ammortamenti: `ICI015`
- Accantonamenti: `ICI016`
- Esistenze iniziali: `ICI004`
- Acquisti MP: `ICI006`
- Servizi: `ICI008`
- Rimanenze finali: `ICI005`

**Display Location**: Section 2 - "Analisi Economica"

---

#### ✅ **3.02 - Break Even Point**
**Schema Reference**: Page 9

| Element | Schema Formula | Current Implementation | Status |
|---------|---------------|----------------------|--------|
| Formula | `Costi Fissi / (1 - (Costi Variabili / Ricavi))` | ✅ `indicatori.economici.break_even` | ✅ |
| Margine di Sicurezza | `Ricavi - BEP` | ✅ Shows -15.3% (below BEP) | ✅ |
| Alert if below BEP | Warning when revenue < BEP | ✅ Red alert card displayed | ✅ |

**Display Location**: Section 2 - "Analisi Economica"

---

### ⚠️ SEZIONE ADEGUATI ASSETTI (Adequate Structure Assessment)

#### ❌ **Section 4 - ROE Sustainability with Revenue Forecast**
**Schema Reference**: Page 10

**Question**: Can the company absorb consequences of a predictable revenue reduction?

| Element | Schema Formula | Current Implementation | Status |
|---------|---------------|----------------------|--------|
| RO^ (Forecasted Revenue) | Excel `FORECAST.LINEAR` on 2-year revenue | ⚠️ Backend calculates, **not displayed separately** | ⚠️ |
| Formula | `((RO^/RS106) + (RO^/RS106) - (ICI019/(RS110+RS111) × (RS110+RS111)/RS107)) × ((ICI024 - ICI024×0,30) / ICI024)` | ⚠️ Backend may calculate | ⚠️ |
| Alert if Negative | "Fragile structure - cannot resist revenue variations" | ❌ **NOT DISPLAYED** | ❌ |

**Data Codes**:
- RO^: Linear forecast of `ICI001` (2 years)
- Totale Attivo: `RS106`
- Interessi: `ICI019`
- Debiti banche ST: `RS110`
- Debiti banche LT: `RS111`
- Patrimonio Netto: `RS107`
- Reddito: `ICI024`

**What's Missing**:
This is a **complex ROE decomposition analysis** that:
1. Forecasts next year's operating income using linear regression
2. Calculates ROE with forecasted revenue
3. Assesses if the company can sustain a revenue drop
4. Shows alert if result is negative (fragile structure)

**Current Implementation**:
- ✅ Section 6 shows **ROE Sustainability** with DuPont decomposition
- ✅ Shows ROE, ROA, Interest Rate, Leverage, Tax Rate
- ✅ Shows "Projected Operating Income 2024": €48,134
- ❌ Missing the **complete formula** from schema
- ❌ Missing the **fragility alert** (negative result warning)

**Display Location**: Section 6 - "Sostenibilità e Proiezioni" (partially implemented)

---

## Summary Table: KPI Implementation Status

| Section | KPI Code | KPI Name | Status | Priority |
|---------|----------|----------|--------|----------|
| Valutazione | - | Business Valuation | ✅ Complete | - |
| Valutazione | - | EM Score | ✅ Complete | - |
| Valutazione | - | PFN Alert | ❌ Missing | 🔴 High |
| Finanziaria | 1.01 | Debt Management | ✅ Complete | - |
| Finanziaria | 1.02 | Cash Generation | ✅ Complete | - |
| Operativa | 2.01 | Operating Leverage | ✅ Complete | - |
| Operativa | 2.02 | Unused Capacity | ⚠️ Alternative | 🟡 Low |
| Operativa | 2.03 | Production Leverage | ✅ Complete | - |
| Operativa | 2.04 | Productivity per Employee | ✅ Complete | - |
| Economica | 3.01 | Fixed/Variable Costs | ✅ Complete | - |
| Economica | 3.02 | Break-Even Point | ✅ Complete | - |
| Adeguati Assetti | 4 | ROE Sustainability + Forecast | ⚠️ Partial | 🟠 Medium |

**Legend**:
- ✅ Complete: Fully implemented per schema
- ⚠️ Partial: Partially implemented or alternative approach
- ❌ Missing: Not implemented

---

## Missing KPIs - Detailed Analysis

### 🔴 HIGH PRIORITY

#### 1. **PFN Alert (Net Financial Position vs Valuation)**

**What it does**: Compares Net Financial Position (total debt minus cash) with company valuation

**Formula**:
```
PFN = RS110 + RS111 - RS104 - RS105
If PFN > Valuation → Critical Alert!
```

**Why it matters**:
- If debt exceeds company value → Over-leveraged
- Critical warning for bankruptcy risk
- Should trigger immediate action

**Implementation**:
```typescript
// In report-pf.tsx, Section 1 (Valuation)
const pfn = (
  (anno_corrente.quadro_rs.RS110 || 0) +
  (anno_corrente.quadro_rs.RS111 || 0) -
  (anno_corrente.quadro_rs.RS104 || 0) -
  (anno_corrente.quadro_rs.RS105 || 0)
);

const isPFNExceedsValuation = pfn > indicatori.valutazione.valuation;

{isPFNExceedsValuation && (
  <Alert variant="destructive" className="mt-4">
    <IconAlertTriangle className="h-4 w-4" />
    <AlertTitle>⚠️ ALERT: Posizione Finanziaria Critica</AlertTitle>
    <AlertDescription>
      La Posizione Finanziaria Netta (€{pfn.toLocaleString('it-IT')})
      supera il valore aziendale (€{indicatori.valutazione.valuation.toLocaleString('it-IT')}).
      L'azienda è sovra-indebitata.
    </AlertDescription>
  </Alert>
)}
```

**Data Required**:
- RS110: Debiti verso banche (short-term)
- RS111: Debiti verso banche (long-term)
- RS104: Disponibilità liquide
- RS105: Altri crediti finanziari

---

### 🟠 MEDIUM PRIORITY

#### 2. **Adeguati Assetti - Complete Formula (Section 4)**

**What it does**: Assesses if company structure can withstand revenue reductions

**Current State**:
- ✅ Shows projected operating income (€48,134)
- ✅ Shows ROE decomposition (DuPont)
- ❌ Missing complete formula calculation
- ❌ Missing fragility alert

**Complete Formula**:
```
Fragility Index =
  ((RO^/Totale Attivo) + (RO^/Totale Attivo) -
   (Interessi/(Debiti Banche) × (Debiti Banche)/Patrimonio Netto)) ×
  ((Reddito - Reddito×0,30) / Reddito)

Where:
- RO^ = FORECAST.LINEAR(Ricavi 2023, Ricavi 2024) for 2025
- If result < 0 → "Fragile structure" alert
```

**Why it matters**:
- Predicts if company can survive revenue drops
- Uses linear forecasting for next year
- Combines profitability, leverage, and tax effects

**Implementation**:
```typescript
// Backend should calculate:
const ro_forecast = linearForecast([ricavi_2022, ricavi_2023]); // 2024 forecast
const totale_attivo = anno_corrente.quadro_rs.RS106;
const interessi = anno_corrente.costi.interessi_oneri_finanziari;
const debiti_banche = (anno_corrente.quadro_rs.RS110 || 0) + (anno_corrente.quadro_rs.RS111 || 0);
const patrimonio_netto = anno_corrente.quadro_rs.RS107;
const reddito = anno_corrente.risultati.reddito_impresa;

const fragility_index =
  ((ro_forecast/totale_attivo) + (ro_forecast/totale_attivo) -
   (interessi/debiti_banche * debiti_banche/patrimonio_netto)) *
  ((reddito - reddito*0.30) / reddito);

// Frontend display:
{indicatori?.adeguati_assetti && (
  <Card>
    <CardHeader>
      <CardTitle>Adeguatezza Assetti Strutturali</CardTitle>
      <CardDescription>
        Capacità di assorbire una riduzione prevedibile dei ricavi
      </CardDescription>
    </CardHeader>
    <CardContent>
      <div className="text-center mb-4">
        <p className="text-4xl font-bold">
          {indicatori.adeguati_assetti.fragility_index.toFixed(3)}
        </p>
        <p className="text-sm text-muted-foreground">Indice di Fragilità</p>
      </div>

      {indicatori.adeguati_assetti.fragility_index < 0 && (
        <Alert variant="destructive">
          <IconAlertTriangle className="h-4 w-4" />
          <AlertTitle>⚠️ Struttura Fragile</AlertTitle>
          <AlertDescription>
            Gli attuali assetti strutturali sono fragili e non resistono
            a variazioni tendenziali dei ricavi.
          </AlertDescription>
        </Alert>
      )}

      <div className="mt-4 text-sm">
        <p><strong>Ricavi Previsti 2024:</strong> €{indicatori.adeguati_assetti.forecasted_revenue.toLocaleString('it-IT')}</p>
        <p className="text-muted-foreground">
          Proiezione lineare basata su trend storico
        </p>
      </div>
    </CardContent>
  </Card>
)}
```

---

### 🟡 LOW PRIORITY

#### 3. **Capacità Produttiva Inutilizzata (2.02) - Alternative Calculation**

**Current State**:
- ✅ Shows **Asset Turnover**: `Ricavi / Beni Strumentali`
- ❌ Schema shows **Unused Capacity**: `(Beni Strumentali / Ricavi) × 100`

**Relationship**:
- Asset Turnover = 1.81 → Unused Capacity = 55.2% (reciprocal × 100)
- Higher Asset Turnover = Lower Unused Capacity (better)

**Recommendation**: **Keep current implementation** (Asset Turnover)
- Asset Turnover is more intuitive for users
- Shows efficiency (higher = better)
- Unused Capacity is the inverse (higher = worse)

**Optional Enhancement**: Add explanatory note
```typescript
<p className="text-xs text-muted-foreground mt-2">
  Capacità Produttiva Utilizzata: {((1 / asset_turnover_2023) * 100).toFixed(1)}%
  <br />
  (Reciproco dell'Asset Turnover)
</p>
```

---

## Backend vs Frontend Responsibilities

### ✅ Backend Calculations (FastAPI - Python)

**Already Implemented**:
1. ✅ EM Score (Altman Z-Score)
2. ✅ NOPAT calculation
3. ✅ Probability of Default (PD)
4. ✅ Discount Rate (R°)
5. ✅ Business Valuation
6. ✅ Debt Management Rating
7. ✅ Cash Flow (Operating & Free)
8. ✅ Operating Leverage
9. ✅ Asset Turnover
10. ✅ Production Leverage
11. ✅ Productivity per Employee
12. ✅ Fixed/Variable Cost Analysis
13. ✅ Break-Even Point
14. ✅ ROE Decomposition

**To Add**:
1. ❌ PFN calculation → Add to `indicatori.valutazione.pfn`
2. ❌ Adeguati Assetti complete formula → Add `indicatori.adeguati_assetti`

### ✅ Frontend Display (Next.js - TypeScript)

**Already Implemented**:
- ✅ All 6 main sections
- ✅ All KPI cards and visualizations
- ✅ Charts (bi-annual comparison, cost composition)
- ✅ Badges and alerts
- ✅ Interpretations from backend

**To Add**:
1. ❌ PFN Alert in Section 1
2. ❌ Adeguati Assetti section (new Section 7 or expand Section 6)

---

## Recommended Implementation Order

### Phase 1: Critical Alerts (1-2 hours)

**Priority**: 🔴 High

1. **PFN Alert** (30 min)
   - Backend: Add PFN calculation to `indicatori.valutazione`
   - Frontend: Add alert card in Section 1
   - Test with data where PFN > Valuation

### Phase 2: Complete ROE Assessment (2-3 hours)

**Priority**: 🟠 Medium

2. **Adeguati Assetti Formula** (2 hours)
   - Backend: Add linear forecast for revenue
   - Backend: Calculate fragility index
   - Backend: Return `indicatori.adeguati_assetti`
   - Frontend: Add new section or expand Section 6
   - Test edge cases (negative ROE, high leverage)

### Phase 3: Optional Enhancements (30 min)

**Priority**: 🟡 Low

3. **Unused Capacity Note** (15 min)
   - Frontend: Add explanatory note to Asset Turnover
   - Show reciprocal relationship

---

## Testing Checklist

### PFN Alert
- [ ] Test with PFN > Valuation (should show alert)
- [ ] Test with PFN < Valuation (no alert)
- [ ] Test with missing RS data (graceful fallback)
- [ ] Verify calculation: RS110 + RS111 - RS104 - RS105

### Adeguati Assetti
- [ ] Test with positive fragility index (stable)
- [ ] Test with negative fragility index (fragile alert)
- [ ] Verify linear forecast matches Excel FORECAST.LINEAR
- [ ] Test with only 1 year of data (should handle gracefully)
- [ ] Verify complete formula matches schema

### General
- [ ] All alerts display correctly
- [ ] Mobile responsive
- [ ] Italian localization correct
- [ ] Print/PDF export includes new sections

---

## Conclusion

**Current Status**: 84.6% Complete (11/13 KPIs)

**Missing Critical Features**:
1. PFN Alert (High Priority) - 30 min to implement
2. Complete Adeguati Assetti Formula (Medium Priority) - 2 hours to implement

**Recommendation**:
Implement PFN Alert immediately (critical financial health warning), then add complete Adeguati Assetti formula in next sprint.

**Total Estimated Time**: 2.5-3.5 hours to reach 100% compliance with schema.

---

**Files to Modify**:
1. Backend: `reportpf/api_server.py` or formulas module
2. Frontend: `components/reports/report-pf.tsx`
3. Types: `types/report-pf.ts` (add AdeguatiAssetti interface)
