# Market Pulse

A lightweight Python tool that tracks 5 key metrics for stock buying opportunities and sends you email reports with AI-powered analysis.

## The 5 Metrics

| Metric | Buy Signal | Source |
|--------|------------|--------|
| **VIX** | > 30 (extreme fear) | Yahoo Finance |
| **Fed Rate** | Downward trend | FRED API |
| **Margin Debt** | Decreasing | FRED/FINRA |
| **Sector Leaders** | Clear outperformers | Sector ETFs |
| **Earnings** | Strong growth in leaders | Yahoo Finance |

## Setup

### 1. Clone and Install

```bash
cd market-pulse
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

### 3. Get API Keys

**FRED API Key (Required - Free)**
1. Go to https://fred.stlouisfed.org/docs/api/api_key.html
2. Create account and request key
3. Add to `.env`: `FRED_API_KEY=your_key`

**Gmail App Password (Required for email)**
1. Enable 2-Factor Authentication on Google account
2. Go to https://myaccount.google.com/apppasswords
3. Generate app password for "Mail"
4. Add to `.env`:
   ```
   GMAIL_ADDRESS=you@gmail.com
   GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
   EMAIL_RECIPIENT=you@gmail.com
   ```

**AI Analysis (Optional - choose one)**

*Option A: Anthropic Claude*
- Get key at https://console.anthropic.com
- Add: `ANTHROPIC_API_KEY=sk-ant-...`

*Option B: OpenAI*
- Get key at https://platform.openai.com/api-keys
- Add: `OPENAI_API_KEY=sk-...`

*Option C: Ollama (Free, Local)*
```bash
# Install Ollama
brew install ollama

# Pull a model
ollama pull llama3.2

# Run Ollama server
ollama serve
```
No API key needed - the app auto-detects Ollama.

*Option D: No AI*
- Works without any AI key (uses rule-based analysis)

## Usage

```bash
# Run once, print to console
python main.py

# Run once, send email report
python main.py --email

# Output as JSON
python main.py --json

# Run on schedule (9:30 AM & 4:00 PM Mon-Fri)
python main.py --schedule
```

## Sample Output

```
============================================================
MARKET PULSE REPORT
Generated: 2024-03-15 09:30
============================================================

OVERALL:             MODERATE_BUY (3/5 signals)
------------------------------------------------------------
1. VIX:              28.5       elevated
2. Fed Rate:         5.25%      downward        [BUY SIGNAL]
3. Margin Debt:      $780B      decreasing      [BUY SIGNAL]
4. Sector Leaders:   Technology, Healthcare     [BUY SIGNAL]
5. Strong Earnings:  Technology
------------------------------------------------------------
```

## Running on a Schedule (Alternative to --schedule)

### Using cron (Mac/Linux)

```bash
# Edit crontab
crontab -e

# Add (runs at 9:30 AM and 4:00 PM ET, Mon-Fri)
30 9 * * 1-5 cd /path/to/market-pulse && /path/to/venv/bin/python main.py --email
0 16 * * 1-5 cd /path/to/market-pulse && /path/to/venv/bin/python main.py --email
```

### Using launchd (Mac - persists after restart)

Create `~/Library/LaunchAgents/com.marketpulse.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.marketpulse</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/venv/bin/python</string>
        <string>/path/to/market-pulse/main.py</string>
        <string>--email</string>
    </array>
    <key>StartCalendarInterval</key>
    <array>
        <dict>
            <key>Hour</key><integer>9</integer>
            <key>Minute</key><integer>30</integer>
        </dict>
        <dict>
            <key>Hour</key><integer>16</integer>
            <key>Minute</key><integer>0</integer>
        </dict>
    </array>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.marketpulse.plist
```

## Project Structure

```
market-pulse/
├── main.py                 # Entry point
├── requirements.txt
├── .env.example
├── src/
│   ├── analyzer.py         # AI analysis (Claude/OpenAI/Ollama/rules)
│   ├── emailer.py          # Gmail SMTP sender
│   ├── data_fetchers/
│   │   ├── vix.py          # VIX from Yahoo Finance
│   │   ├── fed_rate.py     # Fed rate from FRED
│   │   ├── margin_debt.py  # Margin debt from FRED
│   │   ├── sectors.py      # Sector ETF performance
│   │   └── earnings.py     # Company earnings data
│   └── models/
│       └── metrics.py      # Data models
```

## Notes

- **Margin debt data** is quarterly with ~2 month lag. For monthly data, check [FINRA](https://www.finra.org/investors/learn-to-invest/advanced-investing/margin-statistics) directly.
- **Earnings data** uses representative large-cap companies per sector as proxies.
- **Free API limits**: Yahoo Finance and FRED have generous limits for personal use.

## Extending

Ideas for future enhancements:
- Add more data sources (put/call ratio, insider buying, etc.)
- Store historical data for trend analysis
- Web dashboard with charts
- Telegram/Slack notifications
- Backtest the signals against historical data
