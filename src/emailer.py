"""
Email sender using Gmail SMTP.

Setup:
1. Enable 2-Factor Authentication on your Google account
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use that 16-character password in GMAIL_APP_PASSWORD
"""

import os
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional
from .models.metrics import MarketPulseReport
from .thresholds import EMAIL_HIGHLIGHT_POSITIVE_PCT, EMAIL_HIGHLIGHT_NEGATIVE_PCT, EMAIL_BOLD_RETURN


def send_email_report(
    report: MarketPulseReport,
    recipient: Optional[str] = None
) -> bool:
    gmail_address = os.getenv("GMAIL_ADDRESS")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")
    recipients_raw = recipient or os.getenv("EMAIL_RECIPIENT", "")
    recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]

    if not all([gmail_address, gmail_password, recipients]):
        print("Error: Gmail credentials not configured. Check .env file.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = _build_subject(report)
        msg["From"] = gmail_address
        msg["To"] = ", ".join(recipients)

        msg.attach(MIMEText(_build_text_report(report), "plain"))
        msg.attach(MIMEText(_build_html_report(report), "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_address, gmail_password)
            server.sendmail(gmail_address, recipients, msg.as_string())

        print(f"Report sent to {', '.join(recipients)}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("Gmail authentication failed. Check your app password.")
        return False
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _highlight_pcts(html: str) -> str:
    """Visually emphasise large positive/negative percentages in prose text."""
    def replacer(m):
        try:
            val = float(m.group(1))
        except ValueError:
            return m.group(0)
        if val > EMAIL_HIGHLIGHT_POSITIVE_PCT:
            return (
                f'<span style="color:#16a34a;font-size:22px;font-weight:900;'
                f'letter-spacing:-0.5px;">{m.group(0)}</span>'
            )
        if val < EMAIL_HIGHLIGHT_NEGATIVE_PCT:
            return (
                f'<span style="color:#dc2626;font-size:18px;font-weight:900;'
                f'letter-spacing:-0.5px;">{m.group(0)}</span>'
            )
        return m.group(0)

    # Match percentages in text content — skip values inside HTML tag attributes
    return re.sub(r'(?<![="\'#;:\w])([+\-]?\d+\.?\d*)%', replacer, html)


def _md_to_html(text: str) -> str:
    if not text:
        return ""
    # Headers
    text = re.sub(r'^### (.+)$', r'<h4 style="margin:14px 0 4px;color:#1f2937;font-size:14px;">\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$',  r'<h3 style="margin:18px 0 6px;color:#1f2937;font-size:15px;">\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$',   r'<h2 style="margin:18px 0 8px;color:#1f2937;font-size:17px;">\1</h2>', text, flags=re.MULTILINE)
    # Bold and italic
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    text = re.sub(r'\*\*(.+?)\*\*',     r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*',         r'<em>\1</em>', text)
    # Bullet lists — collect consecutive items into <ul>
    def replace_list(m):
        items = re.sub(r'^[*\-] (.+)$', r'<li style="margin:3px 0;">\1</li>', m.group(), flags=re.MULTILINE)
        return f'<ul style="margin:8px 0;padding-left:22px;">{items}</ul>'
    text = re.sub(r'(?:^[*\-] .+\n?)+', replace_list, text, flags=re.MULTILINE)
    # Horizontal rules
    text = re.sub(r'^---+$', '<hr style="border:none;border-top:1px solid #e5e7eb;margin:12px 0;">', text, flags=re.MULTILINE)
    # Paragraphs (blank lines)
    paragraphs = re.split(r'\n{2,}', text.strip())
    html_parts = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if re.match(r'^<(h[1-6]|ul|hr)', p):
            html_parts.append(p)
        else:
            p = p.replace('\n', '<br>')
            html_parts.append(f'<p style="margin:8px 0;line-height:1.7;">{p}</p>')
    return "\n".join(html_parts)


def _fmt_pct(val, decimals=1):
    if val is None:
        return "—"
    sign = "+" if val > 0 else ""
    return f"{sign}{val:.{decimals}f}%"


def _pct_color(val):
    if val is None:
        return "#6b7280"
    if val > 0:
        return "#16a34a"
    if val < 0:
        return "#dc2626"
    return "#6b7280"


def _fmt_val(val, suffix="", prefix="", decimals=2):
    if val is None:
        return "—"
    return f"{prefix}{val:.{decimals}f}{suffix}"


# ---------------------------------------------------------------------------
# Subject
# ---------------------------------------------------------------------------

def _build_subject(report: MarketPulseReport) -> str:
    signal = report.signal_strength
    vix = report.vix.current or "N/A"
    date = datetime.now().strftime("%m/%d %H:%M")
    emoji = {"STRONG_BUY": "🟢", "MODERATE_BUY": "🟡", "WEAK_BUY": "🟠", "NEUTRAL": "⚪"}.get(signal, "⚪")
    return f"{emoji} Hannie Market Pulse: {signal} | VIX {vix} | {report.buy_signals_count}/5 signals | {date}"


# ---------------------------------------------------------------------------
# Plain text
# ---------------------------------------------------------------------------

def _build_text_report(report: MarketPulseReport) -> str:
    lines = [
        "=" * 60,
        "MARKET PULSE REPORT",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * 60,
        f"OVERALL: {report.signal_strength} ({report.buy_signals_count}/5 buy signals)",
        "",
        "--- METRICS ---",
    ]

    vix = report.vix
    fed = report.fed_rate
    margin = report.margin_debt

    lines.append(f"1. VIX:        {vix.current or 'N/A'} ({vix.fear_level}) {'✓ BUY' if vix.is_buy_signal else ''}")
    lines.append(f"   History:  5d:{vix.day_5_ago}  20d:{vix.day_20_ago}  60d:{vix.day_60_ago}  90d:{vix.day_90_ago}  180d:{vix.day_180_ago}  1yr:{vix.year_ago}")

    lines.append(f"2. Fed Rate:   {fed.current or 'N/A'}% ({fed.trend}) {'✓ BUY' if fed.is_buy_signal else ''}")
    lines.append(f"   History:  5d:{fed.day_5_ago}%  20d:{fed.day_20_ago}%  60d:{fed.day_60_ago}%  90d:{fed.day_90_ago}%  180d:{fed.day_180_ago}%  1yr:{fed.year_ago}%")

    lines.append(f"3. Margin Debt:{_fmt_val(margin.current_billions, 'B', '$')} ({margin.trend}) {'✓ BUY' if margin.is_buy_signal else ''}")
    lines.append(f"   History:  Q-1:{_fmt_val(margin.previous_quarter and margin.previous_quarter/1000, 'B', '$')}  Q-2:{_fmt_val(margin.two_quarters_ago and margin.two_quarters_ago/1000, 'B', '$')}  Q-3:{_fmt_val(margin.three_quarters_ago and margin.three_quarters_ago/1000, 'B', '$')}  1yr:{_fmt_val(margin.year_ago and margin.year_ago/1000, 'B', '$')}")

    sectors = report.sectors
    lines.append(f"4. Sectors:    Leaders: {', '.join(sectors.leading_sectors)} {'✓ BUY' if sectors.has_clear_leaders else ''}")
    lines.append(f"   Lagging:  {', '.join(sectors.lagging_sectors)}")

    earnings = report.earnings
    lines.append(f"5. Earnings:   Healthy: {', '.join(earnings.healthy_sectors)} {'✓ BUY' if earnings.has_strong_earnings else ''}")

    lines += ["", "--- SECTOR RETURNS ---",
              f"{'Sector':<25} {'1D':>6} {'5D':>6} {'20D':>7} {'60D':>7} {'90D':>7} {'180D':>7} {'1YR':>7}"]
    lines.append("-" * 75)
    for s in sorted(sectors.sectors, key=lambda x: x.day_20_return, reverse=True):
        lines.append(
            f"{s.name:<25} {_fmt_pct(s.day_return):>6} {_fmt_pct(s.day_5_return):>6} "
            f"{_fmt_pct(s.day_20_return):>7} {_fmt_pct(s.day_60_return):>7} "
            f"{_fmt_pct(s.day_90_return):>7} {_fmt_pct(s.day_180_return):>7} {_fmt_pct(s.year_return):>7}"
        )

    lines += ["", "--- EARNINGS ---"]
    for sector, summary in earnings.sector_summaries.items():
        avg = summary.get("avg_earnings_growth")
        lines.append(f"{sector}: avg earnings growth {_fmt_pct(avg)}  ({summary.get('positive_growth_count', 0)}/{summary.get('companies_analyzed', 0)} positive)")
        for company in [c for c in earnings.companies if c.sector == sector]:
            lines.append(
                f"  {company.ticker:<6} PE:{_fmt_val(company.pe_ratio, decimals=1)}  "
                f"RevGrowth:{_fmt_pct(company.revenue_growth and company.revenue_growth*100)}  "
                f"EarnGrowth:{_fmt_pct(company.earnings_growth and company.earnings_growth*100)}  "
                f"Rating:{company.analyst_rating or '—'}"
            )

    lines += ["", "--- AI ANALYSIS ---", "", report.ai_analysis or "No AI analysis available"]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------

def _build_html_report(report: MarketPulseReport) -> str:
    signal_color = {
        "STRONG_BUY": "#16a34a",
        "MODERATE_BUY": "#ca8a04",
        "WEAK_BUY": "#ea580c",
        "NEUTRAL": "#6b7280"
    }.get(report.signal_strength, "#6b7280")

    vix = report.vix
    fed = report.fed_rate
    margin = report.margin_debt
    sectors = report.sectors
    earnings = report.earnings

    def section_header(title):
        return f'''
        <tr>
          <td colspan="99" style="background:#1f2937;color:white;padding:10px 16px;font-size:13px;font-weight:bold;letter-spacing:0.05em;text-transform:uppercase;">
            {title}
          </td>
        </tr>'''

    def signal_row(num, name, value, detail, is_signal):
        bg = "#f0fdf4" if is_signal else "#ffffff"
        badge = '<span style="background:#16a34a;color:white;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold;">BUY</span>' if is_signal else ""
        return f'''
        <tr style="background:{bg};">
          <td style="padding:10px 16px;color:#6b7280;font-size:12px;">{num}</td>
          <td style="padding:10px 8px;font-weight:bold;font-size:14px;">{name}</td>
          <td style="padding:10px 8px;font-size:14px;">{value}</td>
          <td style="padding:10px 8px;color:#6b7280;font-size:13px;">{detail}</td>
          <td style="padding:10px 16px;">{badge}</td>
        </tr>'''

    def hist_header_row(labels):
        cells = "".join(
            f'<th style="padding:6px 10px;text-align:right;font-size:11px;color:#6b7280;font-weight:normal;border-bottom:1px solid #e5e7eb;">{l}</th>'
            for l in labels
        )
        return f"<tr>{cells}</tr>"

    def hist_value_row(label, values, bold_first=True):
        label_cell = f'<td style="padding:6px 10px;font-size:13px;font-weight:bold;border-bottom:1px solid #f3f4f6;white-space:nowrap;">{label}</td>'
        val_cells = ""
        for i, v in enumerate(values):
            fw = "bold" if (bold_first and i == 0) else "normal"
            color = "#111827" if (bold_first and i == 0) else "#374151"
            val_cells += f'<td style="padding:6px 10px;text-align:right;font-size:13px;font-weight:{fw};color:{color};border-bottom:1px solid #f3f4f6;">{v if v is not None else "—"}</td>'
        return f"<tr>{label_cell}{val_cells}</tr>"

    def pct_cell(val):
        color = _pct_color(val)
        fw = "bold" if val and abs(val) > EMAIL_BOLD_RETURN else "normal"
        return f'<td style="padding:6px 10px;text-align:right;font-size:12px;color:{color};font-weight:{fw};border-bottom:1px solid #f3f4f6;white-space:nowrap;">{_fmt_pct(val)}</td>'

    # --- Summary table ---
    summary_rows = "".join([
        signal_row(1, "VIX", vix.current or "N/A", vix.fear_level.replace("_", " ").title(), vix.is_buy_signal),
        signal_row(2, "Fed Rate", f"{fed.current or 'N/A'}%", fed.trend.replace("_", " ").title(), fed.is_buy_signal),
        signal_row(3, "Margin Debt", f"${margin.current_billions or 'N/A'}B", margin.trend.replace("_", " ").title(), margin.is_buy_signal),
        signal_row(4, "Sector Leaders", ", ".join(sectors.leading_sectors[:2]) or "N/A", "Clear leaders" if sectors.has_clear_leaders else "No clear leader", sectors.has_clear_leaders),
        signal_row(5, "Earnings", ", ".join(earnings.healthy_sectors[:2]) or "N/A", "Strong" if earnings.has_strong_earnings else "Mixed", earnings.has_strong_earnings),
    ])

    # --- Historical trends ---
    hist_section = f'''
    <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;margin-bottom:0;">
      {section_header("Historical Trends")}
      <tr>
        <td style="padding:16px;" valign="top">
          <table cellpadding="0" cellspacing="0" style="border-collapse:collapse;width:100%;">
            {hist_header_row(["", "Now", "5d ago", "20d ago", "60d ago", "90d ago", "180d ago", "1yr ago"])}
            {hist_value_row("VIX", [vix.current, vix.day_5_ago, vix.day_20_ago, vix.day_60_ago, vix.day_90_ago, vix.day_180_ago, vix.year_ago])}
            {hist_value_row("Fed Rate %", [fed.current, fed.day_5_ago, fed.day_20_ago, fed.day_60_ago, fed.day_90_ago, fed.day_180_ago, fed.year_ago])}
          </table>
        </td>
      </tr>
      <tr>
        <td style="padding:0 16px 16px;">
          <table cellpadding="0" cellspacing="0" style="border-collapse:collapse;width:100%;">
            {hist_header_row(["", "Now ($B)", "Q-1 ($B)", "Q-2 ($B)", "Q-3 ($B)", "1yr ago ($B)", "2yr ago ($B)"])}
            {hist_value_row("Margin Debt",
              [margin.current_billions,
               _fmt_val(margin.previous_quarter and margin.previous_quarter/1000, decimals=2),
               _fmt_val(margin.two_quarters_ago and margin.two_quarters_ago/1000, decimals=2),
               _fmt_val(margin.three_quarters_ago and margin.three_quarters_ago/1000, decimals=2),
               _fmt_val(margin.year_ago and margin.year_ago/1000, decimals=2),
               _fmt_val(margin.two_years_ago and margin.two_years_ago/1000, decimals=2)])}
          </table>
        </td>
      </tr>
    </table>'''

    # --- Sector performance table ---
    sorted_sectors = sorted(sectors.sectors, key=lambda x: x.day_20_return, reverse=True)
    leading_names = set(sectors.leading_sectors)
    lagging_names = set(sectors.lagging_sectors)

    sector_rows = ""
    for s in sorted_sectors:
        if s.name in leading_names:
            bg = "#f0fdf4"
        elif s.name in lagging_names:
            bg = "#fff7f7"
        else:
            bg = "#ffffff"
        name_cell = f'<td style="padding:6px 10px;font-size:13px;font-weight:bold;border-bottom:1px solid #f3f4f6;background:{bg};white-space:nowrap;">{s.name}</td>'
        ticker_cell = f'<td style="padding:6px 10px;font-size:11px;color:#6b7280;border-bottom:1px solid #f3f4f6;background:{bg};">{s.ticker}</td>'
        price_cell = f'<td style="padding:6px 10px;font-size:12px;text-align:right;border-bottom:1px solid #f3f4f6;background:{bg};">${s.current_price}</td>'
        sector_rows += f"<tr style='background:{bg};'>{name_cell}{ticker_cell}{price_cell}{pct_cell(s.day_return)}{pct_cell(s.day_5_return)}{pct_cell(s.day_20_return)}{pct_cell(s.day_60_return)}{pct_cell(s.day_90_return)}{pct_cell(s.day_180_return)}{pct_cell(s.year_return)}</tr>"

    sector_section = f'''
    <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;margin-bottom:0;">
      {section_header("Sector Performance")}
      <tr>
        <td style="padding:0;">
          <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
            <tr style="background:#f9fafb;">
              <th style="padding:8px 10px;text-align:left;font-size:11px;color:#6b7280;font-weight:normal;border-bottom:2px solid #e5e7eb;">Sector</th>
              <th style="padding:8px 10px;text-align:left;font-size:11px;color:#6b7280;font-weight:normal;border-bottom:2px solid #e5e7eb;">ETF</th>
              <th style="padding:8px 10px;text-align:right;font-size:11px;color:#6b7280;font-weight:normal;border-bottom:2px solid #e5e7eb;">Price</th>
              <th style="padding:8px 10px;text-align:right;font-size:11px;color:#6b7280;font-weight:normal;border-bottom:2px solid #e5e7eb;">1D</th>
              <th style="padding:8px 10px;text-align:right;font-size:11px;color:#6b7280;font-weight:normal;border-bottom:2px solid #e5e7eb;">5D</th>
              <th style="padding:8px 10px;text-align:right;font-size:11px;color:#6b7280;font-weight:normal;border-bottom:2px solid #e5e7eb;">20D</th>
              <th style="padding:8px 10px;text-align:right;font-size:11px;color:#6b7280;font-weight:normal;border-bottom:2px solid #e5e7eb;">60D</th>
              <th style="padding:8px 10px;text-align:right;font-size:11px;color:#6b7280;font-weight:normal;border-bottom:2px solid #e5e7eb;">90D</th>
              <th style="padding:8px 10px;text-align:right;font-size:11px;color:#6b7280;font-weight:normal;border-bottom:2px solid #e5e7eb;">180D</th>
              <th style="padding:8px 10px;text-align:right;font-size:11px;color:#6b7280;font-weight:normal;border-bottom:2px solid #e5e7eb;">1YR</th>
            </tr>
            {sector_rows}
          </table>
        </td>
      </tr>
    </table>'''

    # --- Earnings breakdown ---
    earnings_rows = ""
    for sector_name, summary in earnings.sector_summaries.items():
        avg = summary.get("avg_earnings_growth")
        is_healthy = sector_name in earnings.healthy_sectors
        badge = '<span style="background:#16a34a;color:white;padding:1px 6px;border-radius:3px;font-size:10px;margin-left:6px;">STRONG</span>' if is_healthy else ""
        earnings_rows += f'''
        <tr style="background:#f9fafb;">
          <td colspan="8" style="padding:8px 10px;font-weight:bold;font-size:13px;border-bottom:1px solid #e5e7eb;">
            {sector_name}{badge}
            <span style="color:#6b7280;font-weight:normal;font-size:12px;margin-left:8px;">avg earnings growth: {_fmt_pct(avg)}</span>
          </td>
        </tr>'''
        for company in [c for c in earnings.companies if c.sector == sector_name]:
            rev = _fmt_pct(company.revenue_growth * 100 if company.revenue_growth else None)
            earn = _fmt_pct(company.earnings_growth * 100 if company.earnings_growth else None)
            rev_color = _pct_color(company.revenue_growth * 100 if company.revenue_growth else None)
            earn_color = _pct_color(company.earnings_growth * 100 if company.earnings_growth else None)
            margin_pct = _fmt_pct(company.profit_margin * 100 if company.profit_margin else None)
            # colour current vs prev close
            if company.current_price and company.prev_close:
                cur_color = "#16a34a" if company.current_price >= company.prev_close else "#dc2626"
            else:
                cur_color = "#111827"
            earnings_rows += f'''
            <tr>
              <td style="padding:6px 10px 6px 20px;font-size:12px;font-weight:bold;border-bottom:1px solid #f3f4f6;">{company.ticker}</td>
              <td style="padding:6px 4px;font-size:11px;color:#6b7280;border-bottom:1px solid #f3f4f6;">{company.company_name}</td>
              <td style="padding:6px 8px;font-size:12px;text-align:right;color:#6b7280;border-bottom:1px solid #f3f4f6;">{_fmt_val(company.prev_close, decimals=2)}</td>
              <td style="padding:6px 8px;font-size:12px;text-align:right;border-bottom:1px solid #f3f4f6;">{_fmt_val(company.open_price, decimals=2)}</td>
              <td style="padding:6px 8px;font-size:12px;text-align:right;font-weight:bold;color:{cur_color};border-bottom:1px solid #f3f4f6;">{_fmt_val(company.current_price, decimals=2)}</td>
              <td style="padding:6px 8px;font-size:12px;text-align:right;border-bottom:1px solid #f3f4f6;">{_fmt_val(company.market_cap_b, 'B', '$', 0)}</td>
              <td style="padding:6px 8px;font-size:12px;text-align:right;border-bottom:1px solid #f3f4f6;">{_fmt_val(company.pe_ratio, decimals=1)}</td>
              <td style="padding:6px 8px;font-size:12px;text-align:right;color:{rev_color};border-bottom:1px solid #f3f4f6;">{rev}</td>
              <td style="padding:6px 8px;font-size:12px;text-align:right;color:{earn_color};font-weight:bold;border-bottom:1px solid #f3f4f6;">{earn}</td>
              <td style="padding:6px 8px;font-size:12px;text-align:right;border-bottom:1px solid #f3f4f6;">{margin_pct}</td>
              <td style="padding:6px 10px;font-size:11px;color:#6b7280;border-bottom:1px solid #f3f4f6;">{company.analyst_rating or "—"}</td>
            </tr>'''
            if company.quarterly_data:
                q_headers = "".join(
                    f'<td style="padding:3px 8px;text-align:right;font-size:10px;color:#9ca3af;">{q.quarter}</td>'
                    for q in company.quarterly_data
                )
                q_rev = "".join(
                    f'<td style="padding:3px 8px;text-align:right;font-size:11px;color:#374151;">{_fmt_val(q.revenue_b, "B", "$")}</td>'
                    for q in company.quarterly_data
                )
                q_net = "".join(
                    f'<td style="padding:3px 8px;text-align:right;font-size:11px;color:{_pct_color(q.net_income_b)};">{_fmt_val(q.net_income_b, "B", "$")}</td>'
                    for q in company.quarterly_data
                )
                earnings_rows += f'''
                <tr style="background:#fafafa;">
                  <td style="padding:0 10px 6px 28px;border-bottom:1px solid #f3f4f6;" colspan="11">
                    <table cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
                      <tr><td style="padding:3px 8px;font-size:10px;color:#9ca3af;white-space:nowrap;">Quarter</td>{q_headers}</tr>
                      <tr><td style="padding:3px 8px;font-size:10px;color:#6b7280;white-space:nowrap;">Revenue</td>{q_rev}</tr>
                      <tr><td style="padding:3px 8px;font-size:10px;color:#6b7280;white-space:nowrap;">Net Income</td>{q_net}</tr>
                    </table>
                  </td>
                </tr>'''

    earnings_section = f'''
    <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;margin-bottom:0;">
      {section_header("Earnings Breakdown")}
      <tr>
        <td style="padding:0;">
          <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
            <tr style="background:#f9fafb;">
              <th style="padding:8px 10px 8px 20px;text-align:left;font-size:11px;color:#6b7280;font-weight:normal;border-bottom:2px solid #e5e7eb;">Ticker</th>
              <th style="padding:8px 4px;text-align:left;font-size:11px;color:#6b7280;font-weight:normal;border-bottom:2px solid #e5e7eb;">Company</th>
              <th style="padding:8px 8px;text-align:right;font-size:11px;color:#6b7280;font-weight:normal;border-bottom:2px solid #e5e7eb;">Prev Close</th>
              <th style="padding:8px 8px;text-align:right;font-size:11px;color:#6b7280;font-weight:normal;border-bottom:2px solid #e5e7eb;">Open</th>
              <th style="padding:8px 8px;text-align:right;font-size:11px;color:#6b7280;font-weight:normal;border-bottom:2px solid #e5e7eb;">Current</th>
              <th style="padding:8px 8px;text-align:right;font-size:11px;color:#6b7280;font-weight:normal;border-bottom:2px solid #e5e7eb;">Mkt Cap</th>
              <th style="padding:8px 8px;text-align:right;font-size:11px;color:#6b7280;font-weight:normal;border-bottom:2px solid #e5e7eb;">PE</th>
              <th style="padding:8px 8px;text-align:right;font-size:11px;color:#6b7280;font-weight:normal;border-bottom:2px solid #e5e7eb;">Rev Growth</th>
              <th style="padding:8px 8px;text-align:right;font-size:11px;color:#6b7280;font-weight:normal;border-bottom:2px solid #e5e7eb;">Earn Growth</th>
              <th style="padding:8px 8px;text-align:right;font-size:11px;color:#6b7280;font-weight:normal;border-bottom:2px solid #e5e7eb;">Margin</th>
              <th style="padding:8px 10px;text-align:left;font-size:11px;color:#6b7280;font-weight:normal;border-bottom:2px solid #e5e7eb;">Rating</th>
            </tr>
            {earnings_rows}
          </table>
        </td>
      </tr>
    </table>'''

    analysis_html = _highlight_pcts(_md_to_html(report.ai_analysis or "No AI analysis available"))

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:20px;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="max-width:800px;margin:0 auto;">
    <tr><td>

      <!-- Header -->
      <table width="100%" cellpadding="0" cellspacing="0" style="background:{signal_color};border-radius:10px 10px 0 0;overflow:hidden;margin-bottom:0;">
        <tr>
          <td style="padding:24px;text-align:center;color:white;">
            <div style="font-size:22px;font-weight:bold;margin-bottom:4px;">Hannie Market Pulse</div>
            <div style="font-size:34px;font-weight:900;letter-spacing:-1px;">{report.signal_strength}</div>
            <div style="font-size:15px;opacity:0.9;margin-top:4px;">{report.buy_signals_count} of 5 buy signals &nbsp;·&nbsp; {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
          </td>
        </tr>
      </table>

      <!-- Signal Summary -->
      <table width="100%" cellpadding="0" cellspacing="0" style="background:white;border-collapse:collapse;">
        {section_header("Signal Summary")}
        {summary_rows}
      </table>

      <!-- Historical Trends -->
      <table width="100%" cellpadding="0" cellspacing="0" style="background:white;border-collapse:collapse;border-top:4px solid #f3f4f6;">
        {hist_section}
      </table>

      <!-- Sector Performance -->
      <table width="100%" cellpadding="0" cellspacing="0" style="background:white;border-collapse:collapse;border-top:4px solid #f3f4f6;">
        {sector_section}
      </table>

      <!-- Earnings -->
      <table width="100%" cellpadding="0" cellspacing="0" style="background:white;border-collapse:collapse;border-top:4px solid #f3f4f6;">
        {earnings_section}
      </table>

      <!-- AI Analysis -->
      <table width="100%" cellpadding="0" cellspacing="0" style="background:white;border-collapse:collapse;border-top:4px solid #f3f4f6;border-radius:0 0 10px 10px;overflow:hidden;">
        {section_header("AI Analysis")}
        <tr>
          <td style="padding:20px 16px;color:#374151;font-size:14px;line-height:1.7;">
            {analysis_html}
          </td>
        </tr>
        <tr>
          <td style="padding:12px 16px;background:#f9fafb;color:#9ca3af;font-size:11px;text-align:center;">
            Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} · Hannie Market Pulse
          </td>
        </tr>
      </table>

    </td></tr>
  </table>
</body>
</html>"""
