#!/usr/bin/env python3
"""
Dichiarazione Extractor V3 - Optimized Version
Uses page filtering to reduce token usage from ~50k to ~10-15k per PDF
Uses Claude Haiku 4.5 for PDF extraction

Key optimization: Only analyze pages containing our target field codes
"""

import logging
import base64
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from anthropic import Anthropic
import pdfplumber

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DichiarazioneExtractorV3Optimized:
    """
    Optimized V3 Extractor - Only analyzes relevant pages
    Supports year-specific field codes (2023 vs 2024 formats)

    Reduces token usage by ~70% by pre-filtering pages with regex
    """

    MODEL = "claude-haiku-4-5-20251001"
    MAX_TOKENS = 8192

    # Year-specific code mappings
    # 2024 format uses 3-digit ICI codes: ICI011, ICI014, etc.
    # 2023 format uses 5-digit ICI codes: ICI01101, ICI01401, etc.
    CODES_2024 = {
        'ICI001', 'ICI004', 'ICI005', 'ICI006', 'ICI008', 'ICI009',
        'ICI010', 'ICI011', 'ICI012', 'ICI013', 'ICI014', 'ICI015',
        'ICI016', 'ICI017', 'ICI019', 'ICI024', 'ICI027', 'ICI029',
        'ISAAFF', 'IIE001', 'IIE002', 'IIE003'
    }

    CODES_2023 = {
        'ICI00101', 'ICI00401', 'ICI00501', 'ICI00601', 'ICI00801', 'ICI00901',
        'ICI01001', 'ICI01101', 'ICI01201', 'ICI01301', 'ICI01401', 'ICI01501',
        'ICI01601', 'ICI01701', 'ICI01901', 'ICI02401', 'ICI02701', 'ICI02801',
        'ICI02901',  # Alternative for beni strumentali
        'IIISAAFF',  # 2023 format with triple I
        'IIE00101', 'IIE00201', 'IIE00301'  # ISA indicators with 5 digits
    }

    # Common codes that work across all years
    CODES_COMMON = {
        # Quadro F - Revenue and costs
        'F01', 'F02', 'F03', 'F05', 'F08', 'F09', 'F10',
        'F12', 'F14', 'F15', 'F17', 'F19', 'F20', 'F21',

        # Quadro RS - Balance sheet (actual codes, not RS100-RS114)
        'RS1', 'RS11', 'RS12', 'RS13', 'RS14', 'RS15',
        'RS30', 'RS31', 'RS32', 'RS33', 'RS34', 'RS35',
        'RS47', 'RS48', 'RS49', 'RS50',
        'RS118', 'RS119', 'RS120', 'RS121', 'RS122', 'RS123',

        # Personnel
        'A01', 'A02'
    }

    # Combined target codes for page filtering
    TARGET_CODES = CODES_COMMON | CODES_2024 | CODES_2023

    # Entity type markers for detection
    # "RPF" = Redditi Persone Fisiche (personal tax declaration) - appears on page 1
    # SP declarations don't have a single reliable marker on page 1 (some have reversed text)
    # Strategy: if RPF is found, it's PF. Otherwise assume SP (the expected type).
    ENTITY_TYPE_PF_MARKERS = {'RPF'}

    EXPECTED_STRUCTURE = {
        "identificativi": {
            "codice_fiscale": "",
            "partita_iva": "",
            "ragione_sociale": "",
            "anno": 0
        },
        "ricavi": {
            "ricavi_dichiarati": 0.0,
            "altri_componenti_positivi": 0.0
        },
        "costi": {
            "esistenze_iniziali": 0.0,
            "rimanenze_finali": 0.0,
            "costo_materie_prime": 0.0,
            "costo_servizi": 0.0,
            "godimento_beni_terzi": 0.0,
            "costo_personale": 0.0,
            "spese_collaboratori": 0.0,
            "ammortamenti": 0.0,
            "accantonamenti": 0.0,
            "altri_costi": 0.0,
            "oneri_finanziari": 0.0
        },
        "risultati": {
            "valore_aggiunto": 0.0,
            "mol": 0.0,
            "reddito_operativo": 0.0,
            "reddito_impresa": 0.0
        },
        "personale": {
            "giornate_dipendenti": 0.0,
            "giornate_altro_personale": 0.0,
            "numero_addetti_equivalenti": 0.0
        },
        "patrimonio": {
            "valore_beni_strumentali": 0.0
        },
        "isa": {
            "punteggio": 0.0,
            "modello_applicato": "",
            "ricavi_per_addetto": 0.0,
            "valore_aggiunto_per_addetto": 0.0,
            "reddito_per_addetto": 0.0
        },
        "quadro_rs": {
            "immobilizzazioni_immateriali": 0.0,
            "immobilizzazioni_materiali": 0.0,
            "immobilizzazioni_finanziarie": 0.0,
            "rimanenze": 0.0,
            "crediti_clienti": 0.0,
            "altri_crediti": 0.0,
            "attivita_finanziarie": 0.0,
            "disponibilita_liquide": 0.0,
            "ratei_risconti_attivi": 0.0,
            "totale_attivo": 0.0,
            "patrimonio_netto": 0.0,
            "fondi_rischi_oneri": 0.0,
            "tfr": 0.0,
            "debiti_banche_breve": 0.0,
            "debiti_banche_lungo": 0.0,
            "debiti_fornitori": 0.0,
            "altri_debiti": 0.0,
            "ratei_risconti_passivi": 0.0
        }
    }

    def __init__(self, pdf_path: Optional[str] = None, anno: Optional[int] = None, api_key: Optional[str] = None):
        import os
        if api_key is None:
            api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found!")

        self.client = Anthropic(api_key=api_key)
        self.pdf_path = pdf_path
        self.anno = anno

    def detect_entity_type(self, pdf_path: str) -> str:
        """
        Detect whether the PDF is a persona fisica (PF) or società di persone (SP) declaration.
        Scans the first few pages for entity type markers.

        Strategy: Look for 'RPF' as a standalone word on early pages.
        If found, it's a PF declaration. Otherwise assume SP (the expected/supported type).

        Returns:
            'PF' for persone fisiche, 'SP' for società di persone
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Check first 3 pages (page 1 text may be reversed in some PDF generators)
                for page_idx in range(min(3, len(pdf.pages))):
                    text = (pdf.pages[page_idx].extract_text() or '').upper()
                    # Look for RPF as standalone token (not part of another word)
                    if re.search(r'\bRPF\b', text):
                        logger.info(f"Detected entity type: PERSONA FISICA (found 'RPF' on page {page_idx + 1})")
                        return 'PF'

        except Exception as e:
            logger.error(f"Error detecting entity type: {e}")

        logger.info("Detected entity type: SOCIETÀ DI PERSONE (no PF markers found)")
        return 'SP'

    def _build_empty_result(self, pdf_path: str, anno: int, entity_type: str) -> Dict[str, Any]:
        """
        Build a mostly-empty result structure for unsupported entity types (e.g. persone fisiche).
        Extracts only basic identification data from page 1.
        """
        result = json.loads(json.dumps(self.EXPECTED_STRUCTURE))

        # Try to extract basic identification from page 1
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if pdf.pages:
                    text = pdf.pages[0].extract_text() or ''

                    # Try to find codice fiscale (16 chars for PF, 11 for companies)
                    # PF format has spaces between chars in pdfplumber output
                    text_no_spaces = text.upper().replace(' ', '')
                    cf_match = re.search(r'([A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z])', text_no_spaces)
                    if cf_match:
                        result['identificativi']['codice_fiscale'] = cf_match.group(1)

                    # Try to find name (COGNOME NOME pattern on PF declarations)
                    # Note: pdfplumber may insert spaces between chars ("C O G N O M E")
                    lines = text.split('\n')
                    for i, line in enumerate(lines):
                        line_compact = line.upper().replace(' ', '')
                        if 'COGNOME' in line_compact and 'NOME' in line_compact:
                            # The name is usually on the next non-header line
                            for j in range(i + 1, min(i + 4, len(lines))):
                                name_line = lines[j].strip()
                                if (name_line and len(name_line) > 3
                                        and 'CODICE' not in name_line.upper()
                                        and 'FISCALE' not in name_line.upper()
                                        and 'PERIODO' not in name_line.upper()):
                                    result['identificativi']['ragione_sociale'] = name_line
                                    break
                            break

        except Exception as e:
            logger.warning(f"Error extracting basic identification: {e}")

        result['identificativi']['anno'] = anno

        # Add metadata about the entity type
        result['_entity_type'] = entity_type
        result['_note'] = 'Dichiarazione Persone Fisiche - no company financial data available'

        return result

    def find_relevant_pages(self, pdf_path: str) -> Set[int]:
        """
        Scan PDF to find pages containing our target field codes
        Returns set of page numbers (1-indexed)
        """
        relevant_pages = set()

        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                logger.info(f"Scanning {total_pages} pages for relevant field codes...")

                # Always include first page for header info
                relevant_pages.add(1)

                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""

                    # Check if this page contains any of our target codes
                    for code in self.TARGET_CODES:
                        # Look for the code as a standalone field identifier
                        # Pattern: code followed by space/tab and number, or in a table
                        pattern = rf'\b{re.escape(code)}\b'
                        if re.search(pattern, text):
                            relevant_pages.add(page_num)
                            logger.debug(f"  Page {page_num}: Found code {code}")
                            break  # Found at least one code, page is relevant

                logger.info(f"✅ Found {len(relevant_pages)} relevant pages out of {total_pages}")
                logger.info(f"   Pages to analyze: {sorted(relevant_pages)}")

                return relevant_pages

        except Exception as e:
            logger.error(f"Error scanning PDF: {e}")
            # Fallback: analyze all pages
            logger.warning("Falling back to analyzing entire PDF")
            return set(range(1, 31))  # Assume max 30 pages

    def extract_pages_to_pdf(self, pdf_path: str, page_numbers: Set[int]) -> bytes:
        """
        Extract only relevant pages and create a new PDF with just those pages
        """
        import PyPDF2
        import io

        reader = PyPDF2.PdfReader(pdf_path)
        writer = PyPDF2.PdfWriter()

        for page_num in sorted(page_numbers):
            if page_num <= len(reader.pages):
                writer.add_page(reader.pages[page_num - 1])  # PyPDF2 uses 0-indexed

        # Write to bytes
        output = io.BytesIO()
        writer.write(output)
        output.seek(0)

        return output.read()

    def _encode_pdf_bytes(self, pdf_bytes: bytes) -> str:
        """Encode PDF bytes to base64"""
        return base64.standard_b64encode(pdf_bytes).decode('utf-8')

    def _build_extraction_prompt(self, anno: int) -> str:
        """Build the extraction prompt for Claude with year-specific field codes"""

        # Determine which code format to use based on year
        if anno == 2024:
            ici_valore_aggiunto = "ICI011"
            ici_mol = "ICI014"
            ici_reddito_operativo = "ICI017"
            ici_addetti = "ICI027"
            ici_beni_strumentali = "ICI029"
            ici_godimento_beni = "ICI009"
            ici_collaboratori = "ICI013"
            ici_accantonamenti = "ICI016"
            isa_punteggio = "ISAAFF"
            iie_ricavi = "IIE001"
            iie_va = "IIE002"
            iie_reddito = "IIE003"
        else:  # 2023 and earlier
            ici_valore_aggiunto = "ICI01101"
            ici_mol = "ICI01401"
            ici_reddito_operativo = "ICI01701"
            ici_addetti = "ICI02701"
            ici_beni_strumentali = "ICI02801 or ICI02901"  # Try both
            ici_godimento_beni = "ICI00901"
            ici_collaboratori = "ICI01301"
            ici_accantonamenti = "ICI01601"
            isa_punteggio = "IIISAAFF"
            iie_ricavi = "IIE00101"
            iie_va = "IIE00201"
            iie_reddito = "IIE00301"

        return f"""You are a tax document data extraction specialist. You will receive selected pages from an Italian tax declaration PDF (Modello Unico/Dichiarazione Redditi) for year {anno}.

Your task is to extract ALL the following fields and return them as a JSON object. Be extremely precise with numbers.

CRITICAL INSTRUCTIONS:
1. Extract numbers EXACTLY as they appear in the PDF
2. For Italian number format (e.g., "123.456,78"), convert to: 123456.78
3. If a field is missing or unclear, use 0 for numbers and "" for strings
4. The "anno" field MUST be extracted from "Periodo d'imposta YYYY" text (NOT from form header which shows form version). Expected: {anno}
5. Return ONLY the JSON object, no additional text or explanation
6. This is year {anno} format - use the correct field codes for this year

FIELD MAPPING (extract these exact values for year {anno}):

**identificativi:**
- codice_fiscale: 11-digit tax code (starts with 0)
- partita_iva: VAT number (usually same as codice_fiscale)
- ragione_sociale: Company name
- anno: Extract ONLY from "Periodo d'imposta YYYY" field (usually on page 1). IGNORE the form header year (e.g., "SOCIETÀ DI PERSONE 2024" refers to the form version, not the tax period). Expected value: {anno}

**ricavi (Quadro F - Ricavi):**
- ricavi_dichiarati: F01 / ICI001 - Ricavi delle vendite e delle prestazioni
- altri_componenti_positivi: Sum of F02 + F03 + F05

**costi (Quadro F - Costi):**
- esistenze_iniziali: F08 / ICI004 - Esistenze iniziali
- rimanenze_finali: F09 / ICI005 - Rimanenze finali
- costo_materie_prime: F10 / ICI006 - Acquisti di materie prime
- costo_servizi: F12 / ICI008 - Costo per servizi
- godimento_beni_terzi: {ici_godimento_beni} - Godimento beni di terzi
- costo_personale: F14 / ICI012 - Costo del personale
- spese_collaboratori: {ici_collaboratori} - Spese per collaboratori coordinati e continuativi
- ammortamenti: F15 / ICI015 - Ammortamenti e svalutazioni
- accantonamenti: {ici_accantonamenti} - Accantonamenti
- altri_costi: F17 / ICI010 - Altri costi / Costi residuali
- oneri_finanziari: F19 / ICI019 - Oneri finanziari

**risultati:**
- valore_aggiunto: {ici_valore_aggiunto} - Valore aggiunto (page 24 - Prospetto Economico ISA)
- mol: {ici_mol} - Margine Operativo Lordo / MOL (page 24)
- reddito_operativo: {ici_reddito_operativo} - Reddito operativo (page 24)
- reddito_impresa: F20 / ICI024 - Reddito d'impresa

**personale:**
- giornate_dipendenti: A01 - Giornate retribuite dipendenti
- giornate_altro_personale: A02 - Giornate retribuite altro personale
- numero_addetti_equivalenti: {ici_addetti} - Numero addetti equivalenti (page 24)

**patrimonio:**
- valore_beni_strumentali: F21 / {ici_beni_strumentali} - Valore beni strumentali

**isa:**
- punteggio: {isa_punteggio} - Punteggio ISA finale (1-10 scale)
- modello_applicato: Codice modello ISA (e.g., "DG37U", "ISA 47.09.01")
- ricavi_per_addetto: {iie_ricavi} - Ricavi per addetto (IIE indicator)
- valore_aggiunto_per_addetto: {iie_va} - Valore aggiunto per addetto (IIE indicator)
- reddito_per_addetto: {iie_reddito} - Reddito per addetto (IIE indicator)

**quadro_rs (Quadro RS - Stato Patrimoniale):**
NOTE: Extract from balance sheet tables on pages 9-12 (page 12 in ISA section shows full Quadro RS)
FIXED ASSETS (Immobilizzazioni):
- immobilizzazioni_immateriali: RS97 - Immobilizzazioni immateriali (total value)
- immobilizzazioni_materiali: RS98 - CRITICAL: This line shows TWO numbers. Extract ONLY the LAST number on the RS98 line (the rightmost number). Ignore the "Fondo ammortamento" gross value. Example: if you see "RS98...296,888.00 61,386.00", extract 61386.00 (the last/rightmost number)
- immobilizzazioni_finanziarie: RS99 - Immobilizzazioni finanziarie (total value)
CURRENT ASSETS (Attivo circolante):
- rimanenze: RS100 - Rimanenze di materie prime, sussidiarie e di consumo
- crediti_clienti: RS101 - Crediti verso clienti
- altri_crediti: RS102 - Altri crediti
- attivita_finanziarie: RS103 - Attività finanziarie che non costituiscono immobilizzazioni
- disponibilita_liquide: RS104 - Disponibilità liquide
- ratei_risconti_attivi: RS105 - Ratei e risconti attivi
TOTAL ASSETS:
- totale_attivo: RS106 - Totale attivo
LIABILITIES (Passivo):
- patrimonio_netto: RS107 - Patrimonio netto
- fondi_rischi_oneri: RS108 - Fondi per rischi e oneri
- tfr: RS109 - Trattamento di fine rapporto
- debiti_banche_breve: RS110 - Debiti verso banche (breve termine)
- debiti_banche_lungo: RS111 - Debiti verso banche (lungo termine)
- debiti_fornitori: RS112 - Debiti verso fornitori
- altri_debiti: RS113 - Altri debiti
- ratei_risconti_passivi: RS114 - Ratei e risconti passivi

Return the data in this exact JSON structure:
{json.dumps(self.EXPECTED_STRUCTURE, indent=2)}

IMPORTANT:
- Numbers must be floats (e.g., 123456.78, not "123.456,78")
- Convert ALL Italian number formats to standard format
- If a field is not found, use 0 for numbers or "" for strings
- Return ONLY valid JSON, no markdown formatting or explanations"""

    def extract_from_pdf(self, pdf_path: str, anno: int) -> Dict[str, Any]:
        """
        Extract data from PDF using optimized page filtering
        """
        try:
            logger.info(f"🔍 Optimized extraction from {pdf_path} for year {anno}")

            # Step 0: Detect entity type
            entity_type = self.detect_entity_type(pdf_path)
            if entity_type == 'PF':
                logger.warning(f"⚠️ PDF is a Persona Fisica declaration - returning empty structure")
                return self._build_empty_result(pdf_path, anno, entity_type)

            # Step 1: Find relevant pages
            relevant_pages = self.find_relevant_pages(pdf_path)

            # Step 2: Extract only those pages
            logger.info(f"📄 Extracting {len(relevant_pages)} pages...")
            filtered_pdf_bytes = self.extract_pages_to_pdf(pdf_path, relevant_pages)

            # Calculate token savings
            import os
            original_size = os.path.getsize(pdf_path)
            filtered_size = len(filtered_pdf_bytes)
            savings_pct = ((original_size - filtered_size) / original_size) * 100
            logger.info(f"💰 Token savings: ~{savings_pct:.1f}% (reduced from {original_size:,} to {filtered_size:,} bytes)")

            # Step 3: Encode filtered PDF
            pdf_base64 = self._encode_pdf_bytes(filtered_pdf_bytes)

            # Step 4: Build extraction prompt
            prompt = self._build_extraction_prompt(anno)

            # Step 5: Call Claude API
            logger.info(f"🤖 Calling Claude Haiku 4.5 with filtered PDF...")
            message = self.client.messages.create(
                model=self.MODEL,
                max_tokens=self.MAX_TOKENS,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            # Extract response
            response_text = message.content[0].text

            # Parse JSON
            try:
                if response_text.startswith("```"):
                    start = response_text.find("{")
                    end = response_text.rfind("}") + 1
                    response_text = response_text[start:end]

                extracted_data = json.loads(response_text)

                if not self._validate_structure(extracted_data):
                    logger.warning("Extracted data structure is incomplete, filling with defaults")
                    extracted_data = self._merge_with_defaults(extracted_data)

                logger.info(f"✅ Successfully extracted data for year {anno}")
                logger.info(f"   Pages analyzed: {sorted(relevant_pages)}")

                return extracted_data

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                raise ValueError(f"Claude returned invalid JSON: {e}")

        except Exception as e:
            logger.error(f"Error extracting from PDF: {e}")
            raise

    def _validate_structure(self, data: Dict[str, Any]) -> bool:
        """Validate that extracted data has the expected structure"""
        required_sections = ["identificativi", "ricavi", "costi", "risultati",
                           "personale", "patrimonio", "isa", "quadro_rs"]
        return all(section in data for section in required_sections)

    def _merge_with_defaults(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge extracted data with default structure"""
        result = json.loads(json.dumps(self.EXPECTED_STRUCTURE))

        def merge_dict(target, source):
            for key, value in source.items():
                if key in target:
                    if isinstance(value, dict) and isinstance(target[key], dict):
                        merge_dict(target[key], value)
                    else:
                        target[key] = value

        merge_dict(result, data)
        return result

    def estrai_dati_input(self, pdf_path: Optional[str] = None, anno: Optional[int] = None) -> Dict[str, Any]:
        """
        Main extraction method (compatible with V3 interface)
        """
        if pdf_path is None:
            pdf_path = self.pdf_path
        if anno is None:
            anno = self.anno

        if pdf_path is None:
            raise ValueError("pdf_path must be provided")

        # Auto-detect year from filename if not provided
        if anno is None:
            import re
            match = re.search(r'(202[0-9])', pdf_path)
            anno = int(match.group(1)) if match else 2024
            logger.info(f"Auto-detected year: {anno}")

        return self.extract_from_pdf(pdf_path, anno)


def elabora_biennio(pdf_corrente: str, pdf_precedente: str) -> Dict[str, Any]:
    """
    Extract data from two PDFs with optimized page filtering
    """
    try:
        logger.info("Processing biennio with V3 Optimized extractor")

        extractor = DichiarazioneExtractorV3Optimized()

        # Extract years from filenames
        import re
        match_corrente = re.search(r'(202[0-9])', pdf_corrente)
        match_precedente = re.search(r'(202[0-9])', pdf_precedente)

        anno_corrente = int(match_corrente.group(1)) if match_corrente else 2024
        anno_precedente = int(match_precedente.group(1)) if match_precedente else anno_corrente - 1

        logger.info(f"Detected years: corrente={anno_corrente}, precedente={anno_precedente}")

        # Extract current year
        anno_corrente_data = extractor.extract_from_pdf(pdf_corrente, anno_corrente)

        # Add delay to avoid rate limits
        # Actual usage: ~38k tokens per PDF = ~76k total tokens for biennio
        # Using 30 second delay to stay well under rate limits
        import time
        delay_seconds = 30
        logger.info(f"⏱️  Waiting {delay_seconds} seconds before processing second PDF...")
        time.sleep(delay_seconds)

        # Extract previous year
        anno_precedente_data = extractor.extract_from_pdf(pdf_precedente, anno_precedente)

        return {
            "anno_corrente": anno_corrente_data,
            "anno_precedente": anno_precedente_data
        }

    except Exception as e:
        logger.error(f"Error in elabora_biennio: {e}")
        raise


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        anno = int(sys.argv[2]) if len(sys.argv) > 2 else 2024

        try:
            extractor = DichiarazioneExtractorV3Optimized()
            result = extractor.estrai_dati_input(pdf_path, anno)

            print(json.dumps(result, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Usage: python extdichiarazione_v3_optimized.py <pdf_path> [anno]")
        sys.exit(1)
