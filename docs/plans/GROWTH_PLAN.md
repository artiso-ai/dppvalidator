# dppvalidator Growth Plan

> **Version**: 1.0
> **Created**: 2026-05-10
> **Status**: Strategic — adoption & reach
> **Audience**: Maintainers, ARTISO leadership, contributors
> **Pairs with**: [`STRATEGIC_ROADMAP.md`](STRATEGIC_ROADMAP.md) (capability roadmap)
> and [`IMPROVEMENT_ROADMAP.md`](IMPROVEMENT_ROADMAP.md) (technical gap closure).

This document focuses on **distribution, discoverability, and adoption** — not on what we
build, but on how the work we ship becomes the default tool engineers reach for when they
hear "Digital Product Passport." The technical roadmaps already chart capability growth;
this plan layers a growth strategy on top, with explicit emphasis on the **agent-native
ecosystem** (MCP, Claude Code plugins, llms.txt) where dppvalidator can win
disproportionately because virtually no DPP tool is positioned for it today.

______________________________________________________________________

## Executive summary

| Layer                     | Today (2026-05-10)       | 12-month target                  |
| ------------------------- | ------------------------ | -------------------------------- |
| PyPI downloads / month    | **176**                  | **5,000–10,000**                 |
| GitHub stars              | **8**                    | **600+**                         |
| GitHub forks              | **0**                    | **30+**                          |
| External contributors     | 0                        | **8+** (≥ 3 from non-ARTISO)     |
| Reachable agents (MCP)    | 0                        | **All major MCP clients**        |
| Claude Code installs      | 0                        | **listed in official marketplace** |
| Listed in DPP registries  | 0                        | UN/CEFACT, CIRPASS-2, EU DPP-WG  |
| Reference integrations    | 1 (CI snippet)           | **8+** (FastAPI, Action, Docker, dbt, Airflow, Shopify, Cursor, ChatGPT) |

**Strategic thesis (one paragraph).** dppvalidator is technically ahead of every public
DPP validator we can find (7-layer pipeline, dual-family UNTP + CIRPASS-2 support, plugin
system, JSON-LD and VC verification). It is **not** ahead on discovery: a brand engineer
hitting the 2027 ESPR deadline and asking ChatGPT/Claude/Cursor "how do I validate a DPP
in Python?" today gets nothing useful, because the model has nothing in its training set
and no tool to call. The single highest-leverage growth move is therefore to make
dppvalidator **the validator that LLM agents reach for**, by shipping an MCP server, a
Claude Code plugin, and richly cross-linked llms.txt content. The mandate timeline (ESPR
textiles **2027-07**) gives us a ~14-month window before the market hardens around
whichever tools are easiest to find.

______________________________________________________________________

## Critical evaluation of the current state

### What is already good (do not rebuild)

- **Engineering quality.** Multi-Python CI, mutation testing, property tests, ≥90 %
  coverage, ruff + ty, SBOM, pip-audit. This is a credibility asset — most OSS in the
  ESPR space is at "v0.1.0, no tests" maturity. The plan should *amplify* this signal,
  not duplicate it.
- **Two specs in one package.** `dppvalidator migrate` between UNTP 0.6/0.7 and the
  CIRPASS-2 reference structure 1.3 is a unique selling point. No other tool we found
  does this.
- **Documentation surface.** mkdocs site, [`llms.txt`](../llms.txt) and
  [`llms-ctx.txt`](../llms-ctx.txt) are already published — better than 95 % of OSS
  Python packages.
- **Plugin architecture & licence isolation.** Cleanly separates MIT core from
  GPL-3.0 plugins; lets us ship industry packs without licence drag on the core.

### Where growth is bottlenecked (this plan's targets)

| #  | Gap                                                     | Cost of leaving it             | Leverage                                |
| -- | ------------------------------------------------------- | ------------------------------ | --------------------------------------- |
| 1  | **No agent-callable surface** (no MCP server)           | Invisible to ChatGPT/Claude/Cursor agents in 2026 | **Highest** — primary thesis            |
| 2  | **No Claude Code plugin** for end users                 | Loses every "vibe coder" brand engineer    | **High** — small effort, large signal   |
| 3  | **PyPI metadata is dev-only**                           | Doesn't surface to non-Python searchers   | Medium — quick wins in keywords/READMEs |
| 4  | **No UNTP/CIRPASS conformance badge or report**         | Buyers cannot verify our claims | High — authority asset |
| 5  | **No reference integrations** (Action, Docker, FastAPI starter, dbt, Airflow) | Each is a missing onramp | Medium-high — multiplies install paths   |
| 6  | **No comparison/alternatives content**                  | Loses Google + LLM SEO         | Medium — write once, reused forever     |
| 7  | **No JS/TS port or WASM playground**                    | Excludes the Web/Node majority of fashion-tech buyers | High — but expensive (Phase 5)          |
| 8  | **No multi-channel distribution** (Conda-Forge, Docker Hub, Homebrew tap, pre-commit-hooks.org) | Single PyPI bottleneck | Low — one-time setup, perpetual benefit |
| 9  | **No public roadmap or release cadence advertised**     | Looks abandoned to first-time visitors | Low — pure communication |
| 10 | **No conference / regulatory presence**                 | UN/CEFACT, CIRPASS-2 working groups don't know we exist | Variable — high for authority |

### Anti-patterns to avoid (explicit guardrails)

- **Do not** rebuild for a JS audience before the Python core has 1k stars. Cost of a TS
  port is 6+ person-weeks and a parallel maintenance burden; we get more leverage from
  shipping an MCP server (which makes us *language-agnostic* to agent users without a
  port).
- **Do not** spam CIRPASS / DPP Slack / LinkedIn. Authority comes from being cited *by
  others*; outbound posting before we have a UN/CEFACT-published conformance report
  burns credibility we cannot earn back.
- **Do not** add capability-driven roadmap items to this document. Capability lives in
  [`STRATEGIC_ROADMAP.md`](STRATEGIC_ROADMAP.md). This plan only covers reach.
- **Do not** re-license the core. MIT is the right floor for adoption; the GPL-3.0
  plugin pattern already exists for spec-aligned extensions.
- **Do not** ship a hosted SaaS validation endpoint until Phase 5. It splits maintenance
  effort and creates a perceived two-tier project; a public Pyodide-powered playground
  achieves the same demo value with zero ops cost.

______________________________________________________________________

## Cross-cutting threads

These run through every phase rather than living in one of them:

1. **Agent-native by default.** Every artifact we ship — docs page, error message,
   release note, CLI help — is written so an LLM can quote it back to a human. The
   `llms.txt` / `llms-ctx.txt` already do this for the package surface; we extend the
   discipline to the docs site, error registry, and migration guides.
2. **Measurement before motion.** Phase 0 wires up dashboards. Subsequent phases each
   declare a numeric target *before* shipping. We do not declare phases "done" on the
   basis of activity.
3. **Compounding artifacts > one-shot promotion.** Each phase outputs a durable artifact
   (Action, plugin, badge, registry entry, comparison page) that keeps earning attention
   after we stop pushing it. No phase ends in a tweet thread or a one-off blog post.

______________________________________________________________________

## Phase 0 — Baseline & instrumentation (Week 0, 2 days)

> Without numbers we are guessing. The cost is low; the signal lasts for the whole plan.

### Deliverables

- **Public KPI dashboard.** A single
  [`docs/internal/growth-metrics.md`](internal/growth-metrics.md) (or a Notion/Sheets
  link in `STRATEGIC_ROADMAP.md`) with a small Python script in
  [`scripts/`](../scripts/) that snapshots monthly:
  - `pypistats.org` weekly + monthly downloads
  - GitHub stars, forks, watchers, open issues, contributor count
  - GitHub Pages traffic (Plausible or GitHub-native insights)
  - PyPI search rank for keywords `dpp`, `digital product passport`, `untp`, `espr`,
    `cirpass`
  - Mentions across `news.ycombinator.com`, `dev.to`, `medium.com`, `reddit.com/r/python`
- **GitHub repository hygiene** (1 hour). Topics set on the repo: `dpp`, `untp`,
  `cirpass`, `espr`, `digital-product-passport`, `eu-regulation`, `mcp`,
  `claude-code-plugin`, `verifiable-credentials`, `circular-economy`. Repository
  description rewritten to lead with the verb (currently "GDPR compliance engine for
  physical products" → "Validate EU Digital Product Passports in Python: 7-layer
  pipeline, UNTP 0.6/0.7 + CIRPASS-2, MCP-callable.").
- **Release-notes template** committed to `.github/RELEASE_TEMPLATE.md` so every
  release ships with a "What changed for users / agents / integrators" matrix.

### Exit criteria

- Dashboard is auto-updated weekly by a scheduled GitHub Action.
- Baseline values for all KPIs in the table above are captured.

______________________________________________________________________

## Phase 1 — Discoverability hardening (Weeks 1–3)

> Make the package findable through *non-search* channels. The work in this phase pays
> back forever and unblocks every later phase.

### 1.1 PyPI / GitHub frontstage (1 week)

- **Keyword expansion in [`pyproject.toml`](../pyproject.toml).** Existing keyword list
  is good; add `mcp`, `model-context-protocol`, `claude-code`, `agentic`, `llm-tooling`,
  `eu-dpp`, `ecodesign`, `passport-textile`, `passport-battery`, `passport-tyre`,
  `verifiable-credential`, `eudi`, `vc-jwt`, `sd-jwt`. (Order matters; PyPI weights the
  first ~10.)
- **README hero rewrite.** Current README is engineer-shaped. Replace the first 30 lines
  with a three-column "What you get" block targeting:
  - **Python developers** ("validate in 3 lines"),
  - **Agents / LLM tools** ("MCP-callable, plugin available"),
  - **Compliance teams** ("ESPR-aligned, dual-family UNTP+CIRPASS").
  Lead each column with a copy-pasteable code snippet.
- **README badges row** add: PyPI status (Beta), conda-forge (once shipped), MCP
  registry, Claude Code plugin marketplace, CIRPASS-2 alignment, GitHub Action
  marketplace.
- **GitHub social preview image** rendered from
  [`docs/assets/logo.png`](assets/) with the tagline.
- **`SECURITY.md`** already present — link it from the README to surface
  professionalism.

### 1.2 Documentation site amplification (1 week)

- **mkdocs front-page rewrite** to mirror the README hero, adding a "Choose your path"
  navigation: Brand engineer / Compliance lead / AI agent author / Plugin author.
- **`/docs/comparison.md`** — an honest "alternatives" page covering UNTP reference
  validators, generic JSON-LD tools, and the (mostly closed-source) enterprise
  platforms. Includes a feature matrix and links *to* competitors. This page is the
  single biggest LLM-SEO investment we make: when a user asks any LLM "what's the best
  Python DPP validator?" the model returns whatever page best answers the comparison
  question, and ours will be the first one written.
- **Per-version landing pages** at `/docs/versions/0.6.x`, `/0.7.0`, `/cirpass-1.3` so
  the docs canonicalise the keywords most users type.
- **Migration guide upgrade.** [`docs/guides/migration-0-6-to-0-7.md`](guides/migration-0-6-to-0-7.md) is
  already strong; add a "Migration cookbook" with 6–10 specific symptom-to-fix entries
  copy-pasted from real failure logs, because that is what people actually paste into
  search engines.

### 1.3 Agent-readable surface (3 days)

- **Extend `llms.txt`** to include canonical URLs for the comparison page, the migration
  cookbook, the error catalogue, and the version landing pages.
- **Publish per-section bundles** at `/docs/llms/validate.txt`,
  `/docs/llms/migrate.txt`, `/docs/llms/sign.txt`, etc. so that agent authors can pull
  scoped context without a 50KB blob.
- **Error catalogue as JSON.** Already generated by
  [`scripts/generate_error_docs.py`](../scripts/generate_error_docs.py); also publish
  the machine-readable `errors.json` at a stable URL on the docs site so agents can
  resolve `SCH001` / `MDL003` / etc. into structured fixes.

### 1.4 Distribution channel widening (3 days)

- **Conda-Forge feedstock** (~1 day end-to-end). Captures the data-science /
  conda-locked enterprise audience that pip never reaches.
- **Pre-commit-hooks.org listing.** Already have
  `dppvalidator-precommit` exposed in [`pyproject.toml`](../pyproject.toml#L64); just
  needs a `.pre-commit-hooks.yaml` and a PR to `pre-commit/pre-commit-hooks` README.
- **Homebrew tap** (`artiso-ai/homebrew-dppvalidator`) for the macOS-first DevX.
- **Docker Hub image** `artiso/dppvalidator:<version>` with the `[cli,rdf]` extras
  pre-installed and a 30-line `README` showing one-line `docker run` validation.
- **GitHub Action** in `.github/actions/validate-dpp/action.yml` and
  `marketplace.yml` so `uses: artiso-ai/dppvalidator-action@v1` works in any repo.
  Submit it to the GitHub Marketplace.

### Exit criteria

- KPI dashboard shows a measurable lift in `last_month` PyPI downloads (target: ≥ 400 vs
  176 baseline).
- README hero passes the "30-second test" with three external readers (1 brand engineer,
  1 backend dev, 1 compliance lead).
- Comparison page is indexed by Google and cited at least once when asking
  ChatGPT/Claude "compare DPP validators."

______________________________________________________________________

## Phase 2 — Agent-native distribution v1 (Weeks 4–6)

> The thesis phase. We make dppvalidator the validator any AI agent can call.

Background: the [Claude Code skills doc](https://code.claude.com/docs/en/skills), the
[plugins doc](https://code.claude.com/docs/en/plugins), the
[plugin marketplaces doc](https://code.claude.com/docs/en/plugin-marketplaces) and the
[plugin-hint protocol](https://code.claude.com/docs/en/plugin-hints) collectively define
a complete distribution stack: SKILL.md → plugin → marketplace → CLI hint, with the MCP
protocol as the orthogonal cross-vendor surface (ChatGPT, Cursor, Continue.dev, Claude
Desktop, etc.).

### 2.1 Ship `dppvalidator-mcp` (Week 4, ~5 days)

A standalone, side-effect-free MCP server that wraps the existing `ValidationEngine`,
`migrate`, and `JSONLDExporter` surface.

- **Tools exposed** (start small, expand later):
  - `validate_dpp(passport: dict | str, layers?: list[str], strict?: bool, target?: str, schema_version?: str) -> ValidationResult`
  - `detect_dpp_version(passport: dict | str) -> {family, version, confidence}`
  - `migrate_dpp(passport: dict | str, to: str) -> {migrated, warnings}`
  - `export_dpp_jsonld(passport: dict | str, mode: "untp" | "eu-dpp") -> str`
  - `explain_error(code: str) -> {description, fix, docs_url}`
  - `list_supported_versions() -> list[str]`
- **Implementation.** Build on `mcp` Python SDK / FastMCP; package as
  `dppvalidator[mcp]` extra and publish a `dppvalidator-mcp` console script.
- **Distribution surfaces:**
  - PyPI extra: `pip install "dppvalidator[mcp]"`
  - `uvx`: `uvx dppvalidator-mcp` (zero-install for `claude mcp add`)
  - Anthropic MCP Registry submission: <https://api.anthropic.com/mcp-registry>
  - Listed in the README "Use from any agent" section, with pasteable
    `claude mcp add dppvalidator -- uvx dppvalidator-mcp` and ChatGPT/Cursor configs.
- **Resources** (read-only): expose `dppvalidator://schemas/{version}` and
  `dppvalidator://errors/{code}` so agents can browse them without tool calls.

The MCP server is **the multiplier**: every agent ecosystem (Claude, ChatGPT, Cursor,
Continue, Cline, Open Interpreter, custom n8n nodes) gains DPP validation simultaneously.
A 5-day cost buys orders-of-magnitude more reach than any individual integration.

### 2.2 Claude Code plugin: `dppvalidator` (Week 5, ~3 days)

Three components in one plugin:

```text
plugins/claude-code/dppvalidator/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── validate/SKILL.md         # /dppvalidator:validate <file>
│   ├── migrate/SKILL.md          # /dppvalidator:migrate <file> --to <ver>
│   ├── explain-error/SKILL.md    # /dppvalidator:explain-error <code>
│   └── scaffold/SKILL.md         # /dppvalidator:scaffold <product-type>
├── agents/
│   └── dpp-reviewer.md           # subagent that runs full validation + risk summary
├── hooks/
│   └── hooks.json                # PostToolUse on Write|Edit *.dpp.json -> auto-validate
├── .mcp.json                     # registers dppvalidator-mcp at plugin scope
└── README.md
```

- **`SKILL.md` frontmatter conventions** (per the
  [skills reference](https://code.claude.com/docs/en/skills)):
  - `description:` first sentence is the one Claude matches against — front-load DPP /
    UNTP / CIRPASS keywords.
  - `paths:` set to `**/*.dpp.json,**/passport*.json` so the skill auto-loads when the
    user is editing DPP fixtures.
  - `allowed-tools:` `Bash(uvx dppvalidator *)` so the skill never prompts the user for
    permission to run validation.
- **`dpp-reviewer` subagent** with `tools: Read, Grep, Glob, Bash(uvx dppvalidator *)`
  and a system prompt that instructs it to run validation, group errors by severity,
  and emit a markdown report. Triggered automatically by Claude when the user pastes
  DPP JSON or asks "is this DPP valid?".
- **Hook**: `PostToolUse` matcher on `Write|Edit` — when a `*.dpp.json` file is
  saved, run `uvx dppvalidator validate "$file" --strict --json` and attach the
  result. Replicates the ergonomics of `eslint --fix on save` for DPP authors.

Distribution:

- **Marketplace.** Create
  [`artiso-ai/claude-plugins`](https://github.com/artiso-ai/claude-plugins) with a
  `.claude-plugin/marketplace.json` listing `dppvalidator` (and any future ARTISO
  plugins). Users install with:
  ```text
  /plugin marketplace add artiso-ai/claude-plugins
  /plugin install dppvalidator@artiso-claude-plugins
  ```
- **Submit to the official Anthropic marketplace** via
  <https://platform.claude.com/plugins/submit>. A listing there is the prerequisite for
  Phase 2.3.
- **Plugin hint protocol** (Phase 2.3) is the thing that actually drives installs.

### 2.3 CLI plugin-hint emission (Week 5, 1 day)

Per the [plugin hints doc](https://code.claude.com/docs/en/plugin-hints), once the
plugin is in the official marketplace, the CLI emits a one-line stderr marker that
prompts Claude Code users to install it on first contact. Add to
`src/dppvalidator/cli/__init__.py`:

```python
import os, sys
if os.environ.get("CLAUDECODE"):
    print(
        '<claude-code-hint v="1" type="plugin" '
        'value="dppvalidator@claude-plugins-official" />',
        file=sys.stderr,
    )
```

Gate emission on the `--help` path and unknown-subcommand errors (the two highest-yield
touchpoints called out in the docs). Cost: <30 lines of code; benefit: every Claude
Code user who runs `dppvalidator` gets a one-tap install prompt.

### 2.4 ChatGPT Custom Connector + Cursor / Continue.dev recipes (Week 6, 2 days)

The MCP server unlocks all of these with no code changes — only documentation.

- `docs/integrations/chatgpt.md` — ChatGPT custom connector via the OpenAI MCP
  hosting story (or via `mcp-proxy` while native support stabilises).
- `docs/integrations/cursor.md` — Cursor's `.cursor/mcp.json`.
- `docs/integrations/continue.md` — Continue.dev MCP block.
- `docs/integrations/claude-desktop.md` — Claude Desktop config.
- Each page ends with a 30-second screencast (.gif) of "edit a DPP, get a validation
  result inline." These gifs are the unit of social-media currency in this market.

### Exit criteria

- `dppvalidator-mcp` is installable and listed in the Anthropic MCP Registry.
- `dppvalidator` Claude Code plugin is in the official marketplace, with ≥1 install
  prompt fired in our own dogfooding session.
- One agent-ecosystem integration page goes viral on Hacker News / r/LocalLLaMA / X
  (we don't *plan* the virality; we plan the *artifact*).
- KPI: ≥ 750 PyPI downloads in the trailing 30 days; ≥ 50 GitHub stars.

______________________________________________________________________

## Phase 3 — Integration & onramps (Weeks 7–10)

> Once an agent or developer says "yes, I want this," every additional onramp
> compounds. Phase 3 is high-volume, low-creativity execution.

### 3.1 Reference apps (Week 7, 3 days)

A new top-level [`examples/`](../examples/) tree (we already have a starter
`dppvalidator_example_plugin`) containing:

- **`fastapi-validation-service/`** — minimal POST /validate endpoint, Dockerfile,
  Helm chart, OpenAPI spec.
- **`django-supplier-portal/`** — accepts supplier DPP submissions, validates server-side,
  surfaces errors in the admin.
- **`airflow-dag/`** — a `dppvalidator validate` operator + a sensor that watches an S3
  bucket of DPP fixtures.
- **`dbt-project/`** — DPP rows in a warehouse validated as a dbt test.
- **`shopify-admin-app/`** — Remix-based Shopify embedded app skeleton that calls the
  MCP server.
- **`cli-batch/`** — a `find ... -name "*.dpp.json" | xargs dppvalidator` recipe with
  `--accept-warnings`, `--strict`, etc.

Each example **lives in its own README with screen recordings** and is referenced from
the main docs' "Choose your path" navigation.

### 3.2 GitHub Action polish (Week 8, 2 days)

The Phase 1 Action ships as MVP. Phase 3 promotes it to v1:

- Inputs: `path`, `strict`, `target`, `schema-version`, `format` (json | sarif |
  checkstyle), `fail-on-warning`.
- **SARIF output** so violations show up in the GitHub Code Scanning UI exactly like a
  CodeQL alert. This is the killer feature that lifts adoption from "tool people add"
  to "tool people forget they added."
- Marketplace submission with examples; pin the action to a major version branch so we
  can ship patches without breaking pinned pipelines.

### 3.3 IDE + Editor integrations (Week 9, 3 days)

- **VS Code extension** — wraps the CLI, surfaces errors as squiggles via the LSP
  pattern. *Or* shortcut: publish a JSON Schema file at a stable URL so VS Code's
  built-in JSON validation catches schema-level issues with zero extension. Ship the
  schema file first; build the extension only if metrics justify it.
- **JetBrains plugin** — same shortcut: publish JSON Schema mappings.
- **JSON Schema Store entry** so `passport*.json` auto-validates everywhere
  (<https://www.schemastore.org/json/>).

### 3.4 Pre-commit + lint integrations (Week 9, 1 day)

- Already publish `dppvalidator-precommit`. Phase 3 adds the
  `.pre-commit-hooks.yaml`, a PR to `pre-commit/awesome-pre-commit` lists, and a docs
  page ([`docs/integrations/pre-commit.md`](integrations/)) with the canonical block.

### 3.5 Cross-runtime callability (Week 10, 3 days)

This is the targeted, surgical alternative to a full TS port:

- **Pyodide-powered playground** at `https://artiso-ai.github.io/dppvalidator/play/`.
  Validates in-browser, no backend. Source in
  [`docs/play/`](play/) with a 100-line `index.html`. The
  cost is one weekend; the SEO and demo value lasts forever.
- **Single-file CLI binary** via `pyinstaller` or `pex`, attached to GitHub Releases so
  non-Python users can `curl | sh` it. Targets macOS (arm64, x86_64) and Linux
  (x86_64); Windows can wait.

### Exit criteria

- ≥ 5 integration pages published, each with a working repo and a 30-second screencast.
- GitHub Action shows ≥ 100 workflow runs across non-ARTISO repos in the trailing
  30 days (queryable via the Action API).
- Playground load count ≥ 1,000 in the trailing 30 days.
- KPI: ≥ 1,500 PyPI downloads in the trailing 30 days; ≥ 150 GitHub stars.

______________________________________________________________________

## Phase 4 — Authority & community (Weeks 11–16)

> Adoption beyond hobby use requires that "ARTISO says it's compliant" be replaced by
> "UN/CEFACT says it is."

### 4.1 Conformance & certification (Weeks 11–13)

- **Public conformance test report.** Run dppvalidator against the UN/CEFACT-published
  test fixtures, both 0.6.x and 0.7.0, and publish a signed report at
  `https://artiso-ai.github.io/dppvalidator/conformance/<version>/`. Include both pass
  *and* fail cases — transparency is the asset.
- **Submit to UN/CEFACT.** Apply to the UNTP DPP working group for our validator to be
  listed as a conforming implementation. Track via
  [`docs/conformance/untp-application.md`](conformance/).
- **Submit to CIRPASS-2 / EU DPP-WG.** ARTISO's existing relationships are the lever
  here; this plan only schedules the milestone.
- **Aligned with `dpp.vocabulary-hub.eu`** statement is already in the README; back it
  up with a versioned diff page (`docs/conformance/eu-dpp-vocabulary.md`) so claims are
  auditable.

### 4.2 Domain plugin packs (Weeks 13–15)

The plugin system is built and unused in the wild. Each pack is a credibility asset and
a separate PyPI package:

- **`dppvalidator-batteries`** — EU Battery Regulation 2023/1542 fields. Highest demand
  outside textiles; mandate begins **2027-02-18**.
- **`dppvalidator-electronics`** — paired with the upcoming ESPR electronics delegated
  act. Signal early.
- **`dppvalidator-construction`** — CPR + EPC fields. Adjacent vertical, large market.
- **`dppvalidator-tyres`** already exists (GPL-3.0); promote, harden, and document.

Each plugin ships its own SKILL.md set in the Claude Code plugin (Phase 2 stays generic;
Phase 4 layers vertical depth on top).

### 4.3 Community infrastructure (Weeks 11–12, 2 days)

- **GitHub Discussions** enabled with three pinned categories: Q&A, Show & Tell,
  Feature Requests.
- **`CODE_OF_CONDUCT.md`** and **`GOVERNANCE.md`** committed; ARTISO is the BDFL but the
  governance doc names the path to an open contributor council once we hit 5 external
  committers.
- **Issue & PR templates** for bug reports, version-bump migrations (we already have
  the migration plan template), feature requests, and security reports.
- **`good-first-issue` tagging pass** on the existing 1 open issue and on every issue
  created from Phase 3 onward.

### 4.4 Content & SEO (Weeks 13–16)

Each output is a permanent asset, not a tweet.

- **Five long-form pieces** at `docs/blog/`:
  1. "How EU ESPR breaks every DPP we tested in production" (controversy + concrete).
  2. "Validating UNTP 0.7.0 in 200 lines of Python" (canonical search term).
  3. "Why your DPP probably isn't a valid Verifiable Credential (yet)" (signature + JSON-LD).
  4. "From CSV to CIRPASS-2: a migration story" (operational).
  5. "Calling dppvalidator from ChatGPT, Claude, and Cursor" (the agent thesis).
- **Cross-publish** to dev.to and Medium *with canonical links back to the docs site*.
- **Conference talks** (proposals submitted in Phase 1, talks delivered in Phase 4):
  PyCon DE, FOSDEM, SustainabilityCon, Textile Exchange, Première Vision Tech.
- **Podcast circuit.** Aim for 3 appearances on the Python (Talk Python To Me),
  sustainability (The Sustainability Story), and AI-tooling (Latent Space) podcasts.
  Each appearance gets a transcript hosted on the docs site.

### 4.5 Strategic partnerships (Weeks 14–16, ongoing)

- **EUDI Wallet reference projects.** Drop a one-paragraph PR to the EU eIDAS reference
  implementations adding dppvalidator as a recommended verifier for product-related
  credentials.
- **OpenSCM / Open Footprint / Catena-X.** Each of these has a DPP angle; one
  integration repo + a PR per project is enough.
- **fashion-for-good / Textile Exchange.** Listing as a tool partner.
- **Major fashion brands' tech blogs.** Where ARTISO's existing relationships allow,
  ghost-write or co-write a "we used dppvalidator" case study.

### Exit criteria

- ≥ 1 listing in an official UN/CEFACT or EU DPP-WG document.
- ≥ 2 external plugin packages published by non-ARTISO contributors.
- ≥ 3 conference talks delivered with recordings hosted on docs site.
- KPI: ≥ 3,000 PyPI downloads in the trailing 30 days; ≥ 350 GitHub stars; ≥ 5 external
  contributors.

______________________________________________________________________

## Phase 5 — Network effects (Weeks 17–26)

> The point at which we are not pushing growth so much as removing friction from growth
> we already have. If Phase 4 succeeded, Phase 5 is mostly *enabling* others to build on
> top of dppvalidator.

### 5.1 Hosted services (optional)

Prerequisite: ≥ 5,000 monthly downloads and ≥ 3 inbound enterprise inquiries; otherwise
defer.

- **Hosted validation API** at `https://api.dppvalidator.io/` (subdomain, not the
  ARTISO root domain — keeps brands neutral). Free tier 1k requests/day, paid above.
- **Conformance dashboard** (multi-tenant) for brands' supplier networks — same
  validation engine, sold as a thin SaaS skin.
- These exist primarily to **fund** the OSS work and to absorb enterprise demand
  cleanly; they do not change the OSS core.

### 5.2 JS / WASM port (Weeks 20–26)

Now justified by usage:

- **`@artiso-ai/dppvalidator` npm package** with the same surface area as the Python
  CLI/API. Implementation: compile the Python core to WASM via Pyodide, or hand-port
  the stable subset (schema + model + JSON-LD layers). Go with WASM first for time to
  market; switch to a native port only if WASM bundle size becomes a blocker.
- **Browser SDK + Web Component** `<dpp-validator>` for embedding in product pages.
- **TypeScript types generated from Pydantic models** via `datamodel-code-generator`
  + a small post-processor. Single source of truth stays in Python.

### 5.3 Marketplace presences

- **Cloudflare Workers / Vercel Edge / Deno Deploy** templates that wrap the WASM
  build into a one-click hosted validator.
- **AWS Marketplace / GCP Marketplace** SaaS listings of the hosted service (only if
  Phase 5.1 ships).
- **Salesforce / Shopify / Adobe Commerce app stores** wrapping the MCP server.

### 5.4 Standards body engagement

By Phase 5 we should have earned a seat at the table:

- Active participation in UN/CEFACT UNTP working group (track with a public
  [`docs/standards/untp-engagement-log.md`](standards/)).
- Submit RFCs / issues to UNTP-DPP and CIRPASS-2 repos based on real-world bugs we
  catch in fixtures.
- Sponsor a CIRPASS-2 plugfest if budget allows.

### Exit criteria

- ≥ 10,000 monthly PyPI downloads.
- npm package crosses 1k weekly downloads.
- dppvalidator referenced as the canonical Python implementation in ≥ 1 standards-body
  document.
- ≥ 1 ARTISO contributor on a UN/CEFACT or EU DPP-WG editorial team.

______________________________________________________________________

## Phase 6 — Cadence (continuous)

> What we keep doing forever, not phase-bound.

### Release rhythm

- **Patch release every 2 weeks** for the first 6 months of this plan; **monthly**
  thereafter unless a security/conformance fix forces faster.
- **Every release ships:**
  - Conventional-commit changelog (already in place).
  - Updated `llms-ctx.txt` snapshot.
  - Migration notes if any wire-shape semantics changed.
  - One tweet-length announcement per release, posted to
    Mastodon/Bluesky/LinkedIn from the
    `@artisoai` accounts. (No Twitter/X amplification — the audience is mostly EU,
    LinkedIn pulls 10× the click-through.)

### Maintenance commitments (advertised)

Publish in [`SECURITY.md`](../SECURITY.md) and [`CONTRIBUTING.md`](../CONTRIBUTING.md):

- Security fix SLA: **48h triage, 7-day patch** for high-severity.
- Spec-tracking SLA: **30 days** from a UNTP/CIRPASS minor release to a dppvalidator
  release with full support.
- Python version policy: support last 3 minor versions; drop with one full release of
  warning.

### Telemetry (opt-in)

- An **opt-in** anonymous usage ping (`DPPVALIDATOR_TELEMETRY=1`) so we know which
  layers and versions are actually used in the wild. Defaulted to *off*; users opt in
  during `dppvalidator init`. Without telemetry we are guessing on what to deprecate.

______________________________________________________________________

## Risk register

| Risk                                                                  | P  | Impact | Mitigation                                                                                  |
| --------------------------------------------------------------------- | -- | ------ | ------------------------------------------------------------------------------------------- |
| UNTP 1.0 ships breaking changes mid-plan                              | M  | H      | Existing detection layer + compat shims; treat as scheduled work in Phase 4                  |
| Anthropic plugin marketplace approval slow / rejected                 | L  | M      | Self-hosted marketplace (Phase 2.2) ships *first*; official listing is amplification         |
| Competitor lands a hosted SaaS with marketing budget                  | M  | M      | The OSS + agent-native moat is the answer; don't compete on SaaS until Phase 5               |
| MCP protocol changes break our server                                 | M  | M      | Pin `mcp` SDK floor; add an integration test that runs against the latest Claude Desktop      |
| Plugin maintainer burnout (one-person Tyre/Textile pack)              | H  | M      | Governance doc states maintainer SLA; auto-archive plugins not updated in 6 months           |
| GPL-3.0 contamination via a careless plugin import                    | L  | H      | [`/.claude/rules/plugin-licenses.md`](../.claude/rules/plugin-licenses.md) already enforced; add CI check |
| Conformance report exposes embarrassing failures                      | M  | L      | Publish the report **with** the failures and a fix ETA. Transparency wins faster than hiding |

______________________________________________________________________

## How this plan relates to other planning documents

| Document                                                          | Scope                                              |
| ----------------------------------------------------------------- | -------------------------------------------------- |
| [`STRATEGIC_ROADMAP.md`](STRATEGIC_ROADMAP.md)                    | Capability roadmap (what we *build*)               |
| [`IMPROVEMENT_ROADMAP.md`](IMPROVEMENT_ROADMAP.md)                | Technical gap closure (what we *fix*)              |
| [`REFACTORING_PLAN.md`](REFACTORING_PLAN.md)                      | Internal architecture work                         |
| [`UNTTP_PLUGIN_PLAN.md`](UNTTP_PLUGIN_PLAN.md)                    | Single-plugin tactical plan (textiles)             |
| [`VC_WALLET_ROADMAP.md`](VC_WALLET_ROADMAP.md)                    | Wallet-readiness sub-roadmap                       |
| `docs/plans/CIRPASS_2_MIGRATION.md`                               | One-shot migration plan                            |
| **`docs/GROWTH_PLAN.md` (this document)**                         | Reach, distribution, adoption — the *who* and *how it spreads* |

Capability work and growth work compete for the same maintainer-week. When forced to
choose: ship the capability work that *unlocks* a growth phase (e.g. UNTP 1.0 support
unlocks Phase 4.1 conformance), and *defer* the capability work that doesn't. This plan
exists so we know which is which.

______________________________________________________________________

## Appendix A — Phase summary at a glance

| Phase | Window      | Theme                       | Headline deliverable                                  | KPI gate (cumulative)      |
| ----- | ----------- | --------------------------- | ----------------------------------------------------- | -------------------------- |
| 0     | Week 0      | Instrumentation             | KPI dashboard + repo hygiene                          | Baseline captured          |
| 1     | Weeks 1–3   | Discoverability             | Comparison page, GitHub Action, Conda-Forge, Docker   | 400 dl/mo, 25 stars        |
| 2     | Weeks 4–6   | Agent-native distribution   | MCP server + Claude Code plugin in marketplaces       | 750 dl/mo, 50 stars        |
| 3     | Weeks 7–10  | Integration & onramps       | 5+ reference apps, SARIF Action, Pyodide playground   | 1,500 dl/mo, 150 stars     |
| 4     | Weeks 11–16 | Authority & community       | UN/CEFACT listing, vertical plugins, conf talks       | 3,000 dl/mo, 350 stars     |
| 5     | Weeks 17–26 | Network effects             | npm/WASM, hosted API (optional), standards seat       | 10,000 dl/mo, 600+ stars   |
| 6     | Continuous  | Cadence                     | Bi-weekly → monthly releases, telemetry, SLA          | Sustained                  |

______________________________________________________________________

## Appendix B — Suggested first commits (Week 0)

These are the smallest possible motions that move the plan from doc to action.
Each is < 1 hour:

1. **PR `chore(repo): expand topics, rewrite GitHub description and social preview`** —
   pure metadata, no code.
2. **PR `docs(plan): add growth plan and link from STRATEGIC_ROADMAP`** — this file +
   one paragraph in `STRATEGIC_ROADMAP.md`.
3. **PR `feat(cli): emit Claude Code install hint when CLAUDECODE=1`** — 8 lines in
   `src/dppvalidator/cli/__init__.py`. Tied off by Phase 2.3 once the plugin is
   marketplace-listed; the hint until then is a no-op (no plugin to install) but the
   wiring is ready.
4. **PR `chore(pyproject): expand keywords for agent / MCP discoverability`** — extend
   the keyword list in [`pyproject.toml`](../pyproject.toml).
5. **Issue `meta: track Phase 0 KPI baseline`** opened with the table from
   §"Executive summary" embedded.

Once these five land, every subsequent phase has a hook to attach to.
