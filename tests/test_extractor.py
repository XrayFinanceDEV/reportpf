#!/usr/bin/env python3
"""
test_extractor.py
Comprehensive test suite for PDF extraction
"""

import json
import sys
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime
import subprocess


def load_reference_data() -> Dict[str, Any]:
    """Load reference data from JSON file"""
    with open('test_reference_data.json', 'r') as f:
        return json.load(f)


def extract_single_pdf(pdf_file: str, add_delay: bool = True) -> Dict[str, Any]:
    """Extract data from a single PDF using the extractor"""
    print(f"  Extracting: {pdf_file}...", end=" ", flush=True)

    try:
        # Set up environment with API key
        env = os.environ.copy()
        if 'ANTHROPIC_API_KEY' not in env:
            # Try to load from .env file
            if Path('.env').exists():
                with open('.env', 'r') as f:
                    for line in f:
                        if line.strip().startswith('ANTHROPIC_API_KEY='):
                            # Remove quotes if present
                            value = line.split('=', 1)[1].strip()
                            value = value.strip('"').strip("'")
                            env['ANTHROPIC_API_KEY'] = value
                            break

        # Run the extractor using venv Python if available
        python_exec = 'venv/bin/python' if Path('venv/bin/python').exists() else 'python3'
        result = subprocess.run(
            [python_exec, 'extdichiarazione_v3_optimized.py', pdf_file],
            capture_output=True,
            text=True,
            timeout=120,
            env=env
        )

        if result.returncode == 0:
            # Parse JSON from stdout (only the JSON part, ignore log messages)
            stdout_lines = result.stdout.strip().split('\n')
            json_str = None
            for line in stdout_lines:
                if line.startswith('{'):
                    json_str = line
                    break

            if json_str:
                try:
                    data = json.loads(json_str)
                    print("✅")

                    # Add delay between API calls to avoid rate limiting
                    if add_delay:
                        print("  ⏳ Waiting 60 seconds to avoid rate limiting...", end=" ", flush=True)
                        time.sleep(60)
                        print("Done")

                    return data
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parsing error: {e}")
                    print(f"   First 200 chars: {json_str[:200]}")
                    return None
            else:
                print(f"❌ No JSON found in output")
                return None
        else:
            print(f"❌ Error: {result.stderr[:100]}")
            return None
    except subprocess.TimeoutExpired:
        print("❌ Timeout")
        return None
    except Exception as e:
        print(f"❌ Exception: {str(e)[:100]}")
        return None


def compare_value(expected: Any, actual: Any, tolerance: float = 0.01) -> Tuple[bool, str]:
    """
    Compare expected vs actual value with tolerance for numeric values

    Returns:
        (match: bool, message: str)
    """
    # If expected is None, we're not testing this field
    if expected is None:
        return (True, "SKIP")

    # If actual is None or missing
    if actual is None:
        return (False, f"MISSING (expected: {expected})")

    # Numeric comparison with tolerance
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        if expected == 0 and actual == 0:
            return (True, "MATCH")

        # Allow small tolerance for floating point
        diff = abs(expected - actual)
        if expected != 0:
            diff_pct = (diff / abs(expected)) * 100
        else:
            diff_pct = 100 if actual != 0 else 0

        if diff_pct <= tolerance * 100:
            return (True, "MATCH")
        else:
            return (False, f"MISMATCH: Expected={expected:,}, Actual={actual:,}, Diff={diff_pct:.2f}%")

    # String comparison (case insensitive, strip whitespace)
    if isinstance(expected, str) and isinstance(actual, str):
        exp_clean = expected.strip().lower()
        act_clean = str(actual).strip().lower()

        if exp_clean == act_clean:
            return (True, "MATCH")
        else:
            return (False, f"MISMATCH: Expected='{expected}', Actual='{actual}'")

    # Exact comparison for other types
    if expected == actual:
        return (True, "MATCH")
    else:
        return (False, f"MISMATCH: Expected={expected}, Actual={actual}")


def compare_extraction(test_case_id: str, expected: Dict, extracted: Dict) -> Dict[str, Any]:
    """
    Compare extracted data against expected reference values

    Returns:
        Comparison report with field-by-field results
    """
    report = {
        'test_case_id': test_case_id,
        'total_fields': 0,
        'matched_fields': 0,
        'mismatched_fields': 0,
        'skipped_fields': 0,
        'missing_fields': 0,
        'field_results': {},
        'accuracy': 0.0
    }

    def compare_section(section_name: str, expected_section: Dict, extracted_section: Dict):
        """Recursively compare sections"""
        for field, expected_value in expected_section.items():
            field_path = f"{section_name}.{field}"
            report['total_fields'] += 1

            # Get actual value
            actual_value = extracted_section.get(field) if extracted_section else None

            # Compare
            match, message = compare_value(expected_value, actual_value)

            # Record result
            report['field_results'][field_path] = {
                'expected': expected_value,
                'actual': actual_value,
                'match': match,
                'message': message
            }

            # Update counters
            if message == "SKIP":
                report['skipped_fields'] += 1
            elif match:
                report['matched_fields'] += 1
            elif "MISSING" in message:
                report['missing_fields'] += 1
            else:
                report['mismatched_fields'] += 1

    # Compare each section
    for section_name, expected_section in expected.items():
        if isinstance(expected_section, dict):
            extracted_section = extracted.get(section_name, {})
            compare_section(section_name, expected_section, extracted_section)

    # Calculate accuracy (only for non-skipped fields)
    tested_fields = report['total_fields'] - report['skipped_fields']
    if tested_fields > 0:
        report['accuracy'] = (report['matched_fields'] / tested_fields) * 100

    return report


def print_field_comparison(field_path: str, result: Dict):
    """Print a single field comparison result"""
    if result['message'] == "SKIP":
        return  # Don't print skipped fields

    status = "✅" if result['match'] else "❌"
    print(f"    {status} {field_path}: {result['message']}")


def print_report(report: Dict):
    """Print comparison report"""
    print(f"\n  Accuracy: {report['accuracy']:.1f}%")
    print(f"  Matched: {report['matched_fields']}, "
          f"Mismatched: {report['mismatched_fields']}, "
          f"Missing: {report['missing_fields']}, "
          f"Skipped: {report['skipped_fields']}")

    # Print mismatches and missing fields
    if report['mismatched_fields'] > 0 or report['missing_fields'] > 0:
        print(f"\n  Issues:")
        for field_path, result in report['field_results'].items():
            if not result['match'] and result['message'] != "SKIP":
                print_field_comparison(field_path, result)


def run_test_suite():
    """Run complete test suite"""
    print("="*80)
    print("PDF EXTRACTION TEST SUITE")
    print("="*80)
    print()

    # Load reference data
    reference_data = load_reference_data()
    test_cases = reference_data['test_cases']

    # Results tracking
    all_reports = {}
    total_accuracy = 0
    valid_tests = 0

    # Test each case
    test_case_items = list(test_cases.items())
    total_tests = len(test_case_items)

    for idx, (test_case_id, test_case) in enumerate(test_case_items, 1):
        is_last_test = (idx == total_tests)
        pdf_file = test_case['pdf_file']
        company = test_case['company']
        year = test_case['year']
        expected_values = test_case['expected_values']

        print(f"\n{'='*80}")
        print(f"TEST: {test_case_id} - {company} ({year})")
        print(f"PDF: {pdf_file}")
        print(f"{'='*80}")

        # Check if PDF exists
        if not Path(pdf_file).exists():
            print(f"  ⚠️  PDF file not found: {pdf_file}")
            continue

        # Check if we have expected values
        has_expected = any(
            v is not None
            for section in expected_values.values()
            if isinstance(section, dict)
            for v in section.values()
        )

        if not has_expected:
            print(f"  ⚠️  No reference data - extraction only (no validation)")
            # Still extract to see what we get
            extracted = extract_single_pdf(pdf_file, add_delay=not is_last_test)
            if extracted:
                print(f"\n  📊 Extracted data preview:")
                if 'identificativi' in extracted:
                    print(f"     Company: {extracted['identificativi'].get('ragione_sociale', 'N/A')}")
                    print(f"     CF: {extracted['identificativi'].get('codice_fiscale', 'N/A')}")
                if 'ricavi' in extracted:
                    print(f"     Ricavi: €{extracted['ricavi'].get('ricavi_dichiarati', 0):,}")
            continue

        # Extract from PDF
        extracted = extract_single_pdf(pdf_file, add_delay=not is_last_test)

        if not extracted:
            print(f"  ❌ Extraction failed")
            continue

        # Compare against reference
        report = compare_extraction(
            test_case_id,
            expected_values,
            extracted
        )

        # Print report
        print_report(report)

        # Store report
        all_reports[test_case_id] = report

        # Update totals
        if report['accuracy'] > 0:
            total_accuracy += report['accuracy']
            valid_tests += 1

    # Print summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")

    if valid_tests > 0:
        avg_accuracy = total_accuracy / valid_tests
        print(f"\nTests completed: {valid_tests}/{len(test_cases)}")
        print(f"Average accuracy: {avg_accuracy:.1f}%")

        print(f"\nIndividual results:")
        for test_id, report in all_reports.items():
            status = "✅" if report['accuracy'] >= 95 else "⚠️" if report['accuracy'] >= 80 else "❌"
            print(f"  {status} {test_id}: {report['accuracy']:.1f}% accuracy")
    else:
        print("\nNo tests with reference data completed.")

    # Save detailed report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"test_report_{timestamp}.json"

    with open(report_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'tests_completed': valid_tests,
                'average_accuracy': avg_accuracy if valid_tests > 0 else 0
            },
            'reports': all_reports
        }, f, indent=2)

    print(f"\nDetailed report saved to: {report_file}")
    print()


if __name__ == "__main__":
    try:
        run_test_suite()
    except KeyboardInterrupt:
        print("\n\nTest suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
