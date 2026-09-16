"""Harvest vendor / major-lab harness documentation and technical reports ("grey" sources,
protocol section 5 "major-lab technical reports"; eligibility of systems with no paper:
protocol section 4.3; screening of vendor products: definition.md section 5.1 cases 5 and 14).

A curated list (``SYSTEMS`` below) maps each closed or vendor-documented harness to the
documentation pages and engineering posts that describe it. Every URL is fetched; pages that
resolve with substantive text are kept, failures (404, 403, empty SPA shells, timeouts) are
reported in the SUMMARY line and must be copied to ``data/raw/grey_notes.md``. Nothing is
fabricated: a system with no resolving page produces no record.

GitHub repository / blob URLs are read through raw.githubusercontent.com (README.md or the
file itself) so that the text is the document, not GitHub's chrome.

Record: id = ``grey:<system-slug>``, source = "grey", query_used = "vendor-docs",
title = system name, abstract = first 1,500 characters of the primary page's main text,
url = primary page (first resolving URL in list order), date = page date when the page
declares one (meta tags / <time>), otherwise the retrieval date,
extra = {"vendor", "primary_kind", "docs": [{url, final_url, status, kind, title, date, chars,
excerpt}], "failed": [{url, kind, error}]}.

Usage:
    python scripts/harvest/grey.py [--out data/raw/grey.jsonl] [--count-only]
        [--only "Claude Code,Devin"] [--log-level INFO]
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path
from typing import Any

from common import (
    HttpClient,
    JsonlWriter,
    Record,
    build_parser,
    now_iso,
    print_summary,
    setup_logging,
)

ABSTRACT_CHARS = 1500
EXCERPT_CHARS = 400
MIN_TEXT_CHARS = 300  # below this a page is treated as an empty shell / soft 404

# kind: docs | engineering | announcement | readme | tech_report | system_card
# (vendor, [(url, kind), ...]); first resolving URL becomes the record's primary page.
SYSTEMS: dict[str, tuple[str, list[tuple[str, str]]]] = {
    "Claude Code": (
        "Anthropic",
        [
            ("https://code.claude.com/docs/en/overview", "docs"),
            ("https://docs.claude.com/en/docs/claude-code/overview", "docs"),
            ("https://code.claude.com/docs/en/how-claude-code-works", "docs"),
            ("https://code.claude.com/docs/en/sub-agents", "docs"),
            ("https://code.claude.com/docs/en/hooks", "docs"),
            ("https://www.anthropic.com/engineering/claude-code-best-practices", "engineering"),
            ("https://www.anthropic.com/engineering/building-effective-agents", "engineering"),
            ("https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents", "engineering"),
            ("https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents", "engineering"),
            ("https://www.anthropic.com/engineering/writing-tools-for-agents", "engineering"),
            ("https://www.anthropic.com/engineering/built-multi-agent-research-system", "engineering"),
            ("https://www.anthropic.com/engineering/managed-agents", "engineering"),
        ],
    ),
    "Claude Agent SDK": (
        "Anthropic",
        [
            ("https://platform.claude.com/docs/en/agent-sdk/overview", "docs"),
            ("https://docs.claude.com/en/api/agent-sdk/overview", "docs"),
            ("https://claude.com/blog/building-agents-with-the-claude-agent-sdk", "engineering"),
            ("https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk", "engineering"),
        ],
    ),
    "Codex CLI": (
        "OpenAI",
        [
            ("https://developers.openai.com/codex/cli/", "docs"),
            ("https://developers.openai.com/codex/", "docs"),
            ("https://openai.com/index/unrolling-the-codex-agent-loop/", "engineering"),
            ("https://openai.com/index/introducing-codex/", "announcement"),
            ("https://github.com/openai/codex", "readme"),
            ("https://developers.openai.com/codex/cloud/", "docs"),
        ],
    ),
    "OpenAI Agents SDK": (
        "OpenAI",
        [
            ("https://openai.github.io/openai-agents-python/", "docs"),
            ("https://openai.github.io/openai-agents-python/agents/", "docs"),
            ("https://platform.openai.com/docs/guides/agents", "docs"),
            ("https://openai.com/index/new-tools-for-building-agents/", "announcement"),
            ("https://github.com/openai/openai-agents-python", "readme"),
        ],
    ),
    "OpenAI Operator / CUA": (
        "OpenAI",
        [
            ("https://openai.com/index/computer-using-agent/", "tech_report"),
            ("https://openai.com/index/introducing-operator/", "announcement"),
            ("https://openai.com/index/introducing-chatgpt-agent/", "announcement"),
        ],
    ),
    "Gemini CLI": (
        "Google",
        [
            ("https://geminicli.com/docs/", "docs"),
            ("https://github.com/google-gemini/gemini-cli", "readme"),
            ("https://github.com/google-gemini/gemini-cli/blob/main/docs/core/index.md", "docs"),
            ("https://blog.google/technology/developers/introducing-gemini-cli-open-source-ai-agent/", "announcement"),
            ("https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/", "announcement"),
        ],
    ),
    "Jules": (
        "Google",
        [
            ("https://jules.google/docs", "docs"),
            ("https://jules.google/docs/", "docs"),
            ("https://blog.google/technology/google-labs/jules/", "announcement"),
            ("https://developers.googleblog.com/en/jules-tools-cli/", "announcement"),
        ],
    ),
    "Antigravity": (
        "Google",
        [
            ("https://antigravity.google/docs", "docs"),
            ("https://antigravity.google/docs/cli/overview/", "docs"),
            ("https://antigravity.google/blog/introducing-google-antigravity", "announcement"),
            ("https://antigravity.google/blog/introducing-google-antigravity-cli", "announcement"),
        ],
    ),
    "Google ADK": (
        "Google",
        [
            ("https://google.github.io/adk-docs/", "docs"),
            ("https://google.github.io/adk-docs/agents/llm-agents/", "docs"),
            ("https://github.com/google/adk-python", "readme"),
        ],
    ),
    "Devin": (
        "Cognition",
        [
            ("https://docs.devin.ai/get-started/devin-intro", "docs"),
            ("https://docs.devin.ai/", "docs"),
            ("https://cognition.ai/blog/introducing-devin", "announcement"),
            ("https://cognition.ai/blog/devin-2", "announcement"),
            ("https://cognition.ai/blog/dont-build-multi-agents", "engineering"),
            ("https://cognition.ai/blog/devin-annual-performance-review-2025", "tech_report"),
            ("https://docs.devin.ai/release-notes/2025", "docs"),
        ],
    ),
    "Cursor Agent": (
        "Cursor (Anysphere)",
        [
            ("https://cursor.com/docs/agent/overview", "docs"),
            ("https://docs.cursor.com/agent/overview", "docs"),
            ("https://cursor.com/docs/agent/modes", "docs"),
            ("https://cursor.com/docs/background-agent", "docs"),
            ("https://cursor.com/docs/cli/overview", "docs"),
            ("https://cursor.com/blog/agent-web", "announcement"),
        ],
    ),
    "Replit Agent": (
        "Replit",
        [
            ("https://docs.replit.com/replitai/agent", "docs"),
            ("https://docs.replit.com/replitai/agent-overview", "docs"),
            ("https://blog.replit.com/agent3", "announcement"),
            ("https://blog.replit.com/introducing-replit-agent", "announcement"),
        ],
    ),
    "GitHub Copilot coding agent": (
        "GitHub (Microsoft)",
        [
            ("https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-coding-agent", "docs"),
            ("https://docs.github.com/en/copilot/concepts/coding-agent/about-coding-agent", "docs"),
            ("https://docs.github.com/en/copilot/concepts/about-copilot-coding-agent", "docs"),
            ("https://github.blog/news-insights/product-news/github-copilot-meet-the-new-coding-agent/", "announcement"),
            ("https://github.blog/ai-and-ml/github-copilot/how-to-use-github-copilot-coding-agent-effectively/", "engineering"),
        ],
    ),
    "GitHub Copilot CLI": (
        "GitHub (Microsoft)",
        [
            ("https://docs.github.com/en/copilot/how-tos/use-copilot-agents/use-copilot-cli", "docs"),
            ("https://docs.github.com/en/copilot/concepts/agents/about-copilot-cli", "docs"),
            ("https://github.com/github/copilot-cli", "readme"),
        ],
    ),
    "Amazon Q Developer CLI": (
        "Amazon (AWS)",
        [
            ("https://github.com/aws/amazon-q-developer-cli", "readme"),
            ("https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/what-is.html", "docs"),
            ("https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/command-line-chat.html", "docs"),
            ("https://aws.amazon.com/q/developer/build/", "announcement"),
            ("https://aws.amazon.com/blogs/aws/new-amazon-q-developer-agent-capabilities-include-generating-documentation-code-reviews-and-unit-tests/", "announcement"),
        ],
    ),
    "Kiro": (
        "Amazon (AWS)",
        [
            ("https://kiro.dev/docs/", "docs"),
            ("https://kiro.dev/docs/autonomous-agent/", "docs"),
            ("https://kiro.dev/docs/cli/", "docs"),
            ("https://kiro.dev/blog/introducing-kiro-autonomous-agent/", "announcement"),
            ("https://kiro.dev/blog/introducing-kiro/", "announcement"),
        ],
    ),
    "DeepSeek Harness (dsh)": (
        "DeepSeek",
        [
            ("https://github.com/deepseek-ai/deepseek-harness", "readme"),
            ("https://deepseek-harness.github.io/deepseek-harness/", "docs"),
        ],
    ),
    "Qwen Code": (
        "Alibaba (Qwen)",
        [
            ("https://github.com/QwenLM/qwen-code", "readme"),
            ("https://qwenlm.github.io/qwen-code-docs/en/", "docs"),
            ("https://qwenlm.github.io/qwen-code-docs/", "docs"),
        ],
    ),
    "Qwen-Agent": (
        "Alibaba (Qwen)",
        [
            ("https://github.com/QwenLM/Qwen-Agent", "readme"),
            ("https://qwen.readthedocs.io/en/latest/framework/qwen_agent.html", "docs"),
        ],
    ),
    "Manus": (
        "Manus (Butterfly Effect)",
        [
            ("https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus", "engineering"),
            ("https://manus.im/docs", "docs"),
            ("https://manus.im/docs/introduction/what-is-manus", "docs"),
        ],
    ),
    "OpenClaw": (
        "OpenClaw",
        [
            ("https://docs.openclaw.ai/", "docs"),
            ("https://docs.openclaw.ai/concepts/agent", "docs"),
            ("https://docs.openclaw.ai/concepts/architecture", "docs"),
            ("https://github.com/openclaw/openclaw", "readme"),
        ],
    ),
    "Goose": (
        "Block",
        [
            ("https://goose-docs.ai/docs/getting-started/using-goose", "docs"),
            ("https://goose-docs.ai/docs/", "docs"),
            ("https://goose-docs.ai/docs/guides/goose-permissions", "docs"),
            ("https://github.com/aaif-goose/goose", "readme"),
            ("https://github.com/block/goose", "readme"),
            ("https://goose-docs.ai/blog/2025/03/31/goose-architecture/", "engineering"),
        ],
    ),
    "OpenCode": (
        "SST / Anomaly",
        [
            ("https://opencode.ai/docs/", "docs"),
            ("https://opencode.ai/docs/agents/", "docs"),
            ("https://github.com/sst/opencode", "readme"),
            ("https://github.com/anomalyco/opencode", "readme"),
        ],
    ),
    "Cline": (
        "Cline",
        [
            ("https://docs.cline.bot/getting-started/what-is-cline", "docs"),
            ("https://docs.cline.bot/", "docs"),
            ("https://github.com/cline/cline", "readme"),
        ],
    ),
    "Roo Code": (
        "Roo Code",
        [
            ("https://docs.roocode.com/", "docs"),
            ("https://docs.roocode.com/basic-usage/how-tools-work", "docs"),
            ("https://github.com/RooCodeInc/Roo-Code", "readme"),
        ],
    ),
    "Aider": (
        "Aider",
        [
            ("https://aider.chat/docs/", "docs"),
            ("https://aider.chat/docs/usage.html", "docs"),
            ("https://aider.chat/docs/repomap.html", "docs"),
            ("https://aider.chat/docs/more/edit-formats.html", "docs"),
            ("https://github.com/Aider-AI/aider", "readme"),
        ],
    ),
    "Warp Agent (Oz)": (
        "Warp",
        [
            ("https://docs.warp.dev/agent-platform/local-agents/agents-overview", "docs"),
            ("https://docs.warp.dev/agent-platform/getting-started/agents-in-warp/", "docs"),
            ("https://docs.warp.dev/agent-platform/cloud-agents/harnesses/warp-agent/", "docs"),
            ("https://docs.warp.dev/agent-platform/cloud-agents/platform", "docs"),
            ("https://docs.warp.dev/agents/active-ai", "docs"),
            ("https://www.warp.dev/blog/oz", "announcement"),
        ],
    ),
    "Windsurf Cascade": (
        "Windsurf (Cognition)",
        [
            ("https://docs.windsurf.com/windsurf/cascade/cascade", "docs"),
            ("https://docs.windsurf.com/windsurf/cascade", "docs"),
            ("https://windsurf.com/cascade", "announcement"),
            ("https://cognition.ai/blog/swe-1-5", "tech_report"),
        ],
    ),
    "Factory Droid": (
        "Factory",
        [
            ("https://docs.factory.ai/cli/getting-started/overview", "docs"),
            ("https://docs.factory.ai/", "docs"),
            ("https://docs.factory.ai/cli/configuration/custom-droids", "docs"),
            ("https://factory.ai/news/droid-cli", "announcement"),
        ],
    ),
    "Augment Agent (Auggie)": (
        "Augment Code",
        [
            ("https://docs.augmentcode.com/cli/overview", "docs"),
            ("https://docs.augmentcode.com/", "docs"),
            ("https://docs.augmentcode.com/setup-augment/agent", "docs"),
            ("https://www.augmentcode.com/blog/1-open-source-agent-on-swe-bench-verified-by-combining-claude-3-7-and-o1", "engineering"),
        ],
    ),
    "Amp": (
        "Sourcegraph / Amp",
        [
            ("https://ampcode.com/manual", "docs"),
            ("https://ampcode.com/how-to-build-an-agent", "engineering"),
            ("https://ampcode.com/news/subagents", "engineering"),
        ],
    ),
    "Mistral Vibe": (
        "Mistral AI",
        [
            ("https://docs.mistral.ai/mistral-vibe/introduction", "docs"),
            ("https://docs.mistral.ai/mistral-vibe/overview", "docs"),
            ("https://docs.mistral.ai/vibe/code/cli/agents", "docs"),
            ("https://github.com/mistralai/mistral-vibe", "readme"),
            ("https://mistral.ai/news/mistral-vibe-2-0/", "announcement"),
            ("https://mistral.ai/news/devstral-2-vibe-cli", "announcement"),
        ],
    ),
    "Grok Build": (
        "xAI",
        [
            ("https://docs.x.ai/build/overview", "docs"),
            ("https://github.com/xai-org/grok-build", "readme"),
            ("https://x.ai/news/grok-build-cli", "announcement"),
        ],
    ),
    "Perplexity Computer": (
        "Perplexity",
        [
            ("https://www.perplexity.ai/hub/blog/introducing-perplexity-computer", "announcement"),
            ("https://research.perplexity.ai/articles/designing-refining-and-maintaining-agent-skills-at-perplexity", "engineering"),
            ("https://www.perplexity.ai/help-center/en/articles/12730642-perplexity-computer", "docs"),
        ],
    ),
    "AutoGen": (
        "Microsoft",
        [
            ("https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/index.html", "docs"),
            ("https://microsoft.github.io/autogen/stable/", "docs"),
            ("https://github.com/microsoft/autogen", "readme"),
        ],
    ),
    "Magentic-One": (
        "Microsoft",
        [
            ("https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/magentic-one.html", "docs"),
            ("https://www.microsoft.com/en-us/research/articles/magentic-one-a-generalist-multi-agent-system-for-solving-complex-tasks/", "tech_report"),
        ],
    ),
    "Semantic Kernel Agents": (
        "Microsoft",
        [
            ("https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-architecture", "docs"),
            ("https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/", "docs"),
        ],
    ),
    "Microsoft Agent Framework": (
        "Microsoft",
        [
            ("https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview", "docs"),
            ("https://github.com/microsoft/agent-framework", "readme"),
        ],
    ),
    "Deep Agents (deepagents)": (
        "LangChain",
        [
            ("https://docs.langchain.com/oss/python/deepagents/overview", "docs"),
            ("https://github.com/langchain-ai/deepagents", "readme"),
            ("https://www.langchain.com/deep-agents", "announcement"),
        ],
    ),
    "pi": (
        "Earendil Works",
        [
            ("https://github.com/earendil-works/pi", "readme"),
            ("https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/index.md", "docs"),
            ("https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/sdk.md", "docs"),
            ("https://pi.dev/", "docs"),
        ],
    ),
    "OpenHands": (
        "All Hands AI",
        [
            ("https://docs.all-hands.dev/", "docs"),
            ("https://docs.openhands.dev/", "docs"),
            ("https://github.com/All-Hands-AI/OpenHands", "readme"),
            ("https://github.com/OpenHands/OpenHands", "readme"),
        ],
    ),
    "Trae Agent": (
        "ByteDance",
        [
            ("https://github.com/bytedance/trae-agent", "readme"),
            ("https://docs.trae.ai/ide/agent", "docs"),
        ],
    ),
    "Junie": (
        "JetBrains",
        [
            ("https://www.jetbrains.com/help/junie/get-started-with-junie.html", "docs"),
            ("https://www.jetbrains.com/junie/", "announcement"),
        ],
    ),
    "Zed Agent": (
        "Zed Industries",
        [
            ("https://zed.dev/docs/ai/agent-panel", "docs"),
            ("https://zed.dev/docs/ai/overview", "docs"),
            ("https://zed.dev/blog/fastest-ai-code-editor", "announcement"),
        ],
    ),
    "Kimi CLI": (
        "Moonshot AI",
        [
            ("https://github.com/MoonshotAI/kimi-cli", "readme"),
            ("https://moonshotai.github.io/kimi-cli/en/", "docs"),
        ],
    ),
    "Crush": (
        "Charm",
        [
            ("https://github.com/charmbracelet/crush", "readme"),
        ],
    ),
    "Continue": (
        "Continue",
        [
            ("https://docs.continue.dev/agent/how-it-works", "docs"),
            ("https://docs.continue.dev/", "docs"),
            ("https://github.com/continuedev/continue", "readme"),
        ],
    ),
    "Copilot Workspace / Copilot agent mode": (
        "GitHub (Microsoft)",
        [
            ("https://code.visualstudio.com/docs/copilot/agents", "docs"),
            ("https://code.visualstudio.com/docs/copilot/chat/chat-agent-mode", "docs"),
            ("https://code.visualstudio.com/blogs/2025/02/24/introducing-copilot-agent-mode", "announcement"),
        ],
    ),
}

BROWSER_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/markdown;q=0.8,*/*;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
}
_GH_REPO_RE = re.compile(r"^https?://github\.com/([^/]+)/([^/#?]+)/?$")
_GH_BLOB_RE = re.compile(r"^https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)$")
_META_DATE_KEYS = (
    "article:published_time",
    "article:modified_time",
    "og:updated_time",
    "datePublished",
    "dateModified",
    "date",
    "last-modified",
    "publish_date",
    "pubdate",
    "last_updated",
)


def slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "unnamed"


def clean(text: str) -> str:
    return " ".join(text.split())


def raw_github_candidates(url: str) -> list[str]:
    """Translate a GitHub repo / blob URL into raw.githubusercontent.com candidates."""
    m = _GH_BLOB_RE.match(url)
    if m:
        owner, repo, ref, path = m.groups()
        return [f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"]
    m = _GH_REPO_RE.match(url)
    if m:
        owner, repo = m.groups()
        return [f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{name}" for name in ("README.md", "readme.md", "README.rst", "README")]
    return []


def markdown_to_text(md: str) -> str:
    """Strip the most common markdown / HTML noise from a README and return plain text."""
    t = re.sub(r"<!--.*?-->", " ", md, flags=re.DOTALL)
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", t, flags=re.DOTALL | re.IGNORECASE)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", t)  # images / badges
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)  # links -> text
    t = re.sub(r"```.*?```", " ", t, flags=re.DOTALL)
    t = re.sub(r"^\s{0,3}#{1,6}\s*", "", t, flags=re.MULTILINE)
    t = re.sub(r"[*_`>|]+", " ", t)
    return clean(t)


def html_to_text(page: str) -> tuple[str, str | None, str | None]:
    """Return (main text, <title>, declared date) for an HTML page."""
    from lxml import html as lhtml

    try:
        doc = lhtml.fromstring(page)
    except Exception:  # noqa: BLE001
        return clean(re.sub(r"<[^>]+>", " ", page)), None, None
    title = clean(doc.findtext(".//title") or "") or None
    date = None
    for meta in doc.xpath("//meta[@content]"):
        key = (meta.get("property") or meta.get("name") or meta.get("itemprop") or "").strip()
        if key in _META_DATE_KEYS:
            m = re.match(r"(\d{4}-\d{2}-\d{2})", meta.get("content", ""))
            if m:
                date = m.group(1)
                break
    if date is None:
        for t in doc.xpath("//time[@datetime]"):
            m = re.match(r"(\d{4}-\d{2}-\d{2})", t.get("datetime", ""))
            if m:
                date = m.group(1)
                break
    for bad in doc.xpath("//script|//style|//noscript|//nav|//header|//footer|//aside|//svg|//iframe|//form"):
        parent = bad.getparent()
        if parent is not None:
            parent.remove(bad)
    main = doc.xpath("//main|//article|//*[@role='main']|//*[@id='content']|//*[contains(@class,'markdown-body')]")
    node = main[0] if main else (doc.find("body") if doc.find("body") is not None else doc)
    text = clean(node.text_content())
    if len(text) < MIN_TEXT_CHARS and node is not doc:
        text = clean(doc.text_content())
    return text, title, date


def fetch_page(client: HttpClient, url: str, log: logging.Logger) -> dict[str, Any]:
    """Fetch one URL (GitHub URLs via raw). Returns a dict with status/text/title/date."""
    candidates = raw_github_candidates(url) or [url]
    last: dict[str, Any] = {"url": url, "status": None, "error": "not fetched"}
    for cand in candidates:
        try:
            resp = client.get(cand, headers=BROWSER_HEADERS)
        except Exception as exc:  # noqa: BLE001
            last = {"url": url, "fetched": cand, "status": None, "error": str(exc)[:200]}
            continue
        if resp.status_code != 200:
            last = {"url": url, "fetched": cand, "status": resp.status_code, "error": f"HTTP {resp.status_code}"}
            continue
        ctype = resp.headers.get("Content-Type", "")
        body = resp.text
        if cand.startswith("https://raw.githubusercontent.com/") or "markdown" in ctype or cand.endswith(".md"):
            text, title, date = markdown_to_text(body), None, None
            m = re.search(r"^\s*#\s+(.+)$", body, re.MULTILINE)
            if m:
                title = clean(m.group(1))
        elif "html" in ctype or body.lstrip().startswith("<"):
            text, title, date = html_to_text(body)
        else:
            text, title, date = clean(body), None, None
        if len(text) < MIN_TEXT_CHARS:
            last = {"url": url, "fetched": cand, "status": 200, "error": f"only {len(text)} chars of text (empty shell / client-rendered)"}
            continue
        return {
            "url": url,
            "final_url": resp.url,
            "fetched": cand,
            "status": 200,
            "title": title,
            "date": date or resp.headers.get("Last-Modified"),
            "text": text,
        }
    return last


def main(argv: list[str] | None = None) -> int:
    parser = build_parser("grey", "Fetch vendor / major-lab harness documentation into grey.jsonl.")
    parser.add_argument("--only", default="", help="comma-separated system names (as in SYSTEMS)")
    args = parser.parse_args(argv)
    log = setup_logging(args.log_level)
    wanted = [s.strip() for s in args.only.split(",") if s.strip()] or list(SYSTEMS)
    unknown = [s for s in wanted if s not in SYSTEMS]
    if unknown:
        parser.error(f"unknown system(s): {unknown}")

    client = HttpClient(min_interval=1.0, max_retries=3, timeout=45, logger=log)
    retrieved_at = now_iso()
    fetched: dict[str, list[dict[str, Any]]] = {}
    failed: dict[str, list[dict[str, Any]]] = {}
    written = 0
    with JsonlWriter(args.out, count_only=args.count_only) as w:
        for system in wanted:
            vendor, pages = SYSTEMS[system]
            docs: list[dict[str, Any]] = []
            misses: list[dict[str, Any]] = []
            for url, kind in pages:
                result = fetch_page(client, url, log)
                if result.get("text"):
                    docs.append({**result, "kind": kind})
                    log.info("%s: OK %s (%d chars)", system, url, len(result["text"]))
                else:
                    misses.append({"url": url, "kind": kind, "status": result.get("status"), "error": result.get("error")})
                    log.warning("%s: FAIL %s -> %s", system, url, result.get("error"))
            fetched[system] = [{k: v for k, v in d.items() if k != "text"} for d in docs]
            failed[system] = misses
            if not docs:
                log.warning("%s: no page resolved; no record written", system)
                continue
            primary = docs[0]
            page_date = primary.get("date")
            m = re.match(r"(\d{4}-\d{2}-\d{2})", page_date or "")
            date = m.group(1) if m else retrieved_at[:10]
            rec = Record(
                id=f"grey:{slug(system)}",
                source="grey",
                source_id=slug(system),
                title=system,
                abstract=primary["text"][:ABSTRACT_CHARS],
                authors=[vendor],
                date=date,
                venue="vendor-docs",
                url=primary["url"],
                categories=sorted({d["kind"] for d in docs}),
                query_used="vendor-docs",
                retrieved_at=retrieved_at,
                extra={
                    "vendor": vendor,
                    "primary_kind": primary["kind"],
                    "primary_title": primary.get("title"),
                    "date_source": "page" if m else "retrieval",
                    "docs": [
                        {
                            "url": d["url"],
                            "final_url": d.get("final_url"),
                            "fetched": d.get("fetched"),
                            "kind": d["kind"],
                            "title": d.get("title"),
                            "date": d.get("date"),
                            "chars": len(d["text"]),
                            "excerpt": d["text"][:EXCERPT_CHARS],
                        }
                        for d in docs
                    ],
                    "failed": misses,
                },
            )
            if w.write(rec):
                written += 1
    summary = {
        "systems": len(wanted),
        "records": written,
        "pages_ok": sum(len(v) for v in fetched.values()),
        "pages_failed": sum(len(v) for v in failed.values()),
        "count_only": args.count_only,
        "out": None if args.count_only else str(Path(args.out)),
        "no_record": [s for s in wanted if not fetched.get(s)],
        "failed_urls": {s: [(f["url"], f["error"]) for f in v] for s, v in failed.items() if v},
        "http_requests": client.requests_made,
    }
    print_summary("grey", summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
