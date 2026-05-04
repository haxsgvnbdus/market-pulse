"""
thresholds.py — All configurable signal thresholds for Market Pulse.

Edit values here to tune when buy signals fire and how the email highlights numbers.
No code changes needed elsewhere.
"""

# ── VIX (Fear Index) ──────────────────────────────────────────────────────────
# VIX measures expected 30-day S&P 500 volatility. Spikes indicate panic, which
# historically precede recoveries — the classic contrarian buy signal.

VIX_BUY_SIGNAL = 30     # Above this → "extreme fear", triggers buy signal
VIX_HIGH_FEAR  = 25     # Above this → "high fear", approaching buy zone
VIX_ELEVATED   = 20     # Above this → "elevated" concern
VIX_MODERATE   = 15     # Above this → "moderate"; below → "low fear"

# ── Federal Reserve Rate ──────────────────────────────────────────────────────
# Falling rates = cheaper borrowing = bullish for equities.
# Trend is determined by comparing current rate to 60d and 180d ago.

FED_STABLE_BAND = 0.25  # If total change over 180d is within ±this, trend = "stable"

# ── Margin Debt ───────────────────────────────────────────────────────────────
# Rising margin debt = leveraged speculation = risk. Declining = deleveraging,
# which historically coincides with market bottoms.

MARGIN_DECREASING_QTR =  -5  # Quarterly change below this % AND yearly negative → "decreasing"
MARGIN_INCREASING_QTR =   5  # Quarterly change above this % → "increasing" (bearish)

# ── Sector Leadership ─────────────────────────────────────────────────────────
# Clear sector rotation is a sign of a healthy, directional market.
# Compares top sector's 20-day return to the 3rd-place sector.

SECTOR_LEADER_GAP = 5   # Top sector must outperform 3rd by at least this % (20D return)

# ── Earnings ──────────────────────────────────────────────────────────────────
# Strong earnings in leading sectors = fundamental support for the move.

EARNINGS_HEALTHY_GROWTH_MIN  =  5  # Sector avg earnings growth must exceed this % → "healthy"
EARNINGS_HEALTHY_SECTORS_MIN =  2  # Need at least this many healthy sectors → buy signal

# ── Overall Signal Strength ───────────────────────────────────────────────────
# Counts how many of the 5 metrics are showing a buy signal (0–5).

SIGNAL_STRONG_BUY_MIN   = 4   # 4–5 signals → STRONG_BUY
SIGNAL_MODERATE_BUY_MIN = 3   # 3 signals   → MODERATE_BUY
SIGNAL_WEAK_BUY_MIN     = 2   # 2 signals   → WEAK_BUY
                               # 0–1 signals → NEUTRAL

# ── Email: Bold sector return threshold ──────────────────────────────────────
# In the sector performance table, returns beyond this are shown in bold.

EMAIL_BOLD_RETURN = 5   # Absolute return beyond this % is bolded in the sector table

# ── Email: Analysis text highlight thresholds ─────────────────────────────────
# Percentage values in the AI analysis prose are visually emphasised
# when they cross these thresholds.

EMAIL_HIGHLIGHT_POSITIVE_PCT =  30   # Above this % → large bold green
EMAIL_HIGHLIGHT_NEGATIVE_PCT = -20   # Below this % → large bold red (slightly smaller than positive)
