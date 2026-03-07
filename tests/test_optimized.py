#!/usr/bin/env python3
"""
Test optimized extractor to measure token savings
"""

import os
from extdichiarazione_v3_optimized import DichiarazioneExtractorV3Optimized

def test_page_detection():
    """Test page detection on a sample PDF"""

    # Find a test PDF
    test_pdfs = [
        "USP UNICO REDDITI TESSITURA 2024.pdf",
        "dichiarazione_2024.pdf",
        "dichiarazione_2023.pdf"
    ]

    pdf_path = None
    for pdf in test_pdfs:
        if os.path.exists(pdf):
            pdf_path = pdf
            break

    if not pdf_path:
        print("❌ No test PDF found!")
        print(f"   Looking for: {test_pdfs}")
        return

    print(f"\n{'='*60}")
    print(f"Testing Optimized Extractor")
    print(f"{'='*60}\n")
    print(f"📄 PDF: {pdf_path}")
    print(f"📊 File size: {os.path.getsize(pdf_path):,} bytes")
    print()

    # Create extractor (with dummy API key for testing page detection)
    os.environ['ANTHROPIC_API_KEY'] = 'test-key-for-page-detection'
    extractor = DichiarazioneExtractorV3Optimized()

    # Find relevant pages
    print("🔍 Scanning for relevant pages...")
    relevant_pages = extractor.find_relevant_pages(pdf_path)

    print()
    print(f"✅ Results:")
    print(f"   Total pages scanned: {max(relevant_pages) if relevant_pages else 0}")
    print(f"   Relevant pages found: {len(relevant_pages)}")
    print(f"   Pages to analyze: {sorted(relevant_pages)}")

    # Calculate estimated savings
    if relevant_pages:
        total_pages = max(relevant_pages)
        savings = ((total_pages - len(relevant_pages)) / total_pages) * 100
        print()
        print(f"💰 Estimated token savings: ~{savings:.1f}%")
        print(f"   Only analyzing {len(relevant_pages)}/{total_pages} pages")

    print()
    print(f"{'='*60}\n")


if __name__ == "__main__":
    test_page_detection()
