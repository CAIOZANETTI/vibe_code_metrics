# Empirical studies, frameworks and lessons learned on measuring AI-assisted / agentic software development

Research date: 2026-10-31. Every finding is dated. Labels:
- **[verified]**: confirmed against the primary source, fetched this session.
- **[secondary]**: confirmed only through secondary coverage.
- **[UNVERIFIED — from background knowledge]**: not confirmed this session. Check before citing.

## 1. METR studies (RCT 2025, 2026 follow-up, time horizons)

### Takeaway
METR's July 2025 RCT is the best-known rigorous result. Experienced open-source developers were 19% *slower* with AI, while believing they were about 20% faster. METR's Feb 2026 follow-up pointed toward speedup, but METR itself called that result unreliable. The reason is that randomizing per task broke down: developers refused to work without AI, and they held back the tasks where they expected AI to help most. METR is now redesigning the experiment, which is a central methodological lesson.

### Cited Findings
- **METR RCT (published 2025-07-10; data Feb–Jun 2025)** [verified via a fetch of devs-group.ch, which links the primary source]:
  - Sample: 16 experienced developers, 246 issues, repositories averaging more than 22,000 stars.
  - Randomization: each issue was randomly assigned to "AI allowed" or "AI disallowed".
  - Result: AI increased completion time by 19% (95% CI +2% to +39%).
  - Perception: developers *expected* a 24% speed-up beforehand and *believed afterwards* they had gained about 20%.
  - Sources: [METR blog](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/); [devs-group summary](https://devs-group.ch/en/blog/ai-productivity-studies-2026/)
- **METR follow-up, "We are Changing our Developer Productivity Experiment Design" (2026-02-24)** [verified] — [METR](https://metr.org/blog/2026-02-24-uplift-update/)
  - Authors: Becker, Rush, Cunningham, Rein, Mahamud. The study started in Aug 2025.
  - Sample: 57 developers (10 returning, 47 new from smaller, greenfield and less mature repositories), 143 repositories, more than 800 tasks, median experience 10 years. Pay fell from $150/h to $50/h.
  - Result for returning developers: −18% time (CI −38% to +9%). Negative means faster.
  - Result for new developers: −4% (CI −15% to +9%).
  - METR's assessment: the data is "only very weak evidence" of a speedup, and "the true speedup could be much higher" given who was excluded by selection.
- **Caveats METR listed in the follow-up** [verified] — [METR](https://metr.org/blog/2026-02-24-uplift-update/)
  - Developers declined to take part because they "do not wish to work without AI".
  - 30–50% of developers said they withheld tasks they did not want to do without AI.
  - Developers shifted the types of tasks they did.
  - Quality differed between conditions (code, documentation, tests).
  - Attrition in the no-AI arm: one developer completed no tasks there.
  - Time tracking became unreliable for developers running agents concurrently.
- **Design options METR is considering** [verified]: shorter and more intensive experiments; observational data (commits, transcripts); careful time-use surveys; fixed-task experiments; autonomous agent evaluations; developer-level randomization, which has less statistical power. — [METR](https://metr.org/blog/2026-02-24-uplift-update/)
- **Self-report figure** [secondary]: secondary sources say a METR survey found a median self-reported speed-up of about 3×. The METR post I fetched gives no specific figure, so treat this as unverified. — [dev.to summary](https://dev.to/gabrielanhaia/metrs-ai-coding-speed-study-broke-too-many-developers-wouldnt-work-without-ai-5afm)
- **Time horizons ("Measuring AI Ability to Complete Long Tasks", arXiv 2503.14499, Mar 2025)** [secondary]
  - Method: 170 tasks from HCAST, RE-Bench and SWAA. Each task's length is measured by how long humans took to do it. A logistic fit gives the task length at which a model succeeds 50% of the time.
  - Result: the 50% horizon doubled roughly every 7 months from 2019 to 2025.
  - The 80% horizon is about 5× shorter than the 50% horizon.
  - METR now publishes Time Horizon 1.1, which uses a larger task suite.
  - Sources: [ar5iv paper](https://ar5iv.labs.arxiv.org/html/2503.14499); [summary](https://muratbuffalo.blogspot.com/2026/03/measuring-ai-ability-to-complete-long.html)
  - A claimed ~12h horizon for Opus 4.6 is UNVERIFIED.

### Inferences
- Self-report is not a valid primary metric. A perception gap of about 40 percentage points (+20% perceived vs −19% measured) is the most-cited warning in this literature.
- Within-developer, per-task randomization becomes infeasible once AI is the norm, because of selection and withholding. A methodology repo should plan for that, for example with fixed-task benchmarks plus observational telemetry.
- Concurrent agents make wall-clock time per task ill-defined. The repo should measure human attention time separately from elapsed time.
- Time horizons measure model capability on benchmark tasks, not productivity in a team. Report success at 50% *and* 80%.

### Gaps
- I did not fetch the METR arXiv paper (2507.09089) itself. The Feb 2026 post gave no direct self-report number.
- I found no METR replacement study published after Feb 2026 up to Oct 2026.

## 2. Controlled experiments and field and industry studies (Copilot, Microsoft/Accenture, Google, Microsoft agents 2026, Uplevel, GitClear, Stanford, Faros, DORA, Stack Overflow)

### Takeaway
How large the gains look depends heavily on what is measured.
- Small, self-contained tasks in the lab show large speedups (55%).
- Enterprise field RCTs show moderate gains in output (about 21–26%), with wide CIs.
- Organization-level delivery metrics often show no improvement, plus rising instability, review load and duplication.

### Cited Findings
- **GitHub/Microsoft Copilot experiment (published 2022-09-07; paper Peng et al. 2023, arXiv 2302.06590)** [verified via the devs-group summary]: 95 developers, one task (an HTTP server in JavaScript). The Copilot group was 55% faster (CI 21%–89%), taking 1h11m vs 2h41m. — [GitHub blog](https://github.blog/news-insights/research/research-quantifying-github-copilots-impact-on-developer-productivity-and-happiness/)
- **Cui, Demirer, Jaffe, Musolff, Peng, Salz, "The Effects of Generative AI on High-Skilled Work" (SSRN 2024; Management Science 2025)** [secondary + SSRN abstract]
  - Design: three field RCTs at Microsoft, Accenture and an anonymous Fortune 100 company, 4,867 developers in total.
  - Result: completed tasks rose 26.08% (SE 10.3%). Less experienced developers adopted more and gained more.
  - Adoption was only about 60% after one year. An Accenture arm was reportedly abandoned because of layoffs; that detail comes from secondary sources.
  - Sources: [SSRN](https://papers.ssrn.com/abstract=4945566); [MIT Sloan](https://mitsloan.mit.edu/ideas-made-to-matter/how-generative-ai-affects-highly-skilled-workers)
- **Google enterprise RCT (Paradis et al., arXiv 2410.12944, ICSE-SEIP 2025)** [secondary]: 96 Google engineers. Developers were about 21% faster with AI (96 vs 114 minutes), but the CI was large. — [arXiv](https://arxiv.org/abs/2410.12944)
- **Microsoft CLI agents rollout (Murphy-Hill, Butler, Savelieva, arXiv 2607.01418, 2026-07-01)** [verified]
  - Scope: tens of thousands of Microsoft engineers, early-2026 rollout of Claude Code and Copilot CLI.
  - Result: adopters merged about 24% more PRs than the counterfactual, and the lift persisted over 4 months.
  - Adoption spread through social networks.
  - The authors themselves caution that a merged PR is not the same as value delivered.
  - Source: [arXiv](https://arxiv.org/abs/2607.01418)
- **Faros AI, "The AI Productivity Paradox Report 2025" (2025-07-23)** [verified]
  - Data: telemetry on more than 10,000 developers in 1,255 teams.
  - Method: Spearman correlations; a metric was reported only if it had data from at least 6 companies and p<0.05. The comparison is each team's two lowest-adoption quarters vs its two highest.
  - Results for high-adoption teams: tasks +21%, PRs merged +98%, PR review time +91%, PR size +154%, bugs per developer +9%.
  - No significant correlation with company-level throughput, DORA metrics or quality KPIs.
  - Source: [Faros](https://www.faros.ai/blog/ai-software-engineering)
  - The later Faros 2026 claim of review time up 441% (a median, from a different metric) is UNVERIFIED. — [Faros research](https://faros.ai/research)
- **DORA 2025, "State of AI-assisted Software Development" (Sept 2025)** [verified via Google Cloud blog]
  - Sample: nearly 5,000 respondents plus more than 100 hours of qualitative data.
  - AI use: 90% use AI at work, and more than 80% believe it increased their productivity. 30% have little or no trust in AI-generated code.
  - AI adoption is now *positively* related to throughput and product performance, but still *negatively* related to delivery stability. AI is described as an "amplifier".
  - The report presents seven AI capabilities and seven team profiles.
  - Sources: [Google Cloud](https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report); [DORA year in review](https://dora.dev/insights/dora-2025-year-in-review/)
  - DORA also moved from four to five delivery metrics in 2025 and published "ROI of AI-assisted Software Development" (updated 2026-04-22). — [DORA](https://dora.dev/insights/dora-2025-year-in-review/); [DORA research](https://dora.dev/research/)
- **DORA 2024** [UNVERIFIED — from background knowledge]: each 25% increase in AI adoption was associated with about −1.5% delivery throughput and about −7.2% delivery stability, alongside +3.4% code quality and +7.5% documentation quality. The +3.4% code-quality figure is corroborated by [i-programmer](https://www.i-programmer.info/news/105-artificial-intelligence/17871-gitclear-reveals-ais-negative-impact-on-code-quality.html). — check against [dora.dev/research/2024](https://dora.dev/research/2024/dora-report/)
- **GitClear "AI Copilot Code Quality" 2025 (Feb 2025)** [secondary]
  - Data: 211M changed lines, 2020–2024.
  - "Moved" code, used as a refactoring proxy, fell from 24.8% to 9.5% of changed lines (2021→2024).
  - Copy/pasted lines rose from 8.4% to 12.3%. 2024 was the first year copy/paste exceeded moved code.
  - Duplicated blocks rose about 8× in 2024.
  - This is a correlational trend, not proof of attribution to AI.
  - Sources: [DevClass](https://devclass.com/2025/02/20/ai-is-eroding-code-quality-states-new-in-depth-report/); [LeadDev](https://leaddev.com/software-quality/how-ai-generated-code-accelerates-technical-debt)
  - GitClear 2024 (projected churn doubling) is UNVERIFIED.
- **Stanford, Yegor Denisov-Blanch (AI Engineer talk, 2025)** [secondary; not peer-reviewed; model not disclosed]
  - Data: about 100k developers (some write-ups say about 120k) across more than 600 companies.
  - Output measure: delivered functionality from a code-evaluation model, not commits.
  - Gains: low-complexity greenfield 30–40%; low-complexity brownfield 15–20%; high-complexity brownfield 0–10%, possibly negative. AI-induced rework offsets part of the gain.
  - Sources: [AI Engineer talk](https://www.ai.engineer/talks/tbDDYKRFjhk-ai-developer-productivity); [Sirris summary](https://www.sirris.be/en/inspiration/how-much-more-productive-does-ai-make-developers)
- **Uplevel (2024)** [UNVERIFIED — from background knowledge]: Copilot access was associated with about a 41% higher bug rate and no improvement in cycle time or PR throughput, in a sample of about 800 developers. My search did not surface the primary source.
- **Stack Overflow Developer Survey 2025 (2025-07-29)** [secondary]
  - Sample: more than 49,000 responses from 177 countries.
  - Trust: 46% distrust AI accuracy vs 33% who trust it; only 3% "highly trust". Distrust was 31% in 2024.
  - Frustrations: 66% cite "AI solutions that are almost right, but not quite"; 45% say debugging AI code takes more time. One source gives 64% for the first figure, so coverage is inconsistent.
  - Sources: [InfoWorld](https://infoworld.com/article/4031673/ai-use-among-software-developers-grows-but-trust-remains-an-issue-stack-overflow-survey.html); [VentureBeat](https://venturebeat.com/ai/stack-overflow-data-reveals-the-hidden-productivity-tax-of-almost-right-ai-code)
- **Anthropic Economic Index, "AI's Impact on Software Development" (Apr 2025)** [secondary]
  - Scope: about 500k coding interactions.
  - 79% of Claude Code conversations were "automation" (AI does the task directly), vs 49% on Claude.ai.
  - The Mar 2026 edition notes coding is migrating to Claude Code.
  - Sources: [Anthropic](https://anthropic.com/research/impact-software-development); [PromptHub](https://prompthub.substack.com/p/what-500000-claude-sessions-reveal)
- **Agent PRs and breaking changes (Ferdous et al., arXiv 2603.27524, 2026)** [secondary]
  - Sample: 7,191 agent PRs vs 1,402 human PRs (Python).
  - Breaking-change rate: agent code generation 3.45% vs humans 7.40%; agent refactoring 6.72%; agent chore changes 9.35%.
  - Source: [arXiv](https://arxiv.org/abs/2603.27524)
- **ETH Zurich context-files study (Gloaguen et al., arXiv 2602.11988, 2026)** [secondary]: AGENTS.md-style context files generally did not improve success rates and raised inference cost by more than 20%. — [arXiv](https://arxiv.org/abs/2602.11988)

### Inferences
- The pattern across studies is consistent. Local output metrics rise: PRs, tasks, and lines (+21–98%). Downstream constraints absorb those gains: review time, PR size, instability, duplication. A methodology must measure end-to-end, from commit to production, not just authoring.
- Effect sizes are strongly context-dependent: greenfield vs brownfield, task complexity, developer experience, and organizational maturity (DORA's "amplifier"). Results must be stratified, not reported as a single average.
- Vendor and analytics-vendor reports (GitHub, Faros, GitClear, Uplevel, DX) have commercial interests and mostly correlational designs. Weight them below RCTs and peer-reviewed work.

### Gaps
- I did not fetch the DORA 2025 full report, so exact effect sizes and the list of seven capabilities are missing.
- I did not retrieve the primary sources for Uplevel and GitClear 2024.
- Google's other internal studies (e.g., the ML code-completion blog posts) were not checked.

## 3. Frameworks: DORA, SPACE, DevEx, DX Core 4, DX AI Measurement Framework

### Takeaway
Current consensus guidance is multi-dimensional measurement:
- utilization or adoption;
- impact on speed, quality and developer experience;
- cost and ROI.

It should be anchored to existing delivery metrics (DORA) and should explicitly avoid single proxies such as acceptance rate or lines of code.

### Cited Findings
- **DX AI Measurement Framework (DX, 2025)** [secondary + DX pages] — [DX framework](https://getdx.com/ai-measurement-framework/); [DX research](https://getdx.com/research/measuring-ai-code-assistants-and-agents/); [DX newsletter](https://newsletter.getdx.com/p/measuring-engineering-productivity-in-the-ai-era)
  - Three dimensions:
    - *Utilization*: DAU/WAU by team and role, and the share of PRs that are AI-assisted. DX reports that leading organizations reach only about 60% active usage.
    - *Impact*: time saved (developer hours per week), plus productivity, quality and developer-experience metrics, combined with longitudinal analysis.
    - *Cost*: AI spend in total and per developer; net time gained (time saved minus spend); an "AI hourly rate" (human-equivalent hours ÷ spend).
  - Data sources: telemetry plus self-report.
  - DX deliberately avoids acceptance rate as a measure of impact.
- **DORA**: four keys (deployment frequency, lead time, change failure rate, time to restore), expanded to five delivery metrics in 2025 (the fifth is rework rate, from background knowledge, UNVERIFIED). DORA 2025 adds an AI Capabilities Model with 7 capabilities. Recommended starting points for leaders: clear AI policies, connecting AI to internal context, foundational practices, safety nets, internal platform, user focus. — [DORA year in review](https://dora.dev/insights/dora-2025-year-in-review/); [Google Cloud](https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report)
- **SPACE** (Forsgren, Storey, Maddila, Zimmermann, Houck, Butler; ACM Queue 2021), **DevEx** (Noda, Storey, Forsgren, Greiler; ACM Queue 2023: feedback loops, cognitive load, flow state) and **DX Core 4** (DX, 2024: speed, effectiveness, quality, business impact) [UNVERIFIED — from background knowledge; not fetched this session]
  - [SPACE](https://queue.acm.org/detail.cfm?id=3454124); [DevEx](https://queue.acm.org/detail.cfm?id=3595878); [DX Core 4](https://getdx.com/research/measuring-developer-productivity-with-the-dx-core-4/)
- **Thoughtworks practitioner guidance** [secondary]: track lead time, deployment frequency and *rework rate* (treated as an early warning) to judge whether AI adds value. — [Paradigma interview](https://en.paradigmadigital.com/techbiz/interviewing-thoughtworks-radar-age-ai/)

### Inferences
- A methodology repo can map its metrics to three layers:
  - adoption/utilization (DX);
  - flow and outcome (DORA five metrics plus review time and PR size, given Faros's findings);
  - quality and debt (rework, change failure rate, duplication/moved-code ratio, security findings) plus developer experience (SPACE/DevEx surveys).
  It should add explicit cost per accepted change.

### Gaps
- I did not fetch the DX AI framework PDF itself, so the exact metric list is not confirmed.
- I did not verify that "rework rate" is DORA's fifth metric.

## 4. Lessons learned and pitfalls

### Takeaway
The main known mistakes are:
- trusting perception;
- optimizing vanity output metrics (Goodhart);
- ignoring review and rework cost;
- ignoring security and maintainability debt;
- running one-shot evaluations of non-deterministic systems;
- pooling greenfield and brownfield;
- experimental designs that break under adoption-driven selection.

### Cited Findings
- **Perception vs measurement**: measured −19%, believed +20%. — [METR 2025](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/)
- **Selection and withholding bias** in RCTs once AI is ubiquitous: 30–50% withheld tasks. — [METR 2026](https://metr.org/blog/2026-02-24-uplift-update/)
- **Vanity output metrics (Goodhart)**: PRs +98% with no company-level improvement. — [Faros](https://www.faros.ai/blog/ai-software-engineering)
  - The Microsoft authors caution that merged PRs ≠ value. — [arXiv 2607.01418](https://arxiv.org/abs/2607.01418)
  - DX rejects acceptance rate as an impact metric. — [DX](https://getdx.com/ai-measurement-framework/)
  - Background, UNVERIFIED: Google and Microsoft executives have publicly cited "% of code written by AI" (e.g., 25–30%). This is a widely criticized vanity metric.
- **Hidden review and rework cost**: PR review time +91% and PR size +154%. — [Faros](https://www.faros.ai/blog/ai-software-engineering)
  - "Almost right" frustration (66%) and longer debugging (45%). — [InfoWorld](https://infoworld.com/article/4031673/ai-use-among-software-developers-grows-but-trust-remains-an-issue-stack-overflow-survey.html)
  - Rework offsets gains in the Stanford data. — [Sirris](https://www.sirris.be/en/inspiration/how-much-more-productive-does-ai-make-developers)
- **Security**: Veracode 2025 GenAI Code Security Report (2025-07-30).
  - Method: 80 coding tasks across more than 100 LLMs, checked against CWE categories.
  - Insecure code in about 45% of cases. Java failed more than 70% of the time; Python, C# and JS 38–45%.
  - Models failed to defend against XSS in 86% of relevant samples and against log injection in 88%.
  - Security did not improve as models got larger or newer, even though syntax correctness did.
  - Sources: [Veracode press release](https://www.veracode.com/press-release/ai-generated-code-poses-major-security-risks-in-nearly-half-of-all-development-tasks-veracode-research-reveals/); [Help Net Security](https://www.helpnetsecurity.com/2025/08/07/create-ai-code-security-risks/)
- **Maintainability debt**: less refactoring and more duplication. — [GitClear via DevClass](https://devclass.com/2025/02/20/ai-is-eroding-code-quality-states-new-in-depth-report/)
  - Thoughtworks Radar Vol. 32 (Apr 2025) cautions against "complacency with AI-generated code" and calls for supervised agents. — [Thoughtworks Radar PDF](https://thoughtworks.com/content/dam/thoughtworks/documents/radar/2025/04/tr_technology_radar_vol_32_en.pdf)
- **Instability**: AI adoption remains negatively associated with delivery stability. — [DORA 2025](https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report)
- **Greenfield vs brownfield and complexity**: 30–40% vs 0–10% gains. — [Stanford talk](https://www.ai.engineer/talks/tbDDYKRFjhk-ai-developer-productivity)
  - METR's new cohort, which included greenfield and less mature repositories, showed different effects from the original experts on mature repositories. — [METR 2026](https://metr.org/blog/2026-02-24-uplift-update/)
- **Experience heterogeneity**: juniors gain more in the Microsoft/Accenture RCTs. — [SSRN](https://papers.ssrn.com/abstract=4945566)
  - Agents helped students finish tasks but harmed comprehension (arXiv 2607.26375). — [devs-group summary](https://devs-group.ch/en/blog/ai-productivity-studies-2026/)
- **Reliability thresholds**: the 80% horizon is about 5× shorter than the 50% horizon. — [METR time horizons](https://ar5iv.labs.arxiv.org/html/2503.14499)
- **Context engineering assumptions should be tested**: AGENTS.md files did not raise success and cost more than 20% extra. — [arXiv 2602.11988](https://arxiv.org/abs/2602.11988)
- **LLM non-determinism and benchmark contamination** [UNVERIFIED; no primary source fetched this session]: practitioners report that single runs mislead, so they recommend repeated trials (pass@k / pass^k), reporting variance, and using fresh or private tasks because public benchmarks such as SWE-bench may be contaminated. Sources found: none this session. Candidates to check: SWE-bench Verified documentation, "SWE-bench+" (arXiv 2410.06992), and the τ-bench pass^k metric (arXiv 2406.12045).
- **Practitioner blogs** (Simon Willison, Armin Ronacher, martinfowler.com/Birgitta Böckeler, Anthropic's "How Anthropic teams use Claude Code"): **not retrieved this session**. Search budget ran out, so no claims are made about them. Candidates: [simonwillison.net](https://simonwillison.net/), [lucumr.pocoo.org](https://lucumr.pocoo.org/), [martinfowler.com](https://martinfowler.com/), [Anthropic blog](https://www.anthropic.com/news/how-anthropic-teams-use-claude-code).

### Inferences
Checklist for the methodology repo:
1. Never use self-reported speed-up as the primary outcome. Collect it, but compare it against telemetry.
2. Pre-register the metrics, and pair every output metric (PRs, LOC, % AI code) with a counter-metric for quality or cost: rework, change failure rate, review time, defects, security findings.
3. Measure end-to-end lead time and reviewer time, not just authoring time.
4. Stratify by greenfield/brownfield, task complexity, repository maturity and developer experience.
5. For agent and tool evaluations, use repeated runs with variance and CIs on private, uncontaminated tasks, and report both 50% and 80% reliability.
6. Track cost (tokens and money) per merged, non-reverted change.
7. Define how time is measured when agents run concurrently, separating human attention time from wall-clock time.
8. Expect selection effects and say where the design might break.

### Gaps
- No primary sources were gathered this session on LLM non-determinism or benchmark contamination.
- The individual practitioner blogs (Willison, Ronacher, Fowler) and Anthropic's internal team report were not retrieved.
- The Veracode report PDF was not fetched. The headline numbers come from its press release and trade press.
