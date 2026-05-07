# FORMULE.md — Report PF

Documentazione completa di parametri e formule del **Report Società Persone Fisiche** (`module_id: 3`).

Per ciascuna grandezza calcolata sono indicati:
- **Riga / codice della dichiarazione fiscale** (Quadro F, Quadro RS, Quadro RE, Prospetto ISA)
- **Formula matematica** implementata
- **File e riga di codice** in `formule_report_pf.py`

> Sorgente codici: `extdichiarazione_v3_optimized.py:716-949`
> Sorgente formule: `formule_report_pf.py`

---

## 1. Premesse sui codici della dichiarazione

### 1.1 Quadri utilizzati

| Quadro | Contenuto | Soggetti |
|---|---|---|
| **Quadro F** | Elementi contabili ISA — Imprese | SP, PF_RG (ditta individuale) |
| **Quadro RE** | Lavoro autonomo | PF_RE (libero professionista) |
| **Quadro RS** | Stato patrimoniale (RS97–RS114) | Solo contabilità ordinaria |
| **Prospetto ISA Economico** | Indicatori di sintesi (ICI / ICA) | Tutti i soggetti ISA |
| **Quadro A** | Dati sul personale (A01, A02) | Tutti |

### 1.2 Differenza formato 2023 vs 2024

I codici cambiano lunghezza tra annualità (`extdichiarazione_v3_optimized.py:35-62`):

| Anno | Formato ICI | Formato ICA | Punteggio ISA |
|---|---|---|---|
| **2024** | 3 cifre — es. `ICI001`, `ICI011` | 3 cifre — es. `ICA013` | `ISAAFF` |
| **2023 e precedenti** | 5 cifre — es. `ICI00101`, `ICI01101` | 5 cifre — es. `ICA01301` | `IIISAAFF` |

In tutto il documento verrà indicata la coppia: `ICI001 / ICI00101`.

### 1.3 Tipo entità (entity type)

`detect_entity_type()` (`extdichiarazione_v3_optimized.py:214-228`) distingue:

| Tipo | Descrizione | Quadro reddito | Codici ISA |
|---|---|---|---|
| **SP** | Società di persone | Quadro F | ICI |
| **PF_RG** | Ditta individuale | Quadro F | ICI |
| **PF_RE** | Libero professionista | Quadro RE | ICA |
| **PF** | Persona fisica senza attività | — | — |

### 1.4 Tipo contabilità (accounting type)

`detect_accounting_type()` controlla 18 campi del Quadro RS:

- **Ordinaria** → almeno un campo RS97–RS114 > 0 ⇒ Report completo (valutazione + sostenibilità).
- **Semplificata** → tutti i campi Quadro RS = 0 ⇒ Report ridotto (8 indicatori ISA-based, niente bilancio).

---

## 2. Mappatura completa parametri ↔ righe dichiarazione

### 2.1 Identificativi

| Campo JSON | Sorgente |
|---|---|
| `codice_fiscale` | Frontespizio (11 cifre per SP/PF_RG, 16 caratteri per PF_RE) |
| `partita_iva` | Frontespizio |
| `ragione_sociale` | Frontespizio |
| `anno` | Estratto dal testo "Periodo d'imposta YYYY" (NON dall'header del modulo) |

### 2.2 Ricavi

#### Imprese (Quadro F)

| Campo JSON | Codice | Descrizione |
|---|---|---|
| `ricavi_dichiarati` | **F01** / **ICI001** / `ICI00101` | Ricavi delle vendite e delle prestazioni |
| `altri_componenti_positivi` | **F02 + F03 + F05** | Altre componenti positive |

#### Liberi professionisti (Quadro RE)

| Campo JSON | Codice | Descrizione |
|---|---|---|
| `ricavi_dichiarati` | **RE2** / **ICA001** / `ICA00101` | Compensi attività professionale |
| `altri_componenti_positivi` | **RE3 + RE4 + RE5** | Altre somme + Plusvalenze + Compensi non annotati |

### 2.3 Costi

#### Imprese (Quadro F + ICI)

| Campo JSON | Codice | Descrizione |
|---|---|---|
| `esistenze_iniziali` | **F08** / **ICI004** / `ICI00401` | Esistenze iniziali |
| `rimanenze_finali` | **F09** / **ICI005** / `ICI00501` | Rimanenze finali |
| `costo_materie_prime` | **F10** / **ICI006** / `ICI00601` | Acquisti materie prime |
| `costo_servizi` | **F12** / **ICI008** / `ICI00801` | Costo per servizi |
| `godimento_beni_terzi` | **ICI009** / `ICI00901` | Godimento beni di terzi |
| `costo_personale` | **F14** / **ICI012** / `ICI01201` | Costo del personale |
| `spese_collaboratori` | **ICI013** / `ICI01301` | Co.co.co. |
| `ammortamenti` | **F15** / **ICI015** / `ICI01501` | Ammortamenti e svalutazioni |
| `accantonamenti` | **ICI016** / `ICI01601` | Accantonamenti |
| `altri_costi` | **F17** / **ICI010** / `ICI01001` | Costi residuali |
| `oneri_finanziari` | **F19** / **ICI019** / `ICI01901` | Oneri finanziari |

#### Liberi professionisti (Quadro RE + ICA)

| Campo JSON | Codice | Descrizione |
|---|---|---|
| `esistenze_iniziali` | — | 0 (no rimanenze) |
| `rimanenze_finali` | — | 0 (no rimanenze) |
| `costo_materie_prime` | **ICA008** / RE14 | Consumi |
| `costo_servizi` | **ICA007** / RE12 | Compensi a terzi |
| `godimento_beni_terzi` | **ICA004 + ICA005** / RE8 + RE9 | Canoni leasing + noleggio |
| `costo_personale` | **ICA014** / RE11 | Spese lavoro dipendente |
| `spese_collaboratori` | **ICA015** | Co.co.co. |
| `ammortamenti` | **ICA017** / RE7 | Ammortamenti |
| `accantonamenti` | — | 0 (non presenti in RE) |
| `altri_costi` | **ICA012** / RE19 | Altre spese documentate |
| `oneri_finanziari` | **ICA020** / RE13 | Interessi passivi |

### 2.4 Risultati

#### Imprese

| Campo JSON | Codice | Pagina PDF | Descrizione |
|---|---|---|---|
| `valore_aggiunto` | **ICI011** / `ICI01101` | p. 24 — Prospetto Economico ISA | Valore aggiunto |
| `mol` | **ICI014** / `ICI01401` | p. 24 | Margine Operativo Lordo |
| `reddito_operativo` | **ICI017** / `ICI01701` | p. 24 | Reddito operativo |
| `reddito_impresa` | **F20** / **ICI024** / `ICI02401` | — | Reddito d'impresa |

#### Liberi professionisti

| Campo JSON | Codice | Descrizione |
|---|---|---|
| `valore_aggiunto` | **ICA013** | Valore aggiunto |
| `mol` | **ICA016** | Margine Operativo Lordo |
| `reddito_operativo` | **ICA018** | Reddito operativo |
| `reddito_impresa` | **ICA024** / RE23 | Reddito attività professionali |

### 2.5 Personale

| Campo JSON | Codice | Descrizione |
|---|---|---|
| `giornate_dipendenti` | **A01** | Giornate retribuite dipendenti |
| `giornate_altro_personale` | **A02** | Giornate retribuite altro personale |
| `numero_addetti_equivalenti` | **ICI027** / **ICA027** / `*02701` | Numero addetti equivalenti (p. 24) |

### 2.6 Patrimonio

| Campo JSON | Codice | Descrizione |
|---|---|---|
| `valore_beni_strumentali` | **F21** / **ICI029** / **ICA028** | Valore beni strumentali |

### 2.7 ISA

| Campo JSON | Codice | Descrizione |
|---|---|---|
| `punteggio` | **ISAAFF** (2024) / **IIISAAFF** (2023) | Punteggio ISA finale (scala 1–10) |
| `modello_applicato` | — | Codice modello ISA (es. `DG37U`, `BK04U`) |
| `ricavi_per_addetto` | **IIE001** / `IIE00101` | Indicatore IIE — ricavi/addetto |
| `valore_aggiunto_per_addetto` | **IIE002** / `IIE00201` | Indicatore IIE — VA/addetto |
| `reddito_per_addetto` | **IIE003** / `IIE00301` | Indicatore IIE — reddito/addetto |

### 2.8 Quadro RS — Stato Patrimoniale (solo ordinaria)

Pagine PDF: 9–12 (p. 12 sezione ISA contiene RS97–RS114 in forma compatta).

#### Attivo immobilizzato

| Campo JSON | Codice | Descrizione |
|---|---|---|
| `immobilizzazioni_immateriali` | **RS97** | Immobilizzazioni immateriali |
| `immobilizzazioni_materiali` | **RS98** | Immobilizzazioni materiali (valore netto — ULTIMO numero della riga, non il fondo ammortamento) |
| `immobilizzazioni_finanziarie` | **RS99** | Immobilizzazioni finanziarie |

#### Attivo circolante

| Campo JSON | Codice | Descrizione |
|---|---|---|
| `rimanenze` | **RS100** | Rimanenze materie prime |
| `crediti_clienti` | **RS101** | Crediti verso clienti |
| `altri_crediti` | **RS102** | Altri crediti |
| `attivita_finanziarie` | **RS103** | Attività finanziarie non immobilizzate |
| `disponibilita_liquide` | **RS104** | Disponibilità liquide |
| `ratei_risconti_attivi` | **RS105** | Ratei e risconti attivi |

#### Totale e passivo

| Campo JSON | Codice | Descrizione |
|---|---|---|
| `totale_attivo` | **RS106** | Totale attivo |
| `patrimonio_netto` | **RS107** | Patrimonio netto |
| `fondi_rischi_oneri` | **RS108** | Fondi rischi e oneri |
| `tfr` | **RS109** | TFR |
| `debiti_banche_breve` | **RS110** | Debiti vs banche (breve termine) |
| `debiti_banche_lungo` | **RS111** | Debiti vs banche (lungo termine) |
| `debiti_fornitori` | **RS112** | Debiti verso fornitori |
| `altri_debiti` | **RS113** | Altri debiti |
| `ratei_risconti_passivi` | **RS114** | Ratei e risconti passivi |

### 2.9 Imposte — Quadro RN e RV (solo PF)

Presenti solo nelle dichiarazioni Persone Fisiche (PF_RG, PF_RE). Per le Società di Persone (SP) l'IRPEF è in capo ai singoli soci, quindi questi campi saranno zero.

| Campo JSON | Codice | Descrizione |
|---|---|---|
| `irpef_netta` | **RN26** | IRPEF netta (imposta dopo detrazioni e crediti) |
| `addizionale_regionale` | **RV2** | Addizionale regionale all'IRPEF |
| `addizionale_comunale` | **RV10** | Addizionale comunale all'IRPEF |

---

## 3. Formule — Contabilità Ordinaria

Classe `ReportPFCalculator` (`formule_report_pf.py:41-715`).

### 3.1 Sezione VALUTAZIONE D'IMPRESA

#### 3.1.1 EM Score (Altman Z-Score variant)

`formule_report_pf.py:67-106`

```
Capitale Circolante = RS100 + RS101 + RS102 + RS103 + RS104 + RS105
                    − (RS110 + RS112 + RS113 + RS114)

WC_ratio  = Capitale Circolante / RS106            (working capital / totale attivo)
Prof_ratio = ICI017 / RS106                         (reddito operativo / totale attivo)

EM Score = 3.25 + 6.56 × WC_ratio + 6.72 × Prof_ratio
```

**Note**: i debiti verso banche a breve termine (RS110) sono inclusi nel passivo corrente, mentre i debiti a lungo (RS111) sono esclusi. RS108, RS109, RS111 NON entrano nel calcolo del WC.

#### 3.1.2 Probabilità di Default (PD)

`formule_report_pf.py:108-152` — tabella di mapping da EM Score:

| EM Score | PD (%) | EM Score | PD (%) |
|---|---|---|---|
| ≥ 8.15 | 0.01 | ≥ 4.95 | 0.86 |
| ≥ 7.60 | 0.02 | ≥ 4.75 | 1.43 |
| ≥ 7.30 | 0.03 | ≥ 4.40 | 2.03 |
| ≥ 7.00 | 0.04 | ≥ 4.15 | 2.88 |
| ≥ 6.85 | 0.05 | ≥ 3.75 | 4.09 |
| ≥ 6.65 | 0.07 | ≥ 3.20 | 6.94 |
| ≥ 6.40 | 0.09 | ≥ 2.50 | 11.78 |
| ≥ 6.25 | 0.14 | ≥ 1.75 | 14.00 |
| ≥ 5.85 | 0.21 | < 1.75 | 20.00 |
| ≥ 5.65 | 0.31 | | |
| ≥ 5.25 | 0.52 | | |

#### 3.1.3 Tasso di sconto R°

`formule_report_pf.py:154-176`

```
R° = Risk-free rate + Credit Spread
Risk-free rate = 3.5%   (rendimento medio BTP)
```

| PD (%) | Spread |
|---|---|
| ≤ 0.05 | 2% |
| ≤ 0.50 | 4% |
| ≤ 2.00 | 6% |
| ≤ 5.00 | 8% |
| ≤ 10.00 | 10% |
| > 10.00 | 15% |

#### 3.1.4 Valutazione NOPAT

`formule_report_pf.py:178-215`

```
Tax Rate = tax_rate effettivo (calcolato da Quadro RN/RV per PF, stimato 30% per SP)

NOPAT_t   = ICI017_t × (1 − tax_rate)           # Reddito operativo netto imposte
Avg NOPAT = (NOPAT_corrente + NOPAT_precedente) / 2

Valutazione = Avg NOPAT / R°
```

**Tax Rate effettivo** (solo PF_RG, PF_RE):
```
Imposte totali = RN26 (IRPEF netta) + RV2 (addizionale regionale) + RV10 (addizionale comunale)
Tax Rate = Imposte totali / Reddito Impresa (ICI024 / ICA024)
```
Fallback al 30% stimato se: entity_type = SP, oppure imposte = 0, oppure reddito ≤ 0.
Il tax rate è cappato tra 0% e 60%.

---

### 3.2 Sezione FINANZIARIA

#### 3.2.1 Debt Management — Interest Coverage

`formule_report_pf.py:232-301`

```
Ratio = ICI014 / ICI019              # MOL / Oneri finanziari
                                      # (= ICA016 / ICA020 per professionisti)
```

Casi particolari:
- `MOL < 0` → Rating **N/A**
- `Oneri finanziari = 0` → Rating **AAA**

Mapping ratio → rating creditizio:

| Ratio | Rating | Ratio | Rating |
|---|---|---|---|
| > 12.50 | AAA | > 3.00 | BB |
| > 9.50 | AA | > 2.50 | B+ |
| > 7.50 | A+ | > 2.00 | B |
| > 6.00 | A | > 1.50 | B− |
| > 4.50 | A− | > 1.25 | CCC+ |
| > 4.00 | BBB | > 0.80 | CCC |
| > 3.50 | BB+ | > 0.50 | C |
| | | ≤ 0.50 | D |

#### 3.2.2 Cash Generation — Free Cash Flow

`formule_report_pf.py:303-381`

```
Operating CF = ICI014 + ICI015                       # MOL + Ammortamenti

WC_t = (RS100 + RS101 + RS102 + RS104 + RS105)_t
     − (RS112 + RS113 + RS114)_t                    # ATTENZIONE: differente da EM Score
                                                    # (esclude RS103 "attività finanziarie"
                                                    #  e RS110 "debiti banche breve")

ΔWC   = WC_corrente − WC_precedente
Capex = (F21 / ICI029)_corrente − (F21 / ICI029)_precedente

FCF = Operating CF − ΔWC − Capex
```

**Differenza con EM Score**: il working capital qui esclude le attività finanziarie a breve (RS103) e i debiti verso banche a breve (RS110), perché questi sono considerati posizione finanziaria e non operativa.

---

### 3.3 Sezione OPERATIVA

#### 3.3.1 Operating Leverage — Leva operativa

`formule_report_pf.py:387-417`

```
ΔRicavi  = ICI001_corrente − ICI001_precedente
ΔRO      = ICI017_corrente − ICI017_precedente

Leva Operativa = ΔRO / ΔRicavi
```

#### 3.3.2 Asset Turnover — Capacità produttiva

`formule_report_pf.py:419-446`

```
Ratio_t = (F21 / ICI029)_t / ICI001_t           # Beni strumentali / Ricavi
```

Trend: **Improving** se `Ratio_corrente < Ratio_precedente` (servono meno asset per generare ricavi), altrimenti **Worsening**.

#### 3.3.3 Production Leverage — Leva produttiva

`formule_report_pf.py:448-474`

```
Ratio_t = ICI011_t / ICI012_t                    # Valore Aggiunto / Costo del Personale

Trend % = (Ratio_corr − Ratio_prec) / Ratio_prec × 100
```

#### 3.3.4 Productivity per Capita

`formule_report_pf.py:476-504`

```
Productivity_t = ICI011_t / ICI027_t            # Valore Aggiunto / Numero Addetti

Change % = (Prod_corr − Prod_prec) / Prod_prec × 100
```

---

### 3.4 Sezione ECONOMICA

#### 3.4.1 Costi Fissi vs Variabili

`formule_report_pf.py:510-556`

```
Costi Fissi = ICI009 + ICI012 + ICI013 + ICI010 + ICI015 + ICI016
            = (Godimento beni terzi + Personale + Co.co.co.
             + Costi residuali + Ammortamenti + Accantonamenti)

Costi Variabili = ICI004 + ICI006 + ICI008 − ICI005
                = (Esistenze iniziali + Materie prime + Servizi
                   − Rimanenze finali)

Totale = Fissi + Variabili
% Fissi = Fissi / Totale × 100
```

> **Nota**: `oneri_finanziari` (ICI019) non è classificato né come fisso né come variabile; è escluso dal totale costi operativi.

#### 3.4.2 Break Even Point (BEP)

`formule_report_pf.py:558-610`

```
Contribution Margin Ratio (CMR) = 1 − (Costi Variabili / ICI001)

BEP = Costi Fissi / CMR

Margine di Sicurezza = (ICI001 − BEP) / ICI001 × 100
```

Casi particolari:
- `CMR ≤ 0` (variabili ≥ ricavi) → BEP infinito, **Critical situation**
- `Ricavi = 0` → BEP = 0, non calcolabile

Bande di interpretazione:

| Margine | Giudizio |
|---|---|
| > 30% | Excellent — Low risk |
| > 20% | Good — Moderate risk |
| > 10% | Adequate — Some risk |
| > 0% | Thin — High risk |
| ≤ 0% | Below break-even — Critical |

---

### 3.5 Sezione SOSTENIBILITÀ

#### 3.5.1 ROE proiettato (decomposizione DuPont modificata)

`formule_report_pf.py:616-668`

```
# Trend lineare reddito operativo
Trend_RO    = ICI017_corrente − ICI017_precedente
RO_proiettato = ICI017_corrente + Trend_RO       # estrapolazione anno successivo

# Componenti
ROA = RO_proiettato / RS106                       # ROA su totale attivo
i   = ICI019 / (RS110 + RS111)                    # tasso interesse medio
D/E = (RS110 + RS111) / RS107                     # leverage finanziario
Tax = tax_rate effettivo (da Quadro RN/RV per PF, 30% stimato per SP)

# Formula completa
ROE = [ROA + (ROA − i) × D/E] × (1 − tax_rate)
```

Interpretazione:

| ROE | Giudizio |
|---|---|
| > 15% | Excellent |
| > 10% | Good |
| > 5% | Fair |
| > 0% | Low |
| ≤ 0% | Negative — Loss-making |

**Sostenibilità** = "Sustainable" se ROE > 0, altrimenti "Not sustainable".

---

## 4. Formule — Contabilità Semplificata

Classe `ReportPFCalculatorSemplificato` (`formule_report_pf.py:718-1050`).

Quando tutti i campi RS97–RS114 sono zero, vengono calcolati **solo 8 indicatori basati su Prospetto ISA Economico**. Sezioni omesse: **Valutazione** (richiede totale attivo) e **Sostenibilità** (richiede patrimonio netto).

### 4.1 Indicatori finanziari

#### Debt Management
Identico al caso ordinaria — `ICI014 / ICI019` (vedi §3.2.1).

#### Cash Generation semplificata

`formule_report_pf.py:807-830`

```
ΔBeni = (F21 / ICI029)_corrente − (F21 / ICI029)_precedente
Cash Generation = ICI014 − ΔBeni                # MOL − ΔBeni strumentali
```

> Versione ridotta perché manca il working capital (no Quadro RS).

### 4.2 Indicatori operativi

Tutti **identici** al caso ordinaria:
- Operating Leverage (§3.3.1)
- Asset Turnover (§3.3.2)
- Production Leverage (§3.3.3)
- Productivity per Capita (§3.3.4)

### 4.3 Indicatori economici

Identici al caso ordinaria:
- Costi Fissi/Variabili (§3.4.1)
- Break Even Point (§3.4.2)

---

## 5. Formule — Liberi Professionisti (Quadro RE)

Per **PF_RE** la struttura dati è identica ma i codici cambiano (ICI → ICA, F → RE). La logica di calcolo è la stessa: si applica `ReportPFCalculator` se contabilità ordinaria, `ReportPFCalculatorSemplificato` se semplificata.

### 5.1 Sostituzione codici nelle formule

| Concetto | Codice Imprese | Codice Professionisti |
|---|---|---|
| Ricavi/Compensi | `ICI001` | `ICA001` / RE2 |
| Valore aggiunto | `ICI011` | `ICA013` |
| MOL | `ICI014` | `ICA016` |
| Reddito operativo | `ICI017` | `ICA018` |
| Oneri finanziari | `ICI019` | `ICA020` |
| Costo personale | `ICI012` | `ICA014` / RE11 |
| Ammortamenti | `ICI015` | `ICA017` / RE7 |
| Beni strumentali | `ICI029` / F21 | `ICA028` |
| Numero addetti | `ICI027` | `ICA027` |

### 5.2 Particolarità professionisti

- `esistenze_iniziali` e `rimanenze_finali` = 0 (i professionisti non hanno magazzino) → la formula dei costi variabili si riduce a: `Variabili = ICA008 + ICA007`.
- `accantonamenti` = 0 (non presenti in Quadro RE).
- Quadro RS tipicamente tutto zero → contabilità semplificata di default.

---

## 6. Costanti e parametri configurabili

Valori "hardcoded" nelle formule che potrebbero richiedere configurazione esterna:

| Parametro | Valore | Posizione | Note |
|---|---|---|---|
| **Tax Rate** (NOPAT/ROE) | Effettivo da RN26+RV2+RV10 | `formule_report_pf.py:_calculate_tax_rate()` | Per PF: calcolato da imposte reali. Per SP: 30% stimato. Fallback 30% se dati mancanti. Cap 0-60% |
| **Risk-free rate** | 3.5% | `formule_report_pf.py:160` | Rendimento medio BTP — da aggiornare |
| **Credit spreads** | 2/4/6/8/10/15% | `formule_report_pf.py:163-174` | Bande grossolane |
| **Tabella EM→PD** | 20 fasce | `formule_report_pf.py:113-152` | Calibrazione Altman |
| **Soglie rating debito** | 16 fasce AAA→D | `formule_report_pf.py:272-301` | Da specifica schema |
| **Soglie BEP margin** | 30/20/10/0% | `formule_report_pf.py:601-610` | Giudizi qualitativi |

---

## 7. Pipeline di elaborazione

### 7.1 Flusso ordinaria

1. **Estrazione PDF** → Claude AI legge dichiarazione (Modello Redditi + Prospetto ISA + Quadro RS) — `extdichiarazione_v3_optimized.py`
2. **Parsing** → 2 annualità (anno_corrente + anno_precedente)
3. **Detection** → `detect_entity_type()` + `detect_accounting_type()`
4. **Calcolo** → `ReportPFCalculator.generate_complete_report()`
5. **Commenti AI** (opzionale) → `ai_comment_generator.py`
6. **Output** JSON con sezioni: `valutazione`, `finanziari`, `operativi`, `economici`, `sostenibilita`

### 7.2 Flusso semplificata

1. Estrazione (solo Prospetto ISA Economico — niente Quadro RS)
2. Detection: tutti i valori RS97–RS114 = 0
3. Calcolo: `ReportPFCalculatorSemplificato.generate_complete_report()`
4. Output JSON con `accounting_type: "semplificata"`, sezioni `valutazione` e `sostenibilita` **omesse**.

### 7.3 Flusso PF_RE (professionisti)

1. Detection: presenza codici ICA o header `QUADRO RE`
2. Prompt di estrazione dedicato → `_build_extraction_prompt_re()`
3. Mapping codici ICA → struttura dati standard
4. Calcolo: stessa classe (ordinaria o semplificata in base a Quadro RS)

---

## 8. Formule calcolate nel FRONTEND

Il frontend Next.js (`formulafinance/components/reports/`) calcola **autonomamente** numerosi indicatori che NON arrivano dal backend `formule_report_pf.py`. Questi sono calcoli derivati dai dati grezzi (`anno_corrente`, `anno_precedente`, `quadro_rs`, `costi`, `risultati`, `isa`).

### 8.1 EBITDA (Andamento Economico)

`components/reports/report-pf.tsx:272-274` — il backend espone solo MOL.

```
EBITDA_t = ICI014_t + ICI015_t                  # MOL + Ammortamenti
```

Usato in: card highlight EBITDA, calcolo Equilibrio Economico, Debt Service Coverage.

### 8.2 Trend e incidenze sui ricavi

`pf-andamento-economico.tsx:325-344`

```
Trend Fatturato % = (Fatt_corr − Fatt_prec) / Fatt_prec × 100
Trend EBITDA %    = (EBITDA_corr − EBITDA_prec) / EBITDA_prec × 100
Trend Risultato % = (RisEs_corr − RisEs_prec) / |RisEs_prec| × 100   # uso valore assoluto

Incidenza EBITDA su ricavi % = EBITDA_t / ICI001_t × 100
Incidenza Risultato su ricavi % = RisEs_t / ICI001_t × 100
```

### 8.3 Equilibrio ECONOMICO (semaforo 1–5)

`report-pf.tsx:280-322` — sistema a punti con due rami.

**Ramo A** — se `ISA punteggio > 0`:
```
score = round(ISA / 10 × 5)                    # mapping 0-10 → 0-5
status: < 6 → SOTTO MEDIA
        6-8.5 → NELLA MEDIA
        ≥ 8.5 → OTTIMA
        Reddito impresa < 0 → ASPETTI DI CRITICITÀ (override)
```

**Ramo B** — fallback se ISA non disponibile, sistema a 5 punti:
```
+1 se ICI024 (reddito_impresa) > 0
+1 se ICI024_corr > ICI024_prec
+1 se EBITDA / ICI001 > 10%
+1 se ICI001_corr > ICI001_prec
+1 se ICI011 (valore_aggiunto) > 0
score = clamp(points, 1, 5)
```

### 8.4 Equilibrio PATRIMONIALE (semaforo 1–5)

`report-pf.tsx:361-396`

```
PN % Attivo = RS107 / RS106 × 100               # patrimonio netto su totale attivo
```

| PN % | Score | Status | Color |
|---|---|---|---|
| ≥ 50% | 5 | ECCELLENTE | green |
| ≥ 40% | 4 | BUONO | blue |
| ≥ 30% | 3 | NELLA MEDIA | blue |
| ≥ 20% | 2 | DEBOLE | orange |
| < 20% | 1 | CRITICO | red |
| RS107 < 0 | — | CRITICITÀ | red (override) |

### 8.5 Equilibrio FINANZIARIO (semaforo 1–5)

`report-pf.tsx:418-444` — sistema a punti combinato.

```
Debiti breve = RS110 + RS112 + RS113            # banche breve + fornitori + altri
Liquidity Ratio = RS104 / Debiti breve          # disponibilità / passivo corrente

Oneri % = ICI019 / ICI001 × 100
PD = indicatori.valutazione.probability_default  # da backend

Punteggio (max 5):
+2 se Liquidity ≥ 1.5,  +1 se ≥ 0.8
+2 se Oneri% < 2,       +1 se < 5
+1 se PD < 10
score = clamp(points, 1, 5)
```

Status: `[CRITICO, DEBOLE, NELLA MEDIA, BUONO, ECCELLENTE][score-1]`

### 8.6 Equilibrio TRIBUTARIO

`report-pf.tsx:474-495` — basato su punteggio ISA.

| Punteggio ISA | Status |
|---|---|
| ≥ 8.5 | ECCELLENTE |
| ≥ 7 | BUONO |
| ≥ 6 | NELLA MEDIA |
| < 6 | SOTTO MEDIA |
| ≤ 0 | N.D. |

### 8.7 Imposte e Tax Rate effettivo

`report-pf.tsx:455-472` — usa i dati reali estratti dal Quadro RN/RV.

```
Imposte corrente = RN26 + RV2 + RV10             # dati estratti dal PDF
Tax Rate % = indicatori.tax_rate.value            # dal backend (effettivo per PF, 30% per SP)
```

Per l'anno precedente, se disponibili i dati `imposte`:
```
Tax Rate precedente = (RN26_prec + RV2_prec + RV10_prec) / Reddito Impresa_prec × 100
```
Fallback al tax rate corrente se dati non disponibili.

### 8.8 ADEGUATI ASSETTI (formula completa)

`pf-adeguati-assetti.tsx:42-82` — formula complessa di resistenza alle variazioni.

```
# Forecast lineare ricavi (anno t+1)
RO_forecast = ICI001_corr + (ICI001_corr − ICI001_prec)

# Componente A: ROA forecast doppio
partA = 2 × (RO_forecast / RS106)

# Componente B: costo del debito × leva
totalDebts = RS110 + RS111
partB = (ICI019 / totalDebts) × (totalDebts / RS107)
      = ICI019 / RS107                           # semplificazione algebrica

# Spread netto
partC = partA − partB

# Fattore tasse
taxFactor = 1 − tax_rate / 100        # tax_rate dal backend (effettivo per PF, 30% per SP)
partD = +taxFactor se ICI024 > 0
        −taxFactor se ICI024 ≤ 0

# Risultato finale
Indice = partC × partD
```

**Semaforo**:
- VERDE (✓) — `Indice > 0 AND ICI024 > 0` → "Assetti adeguati e resistenti"
- ROSSO (✗) — altrimenti → "Assetti fragili, non resistenti"

> NB: la formula nel commento del file (`partA = (RO/RS106) + (RO/RS106)`) somma due volte lo stesso valore — comportamento intenzionale, non bug.

### 8.9 DuPont ROE Analysis (Analisi Stato Patrimoniale)

`pf-analisi-stato-patrimoniale.tsx:726-756` — stessa decomposizione DuPont del backend (§3.5.1) ma su dati anno corrente (non proiettati).

```
ROA % = ICI017 / RS106 × 100                    # reddito operativo / totale attivo
Tasso Interesse % = ICI019 / (RS110 + RS111) × 100
Spread % = ROA − Tasso Interesse
Leverage = (RS110 + RS111) / RS107
Spread × Leverage Effect % = Spread × Leverage / 100
ROE % = [ROA + (Spread × Leverage)] × (1 − tax_rate / 100)
Tax Rate = indicatori.tax_rate.value (effettivo per PF, 30% stimato per SP)
```

Visualizzazione decomposizione: `[ROA + (Spread × Leverage)] × (1 - Tax Rate) = ROE`

> **Nota**: il backend (§3.5.1) usa la stessa formula DuPont ma con RO *proiettato* (trend lineare). Il frontend usa RO dell'anno corrente. La decomposizione e il tax rate sono ora allineati.

### 8.10 Indicatori finanziari (sezione Analisi Patrimoniale)

`pf-analisi-stato-patrimoniale.tsx:614-708`

```
Tasso Interesse Medio % = ICI019 / (RS110 + RS111) × 100
Debito Bancario = RS110 + RS111
Debt Service Coverage = EBITDA / ICI019         # quante volte EBITDA copre oneri
Trend % = (val_corr − val_prec) / |val_prec| × 100   # uso |.| per gestire negativi
```

### 8.11 Tabella riepilogo formule frontend-only

| Formula | File | Differenza dal backend |
|---|---|---|
| EBITDA | `report-pf.tsx:273` | Backend ha solo MOL |
| Trend % | vari `pf-*.tsx` | Calcolo ad-hoc, non in JSON |
| Incidenza ricavi % | `pf-andamento-economico.tsx:332-343` | Non in JSON |
| Equilibrio Economico (1-5) | `report-pf.tsx:280-322` | Sistema a punti, non in backend |
| Equilibrio Patrimoniale | `report-pf.tsx:361-396` | Solo PN/TA, non in backend |
| Equilibrio Finanziario | `report-pf.tsx:418-444` | Sistema a punti combinato |
| Tax Rate effettivo | `report-pf.tsx:461-472` | Usa `indicatori.tax_rate.value` dal backend |
| Imposte | `report-pf.tsx:455-459` | Usa dati reali RN26+RV2+RV10 estratti dal PDF |
| Adeguati Assetti | `pf-adeguati-assetti.tsx:42-82` | **Solo frontend** |
| ROE DuPont | `pf-analisi-*.tsx:727-755` | Stessa formula DuPont del backend, ma su dati correnti (non proiettati) |
| Debt Service Coverage | `pf-analisi-*.tsx:639-640` | Backend usa interest coverage MOL/oneri |
| Tasso Interesse Medio | `pf-analisi-*.tsx:626-634` | Non in backend |
| PN % Attivo | `report-pf.tsx:362-395` | Non in backend |
| Liquidity Ratio | `report-pf.tsx:421` | Non in backend |

---

## 9. File chiave

### Backend
```
reportpf/
├── api_server.py                       # FastAPI server, routing, entity/accounting detection
├── extdichiarazione_v3_optimized.py    # Estrazione PDF con Claude AI
│   ├── detect_entity_type()            # SP / PF_RG / PF_RE / PF
│   ├── detect_accounting_type()        # ordinaria / semplificata
│   ├── _build_extraction_prompt()      # Prompt per imprese (ICI)
│   └── _build_extraction_prompt_re()   # Prompt per professionisti (ICA)
├── formule_report_pf.py                # Formule sezioni: valutazione, finanziaria, operativa, economica, sostenibilità
│   ├── ReportPFCalculator              # Report completo (ordinaria)
│   └── ReportPFCalculatorSemplificato  # Report ridotto (semplificata)
├── ai_comment_generator.py             # Commenti AI per ogni sezione
└── validation.py                       # Validazione dati estratti
```

### Frontend
```
formulafinance/components/reports/
├── report-pf.tsx                       # Componente master + EBITDA + 4 equilibri + tax rate
├── pf-andamento-economico.tsx          # Trend e incidenza ricavi
├── pf-stato-patrimoniale.tsx           # PN % attivo
├── pf-focus-finanziario.tsx            # Liquidità, oneri %, PD
├── pf-focus-tributario.tsx             # ISA score, tax rate
├── pf-adeguati-assetti.tsx             # **Formula Adeguati Assetti (solo frontend)**
├── pf-analisi-conto-economico.tsx      # Tabelle CE
├── pf-analisi-stato-patrimoniale.tsx   # **DuPont ROE + Tasso Interesse + DSC**
├── pf-valutazione-rating.tsx           # Display valutazione (dati dal backend)
└── pf-charts.tsx                       # Grafici comparativi biennali
```
