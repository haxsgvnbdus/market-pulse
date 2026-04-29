"""
Email sender using Gmail SMTP.

Setup:
1. Enable 2-Factor Authentication on your Google account
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use that 16-character password in GMAIL_APP_PASSWORD
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional
from .models.metrics import MarketPulseReport


def send_email_report(
    report: MarketPulseReport,
    recipient: Optional[str] = None
) -> bool:
    """
    Send market pulse report via Gmail SMTP.

    Args:
        report: The MarketPulseReport to send
        recipient: Override recipient email (defaults to EMAIL_RECIPIENT env var)

    Returns:
        True if sent successfully, False otherwise
    """
    gmail_address = os.getenv("GMAIL_ADDRESS")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")
    recipient = recipient or os.getenv("EMAIL_RECIPIENT")

    if not all([gmail_address, gmail_password, recipient]):
        print("Error: Gmail credentials not configured. Check .env file.")
        return False

    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = _build_subject(report)
        msg["From"] = gmail_address
        msg["To"] = recipient

        # Plain text version
        text_content = _build_text_report(report)
        msg.attach(MIMEText(text_content, "plain"))

        # HTML version
        html_content = _build_html_report(report)
        msg.attach(MIMEText(html_content, "html"))

        # Send via Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_address, gmail_password)
            server.sendmail(gmail_address, recipient, msg.as_string())

        print(f"Report sent to {recipient}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("Gmail authentication failed. Check your app password.")
        return False
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def _build_subject(report: MarketPulseReport) -> str:
    """Build email subject line."""
    signal = report.signal_strength
    vix = report.vix.current or "N/A"
    date = datetime.now().strftime("%m/%d %H:%M")

    emoji = {
        "STRONG_BUY": "🟢",
        "MODERATE_BUY": "🟡",
        "WEAK_BUY": "🟠",
        "NEUTRAL": "⚪"
    }.get(signal, "⚪")

    return f"{emoji} Market Pulse: {signal} | VIX {vix} | {report.buy_signals_count}/5 signals | {date}"


def _build_text_report(report: MarketPulseReport) -> str:
    """Build plain text version of report."""
    lines = [
        "=" * 50,
        "MARKET PULSE REPORT",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * 50,
        "",
        f"OVERALL: {report.signal_strength} ({report.buy_signals_count}/5 buy signals)",
        "",
        "--- METRICS ---",
        ""
    ]

    # VIX
    vix = report.vix
    signal = "✓ BUY SIGNAL" if vix.is_buy_signal else ""
    lines.append(f"1. VIX: {vix.current or 'N/A'} ({vix.fear_level}) {signal}")

    # Fed Rate
    fed = report.fed_rate
    signal = "✓ BUY SIGNAL" if fed.is_buy_signal else ""
    lines.append(f"2. Fed Rate: {fed.current or 'N/A'}% (Trend: {fed.trend}) {signal}")

    # Margin Debt
    margin = report.margin_debt
    signal = "✓ BUY SIGNAL" if margin.is_buy_signal else ""
    lines.append(f"3. Margin Debt: ${margin.current_billions or 'N/A'}B (Trend: {margin.trend}) {signal}")

    # Sectors
    sectors = report.sectors
    signal = "✓ BUY SIGNAL" if sectors.has_clear_leaders else ""
    lines.append(f"4. Leading Sectors: {', '.join(sectors.leading_sectors) or 'N/A'} {signal}")

    # Earnings
    earnings = report.earnings
    signal = "✓ BUY SIGNAL" if earnings.has_strong_earnings else ""
    lines.append(f"5. Strong Earnings: {', '.join(earnings.healthy_sectors) or 'N/A'} {signal}")

    lines.append("")
    lines.append("--- AI ANALYSIS ---")
    lines.append("")
    lines.append(report.ai_analysis or "No AI analysis available")

    return "\n".join(lines)


def _build_html_report(report: MarketPulseReport) -> str:
    """Build HTML version of report."""
    signal_color = {
        "STRONG_BUY": "#22c55e",
        "MODERATE_BUY": "#eab308",
        "WEAK_BUY": "#f97316",
        "NEUTRAL": "#6b7280"
    }.get(report.signal_strength, "#6b7280")

    def metric_row(name, value, detail, is_signal):
        check = "✓" if is_signal else ""
        bg = "#dcfce7" if is_signal else "#f9fafb"
        return f"""
        <tr style="background: {bg};">
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;"><strong>{name}</strong></td>
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{value}</td>
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{detail}</td>
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; color: #22c55e; font-weight: bold;">{check}</td>
        </tr>
        """

    vix = report.vix
    fed = report.fed_rate
    margin = report.margin_debt
    sectors = report.sectors
    earnings = report.earnings

    analysis_html = (report.ai_analysis or "No AI analysis available").replace("\n", "<br>")

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px; background: #f3f4f6;">
        <div style="background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

            <!-- Header -->
            <div style="background: {signal_color}; color: white; padding: 24px; text-align: center;">
                <h1 style="margin: 0; font-size: 24px;">Market Pulse</h1>
                <p style="margin: 8px 0 0 0; font-size: 32px; font-weight: bold;">{report.signal_strength}</p>
                <p style="margin: 8px 0 0 0; opacity: 0.9;">{report.buy_signals_count} of 5 buy signals active</p>
            </div>

            <!-- Metrics Table -->
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #f9fafb;">
                        <th style="padding: 12px; text-align: left; border-bottom: 2px solid #e5e7eb;">Metric</th>
                        <th style="padding: 12px; text-align: left; border-bottom: 2px solid #e5e7eb;">Value</th>
                        <th style="padding: 12px; text-align: left; border-bottom: 2px solid #e5e7eb;">Status</th>
                        <th style="padding: 12px; text-align: left; border-bottom: 2px solid #e5e7eb;">Signal</th>
                    </tr>
                </thead>
                <tbody>
                    {metric_row("VIX", vix.current or "N/A", vix.fear_level.replace("_", " ").title(), vix.is_buy_signal)}
                    {metric_row("Fed Rate", f"{fed.current or 'N/A'}%", fed.trend.title(), fed.is_buy_signal)}
                    {metric_row("Margin Debt", f"${margin.current_billions or 'N/A'}B", margin.trend.replace("_", " ").title(), margin.is_buy_signal)}
                    {metric_row("Sector Leaders", ", ".join(sectors.leading_sectors[:2]) or "N/A", "Clear leaders" if sectors.has_clear_leaders else "Mixed", sectors.has_clear_leaders)}
                    {metric_row("Earnings", ", ".join(earnings.healthy_sectors[:2]) or "N/A", "Strong" if earnings.has_strong_earnings else "Mixed", earnings.has_strong_earnings)}
                </tbody>
            </table>

            <!-- Analysis -->
            <div style="padding: 24px; border-top: 1px solid #e5e7eb;">
                <h2 style="margin: 0 0 16px 0; font-size: 18px; color: #374151;">Analysis</h2>
                <div style="color: #4b5563; line-height: 1.6;">
                    {analysis_html}
                </div>
            </div>

            <!-- Footer -->
            <div style="padding: 16px 24px; background: #f9fafb; text-align: center; color: #6b7280; font-size: 12px;">
                Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} | Market Pulse
            </div>
        </div>
    </body>
    </html>
    """
