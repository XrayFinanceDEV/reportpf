# Report PF - Directory Structure

**Version**: 3.0.0 (V3 - Claude Haiku 3.5)
**Date**: 2025-11-29
**Status**: Production Ready ✅

---

## 📁 Main Directory (Production Files Only)

### Core Files

#### Extractor
- **`extdichiarazione_v3.py`** - V3 PDF data extractor (Claude Haiku 3.5)
  - Extracts all tax declaration fields from PDFs
  - 5-8 second extraction time
  - 95-99% accuracy

#### API Server
- **`api_server.py`** - FastAPI server for PDF processing
  - Version 3.0.0
  - Uses V3 extractor
  - Endpoints: `/upload/process`, `/upload/extract`, `/validate-and-calculate`

#### Alternative API
- **`api_reportpf.py`** - Alternative API implementation (if needed)

#### Supporting Modules
- **`formule_report_pf.py`** - Financial formula calculations
  - NOPAT, EM Score, valuation indicators
  - ROE decomposition, leverage metrics

- **`validation.py`** - Data validation and enrichment
  - Quality scoring
  - Error detection
  - Warning generation

#### Testing
- **`test_v3_extractor.py`** - V3 extractor test script
  - Test single PDFs or biennio (2 PDFs)
  - Results display and JSON export

---

### Documentation

#### V3 Documentation
- **`README_V3.md`** - Main V3 guide and quick reference
- **`V3_QUICK_START.md`** - Get started in 3 steps
- **`V3_MIGRATION_GUIDE.md`** - Complete migration guide from V2
- **`V3_IMPLEMENTATION_SUMMARY.md`** - Technical implementation details
- **`V3_TEST_RESULTS.md`** - Actual test results with data

#### Project Documentation
- **`README.md`** - General project README
- **`CLEANUP_SUMMARY.md`** - Cleanup actions summary
- **`DIRECTORY_STRUCTURE.md`** - This file

---

## 🗂️ Archive Folder

### `_old/` - Legacy Files (43 files)

**Do NOT use these files for production!**

Contains:
- V1 extractor (`extdichiarazione.py`)
- V2 extractor (`extdichiarazione_v2.py`)
- V1/V2 documentation (11 files)
- Old test files (20 files)
- Debug scripts (10 files)

See `_old/README.md` for details.

---

## 🚀 Usage

### Start API Server
```bash
source venv/bin/activate
export ANTHROPIC_API_KEY="your-key-here"
python api_server.py
```

Server runs at: http://localhost:8001

### Test V3 Extractor
```bash
# Single PDF
python extdichiarazione_v3.py <pdf_file> <year>

# Biennio (2 PDFs)
python test_v3_extractor.py <pdf_2024> <pdf_2023>
```

### API Request
```bash
curl -X POST http://localhost:8001/upload/process \
  -F "pdf_anno_corrente=@dich_2024.pdf" \
  -F "pdf_anno_precedente=@dich_2023.pdf"
```

---

## 📊 File Count

| Location | Files | Description |
|----------|-------|-------------|
| **Main Directory** | 13 | Production files (V3) |
| **_old/** | 43 | Archived legacy files |
| **Total** | 56 | All files |

---

## 🎯 What Each File Does

### Production Files (13)

| File | Purpose |
|------|---------|
| `extdichiarazione_v3.py` | V3 PDF extractor (Claude Haiku 3.5) |
| `api_server.py` | FastAPI server (main) |
| `api_reportpf.py` | Alternative API (if needed) |
| `formule_report_pf.py` | Financial calculations |
| `validation.py` | Data validation |
| `test_v3_extractor.py` | V3 testing script |
| `README_V3.md` | Main V3 guide |
| `V3_QUICK_START.md` | Quick start guide |
| `V3_MIGRATION_GUIDE.md` | Migration guide |
| `V3_IMPLEMENTATION_SUMMARY.md` | Implementation details |
| `V3_TEST_RESULTS.md` | Test results |
| `README.md` | Project README |
| `CLEANUP_SUMMARY.md` | Cleanup summary |

### Archived Files (43)

All in `_old/` folder - see `_old/README.md`

---

## 🔧 Dependencies

### Required
- Python 3.8+
- `anthropic>=0.40.0` - Anthropic SDK for Claude
- `fastapi>=0.104.0` - API framework
- `uvicorn>=0.24.0` - ASGI server
- `python-multipart` - File upload support

### Optional (legacy)
- `pdfplumber` - PDF reading (V2 compatibility)
- `easyocr` - OCR (V2 only, not needed for V3)
- `PyMuPDF` - PDF processing (V2 only)

---

## 📝 Notes

### Clean Structure Benefits
- ✅ Only production files in main directory
- ✅ Easy to find what you need
- ✅ No confusion about which version to use
- ✅ Legacy files preserved in `_old/`
- ✅ Clear documentation

### Version History
- **V1**: Basic regex extraction
- **V2**: Enhanced with OCR fallback (deprecated)
- **V3**: Claude Haiku 3.5 powered (current) ✅

### Production Status
- **V3**: Production Ready ✅
- **V2**: Deprecated (archived)
- **V1**: Deprecated (archived)

---

## 🆘 Need Old Files?

All legacy files are in `_old/` for reference:
```bash
ls _old/
cat _old/README.md
```

**But use V3 for production!**

---

*Last updated: 2025-11-29*
*Current version: V3 (Claude Haiku 3.5)*
*Status: Production Ready* ✅
