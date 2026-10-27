# Day Trader Skill (installiert 2026-10-27)

Quelle: https://github.com/Jakeschincariol/day-trader-skill (MIT, Commit 3d0f4ef)
Installiert als projekt-lokale Skills unter `.claude/skills/trader-*` → verfügbar lokal (Mac) und in Cloud-Sessions.

Befehle: `/trader-scanner`, `/trader-news`, `/trader-entry`, `/trader-exit`, `/trader-timemachine`,
`/trader-risk`, `/trader-budget`, `/trader-broker`, `/trader-alerts`, `/trader-analyst`, `/trader-pelosi`.

Ablauf einer Trade-Idee: scanner → news → entry → exit → timemachine → budget → risk → broker.
Ausgaben landen in `trader/` im Projekt.

Hinweise:
- Python ≥ 3.8, nur Standardbibliothek. Daten: Yahoo Finance, Nasdaq Trader, SEC EDGAR, House Clerk.
- SEC-Tools brauchen `SEC_USER_AGENT="Name email"` (Env-Variable) oder `trader/config.json`.
- `/trader-pelosi` nutzt `pdftotext` (poppler) zum Lesen der PDFs.
- `/trader-broker` setzt Alpaca-MCP voraus, Paper-Trading ist Standard. API-Keys **nur** als Env/`.env`, nie ins Repo.
- In der Cloud-Session ggf. Netzwerkfreigabe für query1/query2.finance.yahoo.com, sec.gov, nasdaqtrader.com, disclosures-clerk.house.gov nötig.
- Keine Anlageberatung.
