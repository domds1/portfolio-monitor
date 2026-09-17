"""Application entrypoint for running the portfolio monitor."""

from portfolio_monitor.orchestrator import monitor_portfolio


if __name__ == "__main__":
    monitor_portfolio()
