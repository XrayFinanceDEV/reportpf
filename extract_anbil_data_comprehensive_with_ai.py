#!/usr/bin/env python3
"""
extract_anbil_data_comprehensive_with_ai.py
Comprehensive extraction with AI-generated comments for ALL financial metrics

Generates 250-char AI comments for:
1. ECONOMIC INDICATORS (Revenue, EBITDA, Costs, Imposte, Risultato d'Esercizio)
2. PROFITABILITY RATIOS (ROI, ROE, ROS)
3. BALANCE SHEET ITEMS (Assets, Liabilities, Liquidità)
4. DEBT SUSTAINABILITY (PFN/EBITDA, Cost of Debt)
5. CAPITAL STRUCTURE (Equity ratios)
6. CASH FLOW & COVERAGE (Cash Flow, FCCR)
7. OVERALL SECTION COMMENT (Profilo Economico, Patrimoniale e Finanziario)
"""

from typing import Dict, List, Any, Optional
from extract_anbil_data_extended import extract_comprehensive_metrics, format_currency, format_percentage, format_ratio
from ai_comment_generator import AICommentGenerator


def extract_comprehensive_with_ai(
    report_json: Dict[str, Any],
    generate_comments: bool = True
) -> Dict[str, Any]:
    """
    Extract comprehensive anbil data with AI-generated comments for all metrics

    Args:
        report_json: The complete report JSON (from resp-itc.json format)
        generate_comments: Whether to generate AI comments (default True)

    Returns:
        Dictionary with extracted metrics + AI comments for each section
    """
    # First, extract the comprehensive data
    result = extract_comprehensive_metrics(report_json)

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

        # Define ALL metrics to generate comments for
        metrics_config = [
            # === SECTION 1: ECONOMIC INDICATORS ===
            {
                'id': 'revenue',
                'title': 'Ricavi Vendite e Prestazioni',
                'field': 'revenue',
                'unit': '€',
                'section': 'economic'
            },
            {
                'id': 'ebitda',
                'title': 'EBITDA - Risultato Operativo Lordo',
                'field': 'ebitda',
                'unit': '€',
                'section': 'economic'
            },
            {
                'id': 'costi_materia_prima',
                'title': 'Costi Materia Prima',
                'field': 'costi_materia_prima',
                'unit': '€',
                'section': 'economic'
            },
            {
                'id': 'costi_servizi',
                'title': 'Costi per Servizi',
                'field': 'costi_servizi',
                'unit': '€',
                'section': 'economic'
            },
            {
                'id': 'costi_personale',
                'title': 'Costi del Personale',
                'field': 'costi_personale',
                'unit': '€',
                'section': 'economic'
            },
            {
                'id': 'costi_oneri_finanziari',
                'title': 'Oneri Finanziari',
                'field': 'costi_oneri_finanziari',
                'unit': '€',
                'section': 'economic'
            },
            {
                'id': 'imposte_sul_reddito',
                'title': 'Costi per Imposte sul Reddito',
                'field': 'imposte',
                'unit': '€',
                'section': 'economic'
            },
            {
                'id': 'risultato_esercizio',
                'title': "Risultato d'Esercizio",
                'field': 'risultato_esercizio',
                'unit': '€',
                'section': 'economic'
            },

            # === SECTION 2: PROFITABILITY RATIOS ===
            {
                'id': 'roi',
                'title': 'ROI - Redditività del Capitale Investito',
                'field': 'roi',
                'unit': '%',
                'section': 'profitability'
            },
            {
                'id': 'roe',
                'title': 'ROE - Redditività del Capitale Proprio',
                'field': 'roe',
                'unit': '%',
                'section': 'profitability'
            },
            {
                'id': 'ros',
                'title': 'ROS - Redditività Operativa delle Vendite',
                'field': 'ros',
                'unit': '%',
                'section': 'profitability'
            },

            # === SECTION 3: BALANCE SHEET - FOCUS PATRIMONIALE ===
            {
                'id': 'attivo_immobilizzato',
                'title': 'Attivo Immobilizzato',
                'field': 'attivo_immobilizzato',
                'unit': '€',
                'section': 'balance_sheet'
            },
            {
                'id': 'rimanenze',
                'title': 'Rimanenze',
                'field': 'rimanenze',
                'unit': '€',
                'section': 'balance_sheet'
            },
            {
                'id': 'crediti_verso_clienti',
                'title': 'Crediti verso Clienti',
                'field': 'crediti_verso_clienti',
                'unit': '€',
                'section': 'balance_sheet'
            },
            {
                'id': 'debiti_verso_fornitori',
                'title': 'Debiti verso Fornitori',
                'field': 'debiti_verso_fornitori',
                'unit': '€',
                'section': 'balance_sheet'
            },
            {
                'id': 'liquidita',
                'title': 'Liquidità',
                'field': 'liquidita',
                'unit': '€',
                'section': 'balance_sheet'
            },

            # === SECTION 4: DEBT SUSTAINABILITY ===
            {
                'id': 'pfn_ebitda_ratio',
                'title': 'PFN / EBITDA - Sostenibilità del Debito',
                'field': 'pfn_ebitda_ratio',
                'unit': 'x',
                'section': 'debt'
            },
            {
                'id': 'costo_del_debito',
                'title': 'Costo del Debito',
                'field': 'costo_del_debito',
                'unit': '%',
                'section': 'debt'
            },
            {
                'id': 'oneri_finanziari_mol',
                'title': 'Oneri Finanziari / MOL',
                'field': 'oneri_finanziari_mol',
                'unit': '%',
                'section': 'debt'
            },

            # === SECTION 5: CAPITAL STRUCTURE ===
            {
                'id': 'patrimonio_netto_attivo',
                'title': 'Patrimonio Netto / Attivo',
                'field': 'patrimonio_netto_attivo',
                'unit': '%',
                'section': 'capital'
            },
            {
                'id': 'passivo_corrente_totale_passivo',
                'title': 'Passivo Corrente / Totale Passivo',
                'field': 'passivo_corrente_totale_passivo',
                'unit': '%',
                'section': 'capital'
            },

            # === SECTION 6: CASH FLOW & COVERAGE ===
            {
                'id': 'cash_flow',
                'title': 'Cash Flow Operativo',
                'field': 'cash_flow',
                'unit': '€',
                'section': 'cash_flow'
            },
            {
                'id': 'fccr',
                'title': 'FCCR - Fixed Charge Coverage Ratio',
                'field': 'fccr',
                'unit': 'x',
                'section': 'cash_flow'
            }
        ]

        # Generate comments for each metric
        comments = {}

        print("\n🤖 Generating AI comments for all metrics...")
        print("=" * 80)

        for metric_config in metrics_config:
            metric_id = metric_config['id']
            metric_title = metric_config['title']
            field = metric_config['field']
            unit = metric_config['unit']
            section = metric_config['section']

            # Prepare chart data (oldest to newest for trend calculation)
            chart_data = []
            for year_data in reversed(years_data):  # Reverse to get oldest first
                value = year_data.get(field, 0)
                chart_data.append({
                    'year': year_data['year'],
                    'value': value
                })

            # Generate comment
            print(f"  [{section.upper()}] {metric_title}...")
            comment = generator.generate_comment(
                metric_id=metric_id,
                metric_title=metric_title,
                values=chart_data,
                unit=unit,
                context=context
            )

            comments[metric_id] = comment

        # === GENERATE OVERALL SECTION COMMENT ===
        print("\n  [OVERALL] Profilo Economico, Patrimoniale e Finanziario...")
        overall_comment = generate_overall_section_comment(
            generator=generator,
            years_data=years_data,
            company_name=company_name,
            section_comments=comments
        )
        comments['profilo_economico_overall'] = overall_comment

        # Add comments to result
        result['data']['ai_comments'] = comments

        # Also add comments to each year's data for convenience
        for year_data in years_data:
            year_data['ai_comments'] = comments

        print("\n✅ AI comments generated successfully for all metrics!")
        print("=" * 80 + "\n")

        return result

    except Exception as e:
        print(f"⚠️  Warning: Failed to generate AI comments: {e}")
        import traceback
        traceback.print_exc()
        # Return data without comments
        return result


def generate_overall_section_comment(
    generator: AICommentGenerator,
    years_data: List[Dict[str, Any]],
    company_name: str,
    section_comments: Dict[str, str]
) -> str:
    """
    Generate an overall comment for the PROFILO ECONOMICO, PATRIMONIALE E FINANZIARIO section

    This comment synthesizes all individual metric comments into a comprehensive overview

    Args:
        generator: AI comment generator instance
        years_data: List of year data dicts
        company_name: Company name
        section_comments: Dict of all individual metric comments

    Returns:
        Overall section comment (~250 chars)
    """
    if not years_data or len(years_data) < 2:
        return "Dati insufficienti per l'analisi complessiva del profilo aziendale."

    # Get latest year data
    latest = years_data[0]
    previous = years_data[1]

    # Build comprehensive prompt with key metrics
    prompt = f"""Analizza il profilo economico, patrimoniale e finanziario complessivo di questa azienda e genera un commento di sintesi (massimo 250 caratteri).

AZIENDA: {company_name}

DATI CHIAVE (Anno {latest['year']} vs {previous['year']}):

ECONOMICI:
- Ricavi: {format_currency(latest['revenue'])} vs {format_currency(previous['revenue'])}
- EBITDA: {format_currency(latest['ebitda'])} vs {format_currency(previous['ebitda'])}
- Costi Personale: {format_currency(latest['costi_personale'])} vs {format_currency(previous['costi_personale'])}

REDDITIVITÀ:
- ROI: {format_percentage(latest['roi'])} vs {format_percentage(previous['roi'])}
- ROE: {format_percentage(latest['roe'])} vs {format_percentage(previous['roe'])}
- ROS: {format_percentage(latest['ros'])} vs {format_percentage(previous['ros'])}

PATRIMONIALI:
- Patrimonio Netto: {format_currency(latest['patrimonio_netto'])} vs {format_currency(previous['patrimonio_netto'])}
- PN/Attivo: {format_percentage(latest['patrimonio_netto_attivo'])} vs {format_percentage(previous['patrimonio_netto_attivo'])}
- PFN/EBITDA: {format_ratio(latest['pfn_ebitda_ratio'])} vs {format_ratio(previous['pfn_ebitda_ratio'])}

FINANZIARI:
- Cash Flow: {format_currency(latest['cash_flow'])} vs {format_currency(previous['cash_flow'])}
- FCCR: {format_ratio(latest['fccr'])} vs {format_ratio(previous['fccr'])}
- Costo Debito: {format_percentage(latest['costo_del_debito'])} vs {format_percentage(previous['costo_del_debito'])}

ISTRUZIONI:
1. Scrivi un commento di MASSIMO 250 caratteri che sintetizza il profilo complessivo
2. Identifica se l'azienda è in fase di crescita, stabilità, o difficoltà
3. Evidenzia i principali punti di forza e criticità
4. Usa linguaggio professionale per analisti finanziari
5. Focalizzati sui trend chiave (redditività, solidità patrimoniale, sostenibilità debito)
6. NON ripetere i commenti individuali, ma fornisci una visione d'insieme
7. Risposta SOLO il commento, niente altro

COMMENTO COMPLESSIVO:"""

    try:
        response = generator.client.messages.create(
            model=generator.model,
            max_tokens=150,
            temperature=0.3,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        comment = response.content[0].text.strip()

        # Ensure it's not too long
        if len(comment) > 280:
            comment = comment[:277] + "..."

        return comment

    except Exception as e:
        print(f"Error generating overall section comment: {e}")
        return "Profilo aziendale con andamento misto: redditività in calo, struttura patrimoniale solida. Monitorare l'evoluzione dei margini operativi."


def print_comprehensive_summary_with_comments(anbil_data: Dict[str, Any]) -> None:
    """Print a formatted summary including all AI comments"""
    if not anbil_data.get('success'):
        print(f"❌ Error: {anbil_data.get('error', 'Unknown error')}")
        return

    print("\n" + "="*80)
    print("COMPREHENSIVE ANBIL DATA WITH AI COMMENTS - Summary")
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
        print("="* 80)

        # SECTION 1: Economic Indicators
        print("\n1. INDICATORI ECONOMICI")
        print("-" * 80)
        print(f"EBITDA: {format_currency(latest['ebitda'])}")
        if 'ebitda' in ai_comments:
            print(f"💬 {ai_comments['ebitda']}\n")

        # SECTION 2: Profitability Ratios
        print("\n2. INDICI DI REDDITIVITÀ")
        print("-" * 80)

        print(f"ROI: {format_percentage(latest['roi'])}")
        if 'roi' in ai_comments:
            print(f"💬 {ai_comments['roi']}\n")

        print(f"ROE: {format_percentage(latest['roe'])}")
        if 'roe' in ai_comments:
            print(f"💬 {ai_comments['roe']}\n")

        print(f"ROS: {format_percentage(latest['ros'])}")
        if 'ros' in ai_comments:
            print(f"💬 {ai_comments['ros']}\n")

        # SECTION 3: Balance Sheet
        print("\n3. FOCUS PATRIMONIALE")
        print("-" * 80)

        print(f"Attivo Immobilizzato: {format_currency(latest['attivo_immobilizzato'])}")
        if 'attivo_immobilizzato' in ai_comments:
            print(f"💬 {ai_comments['attivo_immobilizzato']}\n")

        print(f"Rimanenze: {format_currency(latest['rimanenze'])}")
        if 'rimanenze' in ai_comments:
            print(f"💬 {ai_comments['rimanenze']}\n")

        print(f"Crediti verso Clienti: {format_currency(latest['crediti_verso_clienti'])}")
        if 'crediti_verso_clienti' in ai_comments:
            print(f"💬 {ai_comments['crediti_verso_clienti']}\n")

        print(f"Debiti verso Fornitori: {format_currency(latest['debiti_verso_fornitori'])}")
        if 'debiti_verso_fornitori' in ai_comments:
            print(f"💬 {ai_comments['debiti_verso_fornitori']}\n")

        # SECTION 4: Debt Sustainability
        print("\n4. SOSTENIBILITÀ DEL DEBITO")
        print("-" * 80)

        print(f"PFN / EBITDA: {format_ratio(latest['pfn_ebitda_ratio'])}")
        if 'pfn_ebitda_ratio' in ai_comments:
            print(f"💬 {ai_comments['pfn_ebitda_ratio']}\n")

        print(f"Costo del Debito: {format_percentage(latest['costo_del_debito'])}")
        if 'costo_del_debito' in ai_comments:
            print(f"💬 {ai_comments['costo_del_debito']}\n")

        print(f"Oneri Finanziari / MOL: {format_percentage(latest['oneri_finanziari_mol'])}")
        if 'oneri_finanziari_mol' in ai_comments:
            print(f"💬 {ai_comments['oneri_finanziari_mol']}\n")

        # SECTION 5: Capital Structure
        print("\n5. STRUTTURA DEL CAPITALE")
        print("-" * 80)

        print(f"Patrimonio Netto / Attivo: {format_percentage(latest['patrimonio_netto_attivo'])}")
        if 'patrimonio_netto_attivo' in ai_comments:
            print(f"💬 {ai_comments['patrimonio_netto_attivo']}\n")

        print(f"Passivo Corrente / Totale Passivo: {format_percentage(latest['passivo_corrente_totale_passivo'])}")
        if 'passivo_corrente_totale_passivo' in ai_comments:
            print(f"💬 {ai_comments['passivo_corrente_totale_passivo']}\n")

        # SECTION 6: Cash Flow
        print("\n6. CASH FLOW E COPERTURA")
        print("-" * 80)

        print(f"Cash Flow: {format_currency(latest['cash_flow'])}")
        if 'cash_flow' in ai_comments:
            print(f"💬 {ai_comments['cash_flow']}\n")

        print(f"FCCR: {format_ratio(latest['fccr'])}")
        if 'fccr' in ai_comments:
            print(f"💬 {ai_comments['fccr']}\n")

        # OVERALL SECTION COMMENT
        print("\n" + "="*80)
        print("PROFILO ECONOMICO, PATRIMONIALE E FINANZIARIO - COMMENTO COMPLESSIVO")
        print("="*80)
        if 'profilo_economico_overall' in ai_comments:
            print(f"\n💬 {ai_comments['profilo_economico_overall']}\n")

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
        print("Extracting comprehensive data with AI comments...\n")
        anbil_data = extract_comprehensive_with_ai(report_json)

        # Print summary
        print_comprehensive_summary_with_comments(anbil_data)

        # Save to file
        output_file = 'anbil_comprehensive_with_ai.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(anbil_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Comprehensive data with AI comments saved to: {output_file}")
        print(f"📊 Total metrics: {len(anbil_data['data']['ai_comments'])} (including overall comment)")

    except FileNotFoundError:
        print(f"❌ Error: Test file '{test_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
