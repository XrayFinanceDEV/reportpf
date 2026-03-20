#!/usr/bin/env python3
"""
validation.py
Validation and confidence scoring for PDF extraction

Phase 1 Implementation: Critical Reliability Improvements
"""

from decimal import Decimal
from typing import Dict, Any, List, Tuple
from datetime import datetime


class ExtractionValidator:
    """Validates extracted data and assigns confidence scores"""

    def __init__(self):
        self.warnings = []
        self.errors = []

    def validate_extraction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates extracted data and returns validation report

        Returns:
            {
                'passed': bool,
                'confidence': float (0.0 to 1.0),
                'warnings': List[str],
                'errors': List[str],
                'field_confidence': Dict[str, float],
                'checks_performed': int,
                'checks_passed': int
            }
        """
        self.warnings = []
        self.errors = []
        checks_passed = 0
        checks_total = 0

        # Basic sanity checks
        checks_passed += self._check_ricavi(data)
        checks_total += 2  # Two revenue checks

        checks_passed += self._check_balance_sheet(data)
        checks_total += 1

        checks_passed += self._check_costo_venduto(data)
        checks_total += 1

        checks_passed += self._check_value_ranges(data)
        checks_total += 5  # Multiple range checks

        checks_passed += self._check_isa_ratios(data)
        checks_total += 3  # Three ISA score checks

        checks_passed += self._check_field_relationships(data)
        checks_total += 3  # Multiple relationship checks

        # Calculate overall confidence
        if checks_total > 0:
            pass_rate = checks_passed / checks_total
        else:
            pass_rate = 0.0

        # Confidence based on pass rate and severity of errors
        if len(self.errors) > 0:
            confidence = min(0.5, pass_rate)  # Cap at 0.5 if errors exist
        elif len(self.warnings) > 3:
            confidence = min(0.75, pass_rate)  # Cap at 0.75 if many warnings
        else:
            confidence = pass_rate

        return {
            'passed': len(self.errors) == 0,
            'confidence': round(confidence, 2),
            'warnings': self.warnings,
            'errors': self.errors,
            'checks_performed': checks_total,
            'checks_passed': checks_passed,
            'validation_timestamp': datetime.now().isoformat()
        }

    def _check_ricavi(self, data: Dict[str, Any]) -> int:
        """Check revenue makes sense"""
        checks_passed = 0

        try:
            ricavi_dichiarati = float(data.get('ricavi', {}).get('ricavi_dichiarati', 0))
            altri_componenti = float(data.get('ricavi', {}).get('altri_componenti_positivi', 0))
            ricavi_totali = ricavi_dichiarati + altri_componenti

            # Revenue should be non-negative
            if ricavi_dichiarati < 0:
                self.errors.append(f"❌ Ricavi dichiarati negativi: {ricavi_dichiarati}")
            else:
                checks_passed += 1

            # Total revenue should be reasonable
            if ricavi_totali < 0:
                self.errors.append(f"❌ Ricavi totali negativi: {ricavi_totali}")
            elif ricavi_totali > 10_000_000_000:  # 10 billion
                self.warnings.append(f"⚠️ Ricavi molto alti: €{ricavi_totali:,.0f}")
                checks_passed += 1
            else:
                checks_passed += 1

            # If F01 is zero, should have F02
            if ricavi_dichiarati == 0 and altri_componenti == 0:
                self.warnings.append("⚠️ Nessun ricavo dichiarato (F01=0, F02=0)")

        except Exception as e:
            self.warnings.append(f"⚠️ Errore controllo ricavi: {e}")

        return checks_passed

    def _check_balance_sheet(self, data: Dict[str, Any]) -> int:
        """Check balance sheet balances (Assets = Liabilities + Equity)"""
        checks_passed = 0

        try:
            rs = data.get('quadro_rs', {})
            if not rs:
                self.warnings.append("⚠️ Quadro RS non estratto")
                return 0

            totale_attivo = float(rs.get('totale_attivo', 0))
            patrimonio_netto = float(rs.get('patrimonio_netto', 0))

            # Calculate total liabilities
            totale_passivo = (
                float(rs.get('fondi_rischi_oneri', 0)) +
                float(rs.get('tfr', 0)) +
                float(rs.get('debiti_banche_breve', 0)) +
                float(rs.get('debiti_banche_lungo', 0)) +
                float(rs.get('debiti_fornitori', 0)) +
                float(rs.get('altri_debiti', 0)) +
                float(rs.get('ratei_risconti_passivi', 0))
            )

            # Assets should equal Liabilities + Equity
            totale_passivo_e_netto = patrimonio_netto + totale_passivo

            if totale_attivo > 0:
                diff = abs(totale_attivo - totale_passivo_e_netto)
                diff_pct = (diff / totale_attivo) * 100

                if diff_pct < 0.1:  # Less than 0.1% difference
                    checks_passed += 1
                elif diff_pct < 1.0:  # Less than 1% difference
                    self.warnings.append(
                        f"⚠️ Stato patrimoniale sbilanciato di {diff_pct:.2f}%: "
                        f"Attivo={totale_attivo:,.0f}, Passivo+PN={totale_passivo_e_netto:,.0f}"
                    )
                    checks_passed += 1
                else:
                    self.errors.append(
                        f"❌ Stato patrimoniale sbilanciato di {diff_pct:.1f}%: "
                        f"Attivo={totale_attivo:,.0f}, Passivo+PN={totale_passivo_e_netto:,.0f}"
                    )
            else:
                self.warnings.append("⚠️ Totale attivo = 0")

        except Exception as e:
            self.warnings.append(f"⚠️ Errore controllo stato patrimoniale: {e}")

        return checks_passed

    def _check_costo_venduto(self, data: Dict[str, Any]) -> int:
        """Check cost of goods sold formula"""
        checks_passed = 0

        try:
            costi = data.get('costi', {})
            esistenze_iniziali = float(costi.get('esistenze_iniziali', 0))
            rimanenze_finali = float(costi.get('rimanenze_finali', 0))
            costo_materie_prime = float(costi.get('costo_materie_prime', 0))

            # COGS = Existing Inventory + Purchases - Final Inventory
            costo_venduto_calc = esistenze_iniziali + costo_materie_prime - rimanenze_finali

            # This is a derived calculation, not extracted directly
            # Just check if values make sense
            if costo_venduto_calc < 0 and costo_materie_prime > 0:
                self.warnings.append(
                    f"⚠️ Costo del venduto negativo: "
                    f"Iniz={esistenze_iniziali} + Acq={costo_materie_prime} - Fin={rimanenze_finali}"
                )
            else:
                checks_passed += 1

        except Exception as e:
            self.warnings.append(f"⚠️ Errore controllo costo venduto: {e}")

        return checks_passed

    def _check_value_ranges(self, data: Dict[str, Any]) -> int:
        """Check values are in reasonable ranges"""
        checks_passed = 0

        try:
            # Check ISA score (should be 0-10)
            isa_score = data.get('isa', {}).get('punteggio', 0)
            if 0 <= isa_score <= 10:
                checks_passed += 1
            else:
                self.errors.append(f"❌ ISA score fuori range: {isa_score} (dovrebbe essere 0-10)")

            # Check addetti (should be positive and reasonable)
            addetti = float(data.get('personale', {}).get('numero_addetti_equivalenti', 0))
            if addetti < 0:
                self.errors.append(f"❌ Numero addetti negativo: {addetti}")
            elif addetti > 10000:
                self.warnings.append(f"⚠️ Numero addetti molto alto: {addetti}")
                checks_passed += 1
            else:
                checks_passed += 1

            # Check beni strumentali (should be positive or zero)
            beni = float(data.get('patrimonio', {}).get('valore_beni_strumentali', 0))
            if beni < 0:
                self.errors.append(f"❌ Valore beni strumentali negativo: {beni}")
            else:
                checks_passed += 1

            # Check ammortamenti (should be non-negative)
            ammortamenti = float(data.get('costi', {}).get('ammortamenti', 0))
            if ammortamenti < 0:
                self.errors.append(f"❌ Ammortamenti negativi: {ammortamenti}")
            else:
                checks_passed += 1

            # Check oneri finanziari (typically small positive or zero)
            oneri = float(data.get('costi', {}).get('oneri_finanziari', 0))
            if oneri < 0:
                self.warnings.append(f"⚠️ Oneri finanziari negativi: {oneri}")
            else:
                checks_passed += 1

        except Exception as e:
            self.warnings.append(f"⚠️ Errore controllo range valori: {e}")

        return checks_passed

    def _check_isa_ratios(self, data: Dict[str, Any]) -> int:
        """Check ISA scores are in valid ranges (0-10 scale)"""
        checks_passed = 0

        try:
            isa = data.get('isa', {})

            # ISA per_addetto fields are SCORES (0-10), not euro values
            # Just validate they're in the valid range
            ricavi_per_addetto = isa.get('ricavi_per_addetto', 0)
            valore_aggiunto_per_addetto = isa.get('valore_aggiunto_per_addetto', 0)
            reddito_per_addetto = isa.get('reddito_per_addetto', 0)

            # Check each score is in valid range (0-10)
            for field_name, score in [
                ('ricavi_per_addetto', ricavi_per_addetto),
                ('valore_aggiunto_per_addetto', valore_aggiunto_per_addetto),
                ('reddito_per_addetto', reddito_per_addetto)
            ]:
                if 0 <= score <= 10:
                    checks_passed += 1
                else:
                    self.errors.append(
                        f"❌ ISA {field_name} fuori range: {score} (dovrebbe essere 0-10)"
                    )

        except Exception as e:
            self.warnings.append(f"⚠️ Errore controllo ISA scores: {e}")

        return checks_passed

    def _check_field_relationships(self, data: Dict[str, Any]) -> int:
        """Check relationships between fields"""
        checks_passed = 0

        try:
            # Check MOL = Valore Aggiunto - Costo Personale
            valore_aggiunto = float(data.get('risultati', {}).get('valore_aggiunto', 0))
            mol = float(data.get('risultati', {}).get('mol', 0))
            costo_personale = float(data.get('costi', {}).get('costo_personale', 0))

            mol_calc = valore_aggiunto - costo_personale

            if abs(mol - mol_calc) < max(1, abs(mol) * 0.01):  # Within 1% or 1 euro
                checks_passed += 1
            else:
                self.warnings.append(
                    f"⚠️ MOL discrepanza: Estratto={mol:,.0f}, "
                    f"Calc (VA-Pers)={mol_calc:,.0f}"
                )

            # Check Reddito Operativo <= MOL (usually)
            reddito_op = float(data.get('risultati', {}).get('reddito_operativo', 0))
            if reddito_op <= mol + 100:  # Allow small rounding
                checks_passed += 1
            else:
                self.warnings.append(
                    f"⚠️ Reddito Operativo > MOL: RO={reddito_op:,.0f}, MOL={mol:,.0f}"
                )

            # Check Reddito Impresa is reasonably close to Reddito Operativo - Oneri Finanziari
            # Note: Tax declarations can have extraordinary items and adjustments, so allow 10% variance
            reddito_impresa = float(data.get('risultati', {}).get('reddito_impresa', 0))
            oneri_finanziari = float(data.get('costi', {}).get('oneri_finanziari', 0))

            reddito_impresa_calc = reddito_op - oneri_finanziari

            if abs(reddito_impresa - reddito_impresa_calc) < max(1, abs(reddito_impresa) * 0.10):
                checks_passed += 1
            else:
                self.warnings.append(
                    f"⚠️ Reddito Impresa discrepanza significativa (>10%): "
                    f"Estratto={reddito_impresa:,.0f}, Calc (RO-OnFin)={reddito_impresa_calc:,.0f}"
                )

        except Exception as e:
            self.warnings.append(f"⚠️ Errore controllo relazioni: {e}")

        return checks_passed


class ExtractionMetadata:
    """Generates metadata about extraction process"""

    @staticmethod
    def generate_metadata(data: Dict[str, Any],
                          extraction_time_ms: float = 0,
                          patterns_used: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Generate extraction metadata

        Args:
            data: Extracted data
            extraction_time_ms: Time taken to extract (milliseconds)
            patterns_used: Dict of field -> pattern that matched

        Returns:
            Metadata dictionary
        """
        total_fields = 0
        extracted_fields = 0
        defaulted_fields = 0

        # Count fields in each section
        sections = ['identificativi', 'ricavi', 'costi', 'risultati',
                   'personale', 'patrimonio', 'isa', 'quadro_rs']

        for section in sections:
            section_data = data.get(section, {})
            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    total_fields += 1
                    try:
                        if float(value) != 0:
                            extracted_fields += 1
                        else:
                            defaulted_fields += 1
                    except:
                        # Text fields or non-numeric
                        if value and value != "":
                            extracted_fields += 1
                        else:
                            defaulted_fields += 1

        # Run validation
        validator = ExtractionValidator()
        validation_result = validator.validate_extraction(data)

        return {
            'extraction_timestamp': datetime.now().isoformat(),
            'extraction_time_ms': round(extraction_time_ms, 2),
            'pdf_format': {
                'anno': data.get('identificativi', {}).get('anno'),
                'ragione_sociale': data.get('identificativi', {}).get('ragione_sociale'),
                'codice_fiscale': data.get('identificativi', {}).get('codice_fiscale')
            },
            'field_statistics': {
                'total_fields': total_fields,
                'extracted_fields': extracted_fields,
                'defaulted_fields': defaulted_fields,
                'extraction_rate': round(extracted_fields / total_fields, 2) if total_fields > 0 else 0
            },
            'validation': validation_result,
            'patterns_used': patterns_used or {},
            'quality_score': validation_result.get('confidence', 0)
        }


# Helper function to add to existing extractor
def validate_and_enrich(extracted_data: Dict[str, Any],
                        extraction_time_ms: float = 0) -> Dict[str, Any]:
    """
    Validates extracted data and adds metadata.
    Merges _warnings from the extractor into validation warnings.

    Usage:
        data = extractor.estrai_dati_input()
        enriched_data = validate_and_enrich(data, extraction_time_ms=2341)
    """
    metadata_gen = ExtractionMetadata()
    metadata = metadata_gen.generate_metadata(extracted_data, extraction_time_ms)

    # Merge extractor warnings into validation warnings
    extractor_warnings = extracted_data.get('_warnings', [])
    if extractor_warnings:
        validation = metadata.get('validation', {})
        existing_warnings = validation.get('warnings', [])
        validation['warnings'] = extractor_warnings + existing_warnings
        metadata['validation'] = validation

    return {
        **extracted_data,
        'extraction_metadata': metadata
    }


if __name__ == "__main__":
    # Test with sample data
    print("Testing Validation Module\n" + "="*60)

    sample_data = {
        'identificativi': {
            'codice_fiscale': '65102728600',
            'ragione_sociale': 'F.LLI GRASSI S.n.c.',
            'anno': 2024
        },
        'ricavi': {
            'ricavi_dichiarati': 0,
            'altri_componenti_positivi': 24240
        },
        'costi': {
            'costo_personale': 0,
            'ammortamenti': 0,
            'oneri_finanziari': 22
        },
        'risultati': {
            'valore_aggiunto': -8387,
            'mol': -8387,
            'reddito_operativo': -8387,
            'reddito_impresa': -8408
        },
        'personale': {
            'numero_addetti_equivalenti': 1
        },
        'patrimonio': {
            'valore_beni_strumentali': 7800
        },
        'isa': {
            'punteggio': 2.18,
            'ricavi_per_addetto': 24240,
            'valore_aggiunto_per_addetto': -8387
        },
        'quadro_rs': {
            'totale_attivo': 147103,
            'patrimonio_netto': -513119,
            'debiti_fornitori': 40073,
            'altri_debiti': 511522
        }
    }

    # Validate
    validator = ExtractionValidator()
    result = validator.validate_extraction(sample_data)

    print(f"Validation Result: {'✅ PASSED' if result['passed'] else '❌ FAILED'}")
    print(f"Confidence Score: {result['confidence']:.2%}")
    print(f"Checks: {result['checks_passed']}/{result['checks_performed']} passed")
    print()

    if result['errors']:
        print("❌ ERRORS:")
        for error in result['errors']:
            print(f"  {error}")
        print()

    if result['warnings']:
        print("⚠️  WARNINGS:")
        for warning in result['warnings']:
            print(f"  {warning}")
        print()

    # Generate metadata
    enriched = validate_and_enrich(sample_data, extraction_time_ms=2341)
    print("\n" + "="*60)
    print("Extraction Metadata:")
    print(f"  Quality Score: {enriched['extraction_metadata']['quality_score']:.2%}")
    print(f"  Extraction Rate: {enriched['extraction_metadata']['field_statistics']['extraction_rate']:.2%}")
    print(f"  Extraction Time: {enriched['extraction_metadata']['extraction_time_ms']}ms")
