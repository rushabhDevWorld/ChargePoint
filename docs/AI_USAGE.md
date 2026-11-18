# AI Tool Usage

## 1. Tools

| Tool | How I used it |
|------|---------------|
| **Claude** (chat) | [Project scaffolding, first drafts of the service, tests, dashboard and docs; discussing the data model and scaling options] |
| [GitHub Copilot / ChatGPT / other] | [e.g. inline completion while editing, quick syntax questions] |

## 2. Where AI helped most

| Task | How it helped |
|------|---------------|
| Boilerplate | Project layout, Dockerfile, docker-compose, CI workflow |
| Tests | First set of API and scoring test cases, which I then extended |
| Library syntax | SQLAlchemy 2.0 style models and aggregate queries, Pydantic v2 validation |
| Dashboard | First draft of the HTML/JS page and the inline-SVG trend chart |
| Seed data | Script that generates a realistic mix of healthy and flaky stations |
| Documentation | First draft of the design doc structure and Mermaid diagrams |

## 3. Where AI struggled or needed human work

| Area | What happened | What I did |
|------|---------------|------------|
| Time zones | SQLite returns naive datetimes, Postgres returns aware ones, so comparing report times broke | Added an explicit UTC conversion (`_as_utc`) and a test for out-of-order reports |
| Scoring weights | AI suggested plausible numbers but had no real data behind them | Chose the weights and threshold myself and documented that they are untuned |
| Scope | First drafts kept adding extras (auth, caching, more endpoints) | Cut them and described them in the design doc instead |
| Security in the UI | Easy to render device-supplied IDs with `innerHTML` | Switched to `textContent` and DOM building |
| Generic docs | Design doc text was too generic at first | Rewrote the parts to match what the code really does |
| [add your own] | [what went wrong] | [how you fixed it] |

## 4. Workflow

1. **Decide first.** I chose the tables, endpoints and rules before prompting.
2. **Small prompts.** One piece at a time (a model, a function, a test file), not the whole app.
3. **Review.** Read the output, rename things, remove what I don't need.
4. **Verify.** Run the tests and try the API and dashboard by hand.
5. **Commit small.** So the history shows what changed and why.


## 5. Rough split

| Area | AI-generated (then reviewed) | Written or heavily changed by me |
|------|------------------------------|----------------------------------|
| Application code (`app/`) | [~60%] | [~40%] |
| Tests | [~70%] | [~30%] |
| Dashboard | [~80%] | [~20%] |
| Docker / CI | [~90%] | [~10%] |
| Docs | [~50%] | [~50%] |

These are estimates, not measurements.


## 6. Trade-offs (summary)

AI made the first 80% fast, but the remaining 20% (edge cases, decisions, verification)
is where engineering judgement matters, and that is where I spent my time. More detail
is in section 10 of [DESIGN.md](DESIGN.md).
