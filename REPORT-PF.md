# Report PF - Analisi Finanziaria Dichiarazioni dei Redditi

## Overview

Report PF is a comprehensive financial analysis report for Italian tax declarations (Modello Redditi). It extracts data from two consecutive years and provides detailed economic, patrimonial, and financial analysis.

### Supported Entity Types

| Type | Description | Declaration | Income Quadro | ISA Codes |
|------|-------------|-------------|---------------|-----------|
| **SP** | Società di Persone (partnerships) | Modello Redditi SP | Quadro RG | ICI codes |
| **PF_RG** | Persona Fisica - Ditta Individuale | Modello Redditi PF | Quadro RG | ICI codes |
| **PF_RE** | Persona Fisica - Libero Professionista | Modello Redditi PF | Quadro RE | ICA codes |
| **PF** | Persona Fisica (no business income) | Modello Redditi PF | — | — |

Entity type is auto-detected by scanning PDF content for RPF markers, Quadro RE/RG headers, and ICA/ICI code presence.

### Accounting Types

The system detects two accounting regimes:

- **Ordinaria** (full accounting): Has balance sheet data in Quadro RS. Full report with all 4 sections including valutazione and sostenibilità.
- **Semplificata** (simplified accounting): No balance sheet — all 18 Quadro RS fields are zero. Report uses only ISA Prospetto Economico data with 8 simplified indicators.

Detection is automatic via `detect_accounting_type()` which checks if all Quadro RS balance sheet values are zero.

## Backend Integration

### Endpoint
- **URL**: `http://localhost:8001/docs#/default/upload_process_biennio_upload_process_post`
- **Method**: POST
- **Purpose**: Upload and process two PDF files (current year and previous year) to extract financial data

### Response Structure

```json
{
  "success": true,
  "data": {
    "anno_corrente": { /* 2024 data */ },
    "anno_precedente": { /* 2023 data */ },
    "metadata": {
      "data_elaborazione": "2025-11-25T14:49:44.658945",
      "pdf_corrente": "SOCIETA' DI PERSONE ORDINARIA.pdf",
      "pdf_precedente": "BAR MAZZOLA 2023.pdf"
    }
  },
  "sommario": {
    "ragione_sociale": "F.LLI MAZZOLA S.a.s. di MAZZOLA EZIO",
    "codice_fiscale": "15100141900",
    "confronto": {
      "ricavi": {
        "anno_precedente": 527635,
        "anno_corrente": 453463,
        "variazione_percentuale": -14.05744501407223
      },
      "reddito": {
        "anno_precedente": 6740,
        "anno_corrente": -22144
      },
      "isa": {
        "anno_precedente": 6.4,
        "anno_corrente": 1.8
      }
    }
  }
}
```

### Data Structure (`DatiBiennio`)

Each year contains:

**Identificativi:**
- codice_fiscale
- partita_iva
- ragione_sociale
- anno

**Ricavi:**
- ricavi_dichiarati
- altri_componenti_positivi

**Costi:**
- esistenze_iniziali
- rimanenze_finali
- costo_materie_prime
- costo_servizi
- godimento_beni_terzi
- costo_personale
- spese_collaboratori
- ammortamenti
- accantonamenti
- altri_costi
- oneri_finanziari

**Risultati:**
- valore_aggiunto
- mol (EBITDA)
- reddito_operativo
- reddito_impresa

**Personale:**
- giornate_dipendenti
- giornate_altro_personale
- numero_addetti_equivalenti

**Patrimonio:**
- valore_beni_strumentali

**ISA:**
- punteggio
- modello_applicato
- ricavi_per_addetto
- valore_aggiunto_per_addetto
- reddito_per_addetto

**Quadro RS (Balance Sheet):**
- rimanenze
- crediti_clienti
- altri_crediti
- attivita_finanziarie
- disponibilita_liquide
- ratei_risconti_attivi
- totale_attivo
- patrimonio_netto
- debiti_banche_breve
- debiti_banche_lungo
- debiti_fornitori
- altri_debiti
- ratei_risconti_passivi

## Report Structure

### Ordinaria Reports (Full)

The report is organized into **4 logical sections**:

### 1. Company Profile & Rating (EM SCORE)

**Purpose**: Identify the company and assess its reliability/creditworthiness

**Components**:
- **Company Identification**
  - Codice Fiscale (Tax ID)
  - Partita IVA (VAT Number)
  - Modello ISA (ISA Model Applied)

- **EM SCORE** (Simplified)
  - Formula: `(ISA_score * 0.6) + (profitability_bonus)`
  - Range: 1-10
  - Profitability bonus: 4 if profit > 0, else 1
  - Display: Large number /10 with rating label

- **ISA Score**
  - Current year score
  - Comparison with previous year (trend indicator)
  - Scale: 0-10 (6+ is considered reliable)

- **Per-Employee Metrics**
  - Ricavi per Addetto (Revenue per Employee)
  - Valore Aggiunto per Addetto (Value Added per Employee)
  - Reddito per Addetto (Profit per Employee)
  - Number of equivalent employees

**Visual Design**:
- Gradient header: #003049 → #669bbc
- Large prominence on EM SCORE and ISA ratings
- Grid layout for metrics
- Border and shadow for emphasis

### 2. Economic Section

**Purpose**: Analyze revenues, costs, margins, and profitability

**Components**:

- **Critical Alerts** (if applicable)
  - Loss warnings
  - ISA score below 6

- **Key Performance Indicators** (4 cards)
  1. Ricavi Totali (Total Revenue) - with YoY %
  2. Margine Operativo/MOL (EBITDA) - with absolute variation
  3. Reddito d'Impresa (Net Profit) - with absolute variation
  4. Valore Aggiunto (Value Added)

- **Year-over-Year Comparison Chart**
  - Bar chart showing Ricavi, MOL, Reddito for both years
  - Visual trend analysis

- **Profitability Margins** (3 metrics)
  - MOL Margin % (MOL / Ricavi)
  - Profit Margin % (Reddito / Ricavi)
  - VA/Ricavi % (Value Added / Revenue)

- **Cost Composition**
  - Pie chart of main cost categories
  - Breakdown into:
    - Operating costs (materials, services, personnel, other)
    - Fixed costs & depreciation (depreciation, rent, financial charges, provisions)

**Visual Design**:
- Gradient header: #669bbc → #003049
- KPI cards with icons
- Charts integrated inline
- Detailed cost breakdown in two columns

### 3. Balance Sheet Section

**Purpose**: Show credits, debts, assets, and financial stability

**Components**:

- **Patrimonial Statement (Quadro RS)**
  - **Assets (Attività)**
    - Rimanenze (Inventory)
    - Crediti verso clienti (Accounts Receivable)
    - Altri crediti (Other Receivables)
    - Attività finanziarie (Financial Assets)
    - Disponibilità liquide (Cash & Bank)
    - Ratei e risconti attivi (Prepayments)
    - **Totale Attivo** (Total Assets)

  - **Liabilities & Equity (Passività e Patrimonio Netto)**
    - Patrimonio netto (Shareholders' Equity)
    - Debiti verso banche breve termine (Short-term Bank Debt)
    - Debiti verso banche lungo termine (Long-term Bank Debt)
    - Debiti verso fornitori (Accounts Payable)
    - Altri debiti (Other Liabilities)
    - Ratei e risconti passivi (Deferred Revenue)
    - **Totale Passivo** (Total Liabilities)

- **Financial Ratios** (4 key ratios)
  1. **Indice di Liquidità** (Current Ratio)
     - Formula: (Cash + AR + Other Receivables) / (ST Debt + AP + Other Payables)
     - ✓ Adequate if ≥ 1.0

  2. **Debt/Equity Ratio**
     - Formula: Total Bank Debt / Equity
     - ✓ Good if ≤ 1.0

  3. **ROE** (Return on Equity)
     - Formula: (Net Profit / Equity) × 100
     - Shows return on shareholders' capital

  4. **ROA** (Return on Assets)
     - Formula: (Operating Profit / Total Assets) × 100
     - Shows asset efficiency

**Visual Design**:
- Gradient header: #003049 → #669bbc
- Two-column layout for assets and liabilities
- Bordered sections with totals emphasized
- 4-column grid for financial ratios

### 4. Financial Section

**Purpose**: Analyze cash flow and cost of debt

**Components**:

- **Cash Flow Analysis** (Approximated)
  - **Operating Cash Flow**
    - Formula: MOL + Depreciation
    - Shows cash generated from operations

  - **Free Cash Flow** (Simplified)
    - Formula: Operating Cash Flow - CAPEX (estimated)
    - Shows cash available after investments

  - Component breakdown:
    - MOL (EBITDA)
    - Ammortamenti (Depreciation)

- **Debt Management**
  - **Cost of Debt %**
    - Formula: (Financial Charges / Total Bank Debt) × 100
    - Shows the interest rate on debt

  - **Total Bank Debt**
    - Split by: Short-term + Long-term

  - **Coverage Ratio** (MOL/Financial Charges)
    - Shows how many times EBITDA covers interest
    - Higher is better (indicates ability to service debt)

- **Additional Financial Metrics** (4 indicators)
  1. **Capitale Circolante** (Working Capital)
     - Formula: Current Assets - Current Liabilities

  2. **Equity Ratio** (Financial Independence)
     - Formula: (Equity / Total Assets) × 100

  3. **Disponibilità Liquide** (Cash & Bank)
     - Immediate liquidity available

  4. **Valore Beni Strumentali** (Fixed Assets)
     - Value of tangible fixed assets

**Visual Design**:
- Gradient header: #669bbc → #003049
- Two-column layout for cash flow and debt
- Bordered sections with highlights
- 4-column grid for additional metrics

### Semplificata Reports (Simplified)

When contabilità semplificata is detected (all Quadro RS = 0), the report uses `ReportPFCalculatorSemplificato` and produces only **3 indicator sections** with **8 ISA-based indicators**:

#### Indicatori Finanziari (2 indicators)
1. **Gestione del Debito** — MOL / Interessi passivi (debt coverage ratio)
2. **Capacità di Generare Cassa** — MOL - ΔBeni strumentali (simplified cash generation)

#### Indicatori Operativi (4 indicators)
3. **Leva Operativa** — Costi fissi / Costi variabili
4. **Capacità Produttiva Inutilizzata** — (Ricavi potenziali - Ricavi effettivi) / Ricavi potenziali
5. **Leva Produttiva** — Ricavi / Beni strumentali
6. **Produttività Pro Capite** — Valore aggiunto / Numero addetti

#### Indicatori Economici (2 indicators)
7. **Costi Fissi / Variabili** — Breakdown of cost structure
8. **Break Even Point** — Costi fissi / (1 - Costi variabili / Ricavi)

**Omitted sections** (require balance sheet data):
- Valutazione (EM Score, NOPAT, Enterprise Value)
- Sostenibilità (ROE, ROA, leverage ratios)

## ICA Codes (Liberi Professionisti)

PF_RE entities use ICA codes instead of ICI codes from the ISA Prospetto Economico:

| Code (2024) | Code (2023) | Description |
|-------------|-------------|-------------|
| ICA001 | ICA00001 | Compensi dichiarati |
| ICA003 | ICA00003 | Totale compensi |
| ICA007 | ICA00007 | Compensi corrisposti a terzi |
| ICA013 | ICA00013 | Valore aggiunto |
| ICA014 | ICA00014 | Spese lavoro dipendente |
| ICA015 | ICA00015 | Compensi collaboratori |
| ICA016 | ICA00016 | MOL |
| ICA017 | ICA00017 | Ammortamenti |
| ICA018 | ICA00018 | Reddito operativo |
| ICA020 | ICA00020 | Interessi passivi |
| ICA024 | ICA00024 | Reddito |
| ICA027 | ICA00027 | Numero addetti |
| ICA028 | ICA00028 | Valore beni strumentali |

Note: 2024 declarations use 3-digit format (ICA001), 2023 use 5-digit format (ICA00001).

## Test Data

Test data is stored in `/lib/dati-test-pf.ts` using real Bar Mazzola data:

**Company**: F.LLI MAZZOLA S.a.s. di MAZZOLA EZIO
**Codice Fiscale**: 15100141900

### Year 2024 (Anno Corrente)
- Ricavi: €453,487
- MOL: €-12,137
- Reddito d'Impresa: €-22,144
- ISA Score: 1.8
- Addetti: 4.76

### Year 2023 (Anno Precedente)
- Ricavi: €528,485
- MOL: €14,822
- Reddito d'Impresa: €6,740
- ISA Score: 6.4
- Addetti: 6.05

### Key Observations
- Revenue decline: -14.06%
- Shift from profit to loss: -€28,884
- ISA score drop: -4.6 points (critical decline)
- Employee reduction: -1.29 FTE

### Verified Test PDFs

| PDF | Entity Type | Accounting | Result |
|-----|-------------|------------|--------|
| H.DEA DELLA SALUTE SAS 2025/2024 | SP | semplificata | Pass |
| G&M TERMOIDRAULICA 2024/2023 | SP | semplificata | Pass |
| TOPPI RPF 2024/2023 | PF_RG | semplificata | Pass |
| RADICE RPF 2024/2023 | PF_RE | semplificata | Pass |
| Bar Mazzola SP 2024/2023 | SP | ordinaria | Pass |

## File Structure

```
# Backend (reportpf/)
reportpf/
  api_server.py                    # FastAPI server with entity/accounting detection
  extdichiarazione_v3_optimized.py # PDF extraction (SP, PF_RE, PF_RG detection)
  formule_report_pf.py             # ReportPFCalculator + ReportPFCalculatorSemplificato

# Frontend
/app/reportpf/page.tsx             # Report PF demo page
/components/reports/
  report-pf.tsx                    # Main reorganized report component
  report-pf-improved.tsx           # Alternative version (uses ReportPFComplete type)
  pf-kpi-card.tsx                  # KPI card component
  pf-charts.tsx                    # Chart components (comparison & pie)
  download-pdf-button.tsx          # PDF download functionality
/lib/dati-test-pf.ts               # Test data (Bar Mazzola)
/types/report-pf.ts                # TypeScript types
```

## Key Calculations

### EM Score (Simplified)
```typescript
const emScore = Math.max(1, Math.min(10,
  (isa_score * 0.6) + (reddito_impresa > 0 ? 4 : 1)
));
```

### Profitability Margins
```typescript
const molMargin = (mol / ricavi_totali) * 100;
const profitMargin = (reddito_impresa / ricavi_totali) * 100;
const vaMargin = (valore_aggiunto / ricavi_totali) * 100;
```

### Cash Flow (Approximated)
```typescript
const operatingCashFlow = mol + ammortamenti;
const freeCashFlow = operatingCashFlow - capex; // CAPEX estimated
```

### Cost of Debt
```typescript
const totalDebt = debiti_banche_breve + debiti_banche_lungo;
const costOfDebt = totalDebt > 0
  ? (oneri_finanziari / totalDebt) * 100
  : 0;
```

### Financial Ratios
```typescript
// Current Ratio
const currentRatio =
  (disponibilita_liquide + crediti_clienti + altri_crediti) /
  (debiti_banche_breve + debiti_fornitori + altri_debiti);

// Debt-to-Equity
const debtToEquity = totalDebt / patrimonio_netto;

// ROE
const roe = (reddito_impresa / patrimonio_netto) * 100;

// ROA
const roa = (reddito_operativo / totale_attivo) * 100;

// Working Capital
const workingCapital =
  (rimanenze + crediti_clienti + altri_crediti) -
  (debiti_fornitori + altri_debiti);
```

## Usage

### Accessing the Report
```
http://localhost:3000/reportpf   # Demo with test data
```

### Demo Page Setup
```typescript
// /app/reportpf/page.tsx
const mockReport = {
  id: 1,
  report_type: 'report_pf',
  status: 'completed',
  input_data: {
    codice_fiscale: '15100141900'
  },
  api_response: datiTestPF,  // From lib/dati-test-pf.ts
  created_at: new Date().toISOString(),
  completed_at: new Date().toISOString()
};
```

## Integration with Backend

To integrate with the real backend:

1. **Upload Endpoint**
   - POST to `/upload_process_biennio`
   - Upload 2 PDF files (current + previous year)
   - Receive `DatiBiennio` response

2. **Store Report**
   - Save to database with:
     - `report_type: 'report_pf'`
     - `input_data: { codice_fiscale }`
     - `api_response: DatiBiennio`
     - `status: 'completed'`

3. **Display Report**
   - Fetch from database
   - Pass to `<ReportPF report={report} />`
   - Renders 4-section layout automatically

## Future Enhancements

### Planned Features
1. **Advanced EM Score**
   - More sophisticated calculation
   - Industry benchmarking
   - Historical trend analysis

2. **Cash Flow Statement**
   - Detailed working capital changes
   - Actual CAPEX from statements
   - Cash flow waterfall chart

3. **Ratio Analysis**
   - DuPont analysis for ROE
   - Z-Score for bankruptcy prediction
   - Altman Z-Score adaptation

4. **Industry Comparison**
   - Sector averages
   - Percentile rankings
   - Competitive positioning

5. **Trend Analysis**
   - Multi-year trends (3-5 years)
   - Seasonal patterns
   - Growth forecasting

6. **PDF Export**
   - Complete report export
   - Executive summary
   - Charts and tables included

## Design Principles

1. **Visual Hierarchy**
   - Gradient headers distinguish sections
   - Large numbers for key metrics
   - Color coding for positive/negative values

2. **Progressive Disclosure**
   - Summary metrics first
   - Details expandable/scrollable
   - Critical alerts prominent

3. **Italian Localization**
   - All labels in Italian
   - EUR formatting: €X.XXX
   - Percentage: X.X%

4. **Responsive Design**
   - Grid layouts adapt to screen size
   - Charts scale appropriately
   - Mobile-friendly navigation

5. **Accessibility**
   - Clear contrast ratios
   - Semantic HTML
   - Screen reader friendly

## Testing

Test data verified:
- ✅ Bar Mazzola 2024 data loads correctly
- ✅ Bar Mazzola 2023 data loads correctly
- ✅ All 4 sections render properly
- ✅ Charts display correctly
- ✅ Calculations are accurate
- ✅ YoY comparisons work
- ✅ Critical alerts appear when needed
- ✅ Page compiles without errors
- ✅ HTTP 200 response on /reportpf

## Notes

- The EM Score formula is simplified for demonstration
- Cash flow is approximated (real calculation needs more data)
- Industry benchmarks not yet implemented
- Multi-year trends require additional backend support
- PDF export functionality to be implemented

## Status

**Version**: 2.0
**Last Updated**: 2026-03-07
**Status**: Complete and Tested
**Backend Integration**: Connected
**Supported Entities**: SP, PF_RG, PF_RE
**Accounting Types**: Ordinaria (full), Semplificata (ISA-only)
**Test Data**: Bar Mazzola, H.DEA, G&M Termoidraulica, TOPPI, RADICE
