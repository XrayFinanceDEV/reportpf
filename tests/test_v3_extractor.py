#!/usr/bin/env python3
"""
Test script for V3 extractor

Usage:
    python test_v3_extractor.py <pdf_2024.pdf> <pdf_2023.pdf>

Example:
    python test_v3_extractor.py dichiarazione_2024.pdf dichiarazione_2023.pdf
"""

import sys
import os
import json
import time
from pathlib import Path

# Add reportpf to path if running from parent directory
if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from extdichiarazione_v3 import DichiarazioneExtractorV3, elabora_biennio


def test_single_pdf(pdf_path: str, anno: int):
    """Test extraction from a single PDF"""
    print(f"\n{'='*60}")
    print(f"Testing V3 Extractor - Single PDF")
    print(f"{'='*60}\n")
    print(f"📄 PDF: {pdf_path}")
    print(f"📅 Year: {anno}")
    print(f"\n⏳ Extracting data...\n")

    try:
        start_time = time.time()

        # Initialize extractor
        extractor = DichiarazioneExtractorV3()

        # Extract data
        result = extractor.estrai_dati_input(pdf_path, anno)

        elapsed_time = time.time() - start_time

        print(f"✅ Extraction successful!")
        print(f"⏱️  Time: {elapsed_time:.2f} seconds")
        print(f"\n📊 Results:\n")

        # Display key fields
        print(f"Ragione Sociale: {result['identificativi']['ragione_sociale']}")
        print(f"Codice Fiscale: {result['identificativi']['codice_fiscale']}")
        print(f"Anno: {result['identificativi']['anno']}")
        print(f"\nRicavi Dichiarati: €{result['ricavi']['ricavi_dichiarati']:,.2f}")
        print(f"Reddito Impresa: €{result['risultati']['reddito_impresa']:,.2f}")
        print(f"Punteggio ISA: {result['isa']['punteggio']}")

        # Save full result to file
        output_file = f"v3_extraction_{anno}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Full result saved to: {output_file}")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_biennio(pdf_corrente: str, pdf_precedente: str):
    """Test extraction from two PDFs (biennio)"""
    print(f"\n{'='*60}")
    print(f"Testing V3 Extractor - Biennio (2 PDFs)")
    print(f"{'='*60}\n")
    print(f"📄 Current year PDF: {pdf_corrente}")
    print(f"📄 Previous year PDF: {pdf_precedente}")
    print(f"\n⏳ Extracting data from both PDFs...\n")

    try:
        start_time = time.time()

        # Extract data from both PDFs
        result = elabora_biennio(pdf_corrente, pdf_precedente)

        elapsed_time = time.time() - start_time

        print(f"✅ Extraction successful!")
        print(f"⏱️  Total time: {elapsed_time:.2f} seconds")
        print(f"\n📊 Results:\n")

        # Display key fields from current year
        corrente = result['anno_corrente']
        precedente = result['anno_precedente']

        print(f"Ragione Sociale: {corrente['identificativi']['ragione_sociale']}")
        print(f"Codice Fiscale: {corrente['identificativi']['codice_fiscale']}")

        print(f"\n📈 Comparison:\n")
        print(f"{'Metric':<25} | {'Previous Year':>15} | {'Current Year':>15} | {'Change':>10}")
        print(f"{'-'*75}")

        ricavi_prec = precedente['ricavi']['ricavi_dichiarati']
        ricavi_corr = corrente['ricavi']['ricavi_dichiarati']
        ricavi_change = ((ricavi_corr - ricavi_prec) / ricavi_prec * 100) if ricavi_prec else 0

        reddito_prec = precedente['risultati']['reddito_impresa']
        reddito_corr = corrente['risultati']['reddito_impresa']
        reddito_change = ((reddito_corr - reddito_prec) / reddito_prec * 100) if reddito_prec else 0

        isa_prec = precedente['isa']['punteggio']
        isa_corr = corrente['isa']['punteggio']
        isa_change = isa_corr - isa_prec

        print(f"{'Ricavi':<25} | €{ricavi_prec:>13,.2f} | €{ricavi_corr:>13,.2f} | {ricavi_change:>8.1f}%")
        print(f"{'Reddito Impresa':<25} | €{reddito_prec:>13,.2f} | €{reddito_corr:>13,.2f} | {reddito_change:>8.1f}%")
        print(f"{'Punteggio ISA':<25} | {isa_prec:>15.1f} | {isa_corr:>15.1f} | {isa_change:>+9.1f}")

        # Save full result to file
        output_file = "v3_extraction_biennio.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Full result saved to: {output_file}")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_api_key():
    """Check if ANTHROPIC_API_KEY is set"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("\n❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("\nPlease set your API key:")
        print("  export ANTHROPIC_API_KEY='your-api-key-here'")
        print("\nGet your API key from: https://console.anthropic.com/")
        return False
    print(f"✅ API key found: {api_key[:10]}...{api_key[-4:]}")
    return True


def main():
    """Main test function"""
    print("\n" + "="*60)
    print("V3 Extractor Test Script")
    print("="*60)

    # Check API key
    if not check_api_key():
        sys.exit(1)

    # Check arguments
    if len(sys.argv) < 2:
        print("\n❌ Error: Missing PDF file arguments")
        print("\nUsage:")
        print("  Single PDF:  python test_v3_extractor.py <pdf_2024.pdf> [year]")
        print("  Biennio:     python test_v3_extractor.py <pdf_2024.pdf> <pdf_2023.pdf>")
        print("\nExample:")
        print("  python test_v3_extractor.py dichiarazione_2024.pdf 2024")
        print("  python test_v3_extractor.py dichiarazione_2024.pdf dichiarazione_2023.pdf")
        sys.exit(1)

    # Check if files exist
    for i in range(1, len(sys.argv)):
        pdf_path = sys.argv[i]
        if pdf_path.endswith('.pdf'):
            if not os.path.exists(pdf_path):
                print(f"\n❌ Error: File not found: {pdf_path}")
                sys.exit(1)
            print(f"✅ Found: {pdf_path}")

    # Test based on number of arguments
    if len(sys.argv) == 2:
        # Single PDF, auto-detect year
        pdf_path = sys.argv[1]
        import re
        match = re.search(r'(202[0-9])', pdf_path)
        anno = int(match.group(1)) if match else 2024
        success = test_single_pdf(pdf_path, anno)

    elif len(sys.argv) == 3:
        # Check if second arg is a year or another PDF
        if sys.argv[2].endswith('.pdf'):
            # Two PDFs - biennio test
            success = test_biennio(sys.argv[1], sys.argv[2])
        else:
            # Single PDF with explicit year
            pdf_path = sys.argv[1]
            anno = int(sys.argv[2])
            success = test_single_pdf(pdf_path, anno)

    else:
        print("\n❌ Error: Too many arguments")
        print("Expected: 1-2 PDF files")
        sys.exit(1)

    # Summary
    print("\n" + "="*60)
    if success:
        print("✅ Test completed successfully!")
        print("\nNext steps:")
        print("1. Review the extracted JSON file")
        print("2. Start the API server: python api_server.py")
        print("3. Test via API: curl -X POST http://localhost:8001/upload/process ...")
    else:
        print("❌ Test failed. Check error messages above.")
    print("="*60 + "\n")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
