#!/usr/bin/env python3
"""
ai_comment_generator.py
Generate AI-powered brief comments for financial metrics using Claude Haiku 3.5

Uses Claude Haiku 3.5 to analyze financial trends and generate concise 250-char
comments in Italian for each metric in the anbil dashboard.
"""

import os
from typing import Dict, List, Any, Optional
from anthropic import Anthropic


class AICommentGenerator:
    """Generate AI-powered comments for financial metrics"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the AI comment generator

        Args:
            api_key: Anthropic API key (if None, uses ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. "
                "Please set it as environment variable or pass it as argument."
            )

        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-3-5-haiku-20241022"

    def _format_number(self, value: float, unit: str = '€') -> str:
        """Format a number for Italian display"""
        if unit == '€':
            if abs(value) >= 1_000_000:
                return f"€{value/1_000_000:.1f}M"
            elif abs(value) >= 1_000:
                return f"€{value/1_000:.0f}K"
            else:
                return f"€{value:,.0f}"
        elif unit == '%':
            return f"{value:.1f}%"
        elif unit == 'x':
            return f"{value:.2f}x"
        else:
            return f"{value:,.0f}"

    def _calculate_trend(self, values: List[float]) -> str:
        """
        Calculate trend from values (oldest to newest)

        Returns: 'crescente', 'decrescente', 'stabile', 'volatile'
        """
        if len(values) < 2:
            return 'stabile'

        # Calculate percentage changes
        changes = []
        for i in range(1, len(values)):
            if values[i-1] != 0:
                pct_change = ((values[i] - values[i-1]) / abs(values[i-1])) * 100
                changes.append(pct_change)

        if not changes:
            return 'stabile'

        avg_change = sum(changes) / len(changes)
        std_dev = (sum((x - avg_change) ** 2 for x in changes) / len(changes)) ** 0.5

        # Determine trend
        if std_dev > 30:  # High volatility
            return 'volatile'
        elif abs(avg_change) < 5:  # Small changes
            return 'stabile'
        elif avg_change > 0:
            return 'crescente'
        else:
            return 'decrescente'

    def generate_comment(
        self,
        metric_id: str,
        metric_title: str,
        values: List[Dict[str, Any]],
        unit: str = '€',
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a brief comment for a financial metric

        Args:
            metric_id: Metric identifier (e.g., 'ebitda', 'roi')
            metric_title: Human-readable title
            values: List of {year, value} dicts (ordered oldest to newest)
            unit: Unit of measurement ('€', '%', 'x')
            context: Additional context (company name, sector, etc.)

        Returns:
            A brief Italian comment (~250 chars) analyzing the trend
        """
        if not values or len(values) < 2:
            return "Dati insufficienti per l'analisi del trend."

        # Extract years and values
        years = [v['year'] for v in values]
        nums = [v['value'] for v in values]

        # Calculate trend
        trend = self._calculate_trend(nums)

        # Format values for display
        formatted_values = [
            f"{year}: {self._format_number(val, unit)}"
            for year, val in zip(years, nums)
        ]

        # Calculate YoY change (latest year vs previous)
        if len(nums) >= 2 and nums[-2] != 0:
            yoy_change = ((nums[-1] - nums[-2]) / abs(nums[-2])) * 100
        else:
            yoy_change = 0

        # Build prompt for Claude
        prompt = f"""Analizza questo indicatore finanziario e genera un commento breve (massimo 250 caratteri) in italiano.

INDICATORE: {metric_title}
VALORI: {', '.join(formatted_values)}
TREND: {trend}
VARIAZIONE ANNO SU ANNO: {yoy_change:+.1f}%
"""

        if context:
            if 'company_name' in context:
                prompt += f"\nAZIENDA: {context['company_name']}"
            if 'sector' in context:
                prompt += f"\nSETTORE: {context['sector']}"

        prompt += """

ISTRUZIONI:
1. Scrivi un commento di massimo 250 caratteri
2. Usa linguaggio professionale e tecnico (per analisti finanziari)
3. Menziona il valore più recente e il trend
4. Se il trend è negativo, suggerisci cosa monitorare
5. Se il trend è positivo, evidenzia i punti di forza
6. Usa numeri concreti dal dataset
7. NON usare frasi generiche
8. Risposta SOLO il commento, niente altro

COMMENTO:"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=150,  # ~250 chars
                temperature=0.3,  # Low temperature for consistency
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            comment = response.content[0].text.strip()

            # Ensure it's not too long
            if len(comment) > 280:
                comment = comment[:277] + "..."

            return comment

        except Exception as e:
            print(f"Error generating comment for {metric_id}: {e}")
            return f"Analisi del trend {trend} per {metric_title}."

    def generate_section_comments(
        self,
        section_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Generate comments for all metrics in a section

        Args:
            section_data: Section data with 'metrics' array
            context: Additional context

        Returns:
            Dict mapping metric_id to generated comment
        """
        comments = {}

        metrics = section_data.get('metrics', [])
        for metric in metrics:
            metric_id = metric.get('id')
            metric_title = metric.get('title')
            chart_data = metric.get('chartData', [])
            unit = metric.get('unit', '€')

            if not metric_id or not chart_data:
                continue

            print(f"  Generating comment for: {metric_title}...")

            comment = self.generate_comment(
                metric_id=metric_id,
                metric_title=metric_title,
                values=chart_data,
                unit=unit,
                context=context
            )

            comments[metric_id] = comment

        return comments


# Test function
if __name__ == "__main__":
    # Test with sample data
    generator = AICommentGenerator()

    # Test data: EBITDA
    test_data = {
        'sectionTitle': 'Test Section',
        'metrics': [
            {
                'id': 'ebitda',
                'title': 'EBITDA - Risultato Operativo Lordo',
                'unit': '€',
                'chartData': [
                    {'year': '2022', 'value': 7233107},
                    {'year': '2023', 'value': 3724357},
                    {'year': '2024', 'value': 2245257},
                ]
            },
            {
                'id': 'roi',
                'title': 'ROI - Return on Investment',
                'unit': '%',
                'chartData': [
                    {'year': '2022', 'value': 30.22},
                    {'year': '2023', 'value': 21.07},
                    {'year': '2024', 'value': 11.01},
                ]
            }
        ]
    }

    context = {
        'company_name': 'I.T.C. S.R.L.',
        'sector': 'Metallurgia'
    }

    print("\n" + "="*80)
    print("AI COMMENT GENERATOR - Test")
    print("="*80 + "\n")

    comments = generator.generate_section_comments(test_data, context)

    for metric_id, comment in comments.items():
        print(f"\n{metric_id.upper()}")
        print("-" * 80)
        print(comment)
        print(f"({len(comment)} chars)")

    print("\n" + "="*80 + "\n")
