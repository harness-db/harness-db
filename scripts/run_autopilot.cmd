@echo off
rem Launched by Windows Task Scheduler so the Phase 3 run survives the Claude Code session ending.
cd /d "C:\Users\Bhaskar\Pictures\Research\harness-db"
set PYTHONIOENCODING=utf-8
python scripts\phase3_autopilot.py --tier1-model sonnet --workers 12 --batch-size 8 --limit-wait 20 --deadline-hours 20 --skip-downloads >> data\screening\autopilot_console.log 2>&1
