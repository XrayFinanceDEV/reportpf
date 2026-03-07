# NEW ENDPOINT: Extract ANBIL by Report ID

## 🎉 What's New

**Endpoint:** `POST /extract/anbil/by_report_id/{report_id}`

**Why it's better:**
- ✅ No need to paste entire JSON manually
- ✅ Just pass the report ID
- ✅ Fetches from main backend automatically
- ✅ Supports both comprehensive (31 metrics) and basic (6 metrics) modes
- ✅ Optional AI comments

---

## 🚀 Quick Start

### Option 1: Using Swagger UI (Easiest!)

1. **Open:** http://localhost:8001/docs
2. **Find:** `POST /extract/anbil/by_report_id/{report_id}`
3. **Click:** "Try it out"
4. **Fill in:**
   - `report_id`: `11`
   - `ai_comments`: `false` (or `true` if you have ANTHROPIC_API_KEY)
   - `comprehensive`: `true` (recommended - gets all 31 metrics)
   - `authorization`: Your Bearer token from main backend
5. **Click:** "Execute"

### Option 2: Using curl

```bash
# Without AI comments (fast)
curl -X POST "http://localhost:8001/extract/anbil/by_report_id/11?ai_comments=false&comprehensive=true&authorization=YOUR_TOKEN" \
  -H "accept: application/json" \
  | python3 -m json.tool

# With AI comments (requires ANTHROPIC_API_KEY in environment)
curl -X POST "http://localhost:8001/extract/anbil/by_report_id/11?ai_comments=true&comprehensive=true&authorization=YOUR_TOKEN" \
  -H "accept: application/json" \
  | python3 -m json.tool
```

### Option 3: From Your Main Backend (Python)

```python
import httpx

async def get_anbil_metrics(report_id: int, auth_token: str):
    """
    Fetch comprehensive ANBIL metrics for a report
    """
    url = f"http://localhost:8001/extract/anbil/by_report_id/{report_id}"

    params = {
        "ai_comments": True,  # Enable AI insights
        "comprehensive": True  # Get all 31 metrics
    }

    if auth_token:
        params["authorization"] = auth_token

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, params=params)
        response.raise_for_status()
        return response.json()

# Usage in your FastAPI endpoint
@app.post("/api/v1/reports/{report_id}/process_anbil")
async def process_anbil_report(report_id: int, current_user: User = Depends(get_current_user)):
    """
    Process a report and extract ANBIL metrics
    """
    # Get user's token
    token = current_user.token  # or however you store it

    # Call Report PF API
    anbil_data = await get_anbil_metrics(report_id, token)

    # Save enriched data to database
    await db.execute(
        "UPDATE reports SET anbil_extracted_data = :data WHERE id = :id",
        {"data": anbil_data, "id": report_id}
    )

    return anbil_data
```

---

## 📋 Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `report_id` | int | **Required** | Report ID from main backend |
| `ai_comments` | bool | `false` | Generate AI comments (needs ANTHROPIC_API_KEY) |
| `comprehensive` | bool | `true` | Use v2.0 extraction (31 metrics) vs v1.0 (6 metrics) |
| `authorization` | string | `null` | Bearer token for main backend auth |
| `main_backend_url` | string | `https://kpsfinanciallab.w3pro.it:8000` | Main backend URL |

---

## 📊 Response Structure

### Comprehensive Mode (31 metrics) - RECOMMENDED

```json
{
  "success": true,
  "data": {
    "company_name": "I.T.C. S.R.L.",
    "years": [
      {
        "year": "2024",

        // ECONOMIC INDICATORS (6)
        "revenue": 15130120.0,
        "ebitda": 2245257.0,
        "costi_materia_prima": 10109091.0,
        "costi_servizi": 1570681.0,
        "costi_personale": 1226685.0,
        "costi_oneri_finanziari": 191499.0,

        // PROFITABILITY RATIOS (3)
        "roi": 11.01,
        "roe": 12.74,
        "ros": 10.65,

        // BALANCE SHEET (4)
        "attivo_immobilizzato": 4720368.0,
        "rimanenze": 2837632.0,
        "crediti_verso_clienti": 2247142.0,
        "debiti_verso_fornitori": 1707841.0,

        // DEBT SUSTAINABILITY (4)
        "pfn": 680112.0,
        "pfn_ebitda_ratio": 0.0,
        "costo_del_debito": 3.98,
        "oneri_finanziari_mol": 6.4,

        // CAPITAL STRUCTURE (5)
        "patrimonio_netto": 8700929.0,
        "totale_attivo": 14760690.0,
        "patrimonio_netto_attivo": 58.95,
        "passivo_corrente": 3401070.0,
        "totale_passivo": 14760690.0,
        "passivo_corrente_totale_passivo": 23.04,

        // CASH FLOW & COVERAGE (2)
        "cash_flow": 2245257.0,
        "fccr": 11.72
      },
      // 2023 data...
      // 2022 data...
    ],

    // AI COMMENTS (if ai_comments=true)
    "ai_comments": {
      "revenue": "Ricavi in contrazione...",
      "ebitda": "EBITDA in significativo calo...",
      "roi": "ROI in forte calo...",
      "roe": "ROE diminuito...",
      "ros": "ROS in contrazione...",
      "attivo_immobilizzato": "...",
      "rimanenze": "...",
      "crediti_verso_clienti": "...",
      "debiti_verso_fornitori": "...",
      "pfn_ebitda_ratio": "...",
      "costo_del_debito": "...",
      "oneri_finanziari_mol": "...",
      "patrimonio_netto_attivo": "...",
      "passivo_corrente_totale_passivo": "...",
      "cash_flow": "...",
      "fccr": "...",
      "profilo_economico_overall": "Profilo aziendale complessivo..."  ← SYNTHESIS
    }
  },
  "metadata": {
    "report_id": 11,
    "fetched_from": "https://kpsfinanciallab.w3pro.it:8000/api/v1/reports/11",
    "extraction_mode": "comprehensive",
    "metrics_extracted": 31,
    "ai_comments_enabled": true,
    "company_name": "I.T.C. S.R.L.",
    "years_count": 3,
    "years_available": ["2024", "2023", "2022"]
  }
}
```

---

## 🔒 Authentication

The endpoint needs to authenticate with your main backend. You have two options:

### Option 1: Pass Bearer Token (Recommended)
```bash
curl -X POST "http://localhost:8001/extract/anbil/by_report_id/11?authorization=YOUR_BEARER_TOKEN&comprehensive=true"
```

### Option 2: Make Endpoint Public (For Internal Use Only!)
If the Report PF API runs on the same network as your main backend, you could:
1. Add an internal API key to your main backend
2. Or whitelist the Report PF API IP address
3. Or use a service account token

---

## 🎯 Integration Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ USER REQUESTS REPORT                                         │
├─────────────────────────────────────────────────────────────┤
│ Frontend → Main Backend:                                    │
│   POST /api/v1/reports/new                                  │
│   { module_id: 2, input_data: {...} }                       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ MAIN BACKEND FETCHES ITC REPORT                             │
├─────────────────────────────────────────────────────────────┤
│ Main Backend → ITC API: Get balance analysis               │
│ ITC API → Main Backend: Returns full report JSON           │
│                                                             │
│ Main Backend saves:                                        │
│   reports.api_response = <ITC JSON>                        │
│   reports.status = "completed"                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ MAIN BACKEND CALLS REPORT PF API                           │
├─────────────────────────────────────────────────────────────┤
│ Main Backend → Report PF API:                              │
│   POST /extract/anbil/by_report_id/11                      │
│   ?ai_comments=true&comprehensive=true&authorization=TOKEN  │
│                                                             │
│ Report PF API:                                             │
│   1. Fetches report from main backend                      │
│   2. Extracts 31 metrics                                   │
│   3. Generates 22 AI comments                              │
│   4. Returns enriched JSON                                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ MAIN BACKEND SAVES ENRICHED DATA                           │
├─────────────────────────────────────────────────────────────┤
│ Main Backend saves:                                        │
│   reports.anbil_extracted_data = <enriched JSON>           │
│                                                             │
│ Database now has:                                          │
│   - api_response: Original ITC report                      │
│   - anbil_extracted_data: 31 metrics + 22 AI comments      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND DISPLAYS REPORT                                    │
├─────────────────────────────────────────────────────────────┤
│ Frontend → Main Backend: GET /api/v1/reports/11            │
│ Main Backend → Frontend: Returns both JSONs                │
│                                                             │
│ Frontend renders:                                          │
│   http://localhost:3000/anbil/11                           │
│   - All 31 metrics with 3-year trends                     │
│   - 22 AI insights (250 chars each)                       │
│   - Overall synthesis comment                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔥 Comparison: Old vs New

### OLD Way (Manual JSON)
```bash
# Step 1: Get report from main backend
curl https://kpsfinanciallab.w3pro.it:8000/api/v1/reports/11 > report.json

# Step 2: Manually copy the entire JSON

# Step 3: Paste into Swagger UI (huge JSON, hard to read)
POST /extract/anbil
Body: { "api_response": { ... 10,000 lines ... } }
```

### NEW Way (By Report ID) ✨
```bash
# Just pass the ID!
curl -X POST "http://localhost:8001/extract/anbil/by_report_id/11?authorization=TOKEN&comprehensive=true"
```

**Benefits:**
- ✅ No manual JSON copying
- ✅ Cleaner Swagger UI
- ✅ Easier testing
- ✅ Better for automated workflows
- ✅ Handles auth automatically

---

## 🧪 Testing

### Test 1: Basic Extraction (Fast)
```bash
curl -X POST "http://localhost:8001/extract/anbil/by_report_id/11?ai_comments=false&comprehensive=true&authorization=YOUR_TOKEN"
```

**Expected:** JSON with 31 metrics, no AI comments (~100ms)

### Test 2: With AI Comments (Requires ANTHROPIC_API_KEY)
```bash
export ANTHROPIC_API_KEY="sk-ant-..."

curl -X POST "http://localhost:8001/extract/anbil/by_report_id/11?ai_comments=true&comprehensive=true&authorization=YOUR_TOKEN"
```

**Expected:** JSON with 31 metrics + 22 AI comments (~10-15 seconds)

### Test 3: Legacy Mode (6 metrics only)
```bash
curl -X POST "http://localhost:8001/extract/anbil/by_report_id/11?comprehensive=false&authorization=YOUR_TOKEN"
```

**Expected:** JSON with only 6 basic metrics (v1.0 compatibility)

---

## 📞 Troubleshooting

### Error: "Not authenticated"
**Solution:** Add `authorization` parameter with your Bearer token
```bash
?authorization=YOUR_BEARER_TOKEN
```

### Error: "Failed to fetch report from main backend"
**Solution:** Check:
1. Main backend is running: https://kpsfinanciallab.w3pro.it:8000
2. Report ID exists and has data
3. Authorization token is valid

### Error: "Report does not contain 'api_response' field"
**Solution:** Report hasn't been processed yet or ITC data is missing

### No AI comments in response
**Solution:** Set `ANTHROPIC_API_KEY` environment variable:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## 🎉 Summary

**You can now:**
1. ✅ Call the endpoint with just a report ID (no manual JSON!)
2. ✅ Get all 31 comprehensive metrics automatically
3. ✅ Optionally generate 22 AI comments
4. ✅ Use it directly in Swagger UI for testing
5. ✅ Integrate easily in your main backend

**Try it now:** http://localhost:8001/docs → `POST /extract/anbil/by_report_id/{report_id}`

---

*Created: 2025-12-09*
*Version: 2.0*
