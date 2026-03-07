#!/usr/bin/env python3
"""
extract_anbil_data_extended.py
Extended extraction module for comprehensive ANBIL report metrics

Extracts all metrics needed for the PROFILO ECONOMICO, PATRIMONIALE E FINANZIARIO section:
- Economic indicators (EBITDA, ROI, ROE, ROS)
- Balance sheet items (Assets, Liabilities)
- Financial ratios (debt sustainability, profitability)
- Cash flow indicators
"""

from typing import Dict, List, Any, Optional


def extract_metric_from_list(items: List[Dict], label_keyword: str, exact: bool = False) -> float:
    """
    Extract a metric value from a list of items by label keyword

    Args:
        items: List of items with 'label' and 'group_value' keys
        label_keyword: Keyword to search for in the label (case-insensitive)
        exact: If True, requires exact match (case-insensitive)

    Returns:
        The group_value of the matching item, or 0 if not found
    """
    label_keyword_lower = label_keyword.lower()

    for item in items:
        label = item.get('label', '').lower()

        if exact:
            if label == label_keyword_lower:
                return float(item.get('group_value', 0))
        else:
            if label_keyword_lower in label:
                return float(item.get('group_value', 0))

    return 0.0


def extract_comprehensive_metrics(report_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract comprehensive financial metrics from ITC report JSON

    Args:
        report_json: The complete report JSON (from resp-itc.json format)

    Returns:
        Dictionary with all extracted metrics organized by year
    """
    try:
        # Navigate to financial_analysis
        fa = report_json['api_response']['financial_analysis']
        financial_reports = fa['financial_report']

        # Extract company name from registry
        company_name = "N/A"
        try:
            if 'consolidated_financial_statements' in fa:
                cfs = fa['consolidated_financial_statements']
                if isinstance(cfs, list) and len(cfs) > 0:
                    if 'registry' in cfs[0]:
                        company_name = cfs[0]['registry'].get('name', 'N/A')

            if company_name == "N/A" and 'organization_name' in fa:
                company_name = fa['organization_name']
        except (KeyError, IndexError, TypeError):
            pass

        # Process each year
        years_data = []

        for fr in financial_reports:
            year = fr.get('balance_year', 'N/A')

            # Get source data lists
            pl_items = fr.get('profile_and_loss_account', [])
            bs_items = fr.get('balance_sheet', [])
            fi_items = fr.get('financial_index', [])

            # === PROFIT & LOSS METRICS ===
            materie_prime = extract_metric_from_list(pl_items, 'materie prime')
            var_rimanenze = extract_metric_from_list(pl_items, 'var rim mat prime')

            revenue = extract_metric_from_list(pl_items, 'ricavi vendite')
            ebitda = extract_metric_from_list(pl_items, 'risultato operativo lordo')
            costi_servizi = extract_metric_from_list(pl_items, 'costi per servizi')
            costi_personale = extract_metric_from_list(pl_items, 'costi del personale')
            oneri_finanziari = extract_metric_from_list(pl_items, 'interessi e altri oneri finanziari')
            imposte = extract_metric_from_list(pl_items, 'imposte sul reddito')
            risultato_esercizio = extract_metric_from_list(pl_items, "risultato d'esercizio")

            # === BALANCE SHEET - LIQUIDITY ===
            liquidita = extract_metric_from_list(bs_items, 'liquidità')
            if liquidita == 0:
                liquidita = extract_metric_from_list(bs_items, 'disponibilità liquide')

            # === FINANCIAL RATIOS FROM financial_index ===
            roi = extract_metric_from_list(fi_items, 'redditività del capitale investito (roi)')
            roe = extract_metric_from_list(fi_items, 'redditività del capitale proprio (roe)')
            ros = extract_metric_from_list(fi_items, 'redditività operativa delle vendite (ros)')

            pfn = extract_metric_from_list(fi_items, 'pfn', exact=True)
            ebitda_abs = extract_metric_from_list(fi_items, 'ebitda (valore assoluto)')
            pfn_ebitda_ratio = extract_metric_from_list(fi_items, 'pfn/ebitda')

            # FIX: Fallback calculation if pfn_ebitda_ratio is 0 (sometimes incorrect in financial_index)
            # This matches the frontend logic in anbil-transformer.ts (lines 283-286)
            if pfn_ebitda_ratio == 0 and pfn != 0 and ebitda > 0:
                pfn_ebitda_ratio = pfn / ebitda

            oneri_fin_mol = extract_metric_from_list(fi_items, 'oneri finanziari netti / risultato operativo lordo')

            # === BALANCE SHEET ITEMS ===
            attivo_immobilizzato = extract_metric_from_list(bs_items, 'attivo immobilizzato', exact=True)
            rimanenze = extract_metric_from_list(bs_items, 'rimanenze', exact=True)
            crediti_clienti = extract_metric_from_list(bs_items, 'di cui verso clienti')
            debiti_fornitori = extract_metric_from_list(bs_items, 'di cui verso fornitori')

            patrimonio_netto = extract_metric_from_list(bs_items, 'patrimonio netto', exact=True)
            passivo_corrente = extract_metric_from_list(bs_items, 'passivo corrente', exact=True)
            totale_passivo = extract_metric_from_list(bs_items, 'totale passivo', exact=True)
            totale_attivo = extract_metric_from_list(bs_items, 'totale attivo', exact=True)
            debiti_correnti = extract_metric_from_list(bs_items, 'debiti correnti')
            debiti_oltre_bt = extract_metric_from_list(bs_items, 'debiti oltre il b.t.')

            # === CALCULATED RATIOS ===
            # PATRIMONIO NETTO / ATTIVO
            patrimonio_netto_attivo = (patrimonio_netto / totale_attivo * 100) if totale_attivo != 0 else 0

            # PASSIVO CORRENTE / TOTALE PASSIVO
            passivo_corrente_totale = (passivo_corrente / totale_passivo * 100) if totale_passivo != 0 else 0

            # COSTO DEL DEBITO (Oneri finanziari / Debiti totali)
            debiti_totali = debiti_correnti + debiti_oltre_bt
            costo_del_debito = (oneri_finanziari / debiti_totali * 100) if debiti_totali != 0 else 0

            # === CASH FLOW ESTIMATION ===
            # Simplified: Operating cash flow = EBITDA - Working Capital Change
            # For now, we'll use EBITDA as a proxy (actual cash flow needs more data)
            cash_flow_operativo = ebitda  # Simplified - ideally need WC changes

            # === FCCR (Fixed Charge Coverage Ratio) ===
            # FCCR = (EBITDA - CapEx) / (Interest + Lease Payments)
            # Simplified: EBITDA / Oneri finanziari
            fccr = (ebitda / oneri_finanziari) if oneri_finanziari != 0 else 0

            # Build year metrics dictionary
            year_metrics = {
                'year': year,

                # === SECTION 1: ECONOMIC INDICATORS ===
                'revenue': revenue,
                'ebitda': ebitda,
                'ebitda_abs': ebitda_abs,  # From financial_index
                'costi_materia_prima': materie_prime + var_rimanenze,
                'costi_materia_prima_detail': {
                    'materie_prime_acquistate': materie_prime,
                    'variazione_rimanenze': var_rimanenze
                },
                'costi_servizi': costi_servizi,
                'costi_personale': costi_personale,
                'costi_oneri_finanziari': oneri_finanziari,
                'imposte': imposte,
                'risultato_esercizio': risultato_esercizio,

                # === BALANCE SHEET - LIQUIDITY ===
                'liquidita': liquidita,

                # === SECTION 2: PROFITABILITY RATIOS ===
                'roi': roi,  # %
                'roe': roe,  # %
                'ros': ros,  # %

                # === SECTION 3: BALANCE SHEET - FOCUS PATRIMONIALE ===
                'attivo_immobilizzato': attivo_immobilizzato,
                'rimanenze': rimanenze,
                'crediti_verso_clienti': crediti_clienti,
                'debiti_verso_fornitori': debiti_fornitori,

                # === SECTION 4: DEBT SUSTAINABILITY ===
                'pfn': pfn,
                'pfn_ebitda_ratio': pfn_ebitda_ratio,
                'costo_del_debito': costo_del_debito,  # %
                'oneri_finanziari_mol': oneri_fin_mol,  # %

                # === SECTION 5: CAPITAL STRUCTURE ===
                'patrimonio_netto': patrimonio_netto,
                'totale_attivo': totale_attivo,
                'patrimonio_netto_attivo': patrimonio_netto_attivo,  # %
                'passivo_corrente': passivo_corrente,
                'totale_passivo': totale_passivo,
                'passivo_corrente_totale_passivo': passivo_corrente_totale,  # %

                # === SECTION 6: CASH FLOW & COVERAGE ===
                'cash_flow': cash_flow_operativo,
                'fccr': fccr,  # ratio

                # === RAW DATA FOR REFERENCE ===
                'debiti_totali': debiti_totali,
                'debiti_correnti': debiti_correnti,
                'debiti_oltre_bt': debiti_oltre_bt
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
                'years_available': [y['year'] for y in years_data],
                'metrics_extracted': len(year_metrics.keys()) if years_data else 0
            }
        }

        return result

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to extract comprehensive anbil data from report JSON'
        }


def format_currency(value: float) -> str:
    """Format a number as Italian currency"""
    return f"€ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def format_percentage(value: float) -> str:
    """Format a number as percentage"""
    return f"{value:.2f}%"


def format_ratio(value: float) -> str:
    """Format a number as ratio"""
    return f"{value:.2f}x"


def print_comprehensive_summary(anbil_data: Dict[str, Any]) -> None:
    """Print a formatted summary of all extracted data"""
    if not anbil_data.get('success'):
        print(f"❌ Error: {anbil_data.get('error', 'Unknown error')}")
        return

    print("\n" + "="*80)
    print("COMPREHENSIVE ANBIL DATA EXTRACTION - Summary")
    print("="*80)

    company_name = anbil_data['data'].get('company_name', 'N/A')
    print(f"\n🏢 COMPANY: {company_name}")
    print(f"📊 Metrics Extracted: {anbil_data['metadata']['metrics_extracted']}\n")

    years_data = anbil_data['data']['years']

    # Print latest year data
    if years_data:
        latest = years_data[0]
        year = latest['year']

        print(f"📅 YEAR {year} (LATEST)")
        print("=" * 80)

        print("\n1. INDICATORI ECONOMICI")
        print("-" * 80)
        print(f"  Revenue:                     {format_currency(latest['revenue'])}")
        print(f"  EBITDA:                      {format_currency(latest['ebitda'])}")
        print(f"  Costi Materia Prima:         {format_currency(latest['costi_materia_prima'])}")
        print(f"  Costi Servizi:               {format_currency(latest['costi_servizi'])}")
        print(f"  Costi Personale:             {format_currency(latest['costi_personale'])}")
        print(f"  Oneri Finanziari:            {format_currency(latest['costi_oneri_finanziari'])}")

        print("\n2. INDICI DI REDDITIVITÀ")
        print("-" * 80)
        print(f"  ROI:                         {format_percentage(latest['roi'])}")
        print(f"  ROE:                         {format_percentage(latest['roe'])}")
        print(f"  ROS:                         {format_percentage(latest['ros'])}")

        print("\n3. FOCUS PATRIMONIALE")
        print("-" * 80)
        print(f"  Attivo Immobilizzato:        {format_currency(latest['attivo_immobilizzato'])}")
        print(f"  Rimanenze:                   {format_currency(latest['rimanenze'])}")
        print(f"  Crediti verso Clienti:       {format_currency(latest['crediti_verso_clienti'])}")
        print(f"  Debiti verso Fornitori:      {format_currency(latest['debiti_verso_fornitori'])}")

        print("\n4. SOSTENIBILITÀ DEL DEBITO")
        print("-" * 80)
        print(f"  PFN:                         {format_currency(latest['pfn'])}")
        print(f"  PFN / EBITDA:                {format_ratio(latest['pfn_ebitda_ratio'])}")
        print(f"  Costo del Debito:            {format_percentage(latest['costo_del_debito'])}")
        print(f"  Oneri Fin / MOL:             {format_percentage(latest['oneri_finanziari_mol'])}")

        print("\n5. STRUTTURA DEL CAPITALE")
        print("-" * 80)
        print(f"  Patrimonio Netto:            {format_currency(latest['patrimonio_netto'])}")
        print(f"  Totale Attivo:               {format_currency(latest['totale_attivo'])}")
        print(f"  PN / Attivo:                 {format_percentage(latest['patrimonio_netto_attivo'])}")
        print(f"  Passivo Corrente:            {format_currency(latest['passivo_corrente'])}")
        print(f"  Totale Passivo:              {format_currency(latest['totale_passivo'])}")
        print(f"  PC / Totale Passivo:         {format_percentage(latest['passivo_corrente_totale_passivo'])}")

        print("\n6. CASH FLOW E COPERTURA")
        print("-" * 80)
        print(f"  Cash Flow Operativo:         {format_currency(latest['cash_flow'])}")
        print(f"  FCCR:                        {format_ratio(latest['fccr'])}")

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

        # Extract comprehensive data
        print("Extracting comprehensive anbil data...\n")
        anbil_data = extract_comprehensive_metrics(report_json)

        # Print summary
        print_comprehensive_summary(anbil_data)

        # Save to file
        output_file = 'anbil_extracted_data_comprehensive.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(anbil_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Comprehensive data saved to: {output_file}")

    except FileNotFoundError:
        print(f"❌ Error: Test file '{test_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
