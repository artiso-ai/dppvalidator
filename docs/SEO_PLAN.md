# SEO Improvement Plan for dppvalidator Documentation

**Goal:** Improve documentation discoverability on search engines and social.

______________________________________________________________________

## Phase 1: Foundation (Low Effort, High Impact)

### 1.1 Enable Sitemap Generation

Add to `mkdocs.yml` plugins:

```yaml
plugins:
  - sitemap
```

**Dependency:** `pip install mkdocs-sitemap-plugin` (add to docs group)

### 1.2 Create robots.txt

Create `docs/robots.txt`:

```text
User-agent: *
Allow: /
Sitemap: https://artiso-ai.github.io/dppvalidator/sitemap.xml
```

### 1.3 Add Social Links

Update `mkdocs.yml` extra.social:

```yaml
extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/artiso-ai/dppvalidator
    - icon: fontawesome/brands/python
      link: https://pypi.org/project/dppvalidator/
    - icon: fontawesome/brands/linkedin
      link: https://es.linkedin.com/company/artiso-ai
    - icon: fontawesome/solid/globe
      link: https://artiso.ai/
```

______________________________________________________________________

## Phase 2: Meta & Open Graph (Medium Effort)

### 2.1 Add Meta Plugin

```yaml
plugins:
  - meta
```

### 2.2 Add Page-Level Descriptions

Update key pages with front matter:

**index.md:**

```yaml
---
description: Validate EU Digital Product Passports with Python. 80k ops/sec.
---
```

**getting-started/quickstart.md:**

```yaml
---
description: Get started with dppvalidator in 5 minutes.
---
```

**guides/cli-usage.md:**

```yaml
---
description: CLI reference for validating and exporting DPPs.
---
```

### 2.3 Configure Open Graph Defaults

```yaml
extra:
  meta:
    - property: og:type
      content: website
    - property: og:site_name
      content: dppvalidator
    - name: twitter:card
      content: summary
```

______________________________________________________________________

## Phase 3: Social Cards (Optional, Higher Effort)

### 3.1 Enable Social Card Generation

```yaml
plugins:
  - social
```

**Note:** Requires Cairo/Pango system libraries. On macOS: `brew install cairo pango`

______________________________________________________________________

## Implementation Checklist

- [x] Add `mkdocs-sitemap-plugin` to pyproject.toml docs group ✅ (2026-01-30)
- [x] Add sitemap plugin to mkdocs.yml ✅ (2026-01-30)
- [x] Create docs/robots.txt ✅ (2026-01-30)
- [x] Add LinkedIn and artiso.ai to social links ✅ (2026-01-30)
- [x] Add meta plugin to mkdocs.yml ✅ (2026-01-30)
- [x] Add meta description to index.md ✅ (2026-01-30)
- [x] Add meta description to quickstart.md ✅ (2026-01-30)
- [x] Add meta description to cli-usage.md ✅ (2026-01-30)
- [x] Add social plugin to mkdocs.yml ✅ (2026-01-30)
- [x] Add pillow and cairosvg to pyproject.toml docs group ✅ (2026-01-30)
- [ ] Test build locally: `uv sync --group docs && uv run mkdocs build`

______________________________________________________________________

## Expected Outcomes

| Metric          | Before     | After             |
| --------------- | ---------- | ----------------- |
| Sitemap         | ❌ None    | ✅ Auto-generated |
| Social previews | ❌ Generic | ✅ Rich metadata  |
| LinkedIn link   | ❌ Missing | ✅ Present        |
| Google indexing | ⚠️ Partial | ✅ Complete       |
