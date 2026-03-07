#!/usr/bin/env python3
"""
Compare field codes between 2023 and 2024 PDF formats
"""

import re
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed")
    print("Install with: pip install pdfplumber")
    exit(1)

def extract_field_codes_from_page(text):
    """Extract all field codes from page text"""
    codes = set()

    # Patterns for different field types
    patterns = [
        r'\b(F\d{1,3})\b',      # F01, F02, etc.
        r'\b(ICI\d{1,3})\b',    # ICI001, ICI004, etc.
        r'\b(RS\d{1,3})\b',     # RS100, RS101, etc.
        r'\b(A\d{1,2})\b',      # A01, A02
        r'\b(ISAAFF)\b',        # ISAAFF
        r'\b(IIE\d{1,3})\b',    # IIE001, IIE002, IIE003
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text)
        codes.update(matches)

    return codes

def analyze_pdf(pdf_path):
    """Analyze a PDF and return all field codes with their page numbers"""
    result = {}

    with pdfplumber.open(pdf_path) as pdf:
        print(f"\nAnalyzing: {pdf_path}")
        print(f"Total pages: {len(pdf.pages)}")

        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            codes = extract_field_codes_from_page(text)

            if codes:
                result[page_num] = sorted(codes)
                print(f"  Page {page_num:2d}: {len(codes):2d} codes - {', '.join(sorted(codes)[:5])}{'...' if len(codes) > 5 else ''}")

    return result

def compare_pdfs(pdf_2024, pdf_2023):
    """Compare field codes between two PDFs"""

    print("="*80)
    print("PDF FORMAT COMPARISON: 2024 vs 2023")
    print("="*80)

    # Analyze both PDFs
    codes_2024 = analyze_pdf(pdf_2024)
    codes_2023 = analyze_pdf(pdf_2023)

    # Collect all codes from each PDF
    all_codes_2024 = set()
    all_codes_2023 = set()

    for codes in codes_2024.values():
        all_codes_2024.update(codes)

    for codes in codes_2023.values():
        all_codes_2023.update(codes)

    # Compare
    print("\n" + "="*80)
    print("COMPARISON RESULTS")
    print("="*80)

    print(f"\nTotal unique codes in 2024: {len(all_codes_2024)}")
    print(f"Total unique codes in 2023: {len(all_codes_2023)}")

    only_2024 = all_codes_2024 - all_codes_2023
    only_2023 = all_codes_2023 - all_codes_2024
    common = all_codes_2024 & all_codes_2023

    print(f"\nCommon codes: {len(common)}")
    print(f"Only in 2024: {len(only_2024)}")
    print(f"Only in 2023: {len(only_2023)}")

    if only_2024:
        print("\n❌ CODES ONLY IN 2024:")
        for code in sorted(only_2024):
            print(f"  - {code}")

    if only_2023:
        print("\n❌ CODES ONLY IN 2023:")
        for code in sorted(only_2023):
            print(f"  - {code}")

    if not only_2024 and not only_2023:
        print("\n✅ All field codes are consistent between 2023 and 2024!")
    else:
        print("\n⚠️  WARNING: Format differences detected!")
        print("    The extractor may need updates to handle both years correctly.")

    # Check specific codes mentioned in extractor
    print("\n" + "="*80)
    print("CHECKING TARGET CODES FROM EXTRACTOR")
    print("="*80)

    target_codes = {
        'F01', 'F02', 'F03', 'F05', 'F08', 'F09', 'F10',
        'F12', 'F14', 'F15', 'F17', 'F19', 'F20', 'F21',
        'ICI001', 'ICI004', 'ICI005', 'ICI006', 'ICI008', 'ICI009',
        'ICI010', 'ICI011', 'ICI012', 'ICI013', 'ICI014', 'ICI015',
        'ICI016', 'ICI017', 'ICI019', 'ICI024', 'ICI027', 'ICI029',
        'RS100', 'RS101', 'RS102', 'RS103', 'RS104', 'RS105',
        'RS106', 'RS107', 'RS110', 'RS111', 'RS112', 'RS113', 'RS114',
        'A01', 'A02',
        'ISAAFF', 'IIE001', 'IIE002', 'IIE003'
    }

    missing_2024 = target_codes - all_codes_2024
    missing_2023 = target_codes - all_codes_2023

    if missing_2024:
        print(f"\n❌ Target codes MISSING in 2024 PDF ({len(missing_2024)}):")
        for code in sorted(missing_2024):
            print(f"  - {code}")
    else:
        print("\n✅ All target codes found in 2024 PDF")

    if missing_2023:
        print(f"\n❌ Target codes MISSING in 2023 PDF ({len(missing_2023)}):")
        for code in sorted(missing_2023):
            print(f"  - {code}")
    else:
        print("\n✅ All target codes found in 2023 PDF")

if __name__ == "__main__":
    pdf_2024 = "USP UNICO REDDITI TESSITURA 2024.pdf"
    pdf_2023 = "USP UNICO REDDITI TESSITURA 2023.pdf"

    if not Path(pdf_2024).exists():
        print(f"ERROR: {pdf_2024} not found")
        exit(1)

    if not Path(pdf_2023).exists():
        print(f"ERROR: {pdf_2023} not found")
        exit(1)

    compare_pdfs(pdf_2024, pdf_2023)
