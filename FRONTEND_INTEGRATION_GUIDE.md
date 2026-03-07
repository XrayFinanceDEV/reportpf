# Frontend Integration Guide - ANBIL Report

## 📦 Sample Data File

**Use this file for frontend development:**
```
reportpf/anbil_sample_for_frontend.json
```

This contains:
- ✅ All 31 comprehensive metrics
- ✅ 3 years of data (2024, 2023, 2022)
- ✅ 22 AI comments (250 chars each, professional Italian)
- ✅ Real data from I.T.C. S.R.L.

---

## 🔧 JSON Structure

```typescript
interface AnbilResponse {
  success: boolean;
  data: {
    company_name: string;
    years: YearData[];
    ai_comments: AIComments;
    latest_year: YearData;
  };
  metadata: {
    report_id: number;
    extraction_mode: "comprehensive" | "basic";
    metrics_extracted: number;
    ai_comments_enabled: boolean;
    company_name: string;
    years_count: number;
    years_available: string[];
  };
}

interface YearData {
  year: string;

  // Economic Indicators (€)
  revenue: number;
  ebitda: number;
  costi_materia_prima: number;
  costi_servizi: number;
  costi_personale: number;
  costi_oneri_finanziari: number;

  // Profitability Ratios (%)
  roi: number;
  roe: number;
  ros: number;

  // Balance Sheet (€)
  attivo_immobilizzato: number;
  rimanenze: number;
  crediti_verso_clienti: number;
  debiti_verso_fornitori: number;

  // Debt Sustainability
  pfn: number;  // €
  pfn_ebitda_ratio: number;  // ratio
  costo_del_debito: number;  // %
  oneri_finanziari_mol: number;  // %

  // Capital Structure
  patrimonio_netto: number;  // €
  totale_attivo: number;  // €
  patrimonio_netto_attivo: number;  // %
  passivo_corrente: number;  // €
  totale_passivo: number;  // €
  passivo_corrente_totale_passivo: number;  // %

  // Cash Flow
  cash_flow: number;  // €
  fccr: number;  // ratio
}

interface AIComments {
  revenue: string;
  ebitda: string;
  roi: string;
  roe: string;
  ros: string;
  attivo_immobilizzato: string;
  rimanenze: string;
  crediti_verso_clienti: string;
  debiti_verso_fornitori: string;
  pfn_ebitda_ratio: string;
  costo_del_debito: string;
  oneri_finanziari_mol: string;
  patrimonio_netto_attivo: string;
  passivo_corrente_totale_passivo: string;
  cash_flow: string;
  fccr: string;
  profilo_economico_overall: string;  // ← OVERALL SYNTHESIS
}
```

---

## 🎨 Component Examples

### 1. Load Sample Data (Development)

```typescript
// app/anbil/[reportId]/page.tsx
'use client';

import { useEffect, useState } from 'react';

export default function AnbilReportPage({ params }: { params: { reportId: string } }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // FOR DEVELOPMENT: Load from sample file
    fetch('/api/anbil/sample')
      .then(res => res.json())
      .then(data => {
        setData(data.data);
        setLoading(false);
      });

    // PRODUCTION: Fetch from backend
    // fetch(`/api/reports/${params.reportId}/anbil`)
    //   .then(res => res.json())
    //   .then(data => setData(data.data));
  }, [params.reportId]);

  if (loading) return <div>Loading...</div>;
  if (!data) return <div>No data</div>;

  const latest = data.years[0];  // 2024
  const comments = data.ai_comments;

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">{data.company_name}</h1>

      {/* SECTION 1: PROFILO ECONOMICO */}
      <Section title="PROFILO ECONOMICO, PATRIMONIALE E FINANZIARIO">
        <OverallComment comment={comments.profilo_economico_overall} />

        <SubSection title="EBITDA - Risultato Operativo Lordo">
          <MetricCard
            value={latest.ebitda}
            unit="€"
            comment={comments.ebitda}
            chartData={data.years.map(y => ({
              year: y.year,
              value: y.ebitda
            }))}
          />
        </SubSection>
      </Section>

      {/* SECTION 2: INDICI DI REDDITIVITÀ */}
      <Section title="INDICI DI REDDITIVITÀ">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <MetricCard
            title="ROI"
            subtitle="Redditività del Capitale Investito"
            value={latest.roi}
            unit="%"
            comment={comments.roi}
            chartData={data.years.map(y => ({ year: y.year, value: y.roi }))}
          />
          <MetricCard
            title="ROE"
            subtitle="Redditività del Capitale Proprio"
            value={latest.roe}
            unit="%"
            comment={comments.roe}
            chartData={data.years.map(y => ({ year: y.year, value: y.roe }))}
          />
          <MetricCard
            title="ROS"
            subtitle="Redditività Operativa delle Vendite"
            value={latest.ros}
            unit="%"
            comment={comments.ros}
            chartData={data.years.map(y => ({ year: y.year, value: y.ros }))}
          />
        </div>
      </Section>

      {/* SECTION 3: FOCUS PATRIMONIALE */}
      <Section title="FOCUS PATRIMONIALE">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <MetricCard
            title="Attivo Immobilizzato"
            value={latest.attivo_immobilizzato}
            unit="€"
            comment={comments.attivo_immobilizzato}
          />
          <MetricCard
            title="Rimanenze"
            value={latest.rimanenze}
            unit="€"
            comment={comments.rimanenze}
          />
          <MetricCard
            title="Crediti verso Clienti"
            value={latest.crediti_verso_clienti}
            unit="€"
            comment={comments.crediti_verso_clienti}
          />
          <MetricCard
            title="Debiti verso Fornitori"
            value={latest.debiti_verso_fornitori}
            unit="€"
            comment={comments.debiti_verso_fornitori}
          />
        </div>
      </Section>

      {/* SECTION 4: SOSTENIBILITÀ DEL DEBITO */}
      <Section title="SOSTENIBILITÀ DEL DEBITO">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <MetricCard
            title="PFN / EBITDA"
            subtitle="Sostenibilità del Debito"
            value={latest.pfn_ebitda_ratio}
            unit="x"
            comment={comments.pfn_ebitda_ratio}
          />
          <MetricCard
            title="Costo del Debito"
            value={latest.costo_del_debito}
            unit="%"
            comment={comments.costo_del_debito}
          />
          <MetricCard
            title="Oneri Finanziari / MOL"
            value={latest.oneri_finanziari_mol}
            unit="%"
            comment={comments.oneri_finanziari_mol}
          />
        </div>
      </Section>

      {/* SECTION 5: STRUTTURA DEL CAPITALE */}
      <Section title="STRUTTURA DEL CAPITALE">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <MetricCard
            title="Patrimonio Netto / Attivo"
            value={latest.patrimonio_netto_attivo}
            unit="%"
            comment={comments.patrimonio_netto_attivo}
          />
          <MetricCard
            title="Passivo Corrente / Totale Passivo"
            value={latest.passivo_corrente_totale_passivo}
            unit="%"
            comment={comments.passivo_corrente_totale_passivo}
          />
        </div>
      </Section>

      {/* SECTION 6: CASH FLOW E COPERTURA */}
      <Section title="CASH FLOW E COPERTURA">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <MetricCard
            title="Cash Flow Operativo"
            value={latest.cash_flow}
            unit="€"
            comment={comments.cash_flow}
          />
          <MetricCard
            title="FCCR"
            subtitle="Fixed Charge Coverage Ratio"
            value={latest.fccr}
            unit="x"
            comment={comments.fccr}
          />
        </div>
      </Section>
    </div>
  );
}
```

### 2. MetricCard Component

```typescript
// components/metric-card.tsx
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface MetricCardProps {
  title: string;
  subtitle?: string;
  value: number;
  unit: '€' | '%' | 'x';
  comment?: string;
  chartData?: { year: string; value: number }[];
}

export function MetricCard({ title, subtitle, value, unit, comment, chartData }: MetricCardProps) {
  // Calculate trend
  const trend = chartData && chartData.length >= 2
    ? chartData[chartData.length - 1].value - chartData[chartData.length - 2].value
    : 0;

  const trendIcon = trend > 0
    ? <TrendingUp className="h-4 w-4 text-green-500" />
    : trend < 0
    ? <TrendingDown className="h-4 w-4 text-red-500" />
    : <Minus className="h-4 w-4 text-gray-500" />;

  const formatValue = (val: number, u: string) => {
    switch (u) {
      case '€':
        return new Intl.NumberFormat('it-IT', {
          style: 'currency',
          currency: 'EUR',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0
        }).format(val);
      case '%':
        return `${val.toFixed(2)}%`;
      case 'x':
        return `${val.toFixed(2)}x`;
      default:
        return val.toString();
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">{title}</CardTitle>
            {subtitle && <CardDescription>{subtitle}</CardDescription>}
          </div>
          {trendIcon}
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold mb-4">
          {formatValue(value, unit)}
        </div>

        {/* Mini chart */}
        {chartData && chartData.length > 0 && (
          <div className="h-20 mb-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <XAxis dataKey="year" hide />
                <YAxis hide />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#8884d8"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* AI Comment */}
        {comment && (
          <div className="text-sm text-muted-foreground border-l-4 border-blue-500 pl-3 py-2 bg-blue-50 rounded-r">
            💬 {comment}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
```

### 3. Overall Comment Component

```typescript
// components/overall-comment.tsx
import { Card, CardContent } from '@/components/ui/card';
import { AlertCircle } from 'lucide-react';

interface OverallCommentProps {
  comment: string;
}

export function OverallComment({ comment }: OverallCommentProps) {
  return (
    <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200 mb-6">
      <CardContent className="pt-6">
        <div className="flex items-start gap-4">
          <AlertCircle className="h-8 w-8 text-blue-600 flex-shrink-0 mt-1" />
          <div>
            <h3 className="text-lg font-semibold mb-2 text-blue-900">
              Sintesi del Profilo Aziendale
            </h3>
            <p className="text-blue-800 leading-relaxed">
              {comment}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
```

### 4. Section Component

```typescript
// components/section.tsx
import { ReactNode } from 'react';

interface SectionProps {
  title: string;
  children: ReactNode;
}

export function Section({ title, children }: SectionProps) {
  return (
    <div className="mb-8">
      <h2 className="text-2xl font-bold mb-4 border-b-2 border-gray-200 pb-2">
        {title}
      </h2>
      {children}
    </div>
  );
}

interface SubSectionProps {
  title: string;
  children: ReactNode;
}

export function SubSection({ title, children }: SubSectionProps) {
  return (
    <div className="mb-6">
      <h3 className="text-xl font-semibold mb-3 text-gray-700">
        {title}
      </h3>
      {children}
    </div>
  );
}
```

---

## 📊 Data Format Reference

### Currency Values (€)
```typescript
// Raw value: 15130120.0
// Display: €15.130.120 or €15,1M

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('it-IT', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value);
};
```

### Percentages (%)
```typescript
// Raw value: 11.01
// Display: 11,01%

const formatPercentage = (value: number) => {
  return `${value.toFixed(2)}%`;
};
```

### Ratios (x)
```typescript
// Raw value: 11.72
// Display: 11,72x

const formatRatio = (value: number) => {
  return `${value.toFixed(2)}x`;
};
```

---

## 🔄 API Integration (Production)

When backend is ready, replace sample data with API call:

```typescript
// app/api/reports/[reportId]/anbil/route.ts
import { NextResponse } from 'next/server';

export async function GET(
  request: Request,
  { params }: { params: { reportId: string } }
) {
  // Call main backend
  const response = await fetch(
    `https://kpsfinanciallab.w3pro.it:8000/apiServerIt/extract/anbil/by_report_id/${params.reportId}?comprehensive=true&ai_comments=true`
  );

  const data = await response.json();
  return NextResponse.json(data);
}
```

Then in your page:
```typescript
// Use real API instead of sample
fetch(`/api/reports/${params.reportId}/anbil`)
  .then(res => res.json())
  .then(data => setData(data.data));
```

---

## ✅ Checklist

- [ ] Copy `anbil_sample_for_frontend.json` to your frontend project
- [ ] Create TypeScript interfaces (see above)
- [ ] Build `MetricCard` component with AI comment display
- [ ] Build `OverallComment` component for synthesis
- [ ] Create sections for all 6 categories
- [ ] Add mini charts for trends
- [ ] Test with sample data
- [ ] Replace with API call when backend ready

---

## 📞 Need Help?

Sample file: `reportpf/anbil_sample_for_frontend.json`
Full docs: `reportpf/COMPREHENSIVE_EXTRACTION_SUMMARY.md`

All 31 metrics are in the JSON with realistic data and AI comments! 🎉
