@echo off
rem Phase 4 coding, launched by Task Scheduler so it survives this session ending and waits out each
rem usage-limit window (pass A stopped at 358 of 1116 systems on 2026-09-20 when the monthly
rem allowance ran out; every remaining system failed with HTTP 429).
rem Config measured in data/coded/_calibration/coding_config_calibration.json: Opus at low effort
rem with prompt caching OFF, because every evidence bundle is unique so the cache only ever writes.
cd /d "C:\Users\Bhaskar\Pictures\Research\harness-db"
set PYTHONIOENCODING=utf-8
set DISABLE_PROMPT_CACHING=1
set ENABLE_CLAUDEAI_MCP_SERVERS=false
python scripts\phase4_autopilot.py --workers 8 --limit-wait 30 --deadline-hours 72 >> data\coded\coding_console.log 2>&1
