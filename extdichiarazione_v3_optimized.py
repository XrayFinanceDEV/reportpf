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
    # 2024 format uses 3-digit codes: ICI011, ICA013, etc.
    # 2023 format uses 5-digit codes: ICI01101, ICA01301, etc.
    CODES_2024 = {
        # ICI - Imprese (SP, Ditta Individuale)
        'ICI001', 'ICI004', 'ICI005', 'ICI006', 'ICI008', 'ICI009',
        'ICI010', 'ICI011', 'ICI012', 'ICI013', 'ICI014', 'ICI015',
        'ICI016', 'ICI017', 'ICI019', 'ICI024', 'ICI027', 'ICI029',
        # ICA - Liberi Professionisti (Quadro RE)
        'ICA001', 'ICA003', 'ICA004', 'ICA005', 'ICA006', 'ICA007',
        'ICA008', 'ICA012', 'ICA013', 'ICA014', 'ICA015', 'ICA016',
        'ICA017', 'ICA018', 'ICA020', 'ICA024', 'ICA027', 'ICA028',
        # ISA indicators
        'ISAAFF', 'IIE001', 'IIE002', 'IIE003'
    }

    CODES_2023 = {
        # ICI - Imprese (5-digit format)
        'ICI00101', 'ICI00401', 'ICI00501', 'ICI00601', 'ICI00801', 'ICI00901',
        'ICI01001', 'ICI01101', 'ICI01201', 'ICI01301', 'ICI01401', 'ICI01501',
        'ICI01601', 'ICI01701', 'ICI01901', 'ICI02401', 'ICI02701', 'ICI02801',
        'ICI02901',  # Alternative for beni strumentali
        # ICA - Liberi Professionisti (5-digit format)
        'ICA00101', 'ICA00301', 'ICA00401', 'ICA00501', 'ICA00601', 'ICA00701',
        'ICA00801', 'ICA01201', 'ICA01301', 'ICA01401', 'ICA01501', 'ICA01601',
        'ICA01701', 'ICA01801', 'ICA02001', 'ICA02401', 'ICA02701', 'ICA02801',
        # ISA indicators (2023 format)
        'IIISAAFF',  # 2023 format with triple I
        'IIE00101', 'IIE00201', 'IIE00301'  # ISA indicators with 5 digits
    }

    # Common codes that work across all years
    CODES_COMMON = {
        # Quadro F - Revenue and costs (SP, Ditta Individuale)
        'F01', 'F02', 'F03', 'F05', 'F08', 'F09', 'F10',
        'F12', 'F14', 'F15', 'F17', 'F19', 'F20', 'F21',

        # Quadro RE - Professional Income (Liberi Professionisti)
        'RE1', 'RE2', 'RE3', 'RE6', 'RE7', 'RE8', 'RE9',
        'RE11', 'RE12', 'RE13', 'RE14', 'RE19', 'RE20', 'RE23',

        # Quadro RS - Balance sheet (actual codes, not RS100-RS114)
        'RS1', 'RS11', 'RS12', 'RS13', 'RS14', 'RS15',
        'RS30', 'RS31', 'RS32', 'RS33', 'RS34', 'RS35',
        'RS47', 'RS48', 'RS49', 'RS50',
        'RS118', 'RS119', 'RS120', 'RS121', 'RS122', 'RS123',

        # Quadro RN - IRPEF (Persone Fisiche only)
        'RN26',

        # Quadro RV - Addizionali (Persone Fisiche only)
        'RV2', 'RV10',

        # Personnel
        'A01', 'A02'
    }

    # Combined target codes for page filtering
    TARGET_CODES = CODES_COMMON | CODES_2024 | CODES_2023

    # Keyword-based page detection (for PDFs without field codes)
    # These help find relevant pages even when ICI/ICA codes are absent
    PAGE_KEYWORDS = {
        'PROSPETTO ECONOMICO', 'VALORE AGGIUNTO', 'MARGINE OPERATIVO',
        'REDDITO OPERATIVO', 'PUNTEGGIO', 'AFFIDABILIT',
        'ELEMENTI CONTABILI', 'BENI STRUMENTALI',
        'QUADRO RS', 'QUADRO RF', 'QUADRO RG', 'QUADRO RE',
        'QUADRO RN', 'QUADRO RV',
        'IRPEF NETTA', 'ADDIZIONALE REGIONALE', 'ADDIZIONALE COMUNALE',
        'DATI DI BILANCIO', 'STATO PATRIMONIALE',
        'GIORNATE RETRIBUITE', 'PERSONALE ADDETTO',
    }

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
        },
        "imposte": {
            "irpef_netta": 0.0,
            "addizionale_regionale": 0.0,
            "addizionale_comunale": 0.0
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
        Detect the entity type from the PDF declaration.

        Returns:
            'SP'    - Società di Persone (standard extraction)
            'PF_RE' - Persona Fisica with Quadro RE (Libero Professionista)
            'PF_RG' - Persona Fisica with Quadro RG (Ditta Individuale semplificata)
            'PF'    - Persona Fisica without business income (not supported)
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                is_pf = False
                has_re = False
                has_rg = False

                for page_idx in range(min(len(pdf.pages), 25)):
                    text = (pdf.pages[page_idx].extract_text() or '').upper()

                    # Check first 3 pages for PF marker
                    if page_idx < 3 and re.search(r'\bRPF\b', text):
                        is_pf = True

                    # Check for Quadro RE (lavoro autonomo / professionista)
                    if 'QUADRO RE' in text and 'LAVORO AUTONOMO' in text:
                        has_re = True

                    # Check for Quadro RG (reddito d'impresa semplificata)
                    if 'QUADRO RG' in text and ('REDDITO' in text):
                        has_rg = True

                    # Check for ICA codes (confirms professionista ISA)
                    if re.search(r'\bICA\d{3}\b', text) or re.search(r'\bICA\d{5}\b', text):
                        has_re = True

                if is_pf:
                    if has_re:
                        logger.info("Detected entity type: PF_RE (Persona Fisica - Libero Professionista)")
                        return 'PF_RE'
                    elif has_rg:
                        logger.info("Detected entity type: PF_RG (Persona Fisica - Ditta Individuale)")
                        return 'PF_RG'
                    else:
                        logger.info("Detected entity type: PF (Persona Fisica - no business income)")
                        return 'PF'

        except Exception as e:
            logger.error(f"Error detecting entity type: {e}")

        logger.info("Detected entity type: SOCIETÀ DI PERSONE (no PF markers found)")
        return 'SP'

    @staticmethod
    def detect_accounting_type(extracted_data: Dict[str, Any]) -> str:
        """
        Detect whether this entity uses contabilità semplificata or ordinaria.

        Semplificata entities (Quadro RG) have NO balance sheet (stato patrimoniale):
        all quadro_rs fields are zero. Only ISA Prospetto Economico data is available.

        Returns:
            'semplificata' or 'ordinaria'
        """
        rs = extracted_data.get("quadro_rs", {})
        if not rs:
            return "semplificata"

        # Check if ALL balance sheet values are zero
        rs_values = [
            rs.get("immobilizzazioni_immateriali", 0),
            rs.get("immobilizzazioni_materiali", 0),
            rs.get("immobilizzazioni_finanziarie", 0),
            rs.get("rimanenze", 0),
            rs.get("crediti_clienti", 0),
            rs.get("altri_crediti", 0),
            rs.get("attivita_finanziarie", 0),
            rs.get("disponibilita_liquide", 0),
            rs.get("ratei_risconti_attivi", 0),
            rs.get("totale_attivo", 0),
            rs.get("patrimonio_netto", 0),
            rs.get("fondi_rischi_oneri", 0),
            rs.get("tfr", 0),
            rs.get("debiti_banche_breve", 0),
            rs.get("debiti_banche_lungo", 0),
            rs.get("debiti_fornitori", 0),
            rs.get("altri_debiti", 0),
            rs.get("ratei_risconti_passivi", 0),
        ]

        all_zero = all(float(v or 0) == 0 for v in rs_values)
        if all_zero:
            logger.info("Detected accounting type: SEMPLIFICATA (all quadro_rs fields are zero)")
            return "semplificata"

        logger.info("Detected accounting type: ORDINARIA (quadro_rs has non-zero values)")
        return "ordinaria"

    def detect_available_sections(self, pdf_path: str) -> Dict[str, Any]:
        """
        Scan the entire PDF to detect which data sections are actually present.
        Returns a dict describing what was found, used to generate warnings.
        """
        sections = {
            'has_ici_codes': False,
            'has_ica_codes': False,
            'has_f_codes': False,
            'has_re_codes': False,
            'has_rs_codes': False,
            'has_isa_prospetto': False,
            'has_isa_punteggio': False,
            'has_personnel_data': False,
            'has_rf_codes': False,
            'has_isa_exclusion': False,
            'has_spaced_text': False,
            'detected_year': None,
            'ici_codes_found': [],
            'f_codes_found': [],
        }

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ''
                    text_upper = text.upper()

                    # Detect spaced-out text (common in some PDF generators)
                    if re.search(r'P\s+E\s+R\s+I\s+O\s+D\s+O', text_upper):
                        sections['has_spaced_text'] = True

                    # Year detection (normal + spaced)
                    if not sections['detected_year']:
                        # Normal: "Periodo d'imposta 2023"
                        m = re.search(r"[Pp]eriodo\s+d.imposta\s+(\d{4})", text)
                        if m:
                            sections['detected_year'] = int(m.group(1))
                        else:
                            # Spaced: "P e r io d o d 'i m p o s t a 2 0 2 3"
                            m = re.search(r'(?:P\s*E\s*R\s*I\s*O\s*D\s*O|Periodo).*?(\d)\s+(\d)\s+(\d)\s+(\d)', text, re.IGNORECASE)
                            if m:
                                sections['detected_year'] = int(m.group(1) + m.group(2) + m.group(3) + m.group(4))

                    # Check for ICI codes (both 3-digit and 5-digit)
                    ici = re.findall(r'\bICI\d{3,5}\b', text)
                    if ici:
                        sections['has_ici_codes'] = True
                        sections['ici_codes_found'].extend(ici)

                    # Check for ICA codes
                    if re.search(r'\bICA\d{3,5}\b', text):
                        sections['has_ica_codes'] = True

                    # Check for F-codes (Quadro F - ISA elements contabili)
                    # Only count F01-F21 as real Quadro F codes (not F24 which is a tax payment form reference)
                    f_codes = re.findall(r'\bF(?:0[1-9]|1\d|2[01])\b', text)
                    if f_codes:
                        sections['has_f_codes'] = True
                        sections['f_codes_found'].extend(f_codes)

                    # Check for Quadro RF (contabilita' ordinaria - different from Quadro F)
                    if re.search(r'\bQUADRO RF\b', text_upper) or re.search(r'\bRF[12]\b', text):
                        sections['has_rf_codes'] = True

                    # Check for ISA exclusion
                    if re.search(r'ISA.*cause di esclusione', text, re.IGNORECASE):
                        sections['has_isa_exclusion'] = True

                    # Check for Quadro RE codes
                    if re.search(r'\bRE[1-9]\d?\b', text):
                        sections['has_re_codes'] = True

                    # Check for RS codes (balance sheet)
                    if re.search(r'\bRS(?:9[7-9]|1[01]\d|12[0-3])\b', text):
                        sections['has_rs_codes'] = True

                    # Check for ISA Prospetto Economico
                    if 'PROSPETTO ECONOMICO' in text_upper or re.search(r'\bICI01[147]01\b', text) or re.search(r'\bICI01[147]\b', text):
                        sections['has_isa_prospetto'] = True

                    # Check for ISA punteggio
                    if re.search(r'\bI{1,3}SAAFF\b', text) or ('PUNTEGGIO' in text_upper and 'ISA' in text_upper):
                        sections['has_isa_punteggio'] = True

                    # Check for personnel data
                    if re.search(r'\bA0[12]\b', text) or 'GIORNATE RETRIBUITE' in text_upper:
                        sections['has_personnel_data'] = True

        except Exception as e:
            logger.error(f"Error detecting available sections: {e}")

        return sections

    def _build_warnings(self, sections: Dict[str, Any], entity_type: str) -> List[str]:
        """
        Build warning messages based on which sections are missing from the PDF.
        """
        warnings = []

        # ISA exclusion with no ISA data actually present
        has_isa_data = sections['has_ici_codes'] or sections['has_ica_codes'] or sections['has_isa_prospetto']
        if sections.get('has_isa_exclusion') and not has_isa_data:
            warnings.append(
                "Il contribuente ha una causa di esclusione ISA e nessun dato ISA presente nel PDF. "
                "I campi 'risultati' (valore aggiunto, MOL, reddito operativo) e 'isa' (punteggio, indicatori) "
                "saranno basati solo sui dati del Quadro F/RF, con possibile imprecisione."
            )

        if entity_type in ('SP', 'PF_RG'):
            if not has_isa_data:
                if not sections['has_isa_prospetto'] and not (sections.get('has_isa_exclusion') and not has_isa_data):
                    warnings.append(
                        "ISA Prospetto Economico non trovato nel PDF. "
                        "I campi 'risultati' (valore_aggiunto, MOL, reddito_operativo) e "
                        "'isa' (punteggio, ricavi_per_addetto, etc.) potrebbero essere zero o imprecisi. "
                        "Il PDF potrebbe non includere il modulo ISA."
                    )
                if not sections['has_isa_punteggio']:
                    warnings.append(
                        "Punteggio ISA (ISAAFF/IIISAAFF) non trovato nel PDF. "
                        "Il campo 'isa.punteggio' sara' zero."
                    )

            if not sections['has_f_codes']:
                if sections.get('has_rf_codes'):
                    warnings.append(
                        "Quadro RF (contabilita' ordinaria) rilevato al posto del Quadro F. "
                        "I dati di ricavi e costi verranno estratti dal Quadro RF. "
                        "L'estrazione potrebbe essere meno precisa."
                    )
                else:
                    warnings.append(
                        "Quadro F (Elementi Contabili) non trovato nel PDF. "
                        "I campi 'ricavi' e 'costi' potrebbero essere zero o imprecisi."
                    )

        elif entity_type == 'PF_RE':
            if not sections['has_ica_codes']:
                warnings.append(
                    "Codici ICA (Prospetto Economico professionisti) non trovati nel PDF. "
                    "I campi 'risultati' e 'isa' potrebbero essere zero o imprecisi."
                )
            if not sections['has_re_codes']:
                warnings.append(
                    "Quadro RE (redditi lavoro autonomo) non trovato nel PDF. "
                    "I campi 'ricavi' e 'costi' potrebbero essere zero."
                )

        if not sections['has_rs_codes']:
            warnings.append(
                "Quadro RS - Dati di bilancio (RS97-RS114) non trovato nel PDF. "
                "I campi 'quadro_rs' (stato patrimoniale) saranno zero."
            )

        if not sections['has_personnel_data']:
            warnings.append(
                "Dati personale (A01/A02) non trovati nel PDF. "
                "I campi 'personale.giornate_dipendenti' e 'giornate_altro_personale' saranno zero."
            )

        if sections['has_spaced_text']:
            warnings.append(
                "Il PDF contiene testo con spaziatura anomala (caratteri separati da spazi). "
                "L'estrazione potrebbe essere meno precisa per alcune sezioni."
            )

        return warnings

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

    def analyze_pdf(self, pdf_path: str) -> tuple:
        """
        Combined method: detect available sections AND find relevant pages in a single PDF pass.
        Returns (sections_dict, relevant_pages_set).
        This avoids scanning the PDF twice.
        """
        sections = {
            'has_ici_codes': False,
            'has_ica_codes': False,
            'has_f_codes': False,
            'has_re_codes': False,
            'has_rs_codes': False,
            'has_rf_codes': False,
            'has_isa_exclusion': False,
            'has_isa_prospetto': False,
            'has_isa_punteggio': False,
            'has_personnel_data': False,
            'has_rn_codes': False,
            'has_rv_codes': False,
            'has_spaced_text': False,
            'detected_year': None,
            'ici_codes_found': [],
            'f_codes_found': [],
        }
        relevant_pages = {1}  # Always include first page

        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                logger.info(f"Analyzing {total_pages} pages...")

                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ''
                    text_upper = text.upper()

                    # --- Section detection ---

                    # Detect spaced-out text
                    if not sections['has_spaced_text'] and re.search(r'P\s+E\s+R\s+I\s+O\s+D\s+O', text_upper):
                        sections['has_spaced_text'] = True

                    # Year detection (normal + spaced)
                    if not sections['detected_year']:
                        m = re.search(r"[Pp]eriodo\s+d.imposta\s+(\d{4})", text)
                        if m:
                            sections['detected_year'] = int(m.group(1))
                        else:
                            m = re.search(r'(?:P\s*E\s*R\s*I\s*O\s*D\s*O|Periodo).*?(\d)\s+(\d)\s+(\d)\s+(\d)', text, re.IGNORECASE)
                            if m:
                                sections['detected_year'] = int(m.group(1) + m.group(2) + m.group(3) + m.group(4))

                    # ICI codes
                    ici = re.findall(r'\bICI\d{3,5}\b', text)
                    if ici:
                        sections['has_ici_codes'] = True
                        sections['ici_codes_found'].extend(ici)

                    # ICA codes
                    if re.search(r'\bICA\d{3,5}\b', text):
                        sections['has_ica_codes'] = True

                    # F-codes (Quadro F, F01-F21 only)
                    f_codes = re.findall(r'\bF(?:0[1-9]|1\d|2[01])\b', text)
                    if f_codes:
                        sections['has_f_codes'] = True
                        sections['f_codes_found'].extend(f_codes)

                    # Quadro RF
                    if re.search(r'\bQUADRO RF\b', text_upper) or re.search(r'\bRF[12]\b', text):
                        sections['has_rf_codes'] = True

                    # ISA exclusion
                    if re.search(r'ISA.*cause di esclusione', text, re.IGNORECASE):
                        sections['has_isa_exclusion'] = True

                    # Quadro RE codes
                    if re.search(r'\bRE[1-9]\d?\b', text):
                        sections['has_re_codes'] = True

                    # RS codes (balance sheet)
                    if re.search(r'\bRS(?:9[7-9]|1[01]\d|12[0-3])\b', text):
                        sections['has_rs_codes'] = True

                    # ISA Prospetto Economico
                    if 'PROSPETTO ECONOMICO' in text_upper or re.search(r'\bICI01[147]01\b', text) or re.search(r'\bICI01[147]\b', text):
                        sections['has_isa_prospetto'] = True

                    # ISA punteggio
                    if re.search(r'\bI{1,3}SAAFF\b', text) or ('PUNTEGGIO' in text_upper and 'ISA' in text_upper):
                        sections['has_isa_punteggio'] = True

                    # Quadro RN (IRPEF)
                    if re.search(r'\bRN\d{1,2}\b', text) or 'QUADRO RN' in text_upper:
                        sections['has_rn_codes'] = True

                    # Quadro RV (Addizionali)
                    if re.search(r'\bRV\d{1,2}\b', text) or 'QUADRO RV' in text_upper:
                        sections['has_rv_codes'] = True

                    # Personnel data
                    if re.search(r'\bA0[12]\b', text) or 'GIORNATE RETRIBUITE' in text_upper:
                        sections['has_personnel_data'] = True

                    # --- Page relevance detection ---

                    found = False
                    # Strategy 1: field codes
                    for code in self.TARGET_CODES:
                        if re.search(rf'\b{re.escape(code)}\b', text):
                            relevant_pages.add(page_num)
                            found = True
                            break

                    if not found:
                        # Strategy 2: keywords
                        for keyword in self.PAGE_KEYWORDS:
                            if keyword in text_upper:
                                relevant_pages.add(page_num)
                                found = True
                                break

                    if not found:
                        # Strategy 3: spaced-out codes
                        text_compact = re.sub(r'\s+', '', text_upper)
                        for code in self.TARGET_CODES:
                            if code in text_compact:
                                relevant_pages.add(page_num)
                                break

                logger.info(f"Found {len(relevant_pages)} relevant pages out of {total_pages}")
                logger.info(f"   Pages to analyze: {sorted(relevant_pages)}")

        except Exception as e:
            logger.error(f"Error analyzing PDF: {e}")
            relevant_pages = set(range(1, 31))

        return sections, relevant_pages

    def find_relevant_pages(self, pdf_path: str) -> Set[int]:
        """
        Scan PDF to find pages containing our target field codes or relevant keywords.
        Returns set of page numbers (1-indexed).

        Uses three detection strategies:
        1. Field code matching (ICI, ICA, F01, RS97, etc.)
        2. Keyword matching (PROSPETTO ECONOMICO, VALORE AGGIUNTO, etc.)
        3. Spaced-text code matching (for PDFs with character-spaced text)
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
                    text_upper = text.upper()

                    # Strategy 1: Check for target field codes
                    found_code = False
                    for code in self.TARGET_CODES:
                        pattern = rf'\b{re.escape(code)}\b'
                        if re.search(pattern, text):
                            relevant_pages.add(page_num)
                            logger.debug(f"  Page {page_num}: Found code {code}")
                            found_code = True
                            break

                    if found_code:
                        continue

                    # Strategy 2: Check for relevant keywords
                    for keyword in self.PAGE_KEYWORDS:
                        if keyword in text_upper:
                            relevant_pages.add(page_num)
                            logger.debug(f"  Page {page_num}: Found keyword '{keyword}'")
                            break

                    # Strategy 3: Check for spaced-out field codes
                    # e.g., "I C I 0 1 1" or "F 0 1" in PDFs with character spacing
                    text_compact = re.sub(r'\s+', '', text_upper)
                    if not found_code and page_num not in relevant_pages:
                        for code in self.TARGET_CODES:
                            if code in text_compact:
                                # Verify it's not a false positive by checking nearby context
                                relevant_pages.add(page_num)
                                logger.debug(f"  Page {page_num}: Found spaced code {code}")
                                break

                logger.info(f"Found {len(relevant_pages)} relevant pages out of {total_pages}")
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

**imposte (Quadro RN + RV - Imposte effettive):**
NOTE: Only present in Persone Fisiche declarations (PF_RG, PF_RE). For Società di Persone (SP) these will be 0.
Extract from Quadro RN (calcolo IRPEF) and Quadro RV (addizionali):
- irpef_netta: RN26 - IRPEF netta (imposta netta dopo detrazioni e crediti)
- addizionale_regionale: RV2 - Addizionale regionale all'IRPEF
- addizionale_comunale: RV10 - Addizionale comunale all'IRPEF

Return the data in this exact JSON structure:
{json.dumps(self.EXPECTED_STRUCTURE, indent=2)}

IMPORTANT:
- Numbers must be floats (e.g., 123456.78, not "123.456,78")
- Convert ALL Italian number formats to standard format
- If a field is not found, use 0 for numbers or "" for strings
- Return ONLY valid JSON, no markdown formatting or explanations"""

    def _build_extraction_prompt_re(self, anno: int) -> str:
        """Build extraction prompt for PF with Quadro RE (Libero Professionista)"""

        # ICA code format depends on year
        if anno == 2024:
            ica_compensi = "ICA001"
            ica_totale_compensi = "ICA003"
            ica_canoni_leasing = "ICA004"
            ica_canoni_noleggio = "ICA005"
            ica_compensi_terzi = "ICA007"
            ica_consumi = "ICA008"
            ica_altre_spese = "ICA012"
            ica_valore_aggiunto = "ICA013"
            ica_lavoro_dipendente = "ICA014"
            ica_collaboratori = "ICA015"
            ica_mol = "ICA016"
            ica_ammortamenti = "ICA017"
            ica_reddito_operativo = "ICA018"
            ica_interessi = "ICA020"
            ica_reddito = "ICA024"
            ica_addetti = "ICA027"
            ica_beni_strumentali = "ICA028"
            isa_punteggio = "ISAAFF"
            iie_ricavi = "IIE001"
            iie_va = "IIE002"
            iie_reddito = "IIE003"
        else:  # 2023 and earlier (5-digit format)
            ica_compensi = "ICA00101"
            ica_totale_compensi = "ICA00301"
            ica_canoni_leasing = "ICA00401"
            ica_canoni_noleggio = "ICA00501"
            ica_compensi_terzi = "ICA00701"
            ica_consumi = "ICA00801"
            ica_altre_spese = "ICA01201"
            ica_valore_aggiunto = "ICA01301"
            ica_lavoro_dipendente = "ICA01401"
            ica_collaboratori = "ICA01501"
            ica_mol = "ICA01601"
            ica_ammortamenti = "ICA01701"
            ica_reddito_operativo = "ICA01801"
            ica_interessi = "ICA02001"
            ica_reddito = "ICA02401"
            ica_addetti = "ICA02701"
            ica_beni_strumentali = "ICA02801"
            isa_punteggio = "IIISAAFF"
            iie_ricavi = "IIE00101"
            iie_va = "IIE00201"
            iie_reddito = "IIE00301"

        return f"""You are a tax document data extraction specialist. You will receive selected pages from an Italian PF tax declaration (Redditi Persone Fisiche) for a LIBERO PROFESSIONISTA (Quadro RE) for year {anno}.

Your task is to extract ALL the following fields and return them as a JSON object. Be extremely precise with numbers.

CRITICAL INSTRUCTIONS:
1. Extract numbers EXACTLY as they appear in the PDF
2. For Italian number format (e.g., "123.456,78"), convert to: 123456.78
3. If a field is missing or unclear, use 0 for numbers and "" for strings
4. The "anno" field MUST be extracted from "Periodo d'imposta YYYY" text. Expected: {anno}
5. Return ONLY the JSON object, no additional text or explanation
6. This is a PROFESSIONISTA declaration - income is in Quadro RE (not Quadro F)
7. ISA data uses ICA codes (not ICI codes)

FIELD MAPPING for Libero Professionista (year {anno}):

**identificativi:**
- codice_fiscale: 16-char personal tax code (e.g., RDCMRG51M19C933Z)
- partita_iva: VAT number (11 digits, from page 2)
- ragione_sociale: Full name (COGNOME NOME from page 1)
- anno: Extract from "Periodo d'imposta YYYY". Expected: {anno}

**ricavi (from Quadro RE):**
- ricavi_dichiarati: RE2 / {ica_compensi} - Compensi dall'attività professionale
- altri_componenti_positivi: RE3 + RE4 + RE5 (Altre somme + Plusvalenze + Compensi non annotati)

**costi (from Quadro RE + ISA Prospetto Economico ICA):**
- esistenze_iniziali: 0 (professionals don't have inventory)
- rimanenze_finali: 0 (professionals don't have inventory)
- costo_materie_prime: {ica_consumi} / RE14 - Consumi
- costo_servizi: {ica_compensi_terzi} / RE12 - Compensi corrisposti a terzi
- godimento_beni_terzi: {ica_canoni_leasing} + {ica_canoni_noleggio} / RE8 + RE9 - Canoni di locazione
- costo_personale: {ica_lavoro_dipendente} / RE11 - Spese lavoro dipendente
- spese_collaboratori: {ica_collaboratori} - Spese collaboratori coordinati e continuativi
- ammortamenti: {ica_ammortamenti} / RE7 - Ammortamenti
- accantonamenti: 0 (not in RE)
- altri_costi: {ica_altre_spese} / RE19 - Altre spese documentate (include RE10, RE15, RE16, RE17)
- oneri_finanziari: {ica_interessi} / RE13 - Interessi passivi

**risultati (from ISA Prospetto Economico ICA):**
- valore_aggiunto: {ica_valore_aggiunto} - Valore aggiunto
- mol: {ica_mol} - Margine Operativo Lordo
- reddito_operativo: {ica_reddito_operativo} - Reddito operativo
- reddito_impresa: {ica_reddito} / RE23 - Reddito delle attività professionali

**personale:**
- giornate_dipendenti: A01 - Giornate retribuite dipendenti (0 if not found)
- giornate_altro_personale: A02 - Giornate retribuite altro personale (0 if not found)
- numero_addetti_equivalenti: {ica_addetti} - Numero addetti equivalenti

**patrimonio:**
- valore_beni_strumentali: {ica_beni_strumentali} - Valore beni strumentali in proprietà

**isa:**
- punteggio: {isa_punteggio} - Punteggio ISA finale (1-10 scale)
- modello_applicato: Codice modello ISA (e.g., "BK04U")
- ricavi_per_addetto: {iie_ricavi} - Compensi per addetto
- valore_aggiunto_per_addetto: {iie_va} - Valore aggiunto per addetto
- reddito_per_addetto: {iie_reddito} - Reddito per addetto

**quadro_rs (Quadro RS - Stato Patrimoniale):**
NOTE: For professionisti in contabilità semplificata, these fields are typically ALL ZEROS.
Extract them anyway from pages with "Dati di bilancio" section (RS97-RS114).
- immobilizzazioni_immateriali: RS97
- immobilizzazioni_materiali: RS98 (rightmost number on the line)
- immobilizzazioni_finanziarie: RS99
- rimanenze: RS100
- crediti_clienti: RS101
- altri_crediti: RS102
- attivita_finanziarie: RS103
- disponibilita_liquide: RS104
- ratei_risconti_attivi: RS105
- totale_attivo: RS106
- patrimonio_netto: RS107
- fondi_rischi_oneri: RS108
- tfr: RS109
- debiti_banche_breve: RS110
- debiti_banche_lungo: RS111
- debiti_fornitori: RS112
- altri_debiti: RS113
- ratei_risconti_passivi: RS114

**imposte (Quadro RN + RV - Imposte effettive):**
Extract from Quadro RN (calcolo IRPEF) and Quadro RV (addizionali):
- irpef_netta: RN26 - IRPEF netta (imposta netta dopo detrazioni e crediti)
- addizionale_regionale: RV2 - Addizionale regionale all'IRPEF
- addizionale_comunale: RV10 - Addizionale comunale all'IRPEF

Return the data in this exact JSON structure:
{json.dumps(self.EXPECTED_STRUCTURE, indent=2)}

IMPORTANT:
- Numbers must be floats (e.g., 123456.78, not "123.456,78")
- Convert ALL Italian number formats to standard format
- If a field is not found, use 0 for numbers or "" for strings
- Return ONLY valid JSON, no markdown formatting or explanations"""

    def extract_from_pdf(self, pdf_path: str, anno: int) -> Dict[str, Any]:
        """
        Extract data from PDF using optimized page filtering.
        Includes _warnings list in result for missing sections.
        """
        try:
            logger.info(f"Optimized extraction from {pdf_path} for year {anno}")

            # Step 0a: Detect entity type
            entity_type = self.detect_entity_type(pdf_path)
            if entity_type == 'PF':
                logger.warning(f"PDF is a Persona Fisica declaration without business income - returning empty structure")
                result = self._build_empty_result(pdf_path, anno, entity_type)
                result['_warnings'] = [
                    "Dichiarazione Persone Fisiche senza reddito d'impresa o lavoro autonomo. "
                    "Nessun dato finanziario aziendale disponibile."
                ]
                return result

            # Step 0b: Detect available sections and find relevant pages in a single pass
            sections, relevant_pages = self.analyze_pdf(pdf_path)
            warnings = self._build_warnings(sections, entity_type)

            # Use detected year if auto-detect from filename failed
            if sections['detected_year'] and sections['detected_year'] != anno:
                logger.info(f"Year from PDF content ({sections['detected_year']}) differs from parameter ({anno}), using PDF content year")
                anno = sections['detected_year']

            if warnings:
                for w in warnings:
                    logger.warning(f"  {w}")

            # PF_RG uses same extraction as SP (Quadro F + ICI codes)
            # PF_RE uses different extraction (Quadro RE + ICA codes)
            use_re_prompt = (entity_type == 'PF_RE')

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

            # Step 4: Build extraction prompt (different for professionisti)
            if use_re_prompt:
                logger.info("📋 Using Quadro RE extraction prompt (Libero Professionista)")
                prompt = self._build_extraction_prompt_re(anno)
            else:
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

                # Add entity type metadata
                extracted_data['_entity_type'] = entity_type

                # Add warnings about missing sections
                if warnings:
                    extracted_data['_warnings'] = warnings

                # Fallback: calculate MOL from Valore Aggiunto - Costo Personale
                # when extraction failed to find MOL directly
                risultati = extracted_data.get('risultati', {})
                mol = float(risultati.get('mol', 0))
                if mol == 0:
                    va = float(risultati.get('valore_aggiunto', 0))
                    costo_pers = float(extracted_data.get('costi', {}).get('costo_personale', 0))
                    if va != 0:
                        calculated_mol = va - costo_pers
                        extracted_data['risultati']['mol'] = calculated_mol
                        logger.info(f"MOL fallback: calculated as VA ({va:,.0f}) - Costo Personale ({costo_pers:,.0f}) = {calculated_mol:,.0f}")

                # Post-extraction validation: check if key fields are actually zero
                # and add specific warnings
                post_warnings = self._post_extraction_warnings(extracted_data, sections)
                if post_warnings:
                    existing = extracted_data.get('_warnings', [])
                    extracted_data['_warnings'] = existing + post_warnings

                logger.info(f"Successfully extracted data for year {anno} (entity: {entity_type})")
                logger.info(f"   Pages analyzed: {sorted(relevant_pages)}")
                if extracted_data.get('_warnings'):
                    logger.warning(f"   Warnings: {len(extracted_data['_warnings'])}")

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
                           "personale", "patrimonio", "isa", "quadro_rs", "imposte"]
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

    def _post_extraction_warnings(self, data: Dict[str, Any], sections: Dict[str, Any]) -> List[str]:
        """
        After extraction, check if critical fields are zero and generate targeted warnings.
        This catches cases where Claude couldn't find data even though we sent the pages.
        """
        warnings = []

        ricavi = data.get('ricavi', {}).get('ricavi_dichiarati', 0)
        reddito = data.get('risultati', {}).get('reddito_impresa', 0)
        va = data.get('risultati', {}).get('valore_aggiunto', 0)
        mol = data.get('risultati', {}).get('mol', 0)
        punteggio = data.get('isa', {}).get('punteggio', 0)
        totale_attivo = data.get('quadro_rs', {}).get('totale_attivo', 0)

        if ricavi == 0:
            warnings.append(
                "Ricavi dichiarati estratti come zero. "
                "Verificare manualmente il Quadro F/RE della dichiarazione."
            )

        if va == 0 and mol == 0 and reddito == 0:
            warnings.append(
                "Tutti i risultati economici (valore aggiunto, MOL, reddito) sono zero. "
                "Il Prospetto Economico ISA potrebbe essere assente dal PDF."
            )

        if punteggio == 0:
            warnings.append(
                "Punteggio ISA non estratto (valore zero). "
                "Il PDF potrebbe non contenere il risultato ISA."
            )

        if totale_attivo == 0 and sections.get('has_rs_codes'):
            warnings.append(
                "Totale attivo zero nonostante la presenza del Quadro RS. "
                "Verificare manualmente i dati di bilancio."
            )

        # Check imposte for PF declarations
        entity_type = data.get('_entity_type', '')
        if entity_type in ('PF_RG', 'PF_RE'):
            imposte = data.get('imposte', {})
            irpef = imposte.get('irpef_netta', 0)
            add_reg = imposte.get('addizionale_regionale', 0)
            add_com = imposte.get('addizionale_comunale', 0)
            if irpef == 0 and add_reg == 0 and add_com == 0:
                warnings.append(
                    "Imposte (IRPEF netta, addizionali) tutte zero per dichiarazione PF. "
                    "Il Quadro RN/RV potrebbe essere assente dal PDF. "
                    "Verrà utilizzato il tax rate stimato del 30%."
                )

        return warnings

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
            match = re.search(r'(202[0-9])', pdf_path)
            if match:
                anno = int(match.group(1))
                logger.info(f"Auto-detected year from filename: {anno}")
            else:
                # Try to detect from PDF content (handles files like report453_current.pdf)
                try:
                    with pdfplumber.open(pdf_path) as pdf:
                        for page in pdf.pages[:3]:
                            text = page.extract_text() or ''
                            m = re.search(r"[Pp]eriodo\s+d.imposta\s+(\d{4})", text)
                            if m:
                                anno = int(m.group(1))
                                break
                            # Spaced text: "2 0 2 3"
                            m = re.search(r'(?:PERIODO|Periodo).*?(\d)\s+(\d)\s+(\d)\s+(\d)', text, re.IGNORECASE)
                            if m:
                                anno = int(m.group(1) + m.group(2) + m.group(3) + m.group(4))
                                break
                except Exception:
                    pass
                if anno is None:
                    anno = 2024
                logger.info(f"Auto-detected year from PDF content: {anno}")

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
