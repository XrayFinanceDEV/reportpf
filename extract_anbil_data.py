#!/usr/bin/env python3
"""
extract_anbil_data.py
Extracts key financial metrics from ITC report JSON for anbil dashboard

Extracts 6 key metrics for 3 years (2022-2024):
1. REVENUE (Ricavi Vendite e Prestazioni)
2. EBITDA (Risultato Operativo Lordo)
3. COSTI PER LA MATERIA PRIMA (Materie prime + Variazione rimanenze)
4. COSTI PER I SERVIZI (Costi per servizi)
5. COSTI DEL PERSONALE (Costi del personale)
6. COSTI PER GLI ONERI FINANZIARI (Interessi e altri oneri finanziari)
"""

from typing import Dict, List, Any, Optional


def extract_metric_from_pl(pl_items: List[Dict], label_keyword: str) -> float:
    """
    Extract a metric value from profile_and_loss_account items by label keyword

    Args:
        pl_items: List of profit & loss items
        label_keyword: Keyword to search for in the label (case-insensitive)

    Returns:
        The group_value of the matching item, or 0 if not found
    """
    label_keyword_lower = label_keyword.lower()

    for item in pl_items:
        label = item.get('label', '').lower()
        if label_keyword_lower in label:
            return float(item.get('group_value', 0))

    return 0.0


def extract_anbil_data(report_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract key financial metrics from ITC report JSON

    Args:
        report_json: The complete report JSON (from resp-itc.json format)

    Returns:
        Dictionary with extracted metrics organized by year
    """
    try:
        # Navigate to financial_analysis
        fa = report_json['api_response']['financial_analysis']
        financial_reports = fa['financial_report']

        # Extract company name from registry
        company_name = "N/A"
        try:
            # Try to get from consolidated_financial_statements
            if 'consolidated_financial_statements' in fa:
                cfs = fa['consolidated_financial_statements']
                if isinstance(cfs, list) and len(cfs) > 0:
                    if 'registry' in cfs[0]:
                        company_name = cfs[0]['registry'].get('name', 'N/A')

            # If not found, try organization_name
            if company_name == "N/A" and 'organization_name' in fa:
                company_name = fa['organization_name']
        except (KeyError, IndexError, TypeError):
            pass  # Keep default "N/A"

        # Process each year
        years_data = []

        for fr in financial_reports:
            year = fr.get('balance_year', 'N/A')

            # Get profile_and_loss_account items
            pl_items = fr.get('profile_and_loss_account', [])

            # Extract the 6 key metrics
            # Note: For "Materie prime", we need to add both raw materials and inventory variation
            materie_prime = extract_metric_from_pl(pl_items, 'materie prime')
            var_rimanenze = extract_metric_from_pl(pl_items, 'var rim mat prime')

            year_metrics = {
                'year': year,
                'revenue': extract_metric_from_pl(pl_items, 'ricavi vendite'),
                'ebitda': extract_metric_from_pl(pl_items, 'risultato operativo lordo'),
                'costi_materia_prima': materie_prime + var_rimanenze,
                'costi_materia_prima_detail': {
                    'materie_prime_acquistate': materie_prime,
                    'variazione_rimanenze': var_rimanenze
                },
                'costi_servizi': extract_metric_from_pl(pl_items, 'costi per servizi'),
                'costi_personale': extract_metric_from_pl(pl_items, 'costi del personale'),
                'costi_oneri_finanziari': extract_metric_from_pl(pl_items, 'interessi e altri oneri finanziari'),
            }

            years_data.append(year_metrics)

        # Sort by year (most recent first)
        years_data.sort(key=lambda x: x['year'], reverse=True)

        # Create response structure
        result = {
            'success': True,
            'data': {
                'company_name': company_name,
                'years': years_data,
                'latest_year': years_data[0] if years_data else None
            },
            'metadata': {
                'company_name': company_name,
                'years_count': len(years_data),
                'years_available': [y['year'] for y in years_data]
            }
        }

        return result

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to extract anbil data from report JSON'
        }


def format_currency(value: float) -> str:
    """Format a number as Italian currency"""
    return f"€ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def print_anbil_summary(anbil_data: Dict[str, Any]) -> None:
    """Print a formatted summary of the extracted data"""
    if not anbil_data.get('success'):
        print(f"❌ Error: {anbil_data.get('error', 'Unknown error')}")
        return

    print("\n" + "="*80)
    print("ANBIL DATA EXTRACTION - Summary")
    print("="*80)

    company_name = anbil_data['data'].get('company_name', 'N/A')
    print(f"\n🏢 COMPANY: {company_name}\n")

    years_data = anbil_data['data']['years']

    for year_data in years_data:
        year = year_data['year']
        print(f"\n📅 YEAR {year}")
        print("-" * 80)
        print(f"1. REVENUE:                      {format_currency(year_data['revenue'])}")
        print(f"2. EBITDA:                       {format_currency(year_data['ebitda'])}")
        print(f"3. COSTI MATERIA PRIMA:          {format_currency(year_data['costi_materia_prima'])}")
        print(f"   - Materie prime acquistate:   {format_currency(year_data['costi_materia_prima_detail']['materie_prime_acquistate'])}")
        print(f"   - Variazione rimanenze:       {format_currency(year_data['costi_materia_prima_detail']['variazione_rimanenze'])}")
        print(f"4. COSTI SERVIZI:                {format_currency(year_data['costi_servizi'])}")
        print(f"5. COSTI PERSONALE:              {format_currency(year_data['costi_personale'])}")
        print(f"6. COSTI ONERI FINANZIARI:       {format_currency(year_data['costi_oneri_finanziari'])}")

    print("\n" + "="*80 + "\n")


# Test function
if __name__ == "__main__":
    import json
    import sys

    # Load test data
    test_file = '../docs/new_report/resp-itc.json'

    try:
        with open(test_file, 'r') as f:
            report_json = json.load(f)

        # Extract data
        anbil_data = extract_anbil_data(report_json)

        # Print summary
        print_anbil_summary(anbil_data)

        # Also save to file for inspection
        output_file = 'anbil_extracted_data.json'
        with open(output_file, 'w') as f:
            json.dump(anbil_data, f, indent=2)

        print(f"✅ Data also saved to: {output_file}")

    except FileNotFoundError:
        print(f"❌ Error: Test file '{test_file}' not found")
        print(f"   Please run from the reportpf directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
