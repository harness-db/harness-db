@echo off
rem Phase 4 coding on the Anthropic API instead of the subscription allowance, launched by Task
rem Scheduler so it survives the session ending. Billed against ANTHROPIC_API_KEY in .env; the
rem driver stops by itself when the API reports no credit left.
rem Measured 2026-09-22: $0.29/system steady state - cheaper than the subscription's list-price
rem equivalent, because the API lets the 16,359-token system prompt be cached and read back at a
rem tenth of the price, which the CLI backend cannot do (it caches each unique bundle instead).
cd /d "C:\Users\Bhaskar\Pictures\Research\harness-db"
set PYTHONIOENCODING=utf-8
python scripts\phase4_autopilot.py --backend api --model opus --effort low --workers 6 --deadline-hours 24 >> data\coded\coding_console_api.log 2>&1
