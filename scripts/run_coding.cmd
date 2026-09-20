@echo off
rem Phase 4 coding, launched by Task Scheduler so it survives this session ending.
rem Config measured in data/coded/_calibration/coding_config_calibration.json:
rem Opus at low effort with prompt caching OFF (every bundle is unique, so caching only ever writes).
cd /d "C:\Users\Bhaskar\Pictures\Research\harness-db"
set PYTHONIOENCODING=utf-8
set DISABLE_PROMPT_CACHING=1
set ENABLE_CLAUDEAI_MCP_SERVERS=false
python scripts\code_system.py --pass A --model opus --effort low --workers 8 --text-json >> data\coded\coding_console.log 2>&1
