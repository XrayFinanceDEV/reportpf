#!/usr/bin/env python3
"""
extract_reference_values.py
Helper tool to read PDFs and extract key reference values for test data
"""

import anthropic
import os
import json
from pathlib import Path


def read_pdf_for_reference(pdf_path: str) -> dict:
    """
    Read PDF and extract key reference values using Claude vision

    This is used to build the reference dataset for testing
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    # Read PDF
    with open(pdf_path, 'rb') as f:
        pdf_data = f.read()

    import base64
    pdf_b64 = base64.standard_b64encode(pdf_data).decode('utf-8')

    print(f"\n{'='*80}")
    print(f"Reading PDF: {pdf_path}")
    print(f"{'='*80}\n")

    # Ask Claude to extract key reference values
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4000,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_b64
                        }
                    },
                    {
                        "type": "text",
                        "text": """This is an Italian tax declaration (Redditi) PDF. Extract these KEY reference values for testing:

**IDENTIFICATIVI (from page 1):**
- Codice Fiscale (top section)
- Partita IVA
- Ragione Sociale (company name)
- Anno (year) - from "PERIODO D'IMPOSTA 20XX"

**RICAVI (Quadro RE):**
- F01: Ricavi dichiarati
- F02+F03+F05: Altri componenti positivi (sum if multiple)

**COSTI (Quadro RE):**
- Esistenze iniziali
- Rimanenze finali
- Costo materie prime
- Costo servizi
- Godimento beni di terzi
- Costo personale
- Ammortamenti
- Oneri finanziari

**RISULTATI (Quadro RE):**
- Valore aggiunto
- MOL (Margine Operativo Lordo)
- Reddito operativo
- Reddito d'impresa (final result)

**PERSONALE:**
- Numero addetti equivalenti (giornate lavorate / 312)

**ISA:**
- Punteggio ISA (score 0-10)
- Modello applicato (es: "DM04U", "CD09U")

**QUADRO RS (Balance Sheet - from pages 9-12):**
- Totale Attivo
- Patrimonio Netto
- TFR (Trattamento Fine Rapporto)
- Debiti fornitori

Return the data in JSON format like this:
{
  "identificativi": {
    "codice_fiscale": "...",
    "partita_iva": "...",
    "ragione_sociale": "...",
    "anno": 2024
  },
  "ricavi": {
    "ricavi_dichiarati": 123456,
    "altri_componenti_positivi": 7890
  },
  ...
}

IMPORTANT:
- Return ONLY numeric values (no commas, no currency symbols)
- Use null if a field is not found
- Be precise with numbers from the PDF"""
                    }
                ]
            }
        ]
    )

    # Extract JSON from response
    response_text = message.content[0].text

    # Try to find JSON in the response
    import re
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)

    if json_match:
        try:
            data = json.loads(json_match.group())
            return data
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Response: {response_text}")
            return None
    else:
        print(f"No JSON found in response:")
        print(response_text)
        return None


def main():
    """Extract reference values from all PDFs"""

    pdfs = [
        ("mazzola_2024", "SOCIETA' DI PERSONE ORDINARIA.pdf"),
        ("mazzola_2023", "BAR MAZZOLA 2023.pdf"),
        ("abs_2024", "USP ABS SNC ORDINARIA REDDITI 2024.pdf"),
        ("abs_2023", "USP ABS SNC ORDINARIA REDDITI 2023.pdf"),
        ("farmacia_2024", "USP REDDITI FARMACIA SNC ORDINARIA 2024.pdf"),
        ("farmacia_2023", "USP REDDITI FARMACIA SNC ORDINARIA 2023.pdf"),
        ("tessitura_2024", "USP UNICO REDDITI TESSITURA 2024.pdf"),
        ("tessitura_2023", "USP UNICO REDDITI TESSITURA 2023.pdf"),
    ]

    # Load existing reference data
    with open('test_reference_data.json', 'r') as f:
        reference_data = json.load(f)

    results = {}

    for test_id, pdf_file in pdfs:
        if not Path(pdf_file).exists():
            print(f"⚠️  PDF not found: {pdf_file}")
            continue

        print(f"\nProcessing: {test_id}")
        extracted_values = read_pdf_for_reference(pdf_file)

        if extracted_values:
            results[test_id] = extracted_values

            # Update reference data
            if test_id in reference_data['test_cases']:
                reference_data['test_cases'][test_id]['expected_values'] = extracted_values
                print(f"✅ Updated reference data for {test_id}")
            else:
                print(f"⚠️  Test case {test_id} not found in reference data")

        print()

    # Save updated reference data
    with open('test_reference_data_updated.json', 'w') as f:
        json.dump(reference_data, f, indent=2)

    print(f"\n{'='*80}")
    print(f"Reference data extraction complete!")
    print(f"Updated data saved to: test_reference_data_updated.json")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
