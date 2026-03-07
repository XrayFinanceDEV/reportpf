# PDF Extraction Testing Strategy

## Test Cases Overview

| Company | Year | PDF File | Reference Status |
|---------|------|----------|-----------------|
| Mazzola | 2024 | SOCIETA' DI PERSONE ORDINARIA.pdf | ✅ **EXTRACTED** |
| Mazzola | 2023 | BAR MAZZOLA 2023.pdf | ⏳ Pending |
| ABS S.n.c. | 2024 | USP ABS SNC ORDINARIA REDDITI 2024.pdf | ⏳ Pending |
| ABS S.n.c. | 2023 | USP ABS SNC ORDINARIA REDDITI 2023.pdf | ✅ **FROM FARMACIA.JSON** |
| Farmacia | 2024 | USP REDDITI FARMACIA SNC ORDINARIA 2024.pdf | ✅ **FROM FARMACIA.JSON** |
| Farmacia | 2023 | USP REDDITI FARMACIA SNC ORDINARIA 2023.pdf | ⏳ Pending |
| Tessitura | 2024 | USP UNICO REDDITI TESSITURA 2024.pdf | ⏳ Pending |
| Tessitura | 2023 | USP UNICO REDDITI TESSITURA 2023.pdf | ⏳ Pending |

## Data Sources

1. **Mazzola 2024**: Manually extracted from PDF (pages 1-27, ISA model DG37U)
2. **Farmacia 2024 & ABS 2023**: Already extracted in `farmacia.json`
3. **Remaining 5 PDFs**: Use extractor to fill in

## Testing Approach

### Phase 1: Consolidate Existing Data ✅
- [x] Extract Mazzola 2024 from PDF
- [x] Use farmacia.json for Farmacia 2024 and ABS 2023

### Phase 2: Extract Remaining PDFs
- [ ] Run extractor on Mazzola 2023
- [ ] Run extractor on ABS 2024
- [ ] Run extractor on Farmacia 2023
- [ ] Run extractor on Tessitura 2024
- [ ] Run extractor on Tessitura 2023

### Phase 3: Run Full Test Suite
- [ ] Execute `test_extractor.py` on all 8 PDFs
- [ ] Generate accuracy report
- [ ] Identify patterns in extraction errors
- [ ] Fine-tune extractor based on findings

## Key Fields to Validate

| Category | Fields | Importance |
|----------|--------|------------|
| **Identificativi** | CF, P.IVA, Ragione Sociale, Anno | Critical |
| **Ricavi** | Ricavi dichiarati, Altri componenti | Critical |
| **Costi** | Materie prime, Servizi, Personale, Ammortamenti | High |
| **Risultati** | Valore Aggiunto, MOL, Reddito Operativo, Reddito Impresa | Critical |
| **Personale** | Numero addetti equivalenti | Medium |
| **ISA** | Punteggio, Modello applicato | High |
| **Quadro RS** | Totale Attivo, Patrimonio Netto, TFR, Debiti Fornitori | High |

## Success Criteria

- **Excellent**: >95% accuracy on all critical fields
- **Good**: 80-95% accuracy
- **Needs Improvement**: <80% accuracy

## Expected Challenges

1. **PDF Format Variations**: 2023 vs 2024 formats may differ
2. **ISA Model Differences**: Different ATECO codes → different ISA models
   - Mazzola: DG37U (Bar)
   - Farmacia: DM04U (Pharmacy)
   - ABS: CD09U (Unknown)
   - Tessitura: Unknown model
3. **Balance Sheet Issues**: TFR placement varies by year
4. **Missing Fields**: Some companies may not have all data

## Next Steps

1. Run quick extraction test on one missing PDF
2. If successful → batch extract all remaining PDFs
3. Run full test suite
4. Analyze results and fine-tune patterns
