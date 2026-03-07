# Cleanup Summary - V1/V2 Files Archived

**Date**: 2025-11-29
**Action**: Moved all V1 and V2 files to `_old/` folder

---

## ✅ What Was Done

Created `_old/` folder and moved **23 legacy files**:

### Extractor Files (2)
- `extdichiarazione.py` - V1 extractor
- `extdichiarazione_v2.py` - V2 extractor with OCR

### Documentation Files (10)
- `V2_MIGRATION_COMPLETE.md`
- `V2_EXTRACTOR_GUIDE.md`
- `V2_PRODUCTION_READY.md`
- `EXTRACTOR_QUICK_REF.md`
- `EXTRACTOR_RELIABILITY_ANALYSIS.md`
- `FIELD_MAPPING.md`
- `RELIABILITY_IMPLEMENTATION_GUIDE.md`
- `IMPLEMENTATION_COMPLETE.md`
- `INTEGRATION_COMPLETE.md`
- `COMPLETION_SUMMARY.md`
- `DATA_COMPARISON_2022_2023.md`

### Test & Debug Files (11)
- `test_extractor_comparison.py`
- `compare_pdf_formats.py`
- `test_extraction_fixes.py`
- `debug_pdf.py`
- `debug_all_codes.py`
- `debug_f14_2024.py`
- `debug_mazzola.py`
- `debug_pattern_match.py`
- `debug_rs_extraction.py`
- `debug_tessitura_issues.py`
- (+ others)

---

## 📁 Current Structure

### Production Files (V3)

**Extractor:**
- `extdichiarazione_v3.py` - V3 extractor (Claude Haiku 3.5)

**API Server:**
- `api_server.py` - FastAPI server (uses V3)

**Testing:**
- `test_v3_extractor.py` - V3 test script
- Other test files for API, formulas, etc.

**Documentation:**
- `README_V3.md` - Main V3 guide
- `V3_QUICK_START.md` - Quick start
- `V3_MIGRATION_GUIDE.md` - Migration guide
- `V3_IMPLEMENTATION_SUMMARY.md` - Implementation details
- `V3_TEST_RESULTS.md` - Test results

**Utilities:**
- `formule_report_pf.py` - Formula calculations
- `validation.py` - Data validation

---

## 🗂️ Archive Location

All old files are in:
```
reportpf/_old/
```

With README explaining:
- What files are archived
- Why they were replaced
- How to use V3 instead

---

## 🎯 Benefits

### Before Cleanup
- 50+ files in main directory
- Mix of V1, V2, V3 files
- Confusing which to use
- Old debug files cluttering

### After Cleanup
- Clean main directory
- Only V3 production files
- Clear what to use
- Easy to navigate

---

## ⚠️ Important

**Old files are NOT deleted**, just moved to `_old/` for reference.

If you need to:
- **Reference V2 code**: See `_old/extdichiarazione_v2.py`
- **Check old docs**: See `_old/V2_*.md`
- **Rollback to V2**: Copy files back (not recommended)

---

## 🚀 What to Use Now

### For Development:
```bash
# Test V3 extractor
python test_v3_extractor.py <pdf1> <pdf2>

# Start API server
python api_server.py
```

### For Documentation:
- Read: `README_V3.md`
- Quick start: `V3_QUICK_START.md`
- Full guide: `V3_MIGRATION_GUIDE.md`

### For Production:
- Use: `api_server.py` (configured for V3)
- API docs: http://localhost:8001/docs

---

## 📊 File Count

- **Before**: ~50 files
- **After**: ~30 files (main directory)
- **Archived**: 23 files (in `_old/`)

---

*Cleanup completed: 2025-11-29*
*Current version: V3 (Claude Haiku 3.5)*
*Status: Production ready* ✅
