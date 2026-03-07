# Report PF (Società di Persone) - Integration Plan

## Executive Summary

This document outlines the complete integration plan for the **Report PF** (Partnership/Società di Persone financial analysis report) into the Formula Finance application. The report processes tax declaration PDFs from two consecutive years to generate comprehensive financial analysis.

**Current Status:**
- ✅ FastAPI backend with file upload endpoint at `https://kpsfinanciallab.w3pro.it:8000/apiServerIt`
- ✅ Frontend mockup complete at `/reportpf` with full data visualization
- ✅ TypeScript types defined
- ✅ Module registered in backend (module_id: 4)
- ⚠️ Frontend integration with file upload workflow pending

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Flow                                     │
└─────────────────────────────────────────────────────────────────┘

1. User navigates to /reports/new
2. Selects "Report Società di Persone" module (module_id: 4)
3. Upload dialog appears requesting 2 PDF files:
   - Year N (current year tax declaration - 2024)
   - Year N-1 (previous year tax declaration - 2023)
4. PDFs uploaded to FastAPI backend → receives file paths
5. Report created with file paths in input_data
6. Report row appears in /reports with "pending" status
7. Backend processes PDFs asynchronously (~1 minute)
8. Report status changes to "completed" with api_response JSON
9. User clicks report → opens at /reports/{id}
10. Full financial report displayed with all sections
```

---

## 1. Module Registration

### 1.1 Add New Module to Database

**Module Data:**
```json
{
  "name": "societa_persone",
  "display_name": "Report Società di Persone",
  "description": "Analisi finanziaria biennale per società di persone ordinarie basata su dichiarazioni fiscali ISA",
  "report_type": "report_pf",
  "is_active": true,
  "credits_required": 1
}
```

**SQL (if needed):**
```sql
INSERT INTO modules (name, display_name, description, report_type, is_active, credits_required)
VALUES (
  'societa_persone',
  'Report Società di Persone',
  'Analisi finanziaria biennale per società di persone ordinarie basata su dichiarazioni fiscali ISA',
  'report_pf',
  true,
  1
);
```

### 1.2 Module Icon Mapping

**File:** `app/reports/new/page.tsx`

Add icon mapping:
```typescript
const moduleIcons = {
  de_minimis: IconReportMoney,
  group_de_minimis: IconReportMoney,
  balance_analysis: IconChartBar,
  analisi_bilancio: IconChartBar,
  cr_analysis: IconFileText,
  societa_persone: IconBuildingBank, // NEW
};
```

---

## 2. Frontend Integration

### 2.1 Report Request Flow (`/reports/new`)

**File:** `app/reports/new/page.tsx`

#### Changes Required:

1. **Add PDF Upload State:**
```typescript
const [pdfAnnoCurrent, setPdfAnnoCurrent] = useState<File | null>(null);
const [pdfAnnoPrecedente, setPdfAnnoPrecedente] = useState<File | null>(null);
```

2. **Update Module Click Handler:**
```typescript
const handleRequestClick = (module: any) => {
  setSelectedModule(module);

  // Report PF requires PDF upload, skip confirmation
  if (module.name === 'societa_persone') {
    setShowFormDialog(true);
  } else if (module.name === 'group_de_minimis') {
    setReportMode('bulk');
    setShowFormDialog(true);
  } else {
    setReportMode('single');
    setShowConfirmDialog(true);
  }
};
```

3. **Add PDF Upload UI in Form Dialog:**
```typescript
{selectedModule?.name === 'societa_persone' ? (
  <>
    <div className="grid gap-2">
      <Label htmlFor="pdf_anno_corrente">
        Dichiarazione Anno Corrente (PDF) <span className="text-destructive">*</span>
      </Label>
      <Input
        id="pdf_anno_corrente"
        type="file"
        accept=".pdf"
        onChange={(e) => setPdfAnnoCurrent(e.target.files?.[0] || null)}
        required
      />
      <p className="text-xs text-muted-foreground">
        Dichiarazione fiscale modello ISA dell'anno più recente (es. 2024)
      </p>
    </div>
    <div className="grid gap-2">
      <Label htmlFor="pdf_anno_precedente">
        Dichiarazione Anno Precedente (PDF) <span className="text-destructive">*</span>
      </Label>
      <Input
        id="pdf_anno_precedente"
        type="file"
        accept=".pdf"
        onChange={(e) => setPdfAnnoPrecedente(e.target.files?.[0] || null)}
        required
      />
      <p className="text-xs text-muted-foreground">
        Dichiarazione fiscale modello ISA dell'anno precedente (es. 2023)
      </p>
    </div>
  </>
) : (
  // ... existing form fields
)}
```

4. **Update Submit Handler:**
```typescript
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();

  if (!selectedModule) {
    toast.error('Nessun modulo selezionato');
    return;
  }

  // Handle Report PF submission
  if (selectedModule.name === 'societa_persone') {
    if (!pdfAnnoCurrent || !pdfAnnoPrecedente) {
      toast.error('Inserisci entrambi i file PDF');
      return;
    }

    try {
      // Step 1: Upload PDFs to temporary backend (port 8001)
      const formData = new FormData();
      formData.append('pdf_anno_corrente', pdfAnnoCurrent);
      formData.append('pdf_anno_precedente', pdfAnnoPrecedente);

      const uploadResponse = await fetch('http://localhost:8001/upload/process', {
        method: 'POST',
        body: formData,
      });

      if (!uploadResponse.ok) {
        throw new Error('Errore durante l\'elaborazione dei PDF');
      }

      const extractedData = await uploadResponse.json();

      // Step 2: Create report in main backend with extracted data
      await createReport({
        module_id: selectedModule.id,
        report_type: 'report_pf',
        input_data: {
          pdf_anno_corrente: pdfAnnoCurrent.name,
          pdf_anno_precedente: pdfAnnoPrecedente.name,
          codice_fiscale: extractedData.data?.anno_corrente?.identificativi?.codice_fiscale || '',
        },
        api_response: extractedData.data, // Store the extracted JSON
      });

      setShowFormDialog(false);
      setPdfAnnoCurrent(null);
      setPdfAnnoPrecedente(null);

      toast.success('Report Società di Persone richiesto con successo!');

      setTimeout(() => {
        router.push('/reports');
      }, 2000);
      return;
    } catch (error: any) {
      const errorMessage = error?.message || 'Errore nella creazione del report';
      toast.error(errorMessage);
      console.error('Report PF creation error:', error);
      return;
    }
  }

  // ... existing submission logic for other report types
};
```

### 2.2 Report List Display (`/reports`)

**File:** `app/reports/page.tsx`

**No changes required** - the existing report listing will automatically show Report PF entries when created.

### 2.3 Report Detail View (`/reports/[id]`)

**File:** `app/reports/[id]/page.tsx`

#### Changes Required:

1. **Add Report Type Detection:**
```typescript
const isPFReport = report.report_type === 'report_pf' || report.report_type === 'societa_persone';
```

2. **Add Rendering Logic (already exists):**
```typescript
// Around line 455
if (isPFReport && report.status === 'completed' && report.api_response) {
  // Prepare the report data for the ReportPF component
  const reportData = {
    ...report,
    input_data: {
      codice_fiscale: report.input_data?.cf || report.input_data?.codice_fiscale || '',
      ...report.input_data,
    },
    api_response: report.api_response,
  };

  return (
    <AuthGuard>
      <SidebarProvider>
        <AppSidebar variant="inset" />
        <SidebarInset>
          <SiteHeader />
          <ReportPF report={reportData} />
        </SidebarInset>
      </SidebarProvider>
    </AuthGuard>
  );
}
```

---

## 3. Backend API Requirements

### 3.1 File Upload Endpoint

**Base URL:** `https://kpsfinanciallab.w3pro.it:8000/apiServerIt`

**Status:** ✅ Already exists

**Endpoint:** `POST /api/user_files/upload`

**Documentation:** [Swagger UI](https://kpsfinanciallab.w3pro.it:8000/apiServerIt/docs#/user_files/upload_user_file_api_user_files_upload_post)

**Request:**
- Content-Type: `multipart/form-data`
- Authentication: JWT token (required)
- Body: `file`: File (PDF)

**Response:**
```json
{
  "file_path": "app\\report_files\\1\\USP UNICO REDDITI TESSITURA 2024.pdf",
  "file_id": 123,
  "filename": "USP UNICO REDDITI TESSITURA 2024.pdf"
}
```

**Usage:**
- Upload each PDF file separately
- Call twice: once for 2024 declaration, once for 2023 declaration
- Save both file paths for report creation

### 3.2 Main Backend - Report Creation

#### 3.2.1 Module Management

**Endpoint:** `GET /api/v1/modules/`

**Status:** ✅ Already exists

**Required:** Add "societa_persone" module to database

---

#### 3.2.2 Report Creation

**Endpoint:** `POST /api/v1/reports/new`

**Documentation:** [Swagger UI](https://kpsfinanciallab.w3pro.it:8000/apiServerIt/docs#/reports/create_report_endpoint_api_v1_reports_new_post)

**Status:** ✅ Already works with async processing

**Request Format:**
```json
{
  "module_id": 4,
  "report_type": "report_pf",
  "input_data": {
    "pdf_previous_path": "app\\report_files\\1\\USP UNICO REDDITI TESSITURA 2023.pdf",
    "pdf_current_path": "app\\report_files\\1\\USP UNICO REDDITI TESSITURA 2024.pdf"
  }
}
```

**Response:**
```json
{
  "report_id": 456,
  "status": "pending",
  "created_at": "2025-12-03T10:30:00Z"
}
```

**Processing Flow:**
1. Report is created with status "pending"
2. Backend processes PDFs asynchronously (~1 minute)
3. When complete, report status → "completed"
4. `api_response` field populated with extracted JSON data
5. Frontend can poll or fetch report to check status

---

#### 3.2.3 Report Retrieval

**Endpoint:** `GET /api/v1/reports/{report_id}`

**Status:** ✅ Already exists

**No changes required** - will return report with `api_response` containing the extracted financial data.

---

#### 3.2.4 Report Deletion

**Endpoint:** `DELETE /api/v1/reports/{report_id}`

**Status:** ✅ Already exists

**Note:** The backend should handle PDF file cleanup automatically when a report is deleted.

---

## 4. Data Flow Diagram

```
┌──────────────┐
│    User      │
│  /reports/   │
│     new      │
└──────┬───────┘
       │
       │ 1. Selects "Report Società di Persone" (module_id: 4)
       │ 2. Uploads 2 PDF files (2024 and 2023)
       │
       v
┌──────────────────────────────────────────┐
│   Frontend (Next.js)                     │
│   - Validates PDFs (type, size)          │
│   - Shows loading state                  │
└──────┬───────────────────────────────────┘
       │
       │ 3. POST /api/user_files/upload (File 1: 2024)
       │ 4. POST /api/user_files/upload (File 2: 2023)
       │    (with authentication token)
       v
┌──────────────────────────────────────────┐
│   FastAPI Backend (Port 8000)            │
│   - Stores PDF in user's folder          │
│   - Returns file_path for each PDF      │
└──────┬───────────────────────────────────┘
       │
       │ 5. Returns:
       │    { "file_path": "app\\report_files\\1\\..." }
       │
       v
┌──────────────────────────────────────────┐
│   Frontend (Next.js)                     │
│   - Collects both file paths             │
└──────┬───────────────────────────────────┘
       │
       │ 6. POST /api/v1/reports/new
       │    {
       │      module_id: 4,
       │      report_type: "report_pf",
       │      input_data: {
       │        pdf_previous_path: "...",
       │        pdf_current_path: "..."
       │      }
       │    }
       v
┌──────────────────────────────────────────┐
│   FastAPI Backend (Port 8000)            │
│   - Creates report record                │
│   - Status: "pending"                    │
│   - Starts async PDF processing          │
└──────┬───────────────────────────────────┘
       │
       │ 7. Returns: { "report_id": 456, "status": "pending" }
       │
       v
┌──────────────────────────────────────────┐
│   Frontend (Next.js)                     │
│   - Shows success toast                  │
│   - Redirects to /reports                │
└──────┬───────────────────────────────────┘
       │
       │ 8. Backend processes PDFs (~1 minute)
       │    - Extracts financial data
       │    - Updates report status → "completed"
       │    - Stores JSON in api_response field
       │
       │ 9. User clicks report row (after processing)
       │
       v
┌──────────────────────────────────────────┐
│   /reports/[id]                          │
│   - Fetches report data                  │
│   - Detects report_type = "report_pf"    │
│   - Checks status = "completed"          │
│   - Renders <ReportPF> component         │
│   - Displays api_response JSON data      │
└──────────────────────────────────────────┘
```

---

## 5. Backend Endpoints Summary

### 5.1 Main Backend (Port 8000) Status

| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| `/api/user_files/upload` | POST | ✅ Ready | Upload PDF files, returns file_path |
| `/api/v1/reports/new` | POST | ✅ Ready | Create report with async processing |
| `/api/v1/modules/` | GET | ✅ Ready | Get available modules (includes module_id: 4) |
| `/api/v1/reports/{id}` | GET | ✅ Ready | Get report details with api_response |
| `/api/v1/reports/user/me` | GET | ✅ Ready | Get user's reports list |
| `/api/v1/reports/{id}` | DELETE | ✅ Ready | Delete report (includes file cleanup) |

---

## 6. Frontend Files to Modify

| File | Changes Required | Complexity |
|------|------------------|------------|
| `app/reports/new/page.tsx` | Add PDF upload UI, submission logic | **HIGH** |
| `app/reports/[id]/page.tsx` | ✅ Already handles Report PF | - |
| `components/reports/report-pf.tsx` | ✅ Already complete | - |
| `types/report-pf.ts` | ✅ Already complete | - |
| `lib/dati-test-pf.ts` | ✅ Already complete (for testing) | - |

### 6.1 Detailed Changes for `/reports/new`

**File:** `app/reports/new/page.tsx`

**Lines to Add/Modify:** ~50-100 lines

**Key Changes:**
1. Import `useState` for PDF file management
2. Add state variables for 2 PDF files
3. Update `handleRequestClick` to detect Report PF module
4. Add PDF upload inputs in dialog form
5. Update `handleSubmit` to:
   - Upload PDF 2024 to `/api/user_files/upload` → save file_path
   - Upload PDF 2023 to `/api/user_files/upload` → save file_path
   - Create report with both file paths in `input_data`
   - Show success message and redirect to /reports
6. Add file validation (PDF only, max 50MB)
7. Add loading states during PDF upload and report creation
8. Handle async processing (report starts as "pending")

---

## 7. Testing Checklist

### 7.1 Unit Testing

- [ ] Test PDF upload validation (file type, size)
- [ ] Test extraction service response handling
- [ ] Test report creation with `api_response`
- [ ] Test Report PF component rendering with mock data

### 7.2 Integration Testing

- [ ] Upload 2 valid PDFs → Both files uploaded successfully
- [ ] Receive file paths from backend
- [ ] Report created with status "pending"
- [ ] Upload invalid file → Error message shown
- [ ] Report appears in `/reports` list with "pending" status
- [ ] After ~1 minute, report status changes to "completed"
- [ ] Click report → Opens detail view with all sections
- [ ] All financial ratios calculated correctly
- [ ] Balance sheet balances (Assets = Liabilities)
- [ ] Charts render correctly (Recharts)
- [ ] Italian number formatting (€ symbols, decimals)

### 7.3 E2E Testing

- [ ] Complete user flow from `/reports/new` to `/reports/{id}`
- [ ] Test with real tax declaration PDFs
- [ ] Verify data accuracy against source PDFs
- [ ] Test error scenarios (network failure, invalid PDF)
- [ ] Test concurrent report creation
- [ ] Test report deletion (including PDF cleanup)

---

## 8. Implementation Plan

### 8.1 Current Status

- ✅ Backend APIs deployed and ready at `https://kpsfinanciallab.w3pro.it:8000/apiServerIt`
- ✅ File upload endpoint working
- ✅ Report creation with async processing working
- ✅ Module registered (module_id: 4)
- ✅ Frontend mockup complete at `/reportpf`
- ⚠️ Frontend integration pending

### 8.2 Remaining Tasks

| Task | Complexity | Status |
|------|------------|--------|
| Update `/reports/new` page with PDF upload UI | Medium | Pending |
| Implement file upload to FastAPI backend | Medium | Pending |
| Handle async report processing in UI | Low | Pending |
| Add loading states and error handling | Low | Pending |
| E2E testing with Playwright | Medium | Pending |
| Documentation updates | Low | Pending |

---

## 9. Security Considerations

### 9.1 PDF Upload

- ✅ Validate file type (PDF only)
- ✅ Limit file size (50MB max)
- ✅ Scan for malware (integrate with antivirus)
- ✅ Rate limit uploads (5 per user per hour)
- ✅ Store PDFs outside web root

### 9.2 Data Access

- ✅ Verify report ownership before display
- ✅ Implement role-based access (intermediario can see child reports)
- ✅ Sanitize extracted data before storage
- ✅ Audit log for sensitive operations

### 9.3 API Security

- ✅ Authentication required (JWT)
- ✅ HTTPS only in production
- ✅ CORS configuration
- ✅ Input validation on all endpoints

---

## 10. Performance Optimization

### 10.1 PDF Processing

- **Current:** Synchronous processing (blocks until complete)
- **Improvement:** Implement async processing with queue (Celery/RQ)
- **Benefit:** User doesn't wait for PDF extraction

### 10.2 Caching

- Cache extracted data in Redis
- Cache report list queries
- Implement pagination (already done)

### 10.3 File Storage

- Use object storage (S3/MinIO) instead of local filesystem
- Implement CDN for PDF downloads
- Compress PDFs before storage (if size >5MB)

---

## 11. Future Enhancements

### 11.1 Short Term (1-3 months)

- [ ] PDF download button (regenerate PDF from JSON)
- [ ] Export to Excel
- [ ] Email notification when report completes
- [ ] Comparative analysis (compare with industry averages)

### 11.2 Long Term (3-6 months)

- [ ] Support for other ISA models (beyond DG37U)
- [ ] Bulk processing (upload 10+ company PDFs at once)
- [ ] Trend analysis (3+ years of data)
- [ ] AI-powered insights and recommendations
- [ ] White-label PDF export with company branding

---

## 12. Rollback Plan

If issues arise after deployment:

1. **Frontend Rollback:**
   - Revert changes to `/reports/new`
   - Hide "Report Società di Persone" module (set `is_active = false`)

2. **Backend Rollback:**
   - Revert `POST /api/v1/reports/new` changes
   - Remove PDF upload endpoint

3. **Data Cleanup:**
   - Mark all Report PF reports as "failed"
   - Delete orphaned PDF files

---

## 13. Documentation Requirements

### 13.1 User Documentation

- [ ] How to upload tax declarations
- [ ] Understanding the financial report sections
- [ ] Troubleshooting guide (invalid PDF, missing data)

### 13.2 Developer Documentation

- [ ] API endpoint specifications (OpenAPI/Swagger)
- [ ] Data flow diagrams
- [ ] Database schema changes
- [ ] Error codes and handling

### 13.3 Operations Documentation

- [ ] Deployment procedure
- [ ] Monitoring and alerts
- [ ] Backup and recovery
- [ ] PDF storage cleanup scripts

---

## 14. Success Metrics

### 14.1 Technical Metrics

- Report creation success rate: >95%
- PDF processing time: <30 seconds (average)
- API response time: <500ms
- Error rate: <5%
- Uptime: >99.5%

### 14.2 Business Metrics

- Reports created per day: Track growth
- User satisfaction: Survey after first use
- Support tickets: Monitor for issues
- Credit consumption: Track module popularity

---

## 15. Contact & Support

**Development Team:**
- Frontend: Next.js team
- Backend: FastAPI/Python team
- DevOps: Deployment & infrastructure

**Issue Tracking:**
- GitHub Issues: [repository link]
- Slack Channel: #report-pf-integration

**Documentation:**
- Technical Docs: `/docs/report-pf/`
- User Guide: `/help/report-societa-persone`

---

## Appendix A: API Response Schema

### DatiBiennio (Complete Structure)

```typescript
interface DatiBiennio {
  anno_corrente: DatiAnno;
  anno_precedente: DatiAnno;
  metadata?: {
    data_elaborazione: string;
    pdf_corrente: string;
    pdf_precedente: string;
  };
}

interface DatiAnno {
  identificativi: {
    codice_fiscale: string;
    partita_iva: string;
    ragione_sociale: string;
    anno: number;
  };
  ricavi: {
    ricavi_dichiarati: number;
    altri_componenti_positivi: number;
  };
  costi: {
    esistenze_iniziali: number;
    rimanenze_finali: number;
    costo_materie_prime: number;
    costo_servizi: number;
    godimento_beni_terzi: number;
    costo_personale: number;
    spese_collaboratori: number;
    ammortamenti: number;
    accantonamenti: number;
    altri_costi: number;
    oneri_finanziari: number;
  };
  risultati: {
    valore_aggiunto: number;
    mol: number;
    reddito_operativo: number;
    reddito_impresa: number;
  };
  personale: {
    giornate_dipendenti: number;
    giornate_altro_personale: number;
    numero_addetti_equivalenti: number;
  };
  patrimonio: {
    valore_beni_strumentali: number;
  };
  isa: {
    punteggio: number;
    modello_applicato: string;
    ricavi_per_addetto: number;
    valore_aggiunto_per_addetto: number;
    reddito_per_addetto: number;
  };
  quadro_rs: {
    rimanenze: number;
    crediti_clienti: number;
    altri_crediti: number;
    attivita_finanziarie: number;
    disponibilita_liquide: number;
    ratei_risconti_attivi: number;
    totale_attivo: number;
    patrimonio_netto: number;
    debiti_banche_breve: number;
    debiti_banche_lungo: number;
    debiti_fornitori: number;
    altri_debiti: number;
    ratei_risconti_passivi: number;
  };
}
```

---

## Appendix B: Extracted Fields Reference

Total fields extracted: **43 fields** (100% coverage)

### Field Categories:

1. **Identificativi** (4 fields): Company identification
2. **Ricavi** (2 fields): Revenue data
3. **Costi** (11 fields): Cost structure
4. **Risultati** (4 fields): Financial results
5. **Personale** (3 fields): Personnel metrics
6. **Patrimonio** (1 field): Fixed assets
7. **ISA** (5 fields): Tax compliance indicators
8. **Quadro RS** (13 fields): Balance sheet data

See `reportpf/FIELD_MAPPING.md` for complete field documentation.

---

**Document Version:** 1.0
**Last Updated:** 2025-11-21
**Status:** Ready for Implementation
