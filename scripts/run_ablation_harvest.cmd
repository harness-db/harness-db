@echo off
rem Corpus-wide ablation harvest, stage 3 (extraction), launched by Task Scheduler so it survives
rem the session ending and waits out each usage-limit window (scripts/harvest_ablations_corpus.py).
rem Subscription path only: the API key is cleared so headless Claude Code cannot bill it.
rem Usage: run_ablation_harvest.cmd [T10|T3|all]   (default T10)
cd /d "C:\Users\Bhaskar\Pictures\Research\harness-db"
set PYTHONIOENCODING=utf-8
set ENABLE_CLAUDEAI_MCP_SERVERS=false
set ANTHROPIC_API_KEY=
set TIER=%1
if "%TIER%"=="" set TIER=T10
C:\Python314\python.exe scripts\harvest_ablations_corpus.py --stage extract --tier %TIER% --workers 4 --batch-size 5 --effort low --deadline-hours 96 >> data\analysis\corpus_ablation\console.log 2>&1
