# PDF Format Differences: 2023 vs 2024

## 🚨 Critical Findings

Our optimized extractor (`extdichiarazione_v3_optimized.py`) has **major compatibility issues** with the actual PDF formats.

---

## 📊 Summary of Issues

| Issue | Impact | Severity |
|-------|--------|----------|
| ICI codes only in 2024 | 2023 extraction will fail | **CRITICAL** |
| ISA codes only in 2024 | 2023 extraction will fail | **CRITICAL** |
| RS100-RS114 don't exist | Balance sheet extraction fails for BOTH years | **CRITICAL** |
| Different page layouts | Page filtering may miss data | **HIGH** |

---

## 1. ICI Codes (Economic Indicators)

### ❌ Problem
The extractor looks for ICI codes (ICI001-ICI029) which **only exist in 2024 PDFs**.

### 2024 Format (Page 25)
```
Prospetto ICI001 Ricavi dichiarati                              24240,00
economico ICI002 Ulteriori componenti positivi                      0,00
         ICI003 RICAVI DA GESTIONE CARATTERISTICA              24240,00
         ICI004 Esistenze iniziali                               150,00
         ICI005 Rimanenze finali                                 150,00
         ICI006 Costi per l'acquisto                              47,00
         ICI008 Altri costi per servizi                        11310,00
         ICI009 Costo per godimento di beni di terzi               0,00
         ICI011 Valore aggiunto                                -8387,00
         ICI013 Spese per collaboratori                            0,00
         ICI014 Margine operativo lordo                        -8387,00
         ICI015 Ammortamenti                                       0,00
         ICI016 Accantonamenti                                     0,00
         ICI017 Reddito operativo                              -8387,00
         ICI019 Interessi e altri oneri finanziari                22,00
         ICI024 Reddito                                        -8408,00
         ICI027 Numero addetti                                 1,000000
         ICI029 Valore dei beni strumentali                    7800,00
```

### 2023 Format (Pages 22-24)
**NO ICI CODES!** Instead, data is in narrative format:

```
DETTAGLIO RICAVI PER ADDETTO [IIE00101]
DESCRIZIONE                                          Valore
A Ricavi dichiarati                                  18.769,00
B Ricavi stimati                                     12.151,00

[Later in the document]
A F08 - Esistenze iniziali                           150,00
B F09 - Rimanenze finali                             150,00
C Costo del venduto                                  199,00

[And]
B F12 - Costo per servizi                            14.156,00
```

### 🔧 Solution Required
- **2024**: Extract from structured "Prospetto economico" with ICI codes (Page 25)
- **2023**: Extract from Quadro F (Pages 20-21) + ISA detail pages (22-24)
  - Ricavi: F01 from Quadro F
  - Costi: F08, F09, F10, F12, F14, F15, F17, F19 from Quadro F
  - Economic results: Parse from ISA narrative sections

---

## 2. ISA Codes (Synthetic Reliability Indicators)

### ❌ Problem
ISA codes (ISAAFF, IIE001, IIE002, IIE003) **only exist in 2024**.

### 2024 Format (Page 28)
```
IIE001  Ricavi per addetto                           24240,00
IIE002  Valore aggiunto per addetto                  -8387,00
IIE003  Reddito per addetto                          -8408,00
ISAAFF  Punteggio ISA                                    5,00
```

### 2023 Format
These codes appear **in square brackets** within explanatory text:
```
DETTAGLIO RICAVI PER ADDETTO [IIE00101]
A Ricavi dichiarati                                  18.769,00

DETTAGLIO VALORE AGGIUNTO PER ADDETTO [IIE00201]
```

Note the different format: `[IIE00101]` vs `IIE001`

### 🔧 Solution Required
- **2024**: Extract IIE001-IIE003 and ISAAFF directly from page 28
- **2023**: Parse values from ISA detail sections (pages 22-24), matching the old bracket format `[IIE00101]`, `[IIE00201]`

---

## 3. Quadro RS (Balance Sheet) - RS100-RS114

### ❌ Problem
The extractor searches for **RS100-RS114**, but these codes **don't exist in either year**!

### Actual RS Codes Found

**Both 2024 and 2023 use the same RS numbering:**

| Page | Range | Example Codes |
|------|-------|--------------|
| 9    | RS1-RS29 | RS1, RS11, RS12, RS13, RS14, RS15... |
| 10   | RS30-RS46 | RS30, RS31, RS32, RS33, RS34, RS35... |
| 11   | RS47-RS117 | RS47, RS48, RS49, RS50, RS51... |
| 12   | RS118+ | RS118, RS119, RS120, RS121, RS122, RS123 |

**The RS codes we need are likely:**
- Rimanenze: RS1 or similar
- Crediti clienti: RS11, RS12, RS13?
- Debiti fornitori: RS30-RS46 range?

### 🔧 Solution Required
1. Read Quadro RS pages (9-12) to identify correct field mappings
2. Update FIELD_MAPPING.md with actual RS codes
3. Test extraction on both years to verify correct values

---

## 4. Quadro F (Revenue/Costs)

### ✅ Good News
F codes **are consistent** between both years:

**Both 2024 and 2023 have:**
- F01, F02, F03, F05 (Ricavi)
- F08, F09, F10, F12, F14, F15 (Costi)
- F17, F19, F20, F21 (Altri costi e risultato)

**Location:**
- 2024: Pages 20-21
- 2023: Pages 17-18

---

## 5. Personale (Personnel)

### ✅ Good News
A01, A02 codes **are consistent**:

**Both years:**
- A01: Giornate dipendenti
- A02: Giornate altro personale

**Location:**
- Both 2024 and 2023: Page 15

---

## 📋 Recommended Actions

### 1. **Immediate: Fix RS Code Mapping**
```python
# Current (WRONG):
'RS100', 'RS101', 'RS102', ...

# Need to identify actual codes like:
'RS1', 'RS11', 'RS12', ...
```

### 2. **Critical: Add Year Detection**
```python
def detect_year_format(pdf_path: str) -> str:
    """Detect if PDF uses 2023 or 2024 format"""
    with pdfplumber.open(pdf_path) as pdf:
        # Search for ICI codes
        for page in pdf.pages[20:28]:  # Economic indicator pages
            text = page.extract_text() or ''
            if re.search(r'\bICI001\b', text):
                return '2024'
    return '2023'
```

### 3. **Create Format-Specific Extractors**
- `extract_2024_format()` - Uses ICI codes from page 25
- `extract_2023_format()` - Uses Quadro F + ISA narrative parsing

### 4. **Update TARGET_CODES**
```python
TARGET_CODES_2024 = {
    'F01', 'F02', ...,  # Quadro F
    'ICI001', 'ICI004', ...,  # Economic indicators
    'RS1', 'RS11', ...,  # Balance sheet (actual codes)
    'A01', 'A02',
    'ISAAFF', 'IIE001', 'IIE002', 'IIE003'
}

TARGET_CODES_2023 = {
    'F01', 'F02', ...,  # Quadro F
    'RS1', 'RS11', ...,  # Balance sheet
    'A01', 'A02',
    # NO ICI codes
    # Parse ISA from narrative text
}
```

---

## 📊 Comparison Table

| Field Category | 2023 Format | 2024 Format | Compatible? |
|---------------|-------------|-------------|-------------|
| Quadro F (F01-F21) | ✅ Pages 17-18 | ✅ Pages 20-21 | ✅ YES |
| Personale (A01-A02) | ✅ Page 15 | ✅ Page 15 | ✅ YES |
| Economic Indicators | ❌ Narrative text | ✅ ICI codes (p.25) | ❌ NO |
| ISA Scores | ❌ `[IIE00101]` format | ✅ IIE001 format | ❌ NO |
| Balance Sheet (RS) | ❌ RS1-RS123 | ❌ RS1-RS123 | ⚠️ Wrong codes |

---

## 🎯 Next Steps

1. **Map correct RS codes** - Read pages 9-12 to identify balance sheet field mappings
2. **Create year-aware extractor** - Detect format and use appropriate extraction logic
3. **Test with both PDFs** - Verify all 43 fields extract correctly for both years
4. **Update documentation** - Reflect actual code mappings in FIELD_MAPPING.md

---

## 💡 Testing Command

```bash
# Compare extraction results
source venv/bin/activate
python extdichiarazione_v3_optimized.py "USP UNICO REDDITI TESSITURA 2024.pdf" 2024 > result_2024.json
python extdichiarazione_v3_optimized.py "USP UNICO REDDITI TESSITURA 2023.pdf" 2023 > result_2023.json

# Check for errors
cat result_2024.json | jq '.quadro_rs'  # Should NOT be all zeros
cat result_2023.json | jq '.isa'  # Currently will fail
```
