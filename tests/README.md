# ReportPF Tests Directory

This directory contains all test files, scripts, and documentation for the PDF extractor.

**Note**: This directory is excluded from git (see `/formulafinance/.gitignore`)

## Contents

### Test Scripts
- `test_extractor.py` - Comprehensive test suite for PDF extraction
- `test_v3_extractor.py` - Legacy test script
- `test_optimized.py` - Optimized test script
- `extract_reference_values.py` - Helper to extract reference values from PDFs using Claude vision

### Test Data
- `test_reference_data.json` - Complete reference dataset with expected values for all 8 PDFs

### Extraction Results
- `extract_mazzola_2024.json` - Mazzola 2024 extraction results
- `extract_mazzola_2023.json` - Mazzola 2023 extraction results
- `extract_abs_2024.json` - ABS 2024 extraction results
- `extract_farmacia_2023.json` - Farmacia 2023 extraction results
- `extract_tessitura_2024.json` - Tessitura 2024 extraction results
- `extract_tessitura_2023.json` - Tessitura 2023 extraction results

### Test Reports
- `test_report_*.json` - Test execution reports with timestamps
- `test_run*.log` - Test execution logs

### Documentation
- `TESTING_STRATEGY.md` - Complete testing strategy and approach
- `EXTRACTION_SUMMARY.md` - Summary of extraction results and field coverage

## Test PDFs

The test PDFs are located in the parent directory:
- `SOCIETA' DI PERSONE ORDINARIA.pdf` (Mazzola 2024)
- `BAR MAZZOLA 2023.pdf` (Mazzola 2023)
- `USP ABS SNC ORDINARIA REDDITI 2024.pdf` (ABS 2024)
- `USP ABS SNC ORDINARIA REDDITI 2023.pdf` (ABS 2023)
- `USP REDDITI FARMACIA SNC ORDINARIA 2024.pdf` (Farmacia 2024)
- `USP REDDITI FARMACIA SNC ORDINARIA 2023.pdf` (Farmacia 2023)
- `USP UNICO REDDITI TESSITURA 2024.pdf` (Tessitura 2024)
- `USP UNICO REDDITI TESSITURA 2023.pdf` (Tessitura 2023)

## Running Tests

To run the test suite:

```bash
cd /home/peter/DEV/formulafinance/reportpf
source venv/bin/activate
python tests/test_extractor.py
```

Note: Requires `ANTHROPIC_API_KEY` in `.env` file

## Test Results Summary

✅ **All 8 PDFs successfully extracted**
✅ **100% field coverage** (51 fields per FIELD_MAPPING.md)
✅ **Handles all ISA models**: DG37U, DM04U, CM04U, CD09U, DD09U, DD14U
✅ **Handles edge cases**: Companies in liquidation, negative equity, losses

See `EXTRACTION_SUMMARY.md` for detailed results.
