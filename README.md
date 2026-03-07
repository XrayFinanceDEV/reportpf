# Report Società di Persone - PDF Data Extractor

Estrattore di dati INPUT da PDF di dichiarazioni fiscali per società di persone ordinarie.

## Descrizione

Questo progetto estrae i dati necessari dalle dichiarazioni fiscali PDF (modelli ISA per società di persone) e li converte in formato JSON strutturato per essere utilizzati nella generazione di report finanziari.

### Dati Estratti

Il sistema estrae automaticamente:

1. **Identificativi**: Codice fiscale, P.IVA, Ragione sociale, Anno
2. **Ricavi**: Ricavi dichiarati (F01) e altri componenti positivi
3. **Costi**:
   - Esistenze iniziali/rimanenze finali (F08, F09)
   - Costo materie prime (F10)
   - Costo servizi (F12)
   - Costo personale (F14)
   - Ammortamenti (F15)
   - Altri costi e oneri finanziari
4. **Risultati**: Valore aggiunto, MOL, Reddito operativo, Reddito d'impresa
5. **Personale**: Giornate dipendenti, addetti equivalenti
6. **ISA**: Punteggio, modello applicato, indicatori elementari

## Setup

### 1. Creazione Virtual Environment

```bash
cd /reportpf
python3 -m venv venv
```

### 2. Attivazione Virtual Environment

```bash
# Su Linux/Mac:
source venv/bin/activate

# Su Windows:
venv\Scripts\activate
```

### 3. Installazione Dipendenze

```bash
pip install -r requirements.txt
```

## Utilizzo

### Opzione 1: API Server (Raccomandato)

#### Avvio del Server

```bash
./start_server.sh
```

Il server FastAPI sarà disponibile su:
- **API Base**: http://localhost:8001
- **Swagger UI**: http://localhost:8001/docs (interfaccia interattiva)
- **ReDoc**: http://localhost:8001/redoc (documentazione API)

#### Endpoints Disponibili

1. **POST /upload/single** - Elabora un singolo PDF
   - Upload: 1 file PDF
   - Ritorna: Dati estratti in formato JSON

2. **POST /upload/process** - Elabora biennio (2 PDF)
   - Upload: 2 file PDF (anno corrente + anno precedente)
   - Ritorna: Confronto biennale completo con sommario

3. **GET /health** - Health check del server

#### Test con curl

```bash
# Test singolo PDF
curl -X POST http://localhost:8001/upload/single \
  -F "pdf_file=@dichiarazione_2024.pdf" \
  -o output.json

# Test biennio
curl -X POST http://localhost:8001/upload/process \
  -F "pdf_anno_corrente=@dichiarazione_2024.pdf" \
  -F "pdf_anno_precedente=@dichiarazione_2023.pdf" \
  -o output_biennio.json
```

#### Test con script Python

```bash
# Test singolo PDF
python test_api.py single dichiarazione_2024.pdf

# Test biennio
python test_api.py biennio dichiarazione_2024.pdf dichiarazione_2023.pdf
```

### Opzione 2: Script Command Line

Per elaborare due PDF (anno corrente e anno precedente) e generare un JSON comparativo:

```bash
python extdichiarazione.py <pdf_anno_corrente> <pdf_anno_precedente> [output.json]
```

**Esempio:**

```bash
# Usando il venv
./venv/bin/python extdichiarazione.py dichiarazione_2024.pdf dichiarazione_2023.pdf dati_biennio.json

# Oppure con venv attivo
python extdichiarazione.py dichiarazione_2024.pdf dichiarazione_2023.pdf dati_biennio.json
```

Se non specifichi il nome del file di output, verrà creato automaticamente `dati_biennio.json`.

### Output

Il programma genererà:
- Un file JSON con tutti i dati estratti strutturati per anno corrente e precedente
- Un sommario a video con i principali indicatori:
  - Confronto ricavi con variazione percentuale
  - Confronto reddito
  - Confronto punteggio ISA

## Struttura Output JSON

```json
{
  "anno_corrente": {
    "identificativi": {
      "codice_fiscale": "...",
      "partita_iva": "...",
      "ragione_sociale": "...",
      "anno": 2024
    },
    "ricavi": {
      "ricavi_dichiarati": 453463.0,
      "altri_componenti_positivi": 22.0
    },
    "costi": { ... },
    "risultati": { ... },
    "personale": { ... },
    "isa": { ... }
  },
  "anno_precedente": { ... },
  "metadata": {
    "data_elaborazione": "2024-11-21T10:57:00",
    "pdf_corrente": "...",
    "pdf_precedente": "..."
  }
}
```

## File del Progetto

- `extdichiarazione.py` - Script principale di estrazione (CLI)
- `api_server.py` - FastAPI server per elaborazione via HTTP
- `test_api.py` - Script di test per l'API
- `start_server.sh` - Script di avvio del server FastAPI
- `requirements.txt` - Dipendenze Python
- `report-soc-persone.md` - Documentazione schema dati e formule
- `SCHEMA SOCIETA' DI PERSONE ORDINARIA.docx` - Schema template report
- `SOCIETA' DI PERSONE ORDINARIA.pdf` - PDF di esempio
- `venv/` - Virtual environment Python

## Dipendenze

- Python >= 3.8
- pdfplumber >= 0.11.0 (estrazione dati da PDF)
- fastapi >= 0.104.0 (API server)
- uvicorn >= 0.24.0 (ASGI server)
- python-multipart >= 0.0.6 (upload file)
- requests >= 2.31.0 (client HTTP per testing)

## Note Tecniche

### Pattern di Estrazione

Il sistema utilizza regex per identificare i campi nei PDF basandosi sui codici standard:
- Campi con prefisso `F` (es. F01, F10, F14) per i dati economici
- Campi con prefisso `ICI` (es. ICI011, ICI014) per i dati calcolati
- Campi con prefisso `A` (es. A01, A02) per i dati sul personale
- Campi ISA (es. ISAAFF, IIE001) per i dati del modello ISA

### Gestione Errori

- Se un campo non viene trovato, viene assegnato il valore 0.0 per i numeri o stringa vuota per il testo
- I numeri vengono convertiti correttamente dal formato italiano (es. 1.234.567,89) al formato decimale

## Funzionalità Completate

- ✅ Estrazione dati da PDF dichiarazioni fiscali
- ✅ Elaborazione biennio con confronto automatico
- ✅ API REST con FastAPI per upload e processamento
- ✅ Script di test automatizzati
- ✅ Documentazione Swagger interattiva
- ✅ **Estrazione completa di tutti i campi ICI (100%)**
- ✅ **Estrazione Quadro RS (Balance Sheet) - 13 campi**
- ✅ **Estrazione Patrimonio (ICI029 - Beni strumentali)**

### Campi Estratti (43 totali - 100% coverage):
- **Identificativi**: 4 campi (CF, P.IVA, Ragione sociale, Anno)
- **Ricavi**: 2 campi
- **Costi**: 11 campi (inclusi ICI009, ICI013, ICI016)
- **Risultati**: 4 campi (Valore aggiunto, MOL, Reddito operativo, Reddito d'impresa)
- **Personale**: 3 campi
- **Patrimonio**: 1 campo (ICI029 - Valore beni strumentali)
- **ISA**: 5 campi (Score, modello, indicatori)
- **Quadro RS**: 13 campi (Balance sheet completo)

## Prossimi Passi

- [ ] Aggiungere validazione dei dati estratti
- [ ] Implementare generazione report Word da JSON
- [ ] Aggiungere supporto per altri modelli ISA (oltre DG37U)
- [ ] Creare interfaccia grafica/web frontend
- [ ] Aggiungere autenticazione API
- [ ] Implementare storage persistente dei report
- [ ] Integrare con Formula Finance main app
