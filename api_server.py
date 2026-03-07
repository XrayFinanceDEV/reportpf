#!/usr/bin/env python3
"""
api_server.py
FastAPI server per elaborazione PDF dichiarazioni fiscali

Endpoints:
  POST /upload/process - Elabora biennio (2 PDF) - REQUIRED for Report PF
  POST /extract/anbil - Estrai dati chiave per dashboard anbil da JSON ITC report
  GET /health - Health check

Note: Report PF requires 2 years of data for comparative analysis.
      Single PDF processing is not supported.

Avvio:
  uvicorn api_server:app --host 0.0.0.0 --port 8001 --reload
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Body, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
from typing import Dict, Any, Optional
from datetime import datetime
import time
import httpx

# Import del nostro extractor (V3 Optimized - Only analyzes relevant pages)
from extdichiarazione_v3_optimized import DichiarazioneExtractorV3Optimized as DichiarazioneExtractorMinimal
# Import del calculator per le formule
from formule_report_pf import ReportPFCalculator
# Import del validation module
from validation import validate_and_enrich
# Import anbil data extractor
from extract_anbil_data import extract_anbil_data
from extract_anbil_data_with_ai import extract_anbil_data_with_ai_comments
# Import comprehensive anbil extractor (v2.0)
from extract_anbil_data_extended import extract_comprehensive_metrics
from extract_anbil_data_comprehensive_with_ai import extract_comprehensive_with_ai



# Inizializza FastAPI
app = FastAPI(
    title="Report Società di Persone - PDF Extractor API",
    description="API per estrazione dati da PDF dichiarazioni fiscali (V3 Extractor - Claude Haiku 3.5)",
    version="3.0.0"
)

# CORS middleware per permettere chiamate da frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, specificare domini specifici
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint con info API"""
    return {
        "message": "Report Società di Persone - PDF Extractor API",
        "version": "3.0.0",
        "extractor": "V3 - Claude Haiku 3.5 (LLM-powered, no OCR)",
        "advantages": "Faster, more accurate, lower resource usage than V2",
        "note": "Report PF requires 2 years of data for comparative analysis",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "process_pdfs": "/upload/process (Upload 2 PDFs, get complete report)",
            "extract_anbil": "/extract/anbil (Extract key metrics from ITC report JSON)"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "pdf-extractor-api"
    }


@app.post("/extract/anbil")
async def extract_anbil(
    report_json: Dict[str, Any] = Body(...),
    ai_comments: bool = Query(default=False, description="Generate AI-powered comments using Claude Haiku 3.5")
):
    """
    Estrai dati chiave per dashboard anbil da JSON ITC report

    Args:
        report_json: Complete ITC report JSON (from resp-itc.json format)
        ai_comments: Enable AI-generated comments (default: False)

    Returns:
        JSON con dati estratti:
        - company_name: Nome azienda
        - years: Array con dati per ogni anno (2022-2024)
        - Per ogni anno: revenue, ebitda, costi materia prima, servizi, personale, oneri finanziari
        - ai_comments: Commenti AI per ogni metrica (se abilitati)
        - latest_year: Dati dell'anno più recente
        - metadata: Informazioni sugli anni disponibili

    Query Parameters:
        - ai_comments=true: Generate AI comments (~250 chars each) for all metrics

    Example input:
        {
            "api_response": {
                "financial_analysis": {
                    "financial_report": [...],
                    ...
                }
            },
            ...
        }

    Example output (with ai_comments=true):
        {
            "success": true,
            "data": {
                "company_name": "I.T.C. S.R.L.",
                "years": [
                    {
                        "year": "2024",
                        "revenue": 15130120,
                        "ebitda": 2245257,
                        "costi_materia_prima": 10109091,
                        "costi_servizi": 1570681,
                        "costi_personale": 1226685,
                        "costi_oneri_finanziari": 191499
                    },
                    ...
                ],
                "ai_comments": {
                    "revenue": "Ricavi in contrazione per I.T.C. S.r.l.: €15.1M nel 2024...",
                    "ebitda": "EBITDA in significativo calo: -39.7% nel 2024...",
                    ...
                },
                "latest_year": {...}
            },
            "metadata": {
                "company_name": "I.T.C. S.R.L.",
                "years_count": 3,
                "years_available": ["2024", "2023", "2022"],
                "ai_comments_enabled": true
            }
        }
    """
    try:
        # Extract anbil data (with or without AI comments)
        if ai_comments:
            print("🤖 AI comments requested - using Claude Haiku 3.5...")
            result = extract_anbil_data_with_ai_comments(report_json, generate_comments=True)
            result['metadata']['ai_comments_enabled'] = True
        else:
            result = extract_anbil_data(report_json)
            result['metadata']['ai_comments_enabled'] = False

        if not result.get('success'):
            raise HTTPException(
                status_code=400,
                detail=result.get('error', 'Failed to extract anbil data')
            )

        return JSONResponse(content=result)

    except KeyError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON structure: missing key {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing JSON: {str(e)}"
        )


@app.post("/extract/anbil/by_report_id/{report_id}")
async def extract_anbil_by_report_id(
    report_id: int,
    ai_comments: bool = Query(default=False, description="Generate AI-powered comments using Claude Haiku 3.5"),
    comprehensive: bool = Query(default=True, description="Use comprehensive extraction (31 metrics) vs basic (6 metrics)"),
    authorization: Optional[str] = Query(default=None, description="Authorization token (optional if integrated in same backend)"),
    main_backend_url: Optional[str] = Query(
        default="http://localhost:8000",
        description="Main backend URL (use localhost when integrated)"
    )
):
    """
    Estrai dati anbil da report ID (fetching automatico dal backend principale)

    **NUOVO ENDPOINT v2.0** - Fetches report JSON from main backend automatically!

    Args:
        report_id: ID del report nel backend principale
        ai_comments: Enable AI-generated comments (default: False)
        comprehensive: Use comprehensive extraction with 31 metrics (default: True)
        main_backend_url: URL del backend principale (default: https://kpsfinanciallab.w3pro.it:8000)

    Returns:
        JSON con dati estratti (31 metrics in comprehensive mode, 6 in basic mode)

    Example usage:
        POST /extract/anbil/by_report_id/11?ai_comments=true&comprehensive=true

        No request body needed! The endpoint fetches the report automatically.

    Query Parameters:
        - ai_comments=true: Generate AI comments (~250 chars each)
        - comprehensive=true: Extract all 31 metrics (v2.0) ← RECOMMENDED
        - comprehensive=false: Extract only 6 basic metrics (v1.0)
        - authorization: Bearer token for main backend authentication
        - main_backend_url: Override default backend URL
    """
    try:
        # STEP 1: Fetch report from main backend
        report_url = f"{main_backend_url}/api/v1/reports/{report_id}"

        print(f"📥 Fetching report from: {report_url}")

        # Prepare headers with authorization if provided
        headers = {}
        if authorization:
            headers["Authorization"] = authorization if authorization.startswith("Bearer ") else f"Bearer {authorization}"

        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            try:
                response = await client.get(report_url, headers=headers)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Failed to fetch report from main backend: {e.response.text}"
                )
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=503,
                    detail=f"Could not connect to main backend: {str(e)}"
                )

        report_data = response.json()

        # STEP 2: Extract api_response from report
        if "api_response" not in report_data:
            raise HTTPException(
                status_code=400,
                detail="Report does not contain 'api_response' field"
            )

        report_json = report_data["api_response"]

        print(f"✅ Report fetched successfully (ID: {report_id})")
        print(f"🔧 Extraction mode: {'COMPREHENSIVE (31 metrics)' if comprehensive else 'BASIC (6 metrics)'}")

        # STEP 3: Extract anbil data
        if comprehensive:
            # Use v2.0 comprehensive extraction (31 metrics)
            if ai_comments:
                print("🤖 Generating AI comments for all 31 metrics...")
                result = extract_comprehensive_with_ai(report_json, generate_comments=True)
                result['metadata']['ai_comments_enabled'] = True
            else:
                result = extract_comprehensive_metrics(report_json)
                result['metadata']['ai_comments_enabled'] = False

            result['metadata']['extraction_mode'] = 'comprehensive'
        else:
            # Use v1.0 basic extraction (6 metrics)
            if ai_comments:
                print("🤖 Generating AI comments for 6 basic metrics...")
                result = extract_anbil_data_with_ai_comments(report_json, generate_comments=True)
                result['metadata']['ai_comments_enabled'] = True
            else:
                result = extract_anbil_data(report_json)
                result['metadata']['ai_comments_enabled'] = False

            result['metadata']['extraction_mode'] = 'basic'

        # STEP 4: Add metadata about the fetch
        result['metadata']['report_id'] = report_id
        result['metadata']['fetched_from'] = report_url

        print(f"✅ Extraction complete!")

        return result

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={
            "success": False,
            "error": str(e),
            "message": f"Failed to extract anbil data from report {report_id}"
        })


@app.post("/upload/process")
async def upload_process_biennio(
    pdf_anno_corrente: UploadFile = File(...),
    pdf_anno_precedente: UploadFile = File(...)
):
    """
    Elabora due PDF (anno corrente + precedente) e ritorna confronto biennale con indicatori calcolati

    Args:
        pdf_anno_corrente: PDF dichiarazione anno corrente
        pdf_anno_precedente: PDF dichiarazione anno precedente

    Returns:
        JSON con:
        - data: Dati estratti dai PDF (biennio)
        - sommario: Confronto base (ricavi, reddito, ISA)
        - indicatori: Tutti gli indicatori finanziari calcolati
          - valutazione: NOPAT, EM Score, valutazione aziendale
          - finanziari: Debt management, cash generation
          - operativi: Leverage, produttività, asset turnover
          - economici: Costi fissi/variabili, break-even point
          - sostenibilita: ROE decomposition
    """
    # Validazione tipo file
    if not pdf_anno_corrente.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Il file anno corrente deve essere un PDF")
    if not pdf_anno_precedente.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Il file anno precedente deve essere un PDF")

    temp_corrente = None
    temp_precedente = None

    try:
        start_time = time.time()

        # Salva temporaneamente i file
        with tempfile.NamedTemporaryFile(delete=False, suffix='_corrente.pdf') as temp_file:
            content = await pdf_anno_corrente.read()
            temp_file.write(content)
            temp_corrente = temp_file.name

        with tempfile.NamedTemporaryFile(delete=False, suffix='_precedente.pdf') as temp_file:
            content = await pdf_anno_precedente.read()
            temp_file.write(content)
            temp_precedente = temp_file.name

        # Elabora anno corrente
        extractor_corrente = DichiarazioneExtractorMinimal(temp_corrente)
        dati_corrente_raw = extractor_corrente.estrai_dati_input()

        # Add small delay to avoid rate limits
        # With page filtering, each PDF uses ~10k tokens (vs 50k before)
        # Total: ~20k tokens for both PDFs - well under 50k/min limit
        # Small delay just to be safe
        delay_seconds = 10
        print(f"⏱️  Waiting {delay_seconds} seconds before processing second PDF...")
        print("   (Optimized: only analyzing ~6 pages per PDF instead of 28)")
        time.sleep(delay_seconds)

        # Elabora anno precedente
        extractor_precedente = DichiarazioneExtractorMinimal(temp_precedente)
        dati_precedente_raw = extractor_precedente.estrai_dati_input()

        extraction_time = (time.time() - start_time) * 1000  # Convert to ms

        # ✨ NEW: Add automatic validation and metadata
        dati_corrente = validate_and_enrich(dati_corrente_raw, extraction_time_ms=extraction_time/2)
        dati_precedente = validate_and_enrich(dati_precedente_raw, extraction_time_ms=extraction_time/2)

        # Crea struttura biennale
        dati_biennio = {
            "anno_corrente": dati_corrente,
            "anno_precedente": dati_precedente,
            "metadata": {
                "data_elaborazione": datetime.now().isoformat(),
                "pdf_corrente": pdf_anno_corrente.filename,
                "pdf_precedente": pdf_anno_precedente.filename
            }
        }

        # Converti Decimal in float per JSON
        def decimal_to_float(obj):
            from decimal import Decimal
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: decimal_to_float(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [decimal_to_float(i) for i in obj]
            return obj

        dati_json = decimal_to_float(dati_biennio)

        # Calcola sommario
        # Usa RICAVI TOTALI (F01 + altri componenti) per confronto più accurato
        ricavi_corr = float(dati_corrente['ricavi']['ricavi_dichiarati']) + float(dati_corrente['ricavi']['altri_componenti_positivi'])
        ricavi_prec = float(dati_precedente['ricavi']['ricavi_dichiarati']) + float(dati_precedente['ricavi']['altri_componenti_positivi'])
        var_ricavi = ((ricavi_corr - ricavi_prec) / ricavi_prec * 100) if ricavi_prec else 0

        reddito_corr = float(dati_corrente['risultati']['reddito_impresa'])
        reddito_prec = float(dati_precedente['risultati']['reddito_impresa'])

        isa_corr = dati_corrente['isa']['punteggio']
        isa_prec = dati_precedente['isa']['punteggio']

        sommario = {
            "ragione_sociale": dati_corrente['identificativi']['ragione_sociale'],
            "codice_fiscale": dati_corrente['identificativi']['codice_fiscale'],
            "confronto": {
                "ricavi": {
                    "anno_precedente": ricavi_prec,
                    "anno_corrente": ricavi_corr,
                    "variazione_percentuale": var_ricavi,
                    "dettaglio_corrente": {
                        "ricavi_dichiarati_f01": float(dati_corrente['ricavi']['ricavi_dichiarati']),
                        "altri_componenti_f02_f03_f05": float(dati_corrente['ricavi']['altri_componenti_positivi'])
                    },
                    "dettaglio_precedente": {
                        "ricavi_dichiarati_f01": float(dati_precedente['ricavi']['ricavi_dichiarati']),
                        "altri_componenti_f02_f03_f05": float(dati_precedente['ricavi']['altri_componenti_positivi'])
                    }
                },
                "reddito": {
                    "anno_precedente": reddito_prec,
                    "anno_corrente": reddito_corr
                },
                "isa": {
                    "anno_precedente": isa_prec,
                    "anno_corrente": isa_corr
                }
            }
        }

        # Calcola tutti gli indicatori usando ReportPFCalculator
        try:
            calculator = ReportPFCalculator(
                data_2023=dati_corrente,
                data_2022=dati_precedente
            )
            complete_report = calculator.generate_complete_report()
        except Exception as calc_error:
            print(f"Warning: Error calculating formulas: {calc_error}")
            complete_report = None

        # Cleanup
        os.unlink(temp_corrente)
        os.unlink(temp_precedente)

        # Check if either PDF is a Persona Fisica declaration
        is_pf_corrente = dati_corrente.get('_entity_type') == 'PF'
        is_pf_precedente = dati_precedente.get('_entity_type') == 'PF'
        is_persona_fisica = is_pf_corrente or is_pf_precedente

        # Extract validation results
        validation_corrente = dati_corrente.get('extraction_metadata', {}).get('validation', {})
        validation_precedente = dati_precedente.get('extraction_metadata', {}).get('validation', {})

        # Calculate overall quality score (minimum of both years)
        quality_score_corrente = dati_corrente.get('extraction_metadata', {}).get('quality_score', 1.0)
        quality_score_precedente = dati_precedente.get('extraction_metadata', {}).get('quality_score', 1.0)
        overall_quality = min(quality_score_corrente, quality_score_precedente)

        # Build response with validation info
        response_data = {
            "success": True,
            "entity_type": "PF" if is_persona_fisica else "SP",
            "data": dati_json,
            "sommario": sommario,
            "validation": {
                "overall_quality_score": round(overall_quality, 2),
                "needs_review": overall_quality < 0.80,
                "anno_corrente": {
                    "confidence": validation_corrente.get('confidence', 0),
                    "passed": validation_corrente.get('passed', False),
                    "warnings": validation_corrente.get('warnings', []),
                    "errors": validation_corrente.get('errors', []),
                    "checks_performed": validation_corrente.get('checks_performed', 0),
                    "checks_passed": validation_corrente.get('checks_passed', 0)
                },
                "anno_precedente": {
                    "confidence": validation_precedente.get('confidence', 0),
                    "passed": validation_precedente.get('passed', False),
                    "warnings": validation_precedente.get('warnings', []),
                    "errors": validation_precedente.get('errors', []),
                    "checks_performed": validation_precedente.get('checks_performed', 0),
                    "checks_passed": validation_precedente.get('checks_passed', 0)
                }
            },
            "extraction_info": {
                "extraction_time_ms": round(extraction_time, 2),
                "pdf_corrente": pdf_anno_corrente.filename,
                "pdf_precedente": pdf_anno_precedente.filename,
                "timestamp": datetime.now().isoformat()
            }
        }

        # Add warning flag if validation failed or quality is low
        if not validation_corrente.get('passed', False) or not validation_precedente.get('passed', False):
            response_data['warning'] = "⚠️ Validation issues detected - Manual review recommended"

        if is_persona_fisica:
            response_data['warning'] = "Dichiarazione Redditi Persone Fisiche rilevata - i dati finanziari aziendali non sono disponibili in questo tipo di dichiarazione"
            response_data['entity_type_note'] = "I PDF caricati sono dichiarazioni di persone fisiche, non di società di persone. Il report è stato generato con dati vuoti."
        elif overall_quality < 0.70:
            response_data['alert'] = "🔴 Low confidence extraction - Manual verification required"
        elif overall_quality < 0.80:
            response_data['warning'] = "🟡 Medium confidence extraction - Review recommended"

        # Aggiungi i calcoli se disponibili
        if complete_report:
            response_data["indicatori"] = decimal_to_float(complete_report)

        return JSONResponse(content=response_data)

    except Exception as e:
        # Cleanup in caso di errore
        if temp_corrente and os.path.exists(temp_corrente):
            try:
                os.unlink(temp_corrente)
            except:
                pass
        if temp_precedente and os.path.exists(temp_precedente):
            try:
                os.unlink(temp_precedente)
            except:
                pass

        raise HTTPException(
            status_code=500,
            detail=f"Errore durante l'elaborazione dei PDF: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 Avvio FastAPI Server - Report Società di Persone")
    print("="*60)
    print("\n📍 Server URL: http://localhost:8001")
    print("📖 API Docs: http://localhost:8001/docs")
    print("📄 ReDoc: http://localhost:8001/redoc")
    print("\n" + "="*60 + "\n")

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
