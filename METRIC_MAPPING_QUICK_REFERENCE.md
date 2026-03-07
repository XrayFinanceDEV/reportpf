# Metric Mapping Quick Reference

## JSON Response Structure

```json
{
  "success": true,
  "data": {
    "company_name": "I.T.C. S.R.L.",
    "years": [
      {
        "year": "2024",
        
        // SECTION 1: Economic Indicators
        "revenue": 15130120.0,
        "ebitda": 2245257.0,
        "costi_materia_prima": 10109091.0,
        "costi_servizi": 1570681.0,
        "costi_personale": 1226685.0,
        "costi_oneri_finanziari": 191499.0,
        
        // SECTION 2: Profitability Ratios (%)
        "roi": 11.01,
        "roe": 12.74,
        "ros": 10.65,
        
        // SECTION 3: Balance Sheet (€)
        "attivo_immobilizzato": 4720368.0,
        "rimanenze": 2837632.0,
        "crediti_verso_clienti": 2247142.0,
        "debiti_verso_fornitori": 1707841.0,
        
        // SECTION 4: Debt Sustainability
        "pfn": 680112.0,
        "pfn_ebitda_ratio": 0.0,
        "costo_del_debito": 3.98,  // %
        "oneri_finanziari_mol": 6.4,  // %
        
        // SECTION 5: Capital Structure
        "patrimonio_netto": 8700929.0,
        "totale_attivo": 14760690.0,
        "patrimonio_netto_attivo": 58.95,  // %
        "passivo_corrente": 3401070.0,
        "totale_passivo": 14760690.0,
        "passivo_corrente_totale_passivo": 23.04,  // %
        
        // SECTION 6: Cash Flow
        "cash_flow": 2245257.0,
        "fccr": 11.72  // ratio
      }
    ],
    
    // AI COMMENTS (22 total)
    "ai_comments": {
      "revenue": "Ricavi in contrazione...",
      "ebitda": "EBITDA in significativo calo...",
      "roi": "ROI in forte calo...",
      "roe": "ROE diminuito...",
      "ros": "ROS in contrazione...",
      "attivo_immobilizzato": "Attivo immobilizzato...",
      "rimanenze": "Rimanenze...",
      "crediti_verso_clienti": "Crediti verso clienti...",
      "debiti_verso_fornitori": "Debiti verso fornitori...",
      "pfn_ebitda_ratio": "PFN/EBITDA ratio...",
      "costo_del_debito": "Costo del debito...",
      "oneri_finanziari_mol": "Oneri finanziari / MOL...",
      "patrimonio_netto_attivo": "Patrimonio netto / Attivo...",
      "passivo_corrente_totale_passivo": "Passivo corrente / Totale passivo...",
      "cash_flow": "Cash flow operativo...",
      "fccr": "FCCR - Fixed Charge Coverage...",
      
      // OVERALL SECTION COMMENT
      "profilo_economico_overall": "Profilo aziendale complessivo..."
    }
  }
}
```

## Frontend Usage Map

### Display Section: PROFILO ECONOMICO
```typescript
// Overall comment for entire section
{ai_comments.profilo_economico_overall}

// EBITDA subsection
<MetricCard 
  title="EBITDA - Risultato Operativo Lordo"
  value={latest.ebitda}
  comment={ai_comments.ebitda}
/>
```

### Display Section: INDICI DI REDDITIVITÀ
```typescript
<MetricCard title="ROI" value={latest.roi} unit="%" comment={ai_comments.roi} />
<MetricCard title="ROE" value={latest.roe} unit="%" comment={ai_comments.roe} />
<MetricCard title="ROS" value={latest.ros} unit="%" comment={ai_comments.ros} />
```

### Display Section: FOCUS PATRIMONIALE
```typescript
<MetricCard 
  title="Attivo Immobilizzato" 
  value={latest.attivo_immobilizzato} 
  comment={ai_comments.attivo_immobilizzato} 
/>
<MetricCard 
  title="Rimanenze" 
  value={latest.rimanenze} 
  comment={ai_comments.rimanenze} 
/>
<MetricCard 
  title="Crediti verso Clienti" 
  value={latest.crediti_verso_clienti} 
  comment={ai_comments.crediti_verso_clienti} 
/>
<MetricCard 
  title="Debiti verso Fornitori" 
  value={latest.debiti_verso_fornitori} 
  comment={ai_comments.debiti_verso_fornitori} 
/>
```

### Display Section: SOSTENIBILITÀ DEL DEBITO
```typescript
<MetricCard 
  title="PFN / EBITDA" 
  value={latest.pfn_ebitda_ratio} 
  unit="x" 
  comment={ai_comments.pfn_ebitda_ratio} 
/>
<MetricCard 
  title="Costo del Debito" 
  value={latest.costo_del_debito} 
  unit="%" 
  comment={ai_comments.costo_del_debito} 
/>
<MetricCard 
  title="Oneri Finanziari / MOL" 
  value={latest.oneri_finanziari_mol} 
  unit="%" 
  comment={ai_comments.oneri_finanziari_mol} 
/>
```

### Display Section: STRUTTURA DEL CAPITALE
```typescript
<MetricCard 
  title="Patrimonio Netto / Attivo" 
  value={latest.patrimonio_netto_attivo} 
  unit="%" 
  comment={ai_comments.patrimonio_netto_attivo} 
/>
<MetricCard 
  title="Passivo Corrente / Totale Passivo" 
  value={latest.passivo_corrente_totale_passivo} 
  unit="%" 
  comment={ai_comments.passivo_corrente_totale_passivo} 
/>
```

### Display Section: CASH FLOW E COPERTURA
```typescript
<MetricCard 
  title="Cash Flow Operativo" 
  value={latest.cash_flow} 
  comment={ai_comments.cash_flow} 
/>
<MetricCard 
  title="FCCR - Fixed Charge Coverage Ratio" 
  value={latest.fccr} 
  unit="x" 
  comment={ai_comments.fccr} 
/>
```

## Units Reference

| Field | Unit | Display Format |
|-------|------|----------------|
| revenue | € | Currency |
| ebitda | € | Currency |
| costi_* | € | Currency |
| roi, roe, ros | % | Percentage (2 decimals) |
| attivo_*, rimanenze, crediti_*, debiti_* | € | Currency |
| *_ratio | % or x | Depends on context |
| cash_flow | € | Currency |
| fccr | x | Ratio (2 decimals) |

## Date Range

All data includes **3 years**:
- 2024 (most recent)
- 2023
- 2022

Access via: `data.years[0]` (2024), `data.years[1]` (2023), `data.years[2]` (2022)
