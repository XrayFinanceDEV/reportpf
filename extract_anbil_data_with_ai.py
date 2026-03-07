#!/usr/bin/env python3
"""
extract_anbil_data_with_ai.py
Enhanced version with AI-generated comments for each metric

Extracts key financial metrics + generates AI-powered brief comments
using Claude Haiku 4.5 for trend analysis.
"""

from typing import Dict, List, Any, Optional
from extract_anbil_data import extract_anbil_data, format_currency
from ai_comment_generator import AICommentGenerator


def extract_anbil_data_with_ai_comments(
    report_json: Dict[str, Any],
    generate_comments: bool = True
) -> Dict[str, Any]:
    """
    Extract anbil data with AI-generated comments

    Args:
        report_json: The complete report JSON (from resp-itc.json format)
        generate_comments: Whether to generate AI comments (default True)

    Returns:
        Dictionary with extracted metrics + AI comments
    """
    # First, extract the base data
    result = extract_anbil_data(report_json)

    if not result.get('success') or not generate_comments:
        return result

    try:
        # Initialize AI generator
        generator = AICommentGenerator()

        # Get company context
        company_name = result['data'].get('company_name', 'N/A')
        context = {'company_name': company_name}

        # Get years data
        years_data = result['data']['years']

        if not years_data:
            return result

        # Define metrics to generate comments for
        metrics_config = [
            {
                'id': 'revenue',
                'title': 'Ricavi Vendite e Prestazioni',
                'field': 'revenue',
                'unit': '€'
            },
            {
                'id': 'ebitda',
                'title': 'EBITDA - Risultato Operativo Lordo',
                'field': 'ebitda',
                'unit': '€'
            },
            {
                'id': 'costi_materia_prima',
                'title': 'Costi Materia Prima',
                'field': 'costi_materia_prima',
                'unit': '€'
            },
            {
                'id': 'costi_servizi',
                'title': 'Costi per Servizi',
                'field': 'costi_servizi',
                'unit': '€'
            },
            {
                'id': 'costi_personale',
                'title': 'Costi del Personale',
                'field': 'costi_personale',
                'unit': '€'
            },
            {
                'id': 'costi_oneri_finanziari',
                'title': 'Oneri Finanziari',
                'field': 'costi_oneri_finanziari',
                'unit': '€'
            }
        ]

        # Generate comments for each metric
        comments = {}

        print("\n🤖 Generating AI comments for metrics...")

        for metric_config in metrics_config:
            metric_id = metric_config['id']
            metric_title = metric_config['title']
            field = metric_config['field']
            unit = metric_config['unit']

            # Prepare chart data (oldest to newest for trend calculation)
            chart_data = []
            for year_data in reversed(years_data):  # Reverse to get oldest first
                value = year_data.get(field, 0)
                chart_data.append({
                    'year': year_data['year'],
                    'value': value
                })

            # Generate comment
            print(f"  - {metric_title}...")
            comment = generator.generate_comment(
                metric_id=metric_id,
                metric_title=metric_title,
                values=chart_data,
                unit=unit,
                context=context
            )

            comments[metric_id] = comment

        # Add comments to result
        result['data']['ai_comments'] = comments

        # Also add comments to each year's data for convenience
        for year_data in years_data:
            year_data['ai_comments'] = comments

        print("✅ AI comments generated successfully!\n")

        return result

    except Exception as e:
        print(f"⚠️  Warning: Failed to generate AI comments: {e}")
        # Return data without comments
        return result


def print_anbil_summary_with_comments(anbil_data: Dict[str, Any]) -> None:
    """Print a formatted summary including AI comments"""
    if not anbil_data.get('success'):
        print(f"❌ Error: {anbil_data.get('error', 'Unknown error')}")
        return

    print("\n" + "="*80)
    print("ANBIL DATA EXTRACTION WITH AI COMMENTS - Summary")
    print("="*80)

    company_name = anbil_data['data'].get('company_name', 'N/A')
    print(f"\n🏢 COMPANY: {company_name}\n")

    years_data = anbil_data['data']['years']
    ai_comments = anbil_data['data'].get('ai_comments', {})

    # Print latest year data with comments
    if years_data:
        latest = years_data[0]
        year = latest['year']

        print(f"\n📅 YEAR {year} (LATEST)")
        print("-" * 80)
        print(f"1. REVENUE:                      {format_currency(latest['revenue'])}")
        if 'revenue' in ai_comments:
            print(f"   💬 {ai_comments['revenue']}")

        print(f"\n2. EBITDA:                       {format_currency(latest['ebitda'])}")
        if 'ebitda' in ai_comments:
            print(f"   💬 {ai_comments['ebitda']}")

        print(f"\n3. COSTI MATERIA PRIMA:          {format_currency(latest['costi_materia_prima'])}")
        if 'costi_materia_prima' in ai_comments:
            print(f"   💬 {ai_comments['costi_materia_prima']}")

        print(f"\n4. COSTI SERVIZI:                {format_currency(latest['costi_servizi'])}")
        if 'costi_servizi' in ai_comments:
            print(f"   💬 {ai_comments['costi_servizi']}")

        print(f"\n5. COSTI PERSONALE:              {format_currency(latest['costi_personale'])}")
        if 'costi_personale' in ai_comments:
            print(f"   💬 {ai_comments['costi_personale']}")

        print(f"\n6. COSTI ONERI FINANZIARI:       {format_currency(latest['costi_oneri_finanziari'])}")
        if 'costi_oneri_finanziari' in ai_comments:
            print(f"   💬 {ai_comments['costi_oneri_finanziari']}")

    print("\n" + "="*80 + "\n")


# Test function
if __name__ == "__main__":
    import json
    import sys

    # Load test data
    test_file = '../docs/new_report/resp-itc.json'

    try:
        print("Loading test data...")
        with open(test_file, 'r') as f:
            report_json = json.load(f)

        # Extract data with AI comments
        print("Extracting data with AI comments...\n")
        anbil_data = extract_anbil_data_with_ai_comments(report_json)

        # Print summary
        print_anbil_summary_with_comments(anbil_data)

        # Save to file
        output_file = 'anbil_extracted_data_with_ai.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(anbil_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Data with AI comments saved to: {output_file}")

    except FileNotFoundError:
        print(f"❌ Error: Test file '{test_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
