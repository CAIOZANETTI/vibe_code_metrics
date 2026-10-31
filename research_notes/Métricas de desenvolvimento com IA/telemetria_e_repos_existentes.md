# Telemetria e repositórios existentes para medir desenvolvimento assistido por IA / agentic coding

Notes collected 2026-10-31. Star counts and "updated_at" come from GitHub search API results retrieved on 2026-10-31 (via GitHub MCP search; `updated_at` reflects last repo metadata update, a proxy for activity). Licenses marked "(not verified this session)" come from prior knowledge and must be checked before citing.

## 1. What do the coding agents export natively (OTel / admin APIs)?

### Takeaway
Claude Code has by far the richest native telemetry for this thesis: OTel metrics already include cost (USD), tokens by type, sessions, lines of code added/removed, commits, PRs, edit accept/reject decisions and active time, all tagged by `session.id` and (optionally) repository. Gemini CLI and Codex export tokens/latency/tool decisions via OTel but not cost or commits; Cursor and GitHub Copilot expose org-level admin/usage APIs (enterprise/team plans) rather than per-developer OTel.

### Cited Findings

**Claude Code (Anthropic) — OpenTelemetry**
- Enable with `CLAUDE_CODE_ENABLE_TELEMETRY=1` plus `OTEL_METRICS_EXPORTER` (`console|otlp|prometheus|none`), `OTEL_LOGS_EXPORTER` (`console|otlp|none`), `OTEL_EXPORTER_OTLP_PROTOCOL` (`grpc|http/json|http/protobuf`), `OTEL_EXPORTER_OTLP_ENDPOINT`; traces are beta (`OTEL_TRACES_EXPORTER` + `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1`). Default metric export interval 60 s, logs 5 s; default temporality `delta`. — [Claude Code Monitoring docs](https://code.claude.com/docs/en/monitoring-usage)
- Metrics: `claude_code.session.count` (attr `start_type`), `claude_code.lines_of_code.count` (`type`=added/removed, `model`), `claude_code.pull_request.count`, `claude_code.commit.count`, `claude_code.cost.usage` (USD; `model`, `query_source`=main/subagent/auxiliary, `effort`, `agent.name`, `skill.name`, `mcp_server.name`…), `claude_code.token.usage` (`type`=input/output/cacheRead/cacheCreation), `claude_code.code_edit_tool.decision` (`tool_name` Edit/Write/NotebookEdit, `decision` accept/reject, `source`, `language`), `claude_code.active_time.total` (seconds, `type`=user/cli). — [Claude Code Monitoring docs](https://code.claude.com/docs/en/monitoring-usage)
- Events (logs): `claude_code.user_prompt` (prompt_length; text only with `OTEL_LOG_USER_PROMPTS=1`), `claude_code.assistant_response`, `claude_code.tool_result` (tool_name, success, duration_ms, decision_source, `vcs.ref.head.revision`/`vcs.ref.head.name`), `claude_code.tool_decision` (accept/reject, source incl. `user_reject`, `user_abort`, `permission_mode`), `claude_code.api_request` (model, `cost_usd`, `duration_ms`, input/output/cache tokens, request_id), `claude_code.api_error`, `claude_code.api_refusal`, optional raw bodies (`OTEL_LOG_RAW_API_BODIES`). — [Claude Code Monitoring docs](https://code.claude.com/docs/en/monitoring-usage)
- Standard attributes: `session.id`, `user.id` (anonymous), `user.email`, `user.account_uuid`, `organization.id`, `terminal.type`, `app.version`/`app.entrypoint` (opt-in), and repo attributes `vcs.repository.url.full`, `vcs.repository.name` only with `OTEL_METRICS_INCLUDE_REPOSITORY=true`; arbitrary tags via `OTEL_RESOURCE_ATTRIBUTES` (useful to tag experiment/task IDs). Events also carry `prompt.id`, `agent_id`, `parent_agent_id`, `workflow.run_id`. — [Claude Code Monitoring docs](https://code.claude.com/docs/en/monitoring-usage)
- Privacy controls: `OTEL_LOG_USER_PROMPTS`, `OTEL_LOG_ASSISTANT_RESPONSES`, `OTEL_LOG_TOOL_DETAILS` (Bash commands, file paths), `OTEL_LOG_TOOL_CONTENT`; all disabled by default. — [Claude Code Monitoring docs](https://code.claude.com/docs/en/monitoring-usage)
- Native trace span names reported by a third party: `claude_code.interaction`, `claude_code.llm_request`, `claude_code.tool`, `claude_code.tool.execution`. — [Openlayer docs](https://docs.openlayer.com/integrations/claude-agent-sdk) (secondary; not verified on Anthropic page in this session)

**OpenAI Codex CLI — OpenTelemetry**
- Configured in `~/.codex/config.toml` `[otel]` (ignored in project-local config): `exporter` = `none` (default) | `otlp-http` | `otlp-grpc`, `environment`, `log_user_prompt` (default false). — [Codex advanced config](https://learn.chatgpt.com/docs/config-file/config-advanced) (redirected from developers.openai.com/codex/config-advanced)
- Log events: `codex.conversation_starts`, `codex.api_request`, `codex.sse_event` (token counts on `response.completed`), `codex.websocket_request/_event`, `codex.user_prompt` (length only by default), `codex.tool_decision` (approved/denied, config vs user), `codex.tool_result`. Metrics: `codex.api_request(.duration_ms)`, `codex.sse_event(.duration_ms)`, `codex.tool.call(.duration_ms)`, plus `turn.e2e_duration_ms`, `turn.ttft.duration_ms`, `approval.requested`, `mcp.call`. No native cost metric, no commit/LOC metric. — [Codex advanced config](https://learn.chatgpt.com/docs/config-file/config-advanced)

**Gemini CLI — OpenTelemetry**
- Enable via `.gemini/settings.json` `telemetry.enabled`, `target` (`local`|`gcp`), `otlpEndpoint`, `outfile`, `logPrompts` (default **true**) or env vars `GEMINI_TELEMETRY_ENABLED`, `GEMINI_TELEMETRY_OTLP_ENDPOINT`, etc. — [Gemini CLI telemetry.md](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/telemetry.md)
- Metrics: `gemini_cli.session.count`, `gemini_cli.token.usage`, `gemini_cli.api.request.count/latency`, `gemini_cli.tool.call.count/latency` (with `decision`), `gemini_cli.lines.changed`, `gemini_cli.file.operation.count`, `gemini_cli.agent.run.count/duration/turns`, plus GenAI semconv `gen_ai.client.token.usage`, `gen_ai.client.operation.duration`. Events incl. `gemini_cli.user_prompt`, `gemini_cli.tool_call`, `gemini_cli.api_response` (token counts), `gemini_cli.conversation_finished` (turnCount). No cost metric. — [Gemini CLI telemetry.md](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/telemetry.md)

**Cursor — Admin API + AI Code Tracking API (team/enterprise)**
- `POST /teams/daily-usage-data`: per user/day `totalLinesAdded/Deleted`, `acceptedLinesAdded/Deleted`, `totalApplies/Accepts/Rejects`, `totalTabsShown/Accepted`, `agentRequests`, `composerRequests`, `mostUsedModel` (hourly aggregation, 30-day window). `POST /teams/filtered-usage-events`: per event `model`, `tokenUsage{inputTokens,outputTokens,cacheWriteTokens,cacheReadTokens,totalCents}`, `chargedCents`, `conversationId`, `cloudAgentId`. `POST /teams/spend`. — [Cursor Admin API](https://cursor.com/docs/account/teams/admin-api)
- AI Code Tracking API (Enterprise only, Alpha): `GET /analytics/ai-code/commits` with per-commit `tabLinesAdded`, `composerLinesAdded`, `nonAiLinesAdded`, `commitSource` (ide/cli/cloud), `repoName`, `branchName`; `/analytics/ai-code/changes` per accepted change (TAB vs COMPOSER, model). Non-AI lines = max(0, total − AI). — [Cursor AI Code Tracking API](https://cursor.com/docs/account/teams/ai-code-tracking-api)

**GitHub Copilot — Usage Metrics API**
- Legacy Copilot metrics endpoints were shut down on 2026-04-02; replaced by the "Copilot usage metrics" API that returns signed links to NDJSON reports (`/orgs/{org}/copilot/metrics/reports/organization-1-day`, enterprise equivalents). — [GitHub REST docs (copilot-metrics, zh)](https://docs.github.com/zh/rest/copilot/copilot-metrics)
- Fields: `code_generation_activity_count`, `code_acceptance_activity_count`, `loc_suggested_to_add_sum`, `loc_added_sum`, `loc_deleted_sum`, `used_agent`, `used_copilot_coding_agent`, `monthly_active_agent_users`, `pull_requests{total_created,total_reviewed,total_merged,median_minutes_to_merge}`. `loc_suggested_to_add_sum` excludes agent edits. — [GitHub Copilot usage metrics reference](https://docs.github.com/en/copilot/reference/copilot-usage-metrics/copilot-usage-metrics)
- Per-repository `repos-1-day` reports (GA July 2026) with PRs created/merged by Copilot coding agent and reviewed by Copilot code review. — [GitHub changelog 2026-07-17](https://github.blog/changelog/2026-07-17-repository-level-github-copilot-usage-metrics-generally-available/)
- GitHub Copilot (VS Code) also exports OTel natively and can point at Langfuse; default is metadata-only capture. — [Langfuse coding agent tracing](https://langfuse.com/resources/engineering/coding-agent-tracing)

**Reference implementations of OTel stacks for Claude Code**
- `anthropics/claude-code-monitoring-guide` and `ColeMurray/claude-code-otel` (Prometheus/Grafana stacks) — repos exist per prior knowledge; star counts and status NOT verified this session (gh API blocked).

### Inferences
- For a Python-based, single-developer/research setup, Claude Code OTel → local OTel Collector → Prometheus/ClickHouse or a file exporter is enough to obtain cost/tokens/session/LOC/commit/PR/accept-reject metrics with zero code changes; tagging tasks via `OTEL_RESOURCE_ATTRIBUTES=task.id=...` can join telemetry to experimental tasks.
- "Human intervention" can be proxied passively by `tool_decision` with `source=user_reject/user_abort`, `code_edit_tool.decision=reject`, number of `user_prompt` events per task, and `active_time.total{type=user}`.
- Codex and Gemini lack a cost metric: cost must be computed from token counts × price table (e.g., LiteLLM's model_prices JSON).

### Gaps
- Could not read the second half of the Claude Code monitoring page (trace span names, `subagent_completed`, `safety_event` schema).
- Did not verify whether Anthropic's Admin "Claude Code Analytics API" (org-level usage report) is still current; not fetched this session.
- Cursor has no documented per-developer OTel export found in this session.

## 2. Session-log analyzers (passive, read local JSONL)

### Takeaway
A large, very active ecosystem (2025–2026) of local-first tools parses the session transcripts that agents already write (Claude Code `~/.claude/projects/**.jsonl`, Codex `~/.codex/sessions`, etc.) and computes tokens and API-equivalent cost using LiteLLM pricing. The most thesis-relevant ones go beyond cost: CodeBurn (one-shot rate, retry tax, cost per commit/PR), agentacct (per-task work steps, tests run), git-ai (AI-accepted rate).

### Cited Findings
| Tool | Stars (2026-10-31) | What it reads / outputs | Lang / License |
|---|---|---|---|
| [ccusage/ccusage](https://github.com/ccusage/ccusage) | 19,275 | Local data from Claude Code, Codex, OpenCode, Amp, Gemini CLI, Copilot CLI, Goose, Qwen… Daily/weekly/monthly/session reports, Claude 5-hour "blocks", statusline hook; `--json` output; pricing from pinned LiteLLM data; MIT. — [README](https://github.com/ccusage/ccusage) | Rust (was TS); MIT |
| [getagentseal/codeburn](https://github.com/getagentseal/codeburn) | 11,633 | Session files of 37–42 tools; tokens, API-rate cost, breakdown by tool/model/project/git branch/task category; **one-shot rate** (edit succeeds without retry), cache hit rate, retry tax, **cost per commit and per PR** (`yield`, `sessions --by-pr`); CSV/JSON export; local MCP server. — [README](https://github.com/getagentseal/codeburn) | MIT |
| [Maciek-roboblog/Claude-Code-Usage-Monitor](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor) | 8,788 | Real-time terminal monitor of Claude Code usage with burn-rate predictions/limit warnings. — [repo](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor) | Python |
| [kenn-io/agentsview](https://github.com/kenn-io/agentsview) | 6,312 | Local-first session search, analytics, token stats for Claude Code, Codex + 50 agents. — [repo](https://github.com/kenn-io/agentsview) | Go |
| [junhoyeo/tokscale](https://github.com/junhoyeo/tokscale) | 5,774 | Token usage across coding agents, global leaderboard. — [repo](https://github.com/junhoyeo/tokscale) | — |
| [Javis603/token-monitor](https://github.com/Javis603/token-monitor) | 3,480 | Desktop widget, tokens/costs/limits for 47+ tools. — [repo](https://github.com/Javis603/token-monitor) | — |
| [xiufengsun/TokenTracker](https://github.com/xiufengsun/TokenTracker) | 2,161 | Local token & cost tracker for 31 tools. — [repo](https://github.com/xiufengsun/TokenTracker) | — |
| [chiphuyen/sniffly](https://github.com/chiphuyen/sniffly) | 1,277 | Claude Code dashboard with usage stats, **error analysis**, shareable dashboards. — [repo](https://github.com/chiphuyen/sniffly) | Python |
| [daaain/claude-code-log](https://github.com/daaain/claude-code-log) | 1,253 | Python CLI converting Claude Code transcript JSONL to HTML/Markdown. — [repo](https://github.com/daaain/claude-code-log) | Python |
| [hoangsonww/Claude-Code-Agent-Monitor](https://github.com/hoangsonww/Claude-Code-Agent-Monitor) | 1,134 | Real-time dashboard (hooks → SQLite) for Claude Code & Codex sessions, tools, subagents. — [repo](https://github.com/hoangsonww/Claude-Code-Agent-Monitor) | TS |
| [mikehasa/agentacct](https://github.com/mikehasa/agentacct) | 756 | Breaks each **task** into work steps: tools used, files changed, **tests run**, time and tokens; Claude Code, Codex, OpenCode; local, no telemetry. — [repo](https://github.com/mikehasa/agentacct) | Python |
| [nateherkai/token-dashboard](https://github.com/nateherkai/token-dashboard) | 754 | Claude Code JSONL → local cost analytics, hotspots, per-session. — [repo](https://github.com/nateherkai/token-dashboard) | Python |
| [Arindam200/cc-lens](https://github.com/Arindam200/cc-lens) | 599 | Local analytics dashboard for Claude Code. — [repo](https://github.com/Arindam200/cc-lens) | TS |
| [f/agentlytics](https://github.com/f/agentlytics) | 593 | Analytics for Cursor, Windsurf, Claude Code, VS Code Copilot, Zed, OpenCode. — [repo](https://github.com/f/agentlytics) | JS |
| [opalinehq/cli](https://github.com/opalinehq/cli) | 307 | Claude Code + Codex session analytics. — [repo](https://github.com/opalinehq/cli) | TS |
| [FlorianBruniaux/ccboard](https://github.com/FlorianBruniaux/ccboard) | 99 | TUI/Web: sessions, costs, hooks, MCP, budget alerts. — [repo](https://github.com/FlorianBruniaux/ccboard) | Rust |
| [Mai0313/VibeCodingTracker](https://github.com/Mai0313/VibeCodingTracker) | 14 | "Track AI coding costs" for Claude Code, Codex, Copilot, Gemini. — [repo](https://github.com/Mai0313/VibeCodingTracker) | Rust |

- Caveat: hook-based transcript readers may lack token/cost data; OpenObserve's Claude Code hook page warns "token usage / cost data is not available in the transcript format" for its approach. — [OpenObserve](https://openobserve.ai/docs/integration/claude-code-tracing). (Conflicts with ccusage etc., which compute tokens from JSONL `usage` fields; the likely difference is that cost in USD is not stored in the JSONL and must be computed from a price table.)
- CodeBurn explicitly says its dollar figures are "what your tokens would cost at API rates, not an invoice". — [CodeBurn README](https://github.com/getagentseal/codeburn)

### Inferences
- These tools establish that tokens/cost per session/day/project are a solved passive problem; the novel part for the thesis is joining sessions to **tasks and outcomes** (approved PR, tests passing), which only CodeBurn (per commit/PR), agentacct (per task) and git-ai (accepted rate) partially do.
- For subscription users (Claude Max etc.), all these tools report API-equivalent cost, not actual spend — must be stated in methodology.

### Gaps
- Licenses for most of the smaller repos not verified.
- Default Claude Code log path (`~/.claude/projects/<project>/<session>.jsonl`) is from prior knowledge; ccusage README fetched did not state it explicitly.

## 3. LLM observability platforms

### Takeaway
All major platforms are self-hostable and have Python SDKs; most do per-trace cost via built-in price tables. Several now have direct coding-agent integrations (Langfuse: Claude Code/Codex hooks, Copilot OTel; MLflow: `mlflow autolog claude`; OpenLIT topics include claude-code/codex).

### Cited Findings
| Platform | Stars (2026-10-31) | Notes |
|---|---|---|
| [BerriAI/litellm](https://github.com/BerriAI/litellm) | 62,435 | AI gateway/proxy, Python SDK, "cost tracking, guardrails, load balancing, and logging" for 100+ providers (description says Rust core + Python SDK). Its model price JSON is the de facto pricing source used by ccusage/CodeBurn. — [repo](https://github.com/BerriAI/litellm); [ccusage README](https://github.com/ccusage/ccusage) |
| [langfuse/langfuse](https://github.com/langfuse/langfuse) | 36,794 | Open-source tracing/evals, self-hosted topic; coding-agent integrations: Claude Code (Stop hook), Codex (plugin hooks, Codex ≥0.128), Copilot (native OTel), Cursor, Kiro, OpenCode, Augment; captures tokens per turn, tool calls, sessions; doesn't capture assembled CLAUDE.md context; old self-hosted v1/v2 lack OTLP endpoint. — [repo](https://github.com/langfuse/langfuse); [coding agent tracing](https://langfuse.com/resources/engineering/coding-agent-tracing) |
| [comet-ml/opik](https://github.com/comet-ml/opik) | 23,065 | Tracing/evals for LLM apps and agentic workflows, Python. — [repo](https://github.com/comet-ml/opik) |
| [Arize-ai/phoenix](https://github.com/Arize-ai/phoenix) | 12,081 | AI observability & evaluation, Python, OpenInference/OTel. — [repo](https://github.com/Arize-ai/phoenix) |
| [traceloop/openllmetry](https://github.com/traceloop/openllmetry) | 7,513 | OTel-based instrumentation for LLM apps (opentelemetry-python). — [repo](https://github.com/traceloop/openllmetry) |
| [Helicone/helicone](https://github.com/Helicone/helicone) | 6,248 | Proxy-based LLM observability, `llm-cost` topic. — [repo](https://github.com/Helicone/helicone) |
| [openlit/openlit](https://github.com/openlit/openlit) | 2,896 | OTel-native "agent harness engineering platform", ClickHouse; topics include claude-code, codex, cursor, coding-agents. — [repo](https://github.com/openlit/openlit) |
| MLflow | n/a (not fetched) | `mlflow autolog claude` installs a Claude Code plugin writing `MLFLOW_CLAUDE_TRACING_ENABLED`, `MLFLOW_TRACKING_URI`, `MLFLOW_EXPERIMENT_ID` into `.claude/settings.json`; traces prompts, responses, tool usage, timing, session metadata; MLflow ≥3.4; `mlflow.anthropic.autolog()` for Claude Agent SDK. — [MLflow docs](https://mlflow.org/docs/latest/genai/tracing/integrations/listing/claude_code); [Databricks docs](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/claude-code) |

- Licenses (not verified this session): Langfuse MIT core (EE folder separate); LiteLLM MIT (enterprise dir separate); OpenLLMetry Apache-2.0; OpenLIT Apache-2.0; Helicone Apache-2.0; Phoenix Elastic License 2.0; Opik Apache-2.0; MLflow Apache-2.0.
- Note: proxy-based tools (LiteLLM, Helicone) can intercept Claude Code traffic via `ANTHROPIC_BASE_URL` — prior knowledge, not verified this session.

### Inferences
- For a Python thesis artifact, MLflow (experiment tracking + Claude Code autolog) fits "experiment tracking" naturally; Langfuse fits team dashboards; LiteLLM proxy gives provider-agnostic cost per request with a virtual key per experiment arm.
- These platforms measure the LLM side well but none natively measures "approved task" — needs join with git/CI.

### Gaps
- Did not verify per-platform pricing-table coverage for latest Claude/GPT models.

## 4. AI code attribution (which lines/commits came from AI)

### Takeaway
Two competing open approaches: git-ai (Git Notes, line-level, Apache-2.0, ~2.9k stars, agent hooks for 14+ agents, `git ai stats --json`) and Cursor's Agent Trace spec (JSON trace records, v0.1.0-draft, CC BY 4.0). Vendor APIs (Cursor AI Code Tracking, Copilot `loc_added_sum`) give attribution only at org level.

### Cited Findings
- git-ai: agents call `git-ai checkpoint` when writing files; on commit, line-level attribution stored in Git Notes (`git log --show-notes="ai"`); survives rebase/squash/cherry-pick/amend; "does not use Git hooks" but manages agent hooks; supports Claude Code, Codex, Cursor, Copilot, OpenCode, Gemini, Windsurf, Amp, Continue, Junie, plus background agents (Codex Cloud, Devin…); `git ai stats --json` gives % AI code, AI lines generated vs committed, **accepted rate**, by tool/model, human overrides; `git ai blame`; own "Git AI standard" v3.0.0; Apache-2.0. 2,916 stars. — [git-ai repo](https://github.com/git-ai-project/git-ai)
- Agent Trace: Cursor's open spec, Version 0.1.0-draft, Status: Proposal (Jan 2026); JSON "trace record" linking code ranges to conversations/contributors; contributor types like `ai:autocomplete`, `ai:agent`; storage-agnostic; CC BY 4.0; non-goals: copyright/ownership. — [cursor/agent-trace](https://github.com/cursor/agent-trace); [agent-trace.dev](https://agent-trace.dev/); [InfoQ](https://www.infoq.com/news/2026/02/agent-trace-cursor)
- Reported backers (Cognition, Cloudflare, Vercel, Google Jules, Amp, OpenCode) — secondary source only. — [morphllm](https://www.morphllm.com/agent-trace-spec) (unverified)
- Cursor AI Code Tracking API: per-commit tab/composer/non-AI line counts (Enterprise, Alpha). — [Cursor docs](https://cursor.com/docs/account/teams/ai-code-tracking-api)
- Claude Code itself emits `claude_code.commit.count`, `pull_request.count`, `lines_of_code.count` — which counts commits/PRs/lines *made via Claude Code*, a passive attribution signal. — [Claude Code Monitoring docs](https://code.claude.com/docs/en/monitoring-usage)
- Note: an unrelated `feder-cr/git-ai` ("Git designed for AI agents", 1,029 stars, Oct 2026) exists — do not confuse. — [repo](https://github.com/feder-cr/git-ai)

### Inferences
- `Co-Authored-By: Claude …` trailers (Claude Code default commit attribution) allow commit-level counting via `git log --grep`, but are coarse (whole commit) and can be disabled by users; git-ai gives line-level fidelity.

### Gaps
- Did not fetch Claude Code settings docs to confirm the current name/default of the commit attribution setting (`includeCoAuthoredBy` / `attribution`) — mark as unverified.
- Whether git-ai implements/exports Agent Trace format: not stated on README.

## 5. Repos explicitly doing "vibe coding metrics" / cost per merged PR / AI-coding experiment tracking

### Takeaway
No widely-adopted repo implements the full thesis (cost per approved task + latency + human intervention + quality under an experimental protocol). Closest: CodeBurn (cost per commit/PR, one-shot rate), git-ai (accepted rate, per-PR cost in teams offering), agentacct (per-task steps/tests), Copilot repo-level metrics (PRs merged by coding agent, median minutes to merge). "vibe coding" + metrics repos are tiny (<25 stars).

### Cited Findings
- Most relevant (ranked): CodeBurn [link](https://github.com/getagentseal/codeburn); git-ai [link](https://github.com/git-ai-project/git-ai); agentacct [link](https://github.com/mikehasa/agentacct); ccusage [link](https://github.com/ccusage/ccusage); sniffly (error analysis) [link](https://github.com/chiphuyen/sniffly); agentsview [link](https://github.com/kenn-io/agentsview); builderz-labs/mission-control (6,422 stars, "dispatch tasks, review runs, track spend" for Claude Code/Codex) [link](https://github.com/builderz-labs/mission-control); Claude-Code-Agent-Monitor [link](https://github.com/hoangsonww/Claude-Code-Agent-Monitor); agentlytics [link](https://github.com/f/agentlytics); openlit (coding-agent topics) [link](https://github.com/openlit/openlit); VibeCodingTracker [link](https://github.com/Mai0313/VibeCodingTracker); vibetax (API-price receipt for Claude Code/Codex, 5 stars) [link](https://github.com/TinyFrontier/vibetax); kesslerio/vibe-check-mcp (anti-pattern detection, 23 stars) [link](https://github.com/kesslerio/vibe-check-mcp); darthrater78/claude-vibe-skills (commit approval, release gates, cost control, 22 stars) [link](https://github.com/darthrater78/claude-vibe-skills). — star counts from GitHub search 2026-10-31.
- GitHub search "vibe coding metrics OR ai coding metrics OR agentic coding cost" returned 65 repos, top one 23 stars. — [GitHub search](https://github.com/search?q=vibe+coding+metrics+OR+ai+coding+metrics+OR+agentic+coding+cost&type=repositories)
- Copilot org reports include `pull_requests.total_merged` and `median_minutes_to_merge`; repo-level reports split PRs by Copilot coding agent. — [GitHub docs](https://docs.github.com/en/copilot/reference/copilot-usage-metrics/copilot-usage-metrics); [changelog](https://github.blog/changelog/2026-07-17-repository-level-github-copilot-usage-metrics-generally-available/)

### Inferences
- The gap the thesis can fill: an open, Python, per-repo pipeline that joins agent OTel/session logs + git attribution + CI/PR outcomes into "cost per approved task", "human interventions per task", "time-to-merge", "rework/revert rate" under a defined protocol. Existing tools each cover one slice.

### Gaps
- Did not search Hacker News/blogs for practitioner write-ups on "cost per merged PR" (tool-call budget).
- Academic benchmarks (SWE-bench-style "benchmark your own repo") not covered here (likely covered by another researcher).

## 6. Passive vs protocol-required measurement

### Takeaway
Tokens, cost, latency, sessions, tool accept/reject, LOC and commit counts, AI line attribution, CI pass/fail and PR merge time can all be captured passively. Task definition/boundaries, "approved" criteria, quality judgments, counterfactual (time without AI), and developer effort/cognitive load require an experimental protocol.

### Cited Findings
- Passive via agent OTel: cost, tokens, sessions, LOC, commits, PRs, edit decisions, active time (Claude Code). — [Claude Code Monitoring](https://code.claude.com/docs/en/monitoring-usage); tokens/latency/tool decisions (Codex, Gemini). — [Codex](https://learn.chatgpt.com/docs/config-file/config-advanced); [Gemini](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/telemetry.md)
- Passive via session logs: tokens, API-equivalent cost, one-shot/retry rate, cost per commit/PR. — [CodeBurn](https://github.com/getagentseal/codeburn)
- Passive via git: AI line attribution and accepted rate. — [git-ai](https://github.com/git-ai-project/git-ai)
- Passive via platform APIs: PR merged counts, median minutes to merge. — [GitHub Copilot usage metrics](https://docs.github.com/en/copilot/reference/copilot-usage-metrics/copilot-usage-metrics)
- Hooks are local and can be disabled — "treat them as telemetry, not enforcement". — [Langfuse](https://langfuse.com/resources/engineering/coding-agent-tracing)

### Inferences
- Requires protocol: mapping sessions→tasks (e.g., `OTEL_RESOURCE_ATTRIBUTES=task.id`, branch naming, issue IDs in commits), acceptance criteria for "approved task", quality (defects post-merge, review comments, revert rate within N days — passively measurable only after defining the window), human-intervention taxonomy (interrupt vs reject vs manual edit), and baseline/control condition.
- API-equivalent cost vs actual subscription spend must be distinguished.

### Gaps
- No source found quantifying measurement error of transcript-derived costs vs actual billing.
