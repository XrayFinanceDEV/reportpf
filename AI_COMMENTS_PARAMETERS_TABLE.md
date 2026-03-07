# AI Comments Parameters - Complete Reference Table

**Generated:** 2025-12-11
**Version:** 2.1 (Fixed PFN/EBITDA fallback calculation)

This table lists all 21 financial metrics that receive AI-generated comments, plus the overall section synthesis.

---

## Complete Parameters Table

| # | Section | Metric ID | Display Title | JSON Field | Unit | Data Source | AI Comment |
|---|---------|-----------|---------------|------------|------|-------------|------------|
| **SECTION 1: ECONOMIC INDICATORS** |
| 1 | Economic | `revenue` | Ricavi Vendite e Prestazioni | `revenue` | € | P&L: "ricavi vendite" | ✅ |
| 2 | Economic | `ebitda` | EBITDA - Risultato Operativo Lordo | `ebitda` | € | P&L: "risultato operativo lordo" | ✅ |
| 3 | Economic | `costi_materia_prima` | Costi Materia Prima | `costi_materia_prima` | € | P&L: "materie prime" + "var rim mat prime" | ✅ |
| 4 | Economic | `costi_servizi` | Costi per Servizi | `costi_servizi` | € | P&L: "costi per servizi" | ✅ |
| 5 | Economic | `costi_personale` | Costi del Personale | `costi_personale` | € | P&L: "costi del personale" | ✅ |
| 6 | Economic | `costi_oneri_finanziari` | Oneri Finanziari | `costi_oneri_finanziari` | € | P&L: "interessi e altri oneri finanziari" | ✅ |
| **SECTION 2: PROFITABILITY RATIOS** |
| 7 | Profitability | `roi` | ROI - Redditività del Capitale Investito | `roi` | % | FI: "redditività del capitale investito (roi)" | ✅ |
| 8 | Profitability | `roe` | ROE - Redditività del Capitale Proprio | `roe` | % | FI: "redditività del capitale proprio (roe)" | ✅ |
| 9 | Profitability | `ros` | ROS - Redditività Operativa delle Vendite | `ros` | % | FI: "redditività operativa delle vendite (ros)" | ✅ |
| **SECTION 3: BALANCE SHEET - FOCUS PATRIMONIALE** |
| 10 | Balance Sheet | `attivo_immobilizzato` | Attivo Immobilizzato | `attivo_immobilizzato` | € | BS: "attivo immobilizzato" | ✅ |
| 11 | Balance Sheet | `rimanenze` | Rimanenze | `rimanenze` | € | BS: "rimanenze" | ✅ |
| 12 | Balance Sheet | `crediti_verso_clienti` | Crediti verso Clienti | `crediti_verso_clienti` | € | BS: "di cui verso clienti" | ✅ |
| 13 | Balance Sheet | `debiti_verso_fornitori` | Debiti verso Fornitori | `debiti_verso_fornitori` | € | BS: "di cui verso fornitori" | ✅ |
| **SECTION 4: DEBT SUSTAINABILITY** |
| 14 | Debt | `pfn_ebitda_ratio` | PFN / EBITDA - Sostenibilità del Debito | `pfn_ebitda_ratio` | x | **FI: "pfn/ebitda" (with fallback)** ⚠️ | ✅ |
| 15 | Debt | `costo_del_debito` | Costo del Debito | `costo_del_debito` | % | **Calculated**: oneri_finanziari / debiti_totali * 100 | ✅ |
| 16 | Debt | `oneri_finanziari_mol` | Oneri Finanziari / MOL | `oneri_finanziari_mol` | % | FI: "oneri finanziari netti / risultato operativo lordo" | ✅ |
| **SECTION 5: CAPITAL STRUCTURE** |
| 17 | Capital | `patrimonio_netto_attivo` | Patrimonio Netto / Attivo | `patrimonio_netto_attivo` | % | **Calculated**: patrimonio_netto / totale_attivo * 100 | ✅ |
| 18 | Capital | `passivo_corrente_totale_passivo` | Passivo Corrente / Totale Passivo | `passivo_corrente_totale_passivo` | % | **Calculated**: passivo_corrente / totale_passivo * 100 | ✅ |
| **SECTION 6: CASH FLOW & COVERAGE** |
| 19 | Cash Flow | `cash_flow` | Cash Flow Operativo | `cash_flow` | € | **Simplified**: Uses EBITDA as proxy | ✅ |
| 20 | Cash Flow | `fccr` | FCCR - Fixed Charge Coverage Ratio | `fccr` | x | **Calculated**: ebitda / oneri_finanziari | ✅ |
| **OVERALL SYNTHESIS** |
| 21 | Overall | `profilo_economico_overall` | Profilo Economico, Patrimoniale e Finanziario | `profilo_economico_overall` | - | **AI Synthesis**: All metrics combined | ✅ |

---

## Data Source Legend

| Code | Source | Description |
|------|--------|-------------|
| **P&L** | Profit & Loss Account | `profile_and_loss_account` array |
| **BS** | Balance Sheet | `balance_sheet` array |
| **FI** | Financial Index | `financial_index` array (pre-calculated ratios) |
| **Calculated** | Custom Calculation | Computed from multiple sources |

---

## Important Notes

### ⚠️ Fallback Calculations (v2.1 Fix)

Some metrics in `financial_index` may contain incorrect values (typically 0). The extraction code includes **fallback calculations** to ensure accuracy:

#### PFN/EBITDA Ratio (Metric #14)
```python
# Extract from financial_index
pfn_ebitda_ratio = extract_metric_from_list(fi_items, 'pfn/ebitda')

# FIX: Fallback calculation if value is 0 (incorrect in backend data)
if pfn_ebitda_ratio == 0 and pfn != 0 and ebitda > 0:
    pfn_ebitda_ratio = pfn / ebitda
```

**Why needed:** In production report 11, the backend returned `PFN/EBITDA = 0` for 2024, but the correct value is `0.30`. This fallback ensures AI comments use accurate values.

---

## AI Comment Generation Process

For each metric, the AI receives:

1. **Metric ID**: Unique identifier (e.g., `ebitda`, `roi`)
2. **Metric Title**: Human-readable Italian name
3. **Historical Values**: 3 years of data (oldest to newest)
   ```json
   [
     {"year": "2022", "value": 7233107},
     {"year": "2023", "value": 3724357},
     {"year": "2024", "value": 2245257}
   ]
   ```
4. **Unit**: `€`, `%`, `x`, or dimensionless
5. **Context**: Company name, sector (if available)

### AI Prompt Structure

```
INDICATORE: {metric_title}
VALORI: 2022: €7.2M, 2023: €3.7M, 2024: €2.2M
TREND: decrescente
VARIAZIONE ANNO SU ANNO: -39.7%

AZIENDA: I.T.C. S.R.L.
SETTORE: Metallurgia

ISTRUZIONI:
1. Scrivi un commento di massimo 250 caratteri
2. Usa linguaggio professionale e tecnico
3. Menziona il valore più recente e il trend
4. Se il trend è negativo, suggerisci cosa monitorare
5. Risposta SOLO il commento, niente altro
```

### Output Example

```json
{
  "ebitda": "EBITDA in significativo calo: €2.2M nel 2024 (-39.7% YoY).
             Trend decrescente dal 2022. Monitorare margini operativi e
             efficienza gestionale."
}
```

---

## Verification Checklist

When generating AI comments, verify:

- [ ] All 21 metrics have AI comments generated
- [ ] Values match frontend display (especially PFN/EBITDA)
- [ ] Comments are in Italian
- [ ] Comments are ≤250 characters
- [ ] Trends are accurately described
- [ ] YoY changes are calculated correctly

---

## Usage Example

### Backend Extraction
```python
from extract_anbil_data_comprehensive_with_ai import extract_comprehensive_with_ai

# Extract with AI comments
result = extract_comprehensive_with_ai(
    report_json=report_data,
    generate_comments=True  # Set to False to skip AI
)

# Access AI comments
comments = result['data']['ai_comments']
print(comments['ebitda'])
print(comments['roi'])
print(comments['profilo_economico_overall'])
```

### Frontend Display
```typescript
const { ai_comments, years } = data;
const latest = years[0];

// Display metric with AI comment
<MetricCard
  title="EBITDA - Risultato Operativo Lordo"
  value={latest.ebitda}
  unit="€"
  chartData={years.map(y => ({ year: y.year, value: y.ebitda }))}
  aiComment={ai_comments.ebitda}
/>
```

---

## Version History

- **v2.1** (2025-12-11): Added PFN/EBITDA fallback calculation fix
- **v2.0** (2025-12-09): Expanded from 6 to 21 metrics with comprehensive AI comments
- **v1.1** (2025-12-08): Initial 6 metrics with basic AI comments

---

**Maintained by:** Formula Finance Development Team
**Last Updated:** 2025-12-11
**Status:** ✅ Production Ready
