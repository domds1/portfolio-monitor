# Portfolio Rebalancing Monitor

[![Unit tests](https://github.com/domds1/portfolio-monitor/actions/workflows/tests.yml/badge.svg)](https://github.com/domds1/portfolio-monitor/actions/workflows/tests.yml)
[![CodeQL](https://github.com/domds1/portfolio-monitor/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/domds1/portfolio-monitor/actions/workflows/github-code-scanning/codeql)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/domds1/portfolio-monitor/blob/main/LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

A Python automation tool to monitor portfolio allocation from a transaction CSV, fetch the latest daily closing prices via Yahoo Finance, compare actual weights against target thresholds, and send Telegram alerts when rebalancing is needed.

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
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
- **Market valuation**: queries Yahoo Finance (`yfinance`) for the latest available daily close prices.
- **Flexible rebalancing logic**:
  - **Relative threshold**: compares percentage drift from the target allocation (for example, target 25% with a 20% relative threshold gives a valid range of `[20% - 30%]`).
  - **Absolute threshold**: compares fixed percentage-point deviation (for example, target 30% with a 5% absolute threshold gives a valid range of `[25% - 35%]`).
- **Telegram notifications**: sends formatted alerts for out-of-range assets and a complete target allocation summary.
- **Modular multi-ticker aggregation**: temporarily aggregates secondary positions into primary target assets using isolated code blocks.

---

## Project Structure

The project has been reorganized into a small layered structure to improve maintainability and scalability:

- [PortfolioMonitor.py](PortfolioMonitor.py) — minimal entrypoint for launching the monitor
- [portfolio_monitor/config.py](portfolio_monitor/config.py) — loads runtime configuration from JSON and environment variables
- [portfolio_monitor/orchestrator.py](portfolio_monitor/orchestrator.py) — coordinates the workflow
- [portfolio_monitor/portfolio_loader.py](portfolio_monitor/portfolio_loader.py) — reads the CSV and calculates quantities
- [portfolio_monitor/market_data.py](portfolio_monitor/market_data.py) — fetches market prices from Yahoo Finance
- [portfolio_monitor/rebalance_engine.py](portfolio_monitor/rebalance_engine.py) — computes weights and threshold alerts
- [portfolio_monitor/telegram_notifier.py](portfolio_monitor/telegram_notifier.py) — builds and sends the Telegram payload
- [config.example.json](config.example.json) — public template for configuration
- [config.json](config.json) — private local configuration (ignored by Git)

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

The loader requires these three columns and ignores any additional columns from
broker exports:

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

The checked-in [portfolio-template.csv](portfolio-template.csv) is an example
broker export with additional price, date, and transaction metadata columns.
Only `Symbol`, `Quantity`, and `Transaction Type` are used by the application.

For this project, the real personal portfolio file can be kept local and
untracked, while the public template can be shared.

---

## Configuration Guide

The project now reads its runtime settings from a JSON configuration file and keeps the real values local.

### 1. Public example template

Use the checked-in example as a starting point:

- [config.example.json](config.example.json)

This file is safe to commit because it contains placeholders only.

If `config.json` is absent, the application uses this example configuration
and emits a warning. If the configured private CSV is also unavailable, it
uses `portfolio-template.csv` and emits another warning. Copy the example to
`config.json`, then replace the placeholder values and create your private
`portfolio.csv` before relying on monitoring results.

### 2. Private local config

Create a local file named [config.json](config.json) with your actual values. It is ignored by Git and should not be published.

Example:

```json
{
  "csv_path": "portfolio.csv",
  "telegram_bot_token": "YOUR_TELEGRAM_BOT_TOKEN",
  "telegram_chat_id": "YOUR_TELEGRAM_CHAT_ID",
  "enable_aggregation_workaround": true,
  "target_config": {
    "VWCE.MI": {
      "target_weight": 60.0,
      "type": "RELATIVE",
      "threshold": 20.0
    },
    "GOLD.MI": {
      "target_weight": 10.0,
      "type": "ABSOLUTE",
      "threshold": 0.0
    }
  }
}
```

### 3. Environment variables override

Environment variables still work and override the JSON values if present:

```bash
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyZ"
export TELEGRAM_CHAT_ID="987654321"
export CSV_PATH="portfolio.csv"
```

This makes it easy to keep sensitive values outside the repository while still supporting a reusable sample config.

---

## Workaround Management

The script includes a temporary aggregation feature that merges secondary ticker values into primary target positions.

### Workaround map

- `VAGF.MI` ← aggregates `EGOV.MI` + `XBLC.MI`
- `VWCE.MI` ← aggregates `XDEM.MI` + `MVOL.MI`

### Disabling the workaround

To disable ticker aggregation without changing the project structure, set the flag in the JSON config:

```json
{
  "enable_aggregation_workaround": false
}
```

### Removing the workaround permanently

To remove this feature from the source code, delete the related config entries and the aggregation logic inside [portfolio_monitor/orchestrator.py](portfolio_monitor/orchestrator.py).

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

- [config.example.json](config.example.json) → public template with placeholders
- [config.json](config.json) → local-only file containing real settings and secrets
- [portfolio-template.csv](portfolio-template.csv) → public sample file
- [portfolio.csv](portfolio.csv) → local-only file with actual portfolio data
- code and generic configuration → public and shareable

The project uses [.gitignore](.gitignore) to exclude local-only files, so sensitive data stays on the local machine.
