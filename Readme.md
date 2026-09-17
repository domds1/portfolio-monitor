# Portfolio Rebalancing Monitor

A Python automation tool to monitor portfolio allocation from a transaction CSV, fetch real-time market prices via Yahoo Finance, compare actual weights against target thresholds, and send Telegram alerts when rebalancing is needed.

---

## Table of Contents

- [Features](#features)
- [Prerequisites & Installation](#prerequisites--installation)
- [Telegram Bot Setup](#telegram-bot-setup)
- [CSV File Requirements](#csv-file-requirements)
- [Configuration Guide](#configuration-guide)
- [Workaround Management](#workaround-management)
- [Script Usage](#script-usage)
- [Private Data vs Public Repository](#private-data-vs-public-repository)

---

## Features

- **Transaction-based balance tracking**: reads buy/sell operations from a CSV and computes net holdings per asset.
- **Real-time market valuation**: queries Yahoo Finance (`yfinance`) for updated close prices.
- **Flexible rebalancing logic**:
  - **Relative threshold**: compares percentage drift from the target allocation (for example, target 25% with a 20% relative threshold gives a valid range of `[20% - 30%]`).
  - **Absolute threshold**: compares fixed percentage-point deviation (for example, target 30% with a 5% absolute threshold gives a valid range of `[25% - 35%]`).
- **Telegram notifications**: sends formatted alerts for out-of-range assets and a complete target allocation summary.
- **Modular multi-ticker aggregation**: temporarily aggregates secondary positions into primary target assets using isolated code blocks.

---

## Prerequisites & Installation

### Requirements

- **Python**: version 3.10 or higher.
- **Dependencies**: defined in `requirements.txt`.

```text
pandas>=2.0.0
requests>=2.31.0
yfinance>=0.2.30
```

### Installation steps

1. **Clone the repository**:

   ```bash
   git clone https://github.com/your-username/portfolio-rebalancing-monitor.git
   cd portfolio-rebalancing-monitor
   ```

2. **Create a virtual environment (recommended)**:

   ```bash
   python -m venv myenv
   source myenv/bin/activate  # On Windows: myenv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

---

## Telegram Bot Setup

To receive alerts, you need a Telegram bot token and a chat ID:

1. **Create a bot**:
   - search for `@BotFather` on Telegram;
   - send `/newbot` and follow the prompts to receive the `TELEGRAM_BOT_TOKEN`.
2. **Retrieve your chat ID**:
   - send a message to the bot you created;
   - search for `@userinfobot` and send `/start` to obtain your numeric `TELEGRAM_CHAT_ID`.

If you do not see the chat ID, send a message in the chat first, then check:

```text
https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getUpdates
```

---

## CSV File Requirements

Place the portfolio data file in the project root. The script reads transaction history by adding `BUY` quantities and subtracting `SELL` quantities for each symbol.

### Required CSV format

| Column Name | Type | Example | Description |
| :--- | :--- | :--- | :--- |
| `Symbol` | String | `VAGF.MI`, `XDPU.MI`, `XDEM.MI` | Yahoo Finance ticker symbol |
| `Quantity` | Number | `10`, `15.5` | Number of shares or units transacted |
| `Transaction Type` | String | `BUY`, `SELL` | Type of transaction |

### Example `portfolio.csv`

```csv
Symbol,Quantity,Transaction Type
VWCE.MI,100,BUY
SPY.MI,50,BUY
GOLD.MI,10,SELL
```

> For this project, the real personal portfolio file can be kept local and untracked, while a public template can be shared.

---

## Configuration Guide

The main configuration is defined directly in `PortfolioMonitor.py`.

### 1. Telegram credentials

Do not hardcode these values in the repository. Keep them in your local environment and let the script read them at runtime.

```bash
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyZ"
export TELEGRAM_CHAT_ID="987654321"
```

### 2. Target assets and thresholds (`TARGET_CONFIG`)

Define target portfolio weights and allowed deviation thresholds:

```python
TARGET_CONFIG = {
    "VWCE.MI": {
        "target_weight": 25.0,  # Target weight (%)
        "type": "RELATIVE",     # Mode: RELATIVE or ABSOLUTE
        "threshold": 20.0,      # 20% relative drift -> allowed range: [20.0% - 30.0%]
    },
    "GOLD.MI": {
        "target_weight": 30.0,  # Target weight (%)
        "type": "ABSOLUTE",     # Mode: RELATIVE or ABSOLUTE
        "threshold": 5.0,        # 5 percentage-point drift -> allowed range: [25.0% - 35.0%]
    },
}
```

---

## Workaround Management

The script includes a temporary aggregation feature that merges secondary ticker values into primary target positions.

### Workaround map

- `VAGF.MI` ← aggregates `EGOV.MI` + `XBLC.MI`
- `VWCE.MI` ← aggregates `XDEM.MI` + `MVOL.MI`

### Disabling the workaround

To disable ticker aggregation without changing the project structure, set the flag in the designated block:

```python
ENABLE_AGGREGATION_WORKAROUND = False
```

### Removing the workaround permanently

To remove this feature from the source code, delete the three designated blocks in `PortfolioMonitor.py`:

1. **[WORKAROUND BLOCK 1/3]**: configuration mapping (`ENABLE_AGGREGATION_WORKAROUND` and `WORKAROUND_BUNDLES`).
2. **[WORKAROUND BLOCK 2/3]**: ticker list extension logic in `monitor_portfolio()`.
3. **[WORKAROUND BLOCK 3/3]**: euro-value aggregation loop before alert evaluation.

---

## Script Usage

Run the monitoring script manually from the command line:

```bash
python PortfolioMonitor.py
```

### Example output

```text
All monitored assets are within allowed threshold ranges.
```

Or, if an asset exceeds its threshold:

```text
Telegram alert sent successfully.
```

### Example Telegram notification

```markdown
*PORTFOLIO ALERT*

🔺 *VWCE.MI*
Current Weight: `37.20%` (Target: `30.00%`)
Threshold Config: `Relative 20.0%`
Allowed Range: `[24.00% - 36.00%]`
Current Price: `54.30 EUR`

*Target Allocation Summary*
- *VWCE.MI*: `37.20%` vs target `30.00%`
- *VAGF.MI*: `20.10%` vs target `25.00%`
```

---

## Private Data vs Public Repository

To keep real personal portfolio data private, use this structure:

- `portfolio-template.csv` → shareable example or neutral configuration
- `portfolio.csv` → local-only file containing real data
- code and generic configuration → public and shareable

The project uses `.gitignore` to exclude personal portfolio files, so sensitive data stays on the local machine.
