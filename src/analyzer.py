"""
AI-powered market analysis.

Supports multiple backends:
1. Anthropic (Claude) - requires API key
2. OpenAI (GPT) - requires API key
3. Ollama (local) - free, runs locally
4. Rule-based fallback - no API needed
"""

import os
import json
from typing import Optional
from .models.metrics import MarketPulseReport


def analyze_with_anthropic(report: MarketPulseReport) -> Optional[str]:
    """Use Claude API for analysis."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)

        prompt = _build_analysis_prompt(report)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        return message.content[0].text

    except Exception as e:
        print(f"Anthropic API error: {e}")
        return None


def analyze_with_openai(report: MarketPulseReport) -> Optional[str]:
    """Use OpenAI API for analysis."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        prompt = _build_analysis_prompt(report)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"OpenAI API error: {e}")
        return None


def analyze_with_ollama(report: MarketPulseReport, model: str = "llama3.2") -> Optional[str]:
    """Use local Ollama for analysis (free, runs locally)."""
    try:
        import requests

        prompt = _build_analysis_prompt(report)

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=60
        )

        if response.status_code == 200:
            return response.json().get("response")
        return None

    except Exception as e:
        print(f"Ollama error: {e}")
        return None


def analyze_rule_based(report: MarketPulseReport) -> str:
    """Fallback rule-based analysis when no AI API is available."""
    lines = []
    lines.append("## Market Pulse Analysis\n")

    # VIX Analysis
    vix = report.vix
    if vix.current:
        if vix.is_buy_signal:
            lines.append(f"**VIX ({vix.current})**: EXTREME FEAR - Historically a contrarian buy signal. "
                        f"Market panic often creates buying opportunities.")
        elif vix.fear_level == "high_fear":
            lines.append(f"**VIX ({vix.current})**: HIGH FEAR - Elevated volatility, approaching buy zone.")
        elif vix.fear_level == "elevated":
            lines.append(f"**VIX ({vix.current})**: ELEVATED - Some concern in markets, watch for escalation.")
        else:
            lines.append(f"**VIX ({vix.current})**: CALM - Low fear, markets complacent.")

    # Fed Rate Analysis
    fed = report.fed_rate
    if fed.current:
        if fed.is_buy_signal:
            lines.append(f"\n**Fed Rate ({fed.current}%)**: EASING CYCLE - {fed.trend_description} "
                        f"Lower rates support asset prices.")
        elif fed.trend == "upward":
            lines.append(f"\n**Fed Rate ({fed.current}%)**: TIGHTENING - Headwind for equities.")
        else:
            lines.append(f"\n**Fed Rate ({fed.current}%)**: {fed.trend_description or 'Stable'}")

    # Margin Debt Analysis
    margin = report.margin_debt
    if margin.current_billions:
        if margin.is_buy_signal:
            lines.append(f"\n**Margin Debt (${margin.current_billions}B)**: DELEVERAGING - "
                        f"{margin.trend_description} Reduced leverage can signal bottoming.")
        else:
            lines.append(f"\n**Margin Debt (${margin.current_billions}B)**: {margin.trend_description}")

    # Sector Analysis
    sectors = report.sectors
    if sectors.leading_sectors:
        lines.append(f"\n**Leading Sectors**: {', '.join(sectors.leading_sectors)}")
        if sectors.has_clear_leaders:
            lines.append("Clear sector leadership detected - positive for stock picking.")
        if sectors.high_attention_sectors:
            lines.append(f"High volume/attention: {', '.join(sectors.high_attention_sectors)}")

    # Earnings Analysis
    earnings = report.earnings
    if earnings.healthy_sectors:
        lines.append(f"\n**Strong Earnings Sectors**: {', '.join(earnings.healthy_sectors)}")
        lines.append("Positive earnings growth supports fundamental case.")

    # Overall Signal
    lines.append(f"\n---\n**Overall Signal**: {report.signal_strength} ({report.buy_signals_count}/5 buy signals)")

    if report.signal_strength == "STRONG_BUY":
        lines.append("\nMultiple indicators align for potential buying opportunity. Consider averaging into positions.")
    elif report.signal_strength == "MODERATE_BUY":
        lines.append("\nConditions improving. Watch for additional confirmation.")
    elif report.signal_strength == "WEAK_BUY":
        lines.append("\nMixed signals. Patience recommended.")
    else:
        lines.append("\nNo clear buy signal. Continue monitoring.")

    return "\n".join(lines)


def _build_analysis_prompt(report: MarketPulseReport) -> str:
    """Build the prompt for AI analysis."""
    data = json.dumps(report.to_dict(), indent=2, default=str)

    return f"""You are a market analyst. Analyze these 5 key metrics for stock buying opportunities:

1. VIX > 30 = extreme fear (contrarian buy signal)
2. Fed rate downward trend = easing cycle (bullish)
3. Margin debt decreasing = deleveraging (potential bottom)
4. Clear leading sectors = market health
5. Strong earnings in leading sectors = fundamental support

DATA:
{data}

Provide a concise analysis (200-300 words):
- Assess each metric's current signal
- Identify the strongest/weakest signals
- Give an overall market read
- Suggest actionable next steps
- Note any data gaps or caveats

Be direct and practical. Focus on what matters for timing entry points."""


def get_ai_analysis(report: MarketPulseReport) -> str:
    """
    Get AI analysis using available backend.
    Tries in order: Anthropic > OpenAI > Ollama > Rule-based
    """
    # Try Anthropic first
    analysis = analyze_with_anthropic(report)
    if analysis:
        return f"*Analysis by Claude*\n\n{analysis}"

    # Try OpenAI
    analysis = analyze_with_openai(report)
    if analysis:
        return f"*Analysis by GPT*\n\n{analysis}"

    # Try Ollama (local)
    analysis = analyze_with_ollama(report)
    if analysis:
        return f"*Analysis by Ollama (local)*\n\n{analysis}"

    # Fallback to rule-based
    return analyze_rule_based(report)
